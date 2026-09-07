"""Experiment Supervisor v0。

所有训练实验必须经由本模块启动：验证配置 → 生成 ID → 采集环境 → 监督
subprocess → 分类终态 → 按 result_schema 写入 raw result → 原子 finalize。
失败与成功同样产出完整 result；OOM 未验证可靠识别，绝不猜测。
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import yaml

from . import artifacts as artifacts_mod
from . import environment as env_mod
from . import schema
from .ids import generate_experiment_id

__all__ = [
    "ConfigValidationError",
    "generate_experiment_id",
    "load_and_validate_config",
    "run_experiment",
]

REQUIRED_SECTIONS = ("experiment", "model", "dataset", "training", "monitoring",
                     "output")
VALID_METHODS = ("full", "lora", "qlora")


class ConfigValidationError(Exception):
    """配置未通过 preflight 验证。"""


def load_and_validate_config(config_path: Path | str) -> dict:
    path = Path(config_path)
    if not path.is_file():
        raise ConfigValidationError(f"配置文件不存在：{path}")
    try:
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigValidationError(f"YAML 解析失败：{exc}") from exc
    if not isinstance(config, dict):
        raise ConfigValidationError("配置必须是 YAML 映射")
    for section in REQUIRED_SECTIONS:
        if section not in config:
            raise ConfigValidationError(f"配置缺少必需段：{section}")
    if not config["model"].get("id"):
        raise ConfigValidationError(
            "model.id 为空：正式运行前必须填入经操作者验证的模型身份（preflight 规则）"
        )
    training = config["training"]
    if training.get("method") not in VALID_METHODS:
        raise ConfigValidationError(
            f"training.method 必须是 {'/'.join(VALID_METHODS)}，"
            f"得到 {training.get('method')!r}"
        )
    for field in ("micro_batch_size", "gradient_accumulation_steps",
                  "sequence_length", "seed"):
        value = training.get(field)
        if not isinstance(value, int) or value < 0:
            raise ConfigValidationError(
                f"training.{field} 必须为非负整数，得到 {value!r}"
            )
    if training["method"] in ("lora", "qlora"):
        lora = training.get("lora") or {}
        if not isinstance(lora.get("rank"), int) or lora["rank"] <= 0:
            raise ConfigValidationError("LoRA/QLoRA 要求 lora.rank 为正整数")
        if not lora.get("target_modules"):
            raise ConfigValidationError("LoRA/QLoRA 要求 lora.target_modules 非空")
    if training["method"] == "qlora":
        bits = (training.get("quantization") or {}).get("bits")
        if not isinstance(bits, int) or bits <= 0:
            raise ConfigValidationError(
                "QLoRA 要求 quantization.bits 为正整数（schema 不变量：无量化元数据的 QLoRA 必须拒绝）"
            )
    output = config["output"]
    if not output.get("raw_root"):
        raise ConfigValidationError("output.raw_root 不能为空")
    return config


def _classify(returncode: int | None, stderr_text: str, exc: BaseException | None,
              killed_by_timeout: bool) -> dict:
    """据真实退出证据分类；OOM 无可靠识别方法，不猜。"""
    if killed_by_timeout:
        return {"terminal_state": "timeout", "exit_code": None, "signal": "SIGKILL",
                "error_type": "TimeoutExpired",
                "error_message": "子进程超过 timeout 上限，被 SIGKILL 终止",
                "classification_evidence":
                    "supervisor 在 wait(timeout) 抛出 subprocess.TimeoutExpired 后 kill()"}
    if exc is not None:
        if isinstance(exc, FileNotFoundError):
            return {"terminal_state": "dependency_error", "exit_code": None,
                    "signal": None, "error_type": "FileNotFoundError",
                    "error_message": str(exc),
                    "classification_evidence": "可执行文件不存在（启动失败）"}
        return {"terminal_state": "unknown_failure", "exit_code": None,
                "signal": None, "error_type": type(exc).__name__,
                "error_message": str(exc),
                "classification_evidence": "supervisor 捕获的未预期异常"}
    if returncode == 0:
        return {"terminal_state": "success", "exit_code": 0, "signal": None,
                "error_type": None, "error_message": None,
                "classification_evidence": None}
    if returncode is not None and returncode < 0:
        signum = -returncode
        name = signal.Signals(signum).name
        state = ("user_interrupted" if signum == signal.SIGINT
                 else "runtime_error")
        return {"terminal_state": state, "exit_code": None, "signal": name,
                "error_type": f"Signal:{name}",
                "error_message": f"子进程被信号 {name}({signum}) 终止",
                "classification_evidence": f"returncode={returncode}"}
    match = re.search(r"(ModuleNotFoundError|ImportError)[^\n]*", stderr_text or "")
    if match:
        return {"terminal_state": "dependency_error", "exit_code": returncode,
                "signal": None, "error_type": "ImportError",
                "error_message": match.group(0)[:500],
                "classification_evidence": "stderr 中存在明确的 ImportError 证据"}
    return {"terminal_state": "runtime_error", "exit_code": returncode,
            "signal": None, "error_type": "NonZeroExitCode",
            "error_message": (stderr_text or "").strip()[-500:] or None,
            "classification_evidence": f"returncode={returncode}，非零且无更具体证据"}


def _measurement_from_swap(value, timestamp):
    return schema.measurement(
        value=value, unit="bytes",
        source="sysctl -n vm.swapusage（used，MB 两位小数换算）",
        status="measured" if value is not None else "unavailable",
        sample_time_utc=timestamp,
        notes="源输出为 MB 两位小数，按 1024×1024 换算为字节" if value is not None
        else "sysctl vm.swapusage 不可用",
        raw_artifact_path="environment/raw_environment.txt")


def _vm_measurement(snapshot: dict, timestamp: str, phase: str):
    return schema.measurement(
        value={"page_size_bytes": snapshot["page_size"],
               "counters_pages": snapshot["counters"]},
        unit="pages/count",
        source="vm_stat",
        status="measured" if snapshot["raw"] else "unavailable",
        sample_time_utc=timestamp,
        notes=None if snapshot["raw"] else "vm_stat 输出不可用",
        raw_artifact_path=f"environment/vm_stat_{phase}.txt")


def _power_measurement(value, timestamp):
    return schema.measurement(
        value=value, unit="enum", source="pmset -g batt",
        status="measured" if value else "unavailable",
        sample_time_utc=timestamp,
        notes=None if value else "pmset 输出不可用",
        raw_artifact_path="environment/raw_environment.txt")


def run_experiment(config_path: Path | str, command: list[str],
                   timeout_seconds: float | None = None) -> Path:
    config = load_and_validate_config(config_path)
    experiment_id = generate_experiment_id(config)

    raw_root = Path(config["output"]["raw_root"]).resolve()
    raw_root.mkdir(parents=True, exist_ok=True)
    final_dir = raw_root / experiment_id
    if final_dir.exists():
        raise RuntimeError(
            f"raw result 目录已存在，拒绝覆盖（不可变策略）：{final_dir}"
        )
    staging = raw_root / f".{experiment_id}.staging"
    if staging.exists():
        shutil.rmtree(staging)  # 上次崩溃的半成品，协议允许重做
    (staging / "logs").mkdir(parents=True)
    (staging / "environment").mkdir()

    # ---- 静态 artifact：配置 / 命令 / 生效配置 ----
    config_copy = staging / "config.yaml"
    shutil.copyfile(config_path, config_copy)
    working_directory = os.getcwd()
    command_record = {
        "argv": list(command),
        "display": shlex.join(command),
        "working_directory": working_directory,
        "timeout_seconds": timeout_seconds,
    }
    (staging / "command.txt").write_text(
        json.dumps(command_record, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    effective = staging / "effective_config.json"
    effective.write_text(
        json.dumps(config, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8")
    config_digest = schema.config_sha256(config)

    # ---- 环境 preflight 采集 ----
    monitoring = config.get("monitoring", {})
    git = env_mod.collect_git_provenance()
    software = env_mod.collect_software()
    hardware = env_mod.collect_hardware()
    filesystem = env_mod.collect_filesystem(raw_root)
    before_ts = env_mod.utc_now()
    vm_before = (env_mod.collect_vm_stat()
                 if monitoring.get("capture_vm_stat", True)
                 else {"raw": None, "page_size": None, "counters": {}})
    swap_before_value, swap_before_raw = (
        env_mod.collect_swap_bytes()
        if monitoring.get("capture_swap_usage", True) else (None, None))
    power_before_value, power_before_raw = (
        env_mod.collect_power_source()
        if monitoring.get("capture_power_source", True) else (None, None))

    if vm_before["raw"]:
        (staging / "environment" / "vm_stat_before.txt").write_text(
            vm_before["raw"], encoding="utf-8")

    # ---- 执行子进程 ----
    stdout_path = staging / "logs" / "stdout.log"
    stderr_path = staging / "logs" / "stderr.log"
    start_utc = None
    wall = None
    killed_by_timeout = False
    caught: BaseException | None = None
    returncode: int | None = None
    monotonic_start = time.monotonic()
    try:
        with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
            start_utc = env_mod.utc_now()
            child_env = {**os.environ,
                         "BENCH_EXPERIMENT_ARTIFACTS_DIR": str(staging)}
            proc = subprocess.Popen(command, stdout=out, stderr=err,
                                    cwd=working_directory, env=child_env)
            try:
                returncode = proc.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                killed_by_timeout = True
                proc.kill()
                proc.wait()
    except KeyboardInterrupt as exc:  # 操作者中断
        caught = exc
    except FileNotFoundError as exc:
        caught = exc
    except OSError as exc:
        caught = exc
    wall = time.monotonic() - monotonic_start
    end_utc = env_mod.utc_now()

    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace") \
        if stderr_path.exists() else ""
    classification = _classify(returncode, stderr_text, caught, killed_by_timeout)
    training_metrics = _load_json_tolerant(staging / "training_metrics.json")

    # ---- 终态快照 ----
    after_ts = env_mod.utc_now()
    vm_after = (env_mod.collect_vm_stat()
                if monitoring.get("capture_vm_stat", True)
                else {"raw": None, "page_size": None, "counters": {}})
    swap_after_value, swap_after_raw = (
        env_mod.collect_swap_bytes()
        if monitoring.get("capture_swap_usage", True) else (None, None))
    power_after_value, power_after_raw = (
        env_mod.collect_power_source()
        if monitoring.get("capture_power_source", True) else (None, None))
    if vm_after["raw"]:
        (staging / "environment" / "vm_stat_after.txt").write_text(
            vm_after["raw"], encoding="utf-8")

    # ---- raw environment evidence（脱敏） ----
    sp_raw = env_mod._hardware_snapshot_cached().get("sp_raw")
    evidence = [
        "# 环境 preflight 证据（由 supervisor 采集）",
        f"# 采集时间: {before_ts}",
        "## git rev-parse HEAD", git["git_commit_sha"] or "(不可用)",
        "## git status --porcelain=v1", git["git_status_porcelain"] or "(干净)",
        "## sw_vers", _sw_vers_text(software),
        "## python", f"{software['python_implementation']} {sys.version}",
        "## system_profiler SPHardwareDataType（序列号已脱敏）",
        env_mod.redact_hardware_json(sp_raw),
        "## df -kP <raw_root>", f"filesystem={filesystem['filesystem']} "
        f"free_bytes={filesystem['free_disk_bytes']}",
        "## vm_stat (before)", vm_before["raw"] or "(未启用/不可用)",
        "## sysctl vm.swapusage (before)", swap_before_raw or "(未启用/不可用)",
        "## pmset -g batt (before)", power_before_raw or "(未启用/不可用)",
        "## vm_stat (after)", vm_after["raw"] or "(未启用/不可用)",
        "## sysctl vm.swapusage (after)", swap_after_raw or "(未启用/不可用)",
        "## pmset -g batt (after)", power_after_raw or "(未启用/不可用)",
    ]
    env_evidence = staging / "environment" / "raw_environment.txt"
    env_evidence.write_text("\n\n".join(evidence) + "\n", encoding="utf-8")

    # ---- 组装 result ----
    result = _build_result(
        config=config, experiment_id=experiment_id, command=command,
        working_directory=working_directory, config_digest=config_digest,
        git=git, software=software, hardware=hardware,
        filesystem=filesystem, monitoring=monitoring,
        start_utc=start_utc, end_utc=end_utc, wall=wall,
        before_ts=before_ts, after_ts=after_ts,
        vm_before=vm_before, vm_after=vm_after,
        swap_before_value=swap_before_value, swap_after_value=swap_after_value,
        power_before_value=power_before_value,
        power_after_value=power_after_value,
        classification=classification, staging=staging,
        training_metrics=training_metrics,
    )
    (staging / "result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return artifacts_mod.finalize(staging, final_dir)


def _sw_vers_text(software: dict) -> str:
    return (f"ProductVersion={software['macos_version']} "
            f"BuildVersion={software['macos_build']}")


def _load_json_tolerant(path: Path) -> dict | None:
    """子进程产出的 metrics 容错读取：不存在/损坏一律 None，不影响主流程。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _build_result(*, config, experiment_id, command, working_directory,
                  config_digest, git, software, hardware, filesystem,
                  monitoring, start_utc, end_utc, wall, before_ts, after_ts,
                  vm_before, vm_after, swap_before_value, swap_after_value,
                  power_before_value, power_after_value, classification,
                  staging, training_metrics=None) -> dict:
    model_section, dataset_section = schema.build_model_dataset_sections(config)
    exp_cfg = config["experiment"]

    software_section = {
        **software,
        "lockfile": schema.artifact_ref(
            "uv.lock", size_bytes=None, sha256=None, media_type="text/plain")
        if (env_mod.REPO_ROOT / "uv.lock").exists() else None,
        "package_snapshot": None,  # v0 未采集 pip freeze 快照
        "git_commit_sha": git["git_commit_sha"],
        "git_dirty": git["git_dirty"],
        "git_patch": None,
        "libraries": {"pyyaml": _dist("pyyaml"),
                      "huggingface_hub": _dist("huggingface-hub")},
        "environment_allowlist": {},
        "raw_environment_artifact": schema.artifact_ref(
            "environment/raw_environment.txt",
            size_bytes=(staging / "environment" / "raw_environment.txt").stat().st_size,
            media_type="text/plain"),
    }

    runtime_section = {
        "start_time_utc": start_utc,
        "end_time_utc": end_utc,
        "wall_clock_seconds": wall,
        "model_load_seconds": None,
        "training_loop_seconds": None,
        "successful_steps": None,
        "attempted_micro_steps": None,
        "measured_steps": None,
        "excluded_warmup_steps": None,
        "average_step_time_seconds": None,
        "median_step_time_seconds": None,
        "tokens_processed": None,
        "token_count_definition": None,
        "tokens_per_second": None,
        "samples_processed": None,
        "samples_per_second": None,
        "throughput_interval_definition": None,
        "peak_process_memory_bytes": schema.unresolved(
            "bytes", "/usr/bin/time -l candidate",
            "计数器语义未验证，v0 不启用；不可用不是 0"),
        "peak_system_memory_bytes": schema.unresolved(
            "bytes", None, "系统级峰值内存无已验证的聚合定义"),
        "initial_system_memory": _vm_measurement(vm_before, before_ts, "before"),
        "initial_swap_bytes": _measurement_from_swap(
            swap_before_value, before_ts),
        "peak_swap_bytes": schema.unresolved(
            "bytes", "sampled sysctl vm.swapusage",
            "v0 无周期采样，仅 before/after 快照，峰值不可得"),
        "process_page_faults": schema.unresolved(
            "count", "/usr/bin/time -l candidate", "计数器语义未验证"),
        "process_page_reclaims": schema.unresolved(
            "count", "/usr/bin/time -l candidate", "计数器语义未验证"),
        "system_vm_counters_before": _vm_measurement(vm_before, before_ts, "before"),
        "system_vm_counters_after": _vm_measurement(vm_after, after_ts, "after"),
        "energy_joules": schema.unresolved(
            "joules", None,
            "无校准外部计量方法；powermetrics 估计不得写入本字段"),
        "thermal_state_before": schema.unresolved(
            "enum", "Foundation helper candidate", "未验证，不猜"),
        "thermal_state_peak": schema.unresolved(
            "enum", "Foundation helper candidate", "未验证，不猜"),
        "power_source_before": _power_measurement(
            power_before_value, before_ts),
        "power_source_after": _power_measurement(
            power_after_value, after_ts),
        "monitoring_interval_seconds": monitoring.get("interval_seconds"),
        "monitoring_overhead_validated": False,
        "step_timing_artifact": None,
        "system_monitor_artifact": None,
    }

    status_section = {
        **classification,
        "error_phase": None,
        "result_complete": True,
    }

    def log_ref(name: str) -> dict:
        path = staging / "logs" / name
        return schema.artifact_ref(f"logs/{name}",
                                   size_bytes=path.stat().st_size,
                                   media_type="text/plain")

    artifacts_section = {
        "stdout_log": log_ref("stdout.log"),
        "stderr_log": log_ref("stderr.log"),
        "config": schema.artifact_ref(
            "config.yaml",
            size_bytes=(staging / "config.yaml").stat().st_size,
            media_type="text/yaml"),
        "effective_config": schema.artifact_ref(
            "effective_config.json",
            size_bytes=(staging / "effective_config.json").stat().st_size,
            media_type="application/json"),
        "command": schema.artifact_ref(
            "command.txt", size_bytes=(staging / "command.txt").stat().st_size,
            media_type="application/json"),
        "environment_directory": schema.artifact_ref(
            "environment", size_bytes=None, media_type="inode/directory"),
        "checkpoints": [],
        "additional": [],
        "manifest_sha256_path": "manifest.sha256",
        "manifest_sha256": None,  # 自引用问题：按 schema 存外部/追加式索引，v0 未建
    }

    hardware_section = {
        **hardware,
        "machine_id": None,
        "machine_id_method": None,
        "storage_type": None,  # SPStorageDataType 解析未验证
        "output_filesystem": filesystem["filesystem"],
        "free_disk_before_bytes": schema.measurement(
            value=filesystem["free_disk_bytes"], unit="bytes",
            source="df -kP <raw_root>",
            status="measured" if filesystem["free_disk_bytes"] is not None
            else "unavailable",
            sample_time_utc=before_ts,
            raw_artifact_path="environment/raw_environment.txt"),
    }

    # ---- 子进程 training_metrics 回填（存在且类型合法才覆盖，否则保持 null） ----
    tm = training_metrics or {}

    def tm_num(name: str):
        value = tm.get(name)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return value
        return None

    def tm_str(name: str):
        value = tm.get(name)
        return value if isinstance(value, str) else None

    for key in ("model_load_seconds", "training_loop_seconds",
                "successful_steps", "attempted_micro_steps", "measured_steps",
                "excluded_warmup_steps", "average_step_time_seconds",
                "median_step_time_seconds", "tokens_processed",
                "tokens_per_second", "samples_processed", "samples_per_second"):
        if tm_num(key) is not None:
            runtime_section[key] = tm_num(key)
    for key in ("token_count_definition", "throughput_interval_definition"):
        if tm_str(key) is not None:
            runtime_section[key] = tm_str(key)
    step_timing = staging / "step_timings.jsonl"
    if step_timing.is_file():
        runtime_section["step_timing_artifact"] = schema.artifact_ref(
            "step_timings.jsonl", size_bytes=step_timing.stat().st_size,
            media_type="application/x-ndjson")

    metrics_section = schema.build_metrics_section()
    if tm_num("training_loss_final") is not None:
        metrics_section["training_loss_final"] = tm_num("training_loss_final")

    training_section = schema.build_training_section(config)
    trainable = tm_num("trainable_parameters")
    total = tm_num("total_parameters")
    if trainable is not None:
        training_section["trainable_parameters"] = int(trainable)
    if total is not None:
        training_section["total_parameters"] = int(total)
    if trainable is not None and total:
        training_section["trainable_parameter_ratio"] = trainable / total

    for key in ("parameter_count_method", "quantization_state",
                "quantization_scheme", "resolved_revision", "revision_source"):
        if tm_str(key) is not None:
            model_section[key] = tm_str(key)
    if tm_str("model_architecture") is not None:
        model_section["architecture"] = tm_str("model_architecture")
    quant_bits = tm.get("quantization_bits")
    if isinstance(quant_bits, int) and not isinstance(quant_bits, bool):
        model_section["quantization_bits"] = quant_bits
    parameter_count = tm.get("parameter_count")
    if isinstance(parameter_count, int) and not isinstance(parameter_count, bool):
        model_section["parameter_count"] = parameter_count

    return {
        "schema_version": schema.SCHEMA_VERSION,
        "protocol_version": schema.PROTOCOL_VERSION,
        "experiment": {
            "id": experiment_id,
            "created_at_utc": before_ts,
            "run_kind": exp_cfg.get("run_kind", "measured"),
            "comparison_group_id": exp_cfg.get("comparison_group_id"),
            "repeat_index": exp_cfg.get("repeat_index", 0),
            "supersedes_experiment_id": exp_cfg.get("supersedes_experiment_id"),
            "parent_experiment_id": exp_cfg.get("parent_experiment_id"),
            "sweep_dimensions": {},
            "exact_command_argv": list(command),
            "exact_command_display": shlex.join(command),
            "working_directory": working_directory,
            "config_path": "config.yaml",
            "effective_config_path": "effective_config.json",
            "config_sha256": config_digest,
            "conditions": schema.experiment_conditions(),
            "validity": {"protocol_valid": False, "performance_valid": False,
                         "exclusion_reasons": ["v0：最终验证器未实现"]},
        },
        "hardware": hardware_section,
        "software": software_section,
        "model": model_section,
        "dataset": dataset_section,
        "training": training_section,
        "runtime": runtime_section,
        "metrics": metrics_section,
        "status": status_section,
        "artifacts": artifacts_section,
    }


def _dist(name: str) -> str | None:
    import importlib.metadata
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None
