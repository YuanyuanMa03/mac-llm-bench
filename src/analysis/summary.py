"""生成 results/processed/key_numbers.json：论文 prose 引用的全部关键数字。

每个数字附 experiment group / 来源字段，保证 paper sentence → processed → raw
可回溯（Phase 12 audit 的依据）。
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .stats import loglog_fit, mean_sd_ci, paired_ratio

ROOT = Path(__file__).resolve().parents[2]


def _agg(sub: pd.DataFrame, col: str) -> dict | None:
    return mean_sd_ci([float(v) for v in sub[col]])


def main() -> int:
    df = pd.read_csv(ROOT / "results" / "processed" / "experiments.csv",
                     low_memory=False)
    formal = df[df["experiment.comparison_group_id"].astype(str)
                .str.startswith("formal-")]
    ok = formal[formal["status.terminal_state"] == "success"].copy()

    out = {"scale_axis": {}, "context_axis": {}, "paired": {}, "notes": [
        "all numbers derived from results/raw via src/analysis; regenerable"]}

    # 轴 1：模型规模
    combos = [(m, meth) for m in ("0.6b", "1.7b", "4b", "8b", "14b")
              for meth in ("lora", "qlora", "full")
              if (m, meth) in [(x[0], x[1]) for x in
                               [("0.6b", "lora"), ("1.7b", "lora"), ("4b", "lora"),
                                ("0.6b", "qlora"), ("1.7b", "qlora"), ("4b", "qlora"),
                                ("8b", "qlora"), ("14b", "qlora"), ("0.6b", "full")]]]
    for model, meth in combos:
        g = f"formal-axis1-{model}-{meth}"
        sub = ok[ok["experiment.comparison_group_id"] == g]
        if sub.empty:
            continue
        params = float(sub["tm.logical_parameter_count"].iloc[0]) / 1e9
        out["scale_axis"][g] = {
            "params_B": params,
            "median_step_s": _agg(sub, "tm.median_step_time_seconds"),
            "peak_mem_gib": {k: (v / 2**30 if v is not None else None)
                             for k, v in (_agg(sub, "tm.peak_metal_gpu_memory_bytes")
                                          or {}).items() if k != "values"},
            "tokens_per_s": _agg(sub, "runtime.tokens_per_second"),
            "val_loss_final": _agg(sub, "metrics.validation_loss_final"),
            "val_loss_initial_mean": round(sum(
                json.loads(v)[0]["loss"] for v in
                sub["tm.validation_loss_trajectory"]), 4) / len(sub),
        }

    # 轴 2：context
    for ctx, g in ((512, "formal-axis1-4b-4bit-qlora"),
                   (1024, "formal-axis2-ctx1024"),
                   (2048, "formal-axis2-ctx2048")):
        sub = ok[ok["experiment.comparison_group_id"] == g]
        if sub.empty:
            continue
        out["context_axis"][str(ctx)] = {
            "group": g,
            "median_step_s": _agg(sub, "tm.median_step_time_seconds"),
            "peak_mem_gib": {k: (v / 2**30 if v is not None else None)
                             for k, v in (_agg(sub, "tm.peak_metal_gpu_memory_bytes")
                                          or {}).items() if k != "values"},
            "tokens_per_s": _agg(sub, "runtime.tokens_per_second"),
        }

    # RQ4 配对（同模型同 seed）
    for model in ("0.6b", "1.7b", "4b"):
        ga, gb = f"formal-axis1-{model}-bf16-lora", f"formal-axis1-{model}-4bit-qlora"
        entry = {}
        for col in ("tm.peak_metal_gpu_memory_bytes",
                    "tm.median_step_time_seconds", "runtime.tokens_per_second"):
            pr = paired_ratio(ok, ga, gb, value_col=col)
            if pr:
                entry[col] = {
                    "ratios": [round(p["ratio_b_over_a"], 4) for p in pr],
                    "mean": round(sum(p["ratio_b_over_a"] for p in pr) / len(pr), 4)}
        out["paired"][model] = entry

    # scaling fits
    for label, gnames in (
        ("bf16_lora", ["formal-axis1-0.6b-bf16-lora", "formal-axis1-1.7b-bf16-lora",
                       "formal-axis1-4b-bf16-lora"]),
        ("4bit_qlora", ["formal-axis1-0.6b-4bit-qlora", "formal-axis1-1.7b-4bit-qlora",
                        "formal-axis1-4b-4bit-qlora", "formal-axis1-8b-4bit-qlora",
                        "formal-axis1-14b-4bit-qlora"]),
    ):
        xs, ys_mem, ys_time = [], [], []
        for g in gnames:
            sub = ok[ok["experiment.comparison_group_id"] == g]
            if sub.empty:
                continue
            xs.append(float(sub["tm.logical_parameter_count"].iloc[0]) / 1e9)
            ys_mem.append(float(sub["tm.peak_metal_gpu_memory_bytes"].iloc[0]) / 2**30)
            ys_time.append(float(sub["tm.median_step_time_seconds"].iloc[0]))
        out.setdefault("fits", {})[label] = {
            "memory": loglog_fit(xs, ys_mem),
            "step_time": loglog_fit(xs, ys_time),
        }

    path = ROOT / "results" / "processed" / "key_numbers.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print(f"[summary] → {path.relative_to(ROOT)}")
    return 0
