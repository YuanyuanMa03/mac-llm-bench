"""实验前环境采集：只采集当前已验证可可靠获取的指标；命令失败即 null，绝不猜。

可靠来源（macOS，已实机验证可用）：
- git rev-parse / git status --porcelain=v1
- sw_vers；sys.version / sys.executable；importlib.metadata（mlx/mlx-lm）
- system_profiler -json SPHardwareDataType；sysctl hw.memsize/hw.physicalcpu/hw.logicalcpu
- df -kP <输出目录>
- vm_stat；sysctl vm.swapusage；pmset -g batt
明确不采集（未验证可靠性）：GPU 核心数、thermal、energy、page faults 细分语义。
硬件序列号绝不入库（raw evidence 亦需脱敏）。
"""

from __future__ import annotations

import datetime as _dt
import functools
import importlib.metadata
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# 绝不写入结果或 raw evidence 的硬件键（协议 §3.2：不得存储序列号）
_REDACTED_HARDWARE_KEYS = {"serial_number", "serial_number_system", "platform_UUID"}


def utc_now() -> str:
    """RFC 3339 UTC 含微秒。"""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _run(command: list[str], timeout: float = 15.0) -> str | None:
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def collect_git_provenance(repo_root: Path = REPO_ROOT) -> dict:
    """Git commit 与 dirty 状态；非 git 环境返回 (None, None)。"""
    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", "-C", str(repo_root), *args],
                              capture_output=True, text=True)

    sha_proc = git("rev-parse", "HEAD")
    sha = sha_proc.stdout.strip() if sha_proc.returncode == 0 else None
    # 排除 results/：实验产物（staging/finalized 目录）不算源码 dirty——
    # dirty 的语义是"源码或配置相对 HEAD 有无改动"
    status_proc = git("status", "--porcelain=v1", "--", ".", ":(exclude)results")
    dirty = bool(status_proc.stdout.strip()) if status_proc.returncode == 0 else None
    return {
        "git_commit_sha": sha,
        "git_dirty": dirty,
        "git_status_porcelain": status_proc.stdout if status_proc.returncode == 0 else "",
    }


@functools.lru_cache(maxsize=1)
def collect_software() -> dict:
    sw_vers = _run(["sw_vers"])
    macos_version = macos_build = None
    if sw_vers:
        for line in sw_vers.splitlines():
            match = re.match(r"ProductVersion:\s*(.+)", line)
            if match:
                macos_version = match.group(1).strip()
            match = re.match(r"BuildVersion:\s*(.+)", line)
            if match:
                macos_build = match.group(1).strip()

    def dist_version(name: str) -> str | None:
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            return None

    package_manager = "uv (uv.lock)" if (REPO_ROOT / "uv.lock").exists() else None
    return {
        "macos_version": macos_version,
        "macos_build": macos_build,
        "python_implementation": platform.python_implementation(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "mlx_version": dist_version("mlx"),
        "mlx_lm_version": dist_version("mlx-lm"),
        "package_manager": package_manager,
        "environment_type": "venv" if sys.prefix != sys.base_prefix else "system",
        "environment_path": sys.prefix,
    }


@functools.lru_cache(maxsize=1)
def _hardware_snapshot_cached() -> dict:
    sp_json = _run(["system_profiler", "-json", "SPHardwareDataType"], timeout=30.0)
    mac_model = chip = None
    unified_memory = None
    if sp_json:
        try:
            data = json.loads(sp_json)
            item = data.get("SPHardwareDataType", [{}])[0]
            mac_model = item.get("machine_model")
            chip = item.get("chip_type")
            unified_memory = item.get("physicalMemory")
        except (json.JSONDecodeError, IndexError, AttributeError):
            pass

    def sysctl_int(key: str) -> int | None:
        text = _run(["sysctl", "-n", key])
        if text is None:
            return None
        try:
            return int(text.strip())
        except ValueError:
            return None

    return {
        "mac_model": mac_model,
        "apple_chip_model": chip,
        "unified_memory_bytes": unified_memory,
        "cpu_physical_cores": sysctl_int("hw.physicalcpu"),
        "cpu_logical_cores": sysctl_int("hw.logicalcpu"),
        # GPU 核心数：system_profiler/sysctl 无稳定键显式报告，未验证 → null
        "gpu_cores": None,
        "sp_raw": sp_json,
    }


def collect_hardware() -> dict:
    snapshot = dict(_hardware_snapshot_cached())
    snapshot.pop("sp_raw", None)
    return snapshot


def collect_filesystem(output_dir: Path) -> dict:
    df = _run(["df", "-kP", str(output_dir)])
    filesystem = None
    free_kb = None
    if df:
        lines = [line for line in df.splitlines() if line.strip()]
        if len(lines) >= 2:
            fields = lines[-1].split()
            if len(fields) >= 4:
                filesystem = fields[0]
                try:
                    free_kb = int(fields[3])
                except ValueError:
                    free_kb = None
    return {
        "filesystem": filesystem,
        "free_disk_bytes": free_kb * 1024 if free_kb is not None else None,
    }


def collect_vm_stat() -> dict:
    """vm_stat 原文 + 解析计数（页数）与页大小。"""
    raw = _run(["vm_stat"])
    page_size = None
    counters: dict[str, int] = {}
    if raw:
        match = re.search(r"page size of (\d+) bytes", raw)
        if match:
            page_size = int(match.group(1))
        for line in raw.splitlines():
            match = re.match(r'^(.+?):\s+(\d+)\.?$', line.strip())
            if match:
                key = re.sub(r"[^a-z0-9]+", "_", match.group(1).strip().lower())
                key = key.strip("_")
                if key:
                    counters[key] = int(match.group(2))
    return {"raw": raw, "page_size": page_size, "counters": counters}


def collect_swap_bytes() -> tuple[int | None, str | None]:
    """sysctl vm.swapusage 的 used 字节数（源为 2 位小数 MB，换算按 1024×1024）。"""
    raw = _run(["sysctl", "-n", "vm.swapusage"])
    if raw is None:
        return None, raw
    match = re.search(r"used\s*=\s*([\d.]+)M", raw)
    if not match:
        return None, raw
    return int(round(float(match.group(1)) * 1024 * 1024)), raw


def collect_power_source() -> tuple[str | None, str | None]:
    raw = _run(["pmset", "-g", "batt"])
    if raw is None:
        return None, raw
    if "AC Power" in raw:
        return "AC Power", raw
    match = re.search(r"Battery Power", raw)
    return ("Battery Power", raw) if match else (None, raw)


def redact_hardware_json(sp_raw: str | None) -> str:
    """system_profiler 原文脱敏：序列号与平台 UUID 替换为 [REDACTED]。"""
    if not sp_raw:
        return ""
    try:
        data = json.loads(sp_raw)
    except json.JSONDecodeError:
        return re.sub(r'("(?:serial_number[^"]*|platform_UUID)"\s*:\s*)"[^"]*"',
                      r'\1"[REDACTED]"', sp_raw)

    def redact(node):
        if isinstance(node, dict):
            return {k: ("[REDACTED]" if k in _REDACTED_HARDWARE_KEYS else redact(v))
                    for k, v in node.items()}
        if isinstance(node, list):
            return [redact(item) for item in node]
        return node

    return json.dumps(redact(data), indent=2, ensure_ascii=False)
