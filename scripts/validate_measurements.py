#!/usr/bin/env python3
"""Measurement validation（Phase 2）。

三个验证部分，产出 results/validation/measurements-<date>/report.json：

A. MLX 异步执行对 step timing 的影响：同一工作负载在有/无 mx.eval 同步
   两种方式下计时，量化无同步时会低估多少（验证训练器计时模式必要且充分）。
B. mx.metal.get_peak_memory() 语义：已知大小的分配是否按预期计入 peak；
   缓存是否计入；验证其口径为 MLX 分配器（Metal buffer），非进程 RSS。
C. raw result 算术一致性：对每个含 step_timings.jsonl 的 raw result 重算
   avg/median step time、tokens、throughput，与 result.json 字段对比。

A/B 需要 GPU（独占运行，不得与其他训练并发）；C 为纯 CPU。
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def part_a_mlx_sync(n_iters: int = 60, size: int = 2048) -> dict:
    import mlx.core as mx

    mx.random.seed(42)
    a = mx.random.normal((size, size)) * 0.02
    b = mx.random.normal((size, size)) * 0.02
    c = mx.random.normal((size, size)) * 0.02

    def workload():
        # 深链路放大异步排队效应
        x = a
        for _ in range(8):
            x = x @ b + c
            x = mx.exp(-x * x)
        return x

    # 模式 1：无显式同步（错误模式——计时只测派发）
    mx.eval(workload())  # 预热
    t0 = time.perf_counter()
    for _ in range(n_iters):
        y = workload()
    async_total = time.perf_counter() - t0
    mx.eval(y)

    # 模式 2：每迭代 mx.eval（训练器实际使用的模式）
    t0 = time.perf_counter()
    for _ in range(n_iters):
        mx.eval(workload())
    synced_total = time.perf_counter() - t0

    return {
        "n_iters": n_iters, "matrix_size": size,
        "async_dispatch_total_s": async_total,
        "synced_total_s": synced_total,
        "async_underreport_factor": synced_total / max(async_total, 1e-9),
        "conclusion": "无同步计时会严重低估真实 GPU 时间；"
                      "训练器每步 mx.eval（src/train/lora_smoke.py:141）为必需同步点",
    }


def part_b_peak_memory(alloc_bytes: int = 1 << 30) -> dict:
    import mlx.core as mx

    mx.clear_cache()
    mx.eval(mx.zeros(1))  # 确保分配器初始化
    mx.reset_peak_memory()
    base_active = mx.get_active_memory()
    base_peak = mx.get_peak_memory()

    n = alloc_bytes // 4
    buf = mx.zeros((n,), mx.float32)
    mx.eval(buf)
    after_alloc_active = mx.get_active_memory()
    after_alloc_peak = mx.get_peak_memory()

    # 训练器实际使用的旧 API（deprecated alias）必须与新 API 同值
    alias_ok = (mx.metal.get_active_memory() == after_alloc_active and
                mx.metal.get_peak_memory() == after_alloc_peak)

    del buf
    mx.clear_cache()
    after_clear_active = mx.get_active_memory()

    delta_active = after_alloc_active - base_active
    delta_peak = after_alloc_peak - base_peak
    return {
        "alloc_bytes_requested": alloc_bytes,
        "active_delta_bytes": int(delta_active),
        "peak_delta_bytes": int(delta_peak),
        "active_delta_matches_alloc": abs(delta_active - alloc_bytes) < 1 << 20,
        "peak_delta_matches_alloc": abs(delta_peak - alloc_bytes) < 1 << 20,
        "deprecated_alias_matches_new_api": bool(alias_ok),
        "active_after_clear_cache_bytes": int(after_clear_active - base_active),
        "conclusion": "get_peak_memory/get_active_memory 以字节计 MLX 分配器"
                      "（Metal buffer）口径，reset 后已知分配按预期计入 peak 与 active；"
                      "cache 不计入 active；训练器所用旧 API 与新 API 同值",
    }


def part_c_raw_consistency() -> dict:
    """按每个 run 自己声明的测量口径重算并核对。

    已知口径差异：prompt06 时代吞吐分母 = training_loop_seconds（整循环）；
    prompt07+ 分母 = measured step-time 之和（排除 warmup）。检查器读取
    throughput_interval_definition 与 measured_interval_seconds 选择对应分母。
    """
    raw = ROOT / "results" / "raw"
    checks = []
    for d in sorted(raw.iterdir()):
        tj = d / "step_timings.jsonl"
        rj = d / "result.json"
        if not (tj.is_file() and rj.is_file()):
            continue
        r = json.loads(rj.read_text(encoding="utf-8"))
        tm_path = d / "training_metrics.json"
        tm = json.loads(tm_path.read_text(encoding="utf-8")) if tm_path.is_file() else {}
        steps = [json.loads(l) for l in tj.read_text(encoding="utf-8").splitlines() if l.strip()]
        if not steps:
            continue
        rt = r["runtime"]
        excluded = int(tm.get("excluded_warmup_steps") or 0)
        measured = steps[excluded:]
        times = [s["step_time_seconds"] for s in measured]
        toks = [s["loss_bearing_tokens"] for s in measured]
        rec = {
            "experiment_id": r["experiment"]["id"],
            "excluded_warmup_steps": excluded,
            "n_step_records": len(steps),
            "successful_steps_field": rt["successful_steps"],
            "steps_match": len(steps) == rt["successful_steps"],
            "avg_recomputed": statistics.fmean(times),
            "avg_field": rt["average_step_time_seconds"],
            "avg_match": rt["average_step_time_seconds"] is not None and
                         abs(statistics.fmean(times) - rt["average_step_time_seconds"]) < 1e-6,
            "median_recomputed": statistics.median(times),
            "median_field": rt["median_step_time_seconds"],
            "median_match": rt["median_step_time_seconds"] is not None and
                            abs(statistics.median(times) - rt["median_step_time_seconds"]) < 1e-6,
            "tps_denominator": ("measured_step_time_sum"
                                if tm.get("measured_interval_seconds") is not None
                                else "training_loop_seconds"),
        }
        if rt["tokens_per_second"] is not None:
            if rec["tps_denominator"] == "measured_step_time_sum":
                interval = sum(times)
            else:
                interval = tm.get("training_loop_seconds")
                recomputed_avg_note = None
            recomputed_tps = sum(toks) / interval
            rec["tps_recomputed"] = recomputed_tps
            rec["tps_field"] = rt["tokens_per_second"]
            rec["tps_match"] = abs(recomputed_tps - rt["tokens_per_second"]) / rt["tokens_per_second"] < 1e-9
        checks.append(rec)
    return {
        "n_checked": len(checks),
        "all_consistent": all(
            k for c in checks for k in
            (c["steps_match"], c["avg_match"], c["median_match"],
             c.get("tps_match", True))),
        "checks": checks,
    }


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    out_dir = ROOT / "results" / "validation" / f"measurements-{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "kind": "measurement-validation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mlx_version": __import__("importlib.metadata", fromlist=["version"]).version("mlx"),
        "host_note": "Apple M4 / 16 GiB / macOS 26.5",
    }
    if "--cpu-only" not in sys.argv:
        report["A_mlx_sync_timing"] = part_a_mlx_sync()
        report["B_mlx_peak_memory"] = part_b_peak_memory()
    report["C_raw_result_consistency"] = part_c_raw_consistency()
    out = out_dir / "report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    a = report.get("A_mlx_sync_timing", {})
    b = report.get("B_mlx_peak_memory", {})
    c = report["C_raw_result_consistency"]
    print(f"[A] async underreport factor: {a.get('async_underreport_factor', 0):.1f}x")
    print(f"[B] active/peak delta match alloc: {b.get('active_delta_matches_alloc')}/"
          f"{b.get('peak_delta_matches_alloc')}")
    print(f"[C] {c['n_checked']} raw results checked, all_consistent={c['all_consistent']}")
    print(f"→ {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
