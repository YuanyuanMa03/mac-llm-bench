from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

import pytest
import yaml

from benchmark.supervisor import (
    ConfigValidationError,
    generate_experiment_id,
    load_and_validate_config,
    run_experiment,
)


REQUIRED_TOP_LEVEL = {
    "schema_version",
    "protocol_version",
    "experiment",
    "hardware",
    "software",
    "model",
    "dataset",
    "training",
    "runtime",
    "metrics",
    "status",
    "artifacts",
}

REQUIRED_RUNTIME = {
    "start_time_utc",
    "end_time_utc",
    "wall_clock_seconds",
    "model_load_seconds",
    "training_loop_seconds",
    "successful_steps",
    "attempted_micro_steps",
    "measured_steps",
    "excluded_warmup_steps",
    "average_step_time_seconds",
    "median_step_time_seconds",
    "tokens_processed",
    "token_count_definition",
    "tokens_per_second",
    "samples_processed",
    "samples_per_second",
    "throughput_interval_definition",
    "peak_process_memory_bytes",
    "peak_system_memory_bytes",
    "initial_system_memory",
    "initial_swap_bytes",
    "peak_swap_bytes",
    "process_page_faults",
    "process_page_reclaims",
    "system_vm_counters_before",
    "system_vm_counters_after",
    "energy_joules",
    "thermal_state_before",
    "thermal_state_peak",
    "power_source_before",
    "power_source_after",
    "monitoring_interval_seconds",
    "monitoring_overhead_validated",
    "step_timing_artifact",
    "system_monitor_artifact",
}


def _valid_config(raw_root: Path) -> dict:
    return {
        "experiment": {
            "run_kind": "warmup",
            "comparison_group_id": "supervisor-v0-tests",
            "repeat_index": 0,
            "parent_experiment_id": None,
            "supersedes_experiment_id": None,
            "tags": ["infrastructure-test"],
        },
        "model": {
            "id": "supervisor-v0-no-model",
            "provider": "local",
            "repository": None,
            "revision": None,
            "local_path": None,
            "tokenizer_id": None,
            "tokenizer_revision": None,
            "trust_remote_code": False,
        },
        "dataset": {
            "name": "supervisor-v0-no-dataset",
            "source": "local-infrastructure-test",
            "revision": None,
            "train_split": "train",
            "validation_split": None,
            "test_split": None,
            "local_paths": [],
            "data_files_sha256": None,
            "shuffle": False,
            "split_seed": 42,
            "preprocessing": {
                "field_mapping": None,
                "prompt_template": None,
                "normalization": None,
                "filtering": None,
                "deduplication": None,
                "packing": False,
                "truncation": True,
                "padding_side": "right",
                "add_special_tokens": True,
                "label_mask_policy": None,
            },
            "tokenizer": {"id": None, "revision": None, "use_fast": None},
            "max_sequence_length": 128,
        },
        "training": {
            "method": "lora",
            "seed": 42,
            "quantization": {"bits": None, "scheme": None, "group_size": None},
            "lora": {
                "rank": 4,
                "alpha": 8,
                "dropout": 0.0,
                "target_modules": ["supervisor_test_target"],
            },
            "trainable_layers": None,
            "micro_batch_size": 1,
            "gradient_accumulation_steps": 1,
            "sequence_length": 128,
            "learning_rate": 0.00001,
            "optimizer": {"name": "adamw", "parameters": None},
            "scheduler": {"name": "constant", "parameters": None},
            "warmup": {"steps": 0, "ratio": None},
            "max_steps": 1,
            "epochs": None,
            "stop_criteria": {"early_stopping": False},
            "gradient_checkpointing": False,
            "precision": {
                "parameter_dtype": None,
                "compute_dtype": None,
                "optimizer_state_dtype": None,
            },
            "evaluation_interval_steps": None,
            "checkpoint_interval_steps": None,
            "logging_interval_steps": 1,
            "resume_checkpoint": None,
        },
        "monitoring": {
            "enabled": True,
            "interval_seconds": 1.0,
            "capture_process_time_l": False,
            "capture_vm_stat": True,
            "capture_swap_usage": True,
            "capture_power_source": True,
            "capture_thermal_state": False,
            "capture_energy": False,
            "required_raw_logs": True,
            "fail_run_on_collector_error": False,
        },
        "output": {
            "raw_root": str(raw_root),
            "processed_root": str(raw_root.parent / "processed"),
            "figures_root": str(raw_root.parent / "figures"),
            "immutable_after_finalize": True,
            "write_sha256_manifest": True,
        },
    }


def _write_config(path: Path, raw_root: Path) -> dict:
    config = _valid_config(raw_root)
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return config


def _make_tree_writable(path: Path) -> None:
    if not path.exists():
        return
    for root, directories, files in os.walk(path):
        os.chmod(root, 0o700)
        for directory in directories:
            os.chmod(Path(root) / directory, 0o700)
        for filename in files:
            os.chmod(Path(root) / filename, 0o600)


