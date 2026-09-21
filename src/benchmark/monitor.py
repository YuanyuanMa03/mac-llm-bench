"""轻量系统采样器：周期采样系统级 swap 使用量，写 JSONL 原始证据。

设计约束（协议 §4/§10）：
- 只采集已验证可靠来源（sysctl vm.swapusage，与 supervisor before/after 快照同一解析器）；
- 采样线程为 daemon，绝不影响子进程退出码路径；
- 每行即写即 flush，崩溃时保留部分轨迹（recoverable partial）；
- 开销必须在正式使用前实测（见 scripts/validate_measurements.py 与
  docs/measurement_validation.md），未验证不声称 negligible。
"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from . import environment as env_mod


class SwapSampler:
    """以固定周期采样 vm.swapusage used 字节数，追加写 JSONL。"""

    def __init__(self, interval_seconds: float, out_path: Path):
        self.interval_seconds = float(interval_seconds)
        self.out_path = Path(out_path)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.peak_bytes: int | None = None
        self.n_samples = 0
        self.errors = 0

    def _sample_once(self) -> None:
        value, raw = env_mod.collect_swap_bytes()
        record = {
            "t_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "monotonic_ns": time.monotonic_ns(),
            "swap_used_bytes": value,
            "raw": raw.strip() if raw else None,
        }
        with self.out_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
        if value is not None:
            self.n_samples += 1
            if self.peak_bytes is None or value > self.peak_bytes:
                self.peak_bytes = value
        else:
            self.errors += 1

    def _run(self) -> None:
        while not self._stop.is_set():
            self._sample_once()
            self._stop.wait(self.interval_seconds)

    def start(self) -> None:
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name="swap-sampler")
        self._thread.start()

    def stop(self) -> dict:
        """停止采样并返回摘要；线程可能正处于 wait，最长一个周期后退出。"""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self.interval_seconds + 5.0)
        return {
            "n_samples": self.n_samples,
            "errors": self.errors,
            "peak_swap_bytes": self.peak_bytes,
        }
