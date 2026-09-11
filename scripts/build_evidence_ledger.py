#!/usr/bin/env python3
"""从 results/raw/ 程序化生成 research/evidence_ledger.csv。

所有数值直接读取 raw result.json / training_metrics.json / manifest 校验结果，
不手工填写；缺失字段输出 null。重新运行即可随 raw results 增长重建。
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"
OUT = ROOT / "research" / "evidence_ledger.csv"

COLUMNS = [
    "experiment_id", "git_commit", "git_dirty", "model", "revision",
    "precision", "method", "context", "batch_micro", "grad_accum", "rank",
    "seed", "steps_requested", "steps_completed", "status", "exit_code",
    "signal", "wall_time_s", "step_time_avg_s", "step_time_median_s",
    "throughput_tok_s", "peak_metal_gpu_memory_bytes",
    "peak_process_memory_bytes", "swap_before_bytes", "swap_after_bytes",
    "training_loss_final", "dataset", "manifest_verified",
    "evidence_quality", "formal_or_probe", "raw_result_path",
]


def verify_manifest(d: Path) -> bool | None:
    mp = d / "manifest.sha256"
    if not mp.exists():
        return None
    for line in mp.read_text(encoding="utf-8").strip().splitlines():
        digest, _, rel = line.partition("  ")
        path = d / rel
        if not path.is_file():
            return False
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            return False
    return True


def swap_after_bytes(d: Path) -> int | None:
    env_txt = d / "environment" / "raw_environment.txt"
    if not env_txt.is_file():
        return None
    matches = re.findall(r"used\s*=\s*([\d.]+)M", env_txt.read_text(encoding="utf-8"))
    if len(matches) < 2:
        return None
    return int(round(float(matches[1]) * 1024 * 1024))


def classify_kind(group: str | None) -> str:
    group = group or ""
    if group.startswith("exp0-smoke"):
        return "smoke"
    if group.startswith("calibration-"):
        return "calibration"
    return "probe"


def row_for(d: Path) -> dict:
    r = json.loads((d / "result.json").read_text(encoding="utf-8"))
    rt, st = r["runtime"], r["status"]
    tr, md, ds = r["training"], r["model"], r["dataset"]
    sw = r["software"]
    tm: dict = {}
    if (d / "training_metrics.json").is_file():
        try:
            tm = json.loads((d / "training_metrics.json").read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            tm = {}

    manifest_ok = verify_manifest(d)
    git_commit = sw.get("git_commit_sha")
    git_dirty = sw.get("git_dirty")
    revision = md.get("resolved_revision")

    if manifest_ok is False:
        quality = "low"
    elif git_commit and not git_dirty and revision:
        quality = "high"
    else:
        quality = "medium"

    qbits = md.get("quantization_bits") or tr.get("quantization_bits")
    model_dtype = tm.get("model_dtype") or ""
    if qbits:
        precision = f"{qbits}bit"
    elif "bfloat" in model_dtype:
        precision = "bf16"
    elif model_dtype:
        precision = model_dtype
    else:
        precision = None

    def num(value, digits=None):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return round(value, digits) if digits is not None else value
        return None

    return {
        "experiment_id": r["experiment"]["id"],
        "git_commit": (git_commit or "null")[:12],
        "git_dirty": git_dirty,
        "model": md.get("id"),
        "revision": revision,
        "precision": precision,
        "method": tr.get("method"),
        "context": tr.get("sequence_length"),
        "batch_micro": tr.get("micro_batch_size"),
        "grad_accum": tr.get("gradient_accumulation_steps"),
        "rank": tr.get("lora_rank"),
        "seed": tr.get("seed"),
        "steps_requested": tr.get("requested_steps"),
        "steps_completed": num(rt.get("successful_steps")),
        "status": st.get("terminal_state"),
        "exit_code": st.get("exit_code"),
        "signal": st.get("signal"),
        "wall_time_s": num(rt.get("wall_clock_seconds"), 3),
        "step_time_avg_s": num(rt.get("average_step_time_seconds"), 6),
        "step_time_median_s": num(rt.get("median_step_time_seconds"), 6),
        "throughput_tok_s": num(rt.get("tokens_per_second"), 4),
        "peak_metal_gpu_memory_bytes": num(tm.get("peak_metal_gpu_memory_bytes")),
        "peak_process_memory_bytes": None,
        "swap_before_bytes": (rt.get("initial_swap_bytes") or {}).get("value"),
        "swap_after_bytes": swap_after_bytes(d),
        "training_loss_final": num(tm.get("training_loss_final"), 6),
        "dataset": ds.get("name"),
        "manifest_verified": manifest_ok,
        "evidence_quality": quality,
        "formal_or_probe": classify_kind(
            r["experiment"].get("comparison_group_id")),
        "raw_result_path": f"results/raw/{d.name}",
    }


def main() -> int:
    rows = []
    for d in sorted(RAW.iterdir()):
        if d.is_dir() and (d / "result.json").is_file():
            rows.append(row_for(d))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: ("null" if row.get(k) is None else row.get(k))
                             for k in COLUMNS})
    print(f"[ledger] {len(rows)} experiments → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