def _read_result(result_dir: Path) -> dict:
    return json.loads((result_dir / "result.json").read_text(encoding="utf-8"))


def _assert_manifest_matches_files(result_dir: Path) -> None:
    manifest_path = result_dir / "manifest.sha256"
    entries = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        digest, relative_path = line.split("  ", 1)
        entries[relative_path] = digest

    actual_files = {
        path.relative_to(result_dir).as_posix()
        for path in result_dir.rglob("*")
        if path.is_file() and path != manifest_path
    }
    assert set(entries) == actual_files
    for relative_path, expected_digest in entries.items():
        actual_digest = hashlib.sha256((result_dir / relative_path).read_bytes()).hexdigest()
        assert actual_digest == expected_digest


def test_load_and_validate_config_rejects_missing_model_identity(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    config = _valid_config(tmp_path / "raw")
    config["model"]["id"] = None
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    with pytest.raises(ConfigValidationError, match=r"model\.id"):
        load_and_validate_config(config_path)


def test_generate_experiment_id_is_filename_safe_uuid7_and_factor_readable(tmp_path: Path) -> None:
    config = _valid_config(tmp_path / "raw")

    experiment_id = generate_experiment_id(config)

    assert re.fullmatch(r"[A-Za-z0-9_-]+", experiment_id)
    assert "__supervisor-v0-no-model__lora-qnone__ctx128__b1-ga1__r4__s42__" in experiment_id
    uuid_text = experiment_id.rsplit("__", 1)[1]
    assert re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", uuid_text)


def test_success_run_writes_schema_complete_immutable_raw_result(tmp_path: Path) -> None:
    config_path = tmp_path / "experiment.yaml"
    raw_root = tmp_path / "raw"
    _write_config(config_path, raw_root)

    result_dir = run_experiment(config_path, ["/usr/bin/true"])
    try:
        result = _read_result(result_dir)
        assert set(result) == REQUIRED_TOP_LEVEL
        assert set(result["runtime"]) == REQUIRED_RUNTIME
        assert result["status"]["terminal_state"] == "success"
        assert result["status"]["exit_code"] == 0
        assert result["status"]["result_complete"] is True
        assert result["experiment"]["exact_command_argv"] == ["/usr/bin/true"]
        assert result["runtime"]["wall_clock_seconds"] >= 0
        assert result["runtime"]["peak_process_memory_bytes"]["value"] is None
        assert result["runtime"]["energy_joules"]["value"] is None
        assert result["software"]["git_commit_sha"] == subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
        assert (result_dir / "logs/stdout.log").read_bytes() == b""
        assert (result_dir / "logs/stderr.log").read_bytes() == b""
        _assert_manifest_matches_files(result_dir)
        assert stat.S_IMODE(result_dir.stat().st_mode) & 0o222 == 0
        assert stat.S_IMODE((result_dir / "result.json").stat().st_mode) & 0o222 == 0
        assert not list(raw_root.glob(".*.staging"))
    finally:
        _make_tree_writable(result_dir)


def test_nonzero_exit_retains_stdout_stderr_and_runtime_error_result(tmp_path: Path) -> None:
    config_path = tmp_path / "experiment.yaml"
    raw_root = tmp_path / "raw"
    _write_config(config_path, raw_root)
    command = [
        sys.executable,
        "-c",
        "import sys; print('stdout evidence'); print('stderr evidence', file=sys.stderr); raise SystemExit(7)",
    ]

    result_dir = run_experiment(config_path, command)
    try:
        result = _read_result(result_dir)
        assert result["status"]["terminal_state"] == "runtime_error"
        assert result["status"]["exit_code"] == 7
        assert result["status"]["error_type"] == "NonZeroExitCode"
        assert result["status"]["result_complete"] is True
        assert (result_dir / "logs/stdout.log").read_text(encoding="utf-8") == "stdout evidence\n"
        assert (result_dir / "logs/stderr.log").read_text(encoding="utf-8") == "stderr evidence\n"
        _assert_manifest_matches_files(result_dir)
    finally:
        _make_tree_writable(result_dir)


def test_timeout_is_terminal_and_retains_result(tmp_path: Path) -> None:
    config_path = tmp_path / "experiment.yaml"
    raw_root = tmp_path / "raw"
    _write_config(config_path, raw_root)

    result_dir = run_experiment(
        config_path,
        [sys.executable, "-c", "import time; time.sleep(5)"],
        timeout_seconds=0.05,
    )
    try:
        result = _read_result(result_dir)
        assert result["status"]["terminal_state"] == "timeout"
        assert result["status"]["error_type"] == "TimeoutExpired"
        assert result["status"]["result_complete"] is True
        _assert_manifest_matches_files(result_dir)
    finally:
        _make_tree_writable(result_dir)


def test_git_provenance_recorded_in_result(tmp_path: Path) -> None:
    config_path = tmp_path / "experiment.yaml"
    _write_config(config_path, tmp_path / "raw")
    result_dir = run_experiment(config_path, ["/usr/bin/true"])
    try:
        result = _read_result(result_dir)
        assert re.fullmatch(r"[0-9a-f]{40}", result["software"]["git_commit_sha"])
        assert isinstance(result["software"]["git_dirty"], bool)
    finally:
        _make_tree_writable(result_dir)


def test_result_json_serializes_without_nan(tmp_path: Path) -> None:
    config_path = tmp_path / "experiment.yaml"
    _write_config(config_path, tmp_path / "raw")
    result_dir = run_experiment(config_path, ["/usr/bin/true"])
    try:
        text = (result_dir / "result.json").read_text(encoding="utf-8")
        json.loads(text, parse_constant=lambda c: (_ for _ in ()).throw(
            ValueError(f"non-finite constant: {c}")))
        json.dumps(json.loads(text), allow_nan=False)
    finally:
        _make_tree_writable(result_dir)


def test_finalized_raw_result_rejects_overwrite(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import benchmark.supervisor as supervisor_module

    config_path = tmp_path / "experiment.yaml"
    _write_config(config_path, tmp_path / "raw")
    monkeypatch.setattr(supervisor_module, "generate_experiment_id",
                        lambda config: "fixed-id-for-overwrite-test")
    result_dir = run_experiment(config_path, ["/usr/bin/true"])
    assert (result_dir / "result.json").is_file()
    try:
        with pytest.raises(RuntimeError, match="拒绝覆盖"):
            run_experiment(config_path, ["/usr/bin/true"])
    finally:
        _make_tree_writable(result_dir)


def test_training_metrics_artifact_enriches_runtime(tmp_path: Path) -> None:
    config_path = tmp_path / "experiment.yaml"
    _write_config(config_path, tmp_path / "raw")
    writer = (
        "import json, os, pathlib\n"
        "d = pathlib.Path(os.environ['BENCH_EXPERIMENT_ARTIFACTS_DIR'])\n"
        "d.joinpath('step_timings.jsonl').write_text('{\"step\": 1}\\n')\n"
        "metrics = {'successful_steps': 20, 'tokens_processed': 1234,\n"
        "  'tokens_per_second': 12.5, 'training_loss_final': 2.5,\n"
        "  'token_count_definition': 'loss-bearing',\n"
        "  'trainable_parameters': 1000, 'total_parameters': 100000,\n"
        "  'model_architecture': 'qwen3', 'parameter_count': 100000,\n"
        "  'quantization_state': 'unquantized',\n"
        "  'resolved_revision': 'c1899de289a0',\n"
        "  'revision_source': 'hf local cache trees'}\n"
        "d.joinpath('training_metrics.json').write_text(json.dumps(metrics))\n"
        "print('ok')\n"
    )
    result_dir = run_experiment(config_path, [sys.executable, "-c", writer])
    try:
        result = _read_result(result_dir)
        assert result["runtime"]["successful_steps"] == 20
        assert result["runtime"]["tokens_processed"] == 1234
        assert result["runtime"]["tokens_per_second"] == 12.5
        assert result["runtime"]["token_count_definition"] == "loss-bearing"
        assert result["runtime"]["step_timing_artifact"]["path"] == "step_timings.jsonl"
        assert result["metrics"]["training_loss_final"] == 2.5
        assert result["training"]["trainable_parameters"] == 1000
        assert result["training"]["trainable_parameter_ratio"] == 0.01
        assert result["model"]["architecture"] == "qwen3"
        assert result["model"]["resolved_revision"] == "c1899de289a0"
        assert result["model"]["quantization_state"] == "unquantized"
        _assert_manifest_matches_files(result_dir)
    finally:
        _make_tree_writable(result_dir)


def test_git_dirty_ignores_results_artifacts(tmp_path: Path) -> None:
    """回归：results/ 下的实验产物（staging/finalized）不应把源码 dirty 判成 True。"""
    import benchmark.environment as env_mod
    repo = tmp_path / "scratch-repo"
    repo.mkdir()
    for args in (["init", "-q"], ["config", "user.name", "t"],
                 ["config", "user.email", "t@t"]):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    (repo / "README.md").write_text("x", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"],
                   check=True, capture_output=True)

    (repo / "results" / "raw" / ".staging-x").mkdir(parents=True)
    (repo / "results" / "raw" / ".staging-x" / "f").write_text("x", encoding="utf-8")
    assert env_mod.collect_git_provenance(repo_root=repo)["git_dirty"] is False

    (repo / "src.py").write_text("change", encoding="utf-8")
    assert env_mod.collect_git_provenance(repo_root=repo)["git_dirty"] is True


def test_resolve_local_revision_sidecar(tmp_path: Path) -> None:
    """ModelScope 等非 hf 缓存布局通过 REVISION sidecar 解析 revision。"""
    from train.lora_smoke import _resolve_local_revision
    rev, src = _resolve_local_revision(tmp_path)
    assert rev is None and src is None
    (tmp_path / "REVISION").write_text("a" * 40 + "\n", encoding="utf-8")
    rev, src = _resolve_local_revision(tmp_path)
    assert rev == "a" * 40 and "sidecar" in src
