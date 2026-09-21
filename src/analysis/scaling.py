"""Single source of truth for model-scale group means and log-log fits."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .stats import loglog_fit

ROOT = Path(__file__).resolve().parents[2]
SERIES_GROUPS = {
    "bf16_lora": [
        "formal-axis1-0.6b-bf16-lora",
        "formal-axis1-1.7b-bf16-lora",
        "formal-axis1-4b-bf16-lora",
    ],
    "4bit_qlora": [
        "formal-axis1-0.6b-4bit-qlora",
        "formal-axis1-1.7b-4bit-qlora",
        "formal-axis1-4b-4bit-qlora",
        "formal-axis1-8b-4bit-qlora",
        "formal-axis1-14b-4bit-qlora",
    ],
}


def build_scaling_series(df: pd.DataFrame, series: str, metric: str,
                         divisor: float = 1.0) -> list[dict]:
    rows = []
    for group in SERIES_GROUPS[series]:
        sub = df[df["experiment.comparison_group_id"] == group]
        x = pd.to_numeric(sub["tm.logical_parameter_count"],
                          errors="coerce").dropna()
        y = pd.to_numeric(sub[metric], errors="coerce").dropna()
        if x.empty or y.empty:
            continue
        rows.append({"group": group,
                     "params_B": float(x.mean()) / 1e9,
                     "group_mean": float(y.mean()) / divisor,
                     "n_runs": int(len(y))})
    return rows


def fit_scaling_from_group_means(df: pd.DataFrame, series: str, metric: str,
                                 divisor: float = 1.0) -> dict | None:
    rows = build_scaling_series(df, series, metric, divisor)
    return loglog_fit([row["params_B"] for row in rows],
                      [row["group_mean"] for row in rows])


def write_scaling_source(df: pd.DataFrame) -> Path:
    payload = {}
    for series in SERIES_GROUPS:
        payload[series] = {
            "memory": build_scaling_series(
                df, series, "tm.peak_metal_gpu_memory_bytes", 2**30),
            "step_time": build_scaling_series(
                df, series, "tm.median_step_time_seconds"),
        }
    path = ROOT / "results" / "processed" / "scaling_group_means.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path

