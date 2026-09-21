"""Analytic memory accounting decomposition（D12 事后探索性分析）。

把实测 MLX allocator peak（tm.peak_metal_gpu_memory_bytes，Metal buffer
高水位）分解为可从 provenance 记录推导的解析账目 + 未记账残差：

  accounted = weights_on_disk + adapter + gradients + optimizer_moments
  unaccounted = measured_peak − accounted
              （ activations / allocator 行为 / 框架 / eval 缓冲——只给
                边界，不归属内容，不估计 ）

账目假设（全部为代码/配置可验证事实，非测量估计）：
- 权重驻留字节 = models/MANIFEST.md 记录的 safetensors 磁盘字节
  （committed provenance 文件，Hub 校验一致；4-bit 模型即量化驻留）；
- LoRA 适配器为 fp32（mlx_lm tuner LoRALinear 以 MLX 默认 dtype=float32
  初始化 lora_a/lora_b——mlx_lm/tuner/lora.py）；
- 梯度与 Adam 两动量按可训练参数 dtype 计（LoRA→fp32；full-FT→bf16，
  mlx.optimizers Adam 的 state 以 zeros_like(param) 建立）；
- 无 gradient checkpointing（effective_config: false）。

输出：
- results/processed/memory_decomposition.json
- results/figures/fig12_memory_decomposition.{pdf,png}
- paper/submission/tables/table16_memory_decomposition.tex
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .figures import BF16_COLOR, Q4_COLOR, RAM_COLOR, _save, plt, ROOT

PROCESSED = ROOT / "results" / "processed"
TABLES = ROOT / "paper" / "submission" / "tables"
GIB = 2**30

AXIS1 = [
    ("formal-axis1-0.6b-4bit-qlora", "0.6B 4bit QLoRA", 4),
    ("formal-axis1-1.7b-4bit-qlora", "1.7B 4bit QLoRA", 4),
    ("formal-axis1-4b-4bit-qlora", "4B 4bit QLoRA", 4),
    ("formal-axis1-8b-4bit-qlora", "8B 4bit QLoRA", 4),
    ("formal-axis1-0.6b-bf16-lora", "0.6B BF16 LoRA", 16),
    ("formal-axis1-1.7b-bf16-lora", "1.7B BF16 LoRA", 16),
    ("formal-axis1-4b-bf16-lora", "4B BF16 LoRA", 16),
    ("formal-axis1-0.6b-bf16-full", "0.6B BF16 full FT", 16),
]


def _git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True,
                              cwd=ROOT).stdout.strip()
    except Exception:
        return "unknown"


def parse_manifest(path: Path | None = None) -> dict[str, float]:
    """models/MANIFEST.md → {model_dir_name: safetensors_bytes}（GB 十进制）。"""
    out = {}
    f = path or (ROOT / "models" / "MANIFEST.md")
    pat = re.compile(r"`models/([^`]+)`\s*\|[^|]+\|[^|]+\|\s*([0-9.]+) GB")
    for line in f.read_text().splitlines():
        m = pat.search(line)
        if m:
            out[m.group(1)] = float(m.group(2)) * 1e9
    return out


def _retained_success() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED / "experiments.csv", low_memory=False)
    formal = df[df["experiment.comparison_group_id"].astype(str)
                .str.startswith("formal-")]
    from .flatten import retained
    ok = retained(formal)
    return ok[ok["status.terminal_state"] == "success"].copy()


def build() -> dict:
    runs = _retained_success()
    manifest = parse_manifest()
    rows = []
    for group, label, bits in AXIS1:
        sub = runs[runs["experiment.comparison_group_id"] == group]
        if sub.empty:
            continue
        r = sub.iloc[0]
        local = str(r["model.local_path"]).rstrip("/")
        model_dir = local.split("/")[-1]
        weights_b = manifest.get(model_dir)
        trainable = float(r["tm.trainable_parameters"])
        logical = float(r["tm.logical_parameter_count"])
        method = str(r["training.method"])
        # LoRA/QLoRA: 适配器 fp32；full-FT: 参数 bf16（梯度/动量随参数 dtype）
        pbytes = 4 if method in ("lora", "qlora") else 2
        adapter_b = trainable * pbytes
        grads_b = trainable * pbytes
        opt_b = 2 * trainable * pbytes
        peak = pd.to_numeric(sub["tm.peak_metal_gpu_memory_bytes"],
                             errors="coerce")
        measured = float(peak.mean()) / GIB
        accounted = ((weights_b or 0) + adapter_b + grads_b + opt_b) / GIB
        rows.append({
            "group": group, "label": label, "method": method,
            "model_dir": model_dir,
            "n_seeds": int(len(sub)),
            "logical_params_B": logical / 1e9,
            "weights_on_disk_gib": (weights_b / GIB) if weights_b else None,
            "adapter_gib": adapter_b / GIB,
            "grads_gib": grads_b / GIB,
            "optimizer_gib": opt_b / GIB,
            "accounted_gib": accounted,
            "measured_peak_gib": measured,
            "measured_peak_sd_gib": (float(peak.std()) / GIB
                                     if len(peak) > 1 else 0.0),
            "unaccounted_gib": measured - accounted,
            "unaccounted_share": (measured - accounted) / measured,
            "bytes_per_logical_param_disk": (weights_b / logical
                                             if weights_b else None),
        })
    return {
        "schema_version": "1.0.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "generator_commit": _git_commit(),
        "analysis_kind": "post-hoc exploratory (deviations.md D12)",
        "accounting_assumptions": [
            "weights resident = safetensors bytes on disk (models/MANIFEST.md, "
            "Hub-verified; 4-bit models stay quantized in the allocator)",
            "LoRA adapters fp32 (mlx_lm LoRALinear default dtype)",
            "gradients + Adam two moments in trainable-parameter dtype "
            "(fp32 LoRA / bf16 full-FT; config schema says 'adamw', the "
            "pinned trainer instantiates mlx.optimizers.Adam — identical "
            "two-moment memory)",
            "no gradient checkpointing (effective_config false)",
            "unaccounted = activations + allocator behavior + framework + "
            "eval buffers — bounded, NOT attributed",
        ],
        "cells": rows,
    }


def fig12(payload: dict) -> None:
    rows = payload["cells"]
    fig, ax = plt.subplots(figsize=(7.0, 3.4), layout="constrained")
    names = [r["label"] for r in rows][::-1]
    y = np.arange(len(rows))
    w = np.array([r["weights_on_disk_gib"] or 0 for r in rows])[::-1]
    ao = np.array([r["adapter_gib"] + r["grads_gib"] + r["optimizer_gib"]
                   for r in rows])[::-1]
    un = np.array([r["unaccounted_gib"] for r in rows])[::-1]
    ax.barh(y, w, height=0.62, color="#7fa8d4", label="weights (on-disk, "
            "quantized as shipped)")
    ax.barh(y, ao, left=w, height=0.62, color="#f0a35e",
            label="adapter + grads + optimizer (analytic)")
    ax.barh(y, np.maximum(un, 0), left=w + ao, height=0.62,
            color="#c8c8c8", label="unaccounted (activations/allocator/etc.)")
    meas = np.array([r["measured_peak_gib"] for r in rows])[::-1]
    ax.scatter(meas, y, marker="|", s=220, color="#222222", zorder=5,
               label="measured allocator peak (mean of seeds)")
    for yi, m in enumerate(meas):
        ax.text(m + 0.25, yi, f"peak {m:.2f} GiB", fontsize=7,
                va="center", color="#222222")
    ax.set_yticks(y, names)
    ax.set_xlabel("memory (GiB)")
    ax.axvline(16, color=RAM_COLOR, lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax.text(16, -0.62, "16 GiB physical RAM", fontsize=7.5,
            color=RAM_COLOR, va="center", ha="center")
    ax.set_xlim(0, max(meas) * 1.24)
    ax.set_ylim(-1.0, len(rows) - 0.4)
    ax.set_title("Peak-memory accounting decomposition (ctx512, b1, r8)",
                 fontsize=9)
    # 图例外置顶部横排（母版式），避免压住条形与数值标注（视觉验收教训）
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    handles = [Patch(fc="#7fa8d4", ec="none"),
               Patch(fc="#f0a35e", ec="none"),
               Patch(fc="#c8c8c8", ec="none"),
               Line2D([], [], color="#222222", marker="|", ms=11, lw=0)]
    labels = ["weights (on-disk, quantized as shipped)",
              "adapter + grads + optimizer (analytic)",
              "unaccounted (activations/allocator/etc.)",
              "measured allocator peak (mean of seeds)"]
    fig.legend(handles, labels, loc="outside upper center", ncol=2,
               frameon=False, fontsize=7.5, handlelength=1.6,
               columnspacing=1.2)
    _save(fig, "fig12_memory_decomposition")


def table16(payload: dict) -> None:
    lines = [
        r"\begin{table}[t]\centering",
        r"\caption{Peak-memory accounting decomposition per axis-1 cell "
        r"(exploratory, D12). Weights = safetensors bytes on disk "
        r"(MANIFEST, Hub-verified); adapter+grads+optimizer = analytic "
        r"(fp32 adapters, two Adam moments, no gradient checkpointing); "
        r"unaccounted = measured allocator peak minus the analytic account "
        r"(activations, allocator behavior, framework, eval buffers --- "
        r"bounded, not attributed). The 4B BF16 row is the single-seed D1 "
        r"boundary observation.}",
        r"\label{tab:memdec}",
        r"\footnotesize\setlength{\tabcolsep}{3.2pt}",
        r"\begin{tabular}{@{}lrrrrr@{}}",
        r"\toprule",
        r"Cell & Peak (GiB) & Weights & Adapt+opt & Unacct. & Unacct.\\",
        r" & measured & disk & analytic & (GiB) & share\\",
        r"\midrule",
    ]
    for r in payload["cells"]:
        lines.append(
            f"{r['label']} & {r['measured_peak_gib']:.2f} & "
            f"{r['weights_on_disk_gib']:.2f} & "
            f"{(r['adapter_gib'] + r['grads_gib'] + r['optimizer_gib']):.2f} & "
            f"{r['unaccounted_gib']:.2f} & "
            f"{r['unaccounted_share'] * 100:.0f}\\%\\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    TABLES.mkdir(parents=True, exist_ok=True)
    (TABLES / "table16_memory_decomposition.tex").write_text(
        "\n".join(lines), encoding="utf-8")
    print("[table] table16_memory_decomposition.tex")


def main() -> int:
    payload = build()
    (PROCESSED / "memory_decomposition.json").write_text(
        json.dumps(payload, indent=1))
    fig12(payload)
    table16(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
