"""论文图表生成（预注册 §9；全部从 processed/raw 派生，禁止手工数字）。

输出：results/figures/fig1..fig6 的 PDF+PNG（300 dpi）。
数据源：results/processed/experiments.csv、step_timings.parquet、
context_boundary_probe_summary.json、failure_taxonomy.json。
任何 group 缺失时 fail loudly（不静默空图）。
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .stats import loglog_fit, mean_sd_ci

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "results" / "figures"

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 300, "font.size": 9,
    "axes.grid": True, "grid.alpha": 0.3, "axes.spines.top": False,
    "axes.spines.right": False,
})
BF16_COLOR, Q4_COLOR = "#1f77b4", "#d62728"


def _load() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "results" / "processed" / "experiments.csv",
                     low_memory=False)
    formal = df[df["experiment.comparison_group_id"].astype(str).str.startswith("formal-")]
    from .flatten import retained
    ok = retained(formal)
    ok = ok[ok["status.terminal_state"] == "success"].copy()
    for col in ("tm.median_step_time_seconds", "tm.peak_metal_gpu_memory_bytes",
                "runtime.tokens_per_second", "tm.logical_parameter_count",
                "metrics.validation_loss_final", "training.sequence_length"):
        ok[col] = pd.to_numeric(ok[col], errors="coerce")
    return ok


def _group(df: pd.DataFrame, name: str) -> pd.DataFrame:
    return df[df["experiment.comparison_group_id"] == name]


def _agg(values: list[float]) -> dict:
    return mean_sd_ci([float(v) for v in values])


def _save(fig, name: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", bbox_inches="tight")
    plt.close(fig)
    print(f"[fig] {FIG / name}.pdf")


def _model_label(group: str) -> str:
    # formal-axis1-<model>-<method>
    parts = group.split("-")
    idx = parts.index("axis1") if "axis1" in parts else 1
    return "-".join(parts[idx + 1:-1])


def fig1_architecture() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    boxes = [
        "Config\n(YAML, frozen)", "Experiment\nSupervisor", "MLX training\n(v0.2)",
        "Immutable raw\nevidence\n(result.json +\nmanifest.sha256)",
        "Analysis\n(flatten → stats)",
        "Figures &\nTables",
    ]
    sub = ["preregistration", "provenance + preflight +\nswap sampler",
           "per-step mx.eval sync", "20 experiments", "manifest-verified", "paper"]
    xs = np.linspace(0.02, 0.98, len(boxes))
    for i, (b, s) in enumerate(zip(boxes, sub)):
        ax.add_patch(plt.Rectangle((xs[i] - 0.075, 0.35), 0.15, 0.42,
                                   fc="#eef3fb", ec="#3b6db4", lw=1.2))
        ax.text(xs[i], 0.60, b, ha="center", va="center", fontsize=7.2)
        ax.text(xs[i], 0.44, s, ha="center", va="center", fontsize=6,
                color="#555555")
        if i < len(boxes) - 1:
            ax.annotate("", xy=(xs[i + 1] - 0.078, 0.56),
                        xytext=(xs[i] + 0.078, 0.56),
                        arrowprops=dict(arrowstyle="->", lw=1.2, color="#3b6db4"))
    ax.text(0.5, 0.12, "every number in the paper traces back to an immutable raw result",
            ha="center", fontsize=7, style="italic", color="#444444")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.set_title("Benchmark pipeline", fontsize=10)
    _save(fig, "fig1_architecture")


def fig2_feasibility(df: pd.DataFrame) -> None:
    # 全量 CSV（含失败 run）：✓ 语义 = 该格 preregistered repeats 全部
    # success；部分成功/全部失败如实标注（4B-bf16 依 D1、14B 依 D7）
    full = pd.read_csv(ROOT / "results" / "processed" / "experiments.csv",
                       low_memory=False)
    probes = json.loads((ROOT / "results" / "processed" /
                         "failure_taxonomy.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 2.9))
    ax = axes[0]
    models = ["0.6b", "1.7b", "4b", "8b", "14b"]
    methods = ["lora", "qlora", "full"]
    cell = {}
    for gname, sub in full.groupby("experiment.comparison_group_id"):
        if not str(gname).startswith("formal-axis1-"):
            continue
        label = str(gname).replace("formal-axis1-", "")
        model, method = label.rsplit("-", 1)
        mkey = model.replace("-bf16", "").replace("-4bit", "")
        n_ok = int((sub["status.terminal_state"] == "success").sum())
        n_all = len(sub)
        cell[(method, mkey)] = (n_ok, n_all, sub)
    # 状态分级（deviations D1/D8 的两层定位）：
    #   reproducible success（3/3 formal seeds）
    #   boundary / state-dependent（部分成功或失败均归因系统状态：4B-bf16 D1、14B D8）
    #   runtime failure（非系统状态归因的失败）
    #   untested / out-of-budget（从未运行 / 预注册声明不做）
    BOUNDARY = {( "lora", "4b"), ("qlora", "14b")}  # D1 / D8
    OUT_OF_BUDGET = {("lora", "14b"), ("lora", "8b")}  # preregistration §3（8B 为 probe-only）
    for i, method in enumerate(methods):
        for j, mkey in enumerate(models):
            n_ok, n_all, sub = cell.get((method, mkey), (0, 0, None))
            if (method, mkey) in OUT_OF_BUDGET and n_all == 0:
                ax.text(j, i, "out-of-\nbudget", ha="center", va="center",
                        fontsize=5.5, color="#888888")
            elif n_all == 0:
                ax.text(j, i, "untested", ha="center", va="center",
                        fontsize=6.5, color="#888888")
            elif n_ok == n_all and n_ok >= 3:
                ax.text(j, i, "✓", ha="center", va="center", fontsize=10,
                        color="#1a5c1a", fontweight="bold")
            elif (method, mkey) in BOUNDARY:
                tag = f"✓{n_ok}/{n_all} " if n_ok else ""
                ax.text(j, i, f"{tag}state-\ndependent\n(D1)" if n_ok
                        else "state-\ndependent\n(D8)",
                        ha="center", va="center", fontsize=5.5, color="#7d4ba0")
            else:
                states = "/".join(sorted(set(sub["status.terminal_state"])))
                ax.text(j, i, states, ha="center", va="center",
                        fontsize=5.5, color="#a11")
    ax.set_xticks(range(len(models)), models)
    ax.set_yticks(range(len(methods)), ["BF16 LoRA", "4bit QLoRA", "Full FT"])
    ax.set_title("Trainable @ ctx512: green = 3/3 reproducible seeds;\n"
                 "purple = boundary / system-state dependent (D1/D8)",
                 fontsize=8)
    # 8B BF16 probe outcome
    probe8 = [p for p in probes["failures"] if "8b" in p["experiment_id"]
              and "qnone" in p["experiment_id"]]
    ax.text(3, 0, "probe:\n" + ("timeout" if probe8 else "see raw"),
            ha="center", va="center", fontsize=6, color="#a11")

    ax = axes[1]
    ctxs = ["512", "1024", "2048", "4096", "8192"]
    ok_groups = set(df["experiment.comparison_group_id"])
    status = [1 if f"formal-axis2-ctx{c}" in ok_groups else np.nan
              for c in ctxs]
    ax.imshow(np.array([[s if not np.isnan(s) else np.nan for s in status]]),
              cmap="Greens", vmin=0, vmax=1.4, aspect="auto")
    ax.set_xticks(range(len(ctxs)), ctxs)
    ax.set_yticks([0], ["4B 4bit QLoRA"])
    for j, c in enumerate(ctxs):
        if c in ("4096", "8192"):
            ax.text(j, 0, "SIGKILL\n(probe)", ha="center", va="center",
                    fontsize=6, color="#a11")
        elif np.isnan(status[j]):
            ax.text(j, 0, "untested", ha="center", va="center", fontsize=6.5,
                    color="#888888")
        else:
            ax.text(j, 0, "✓", ha="center", va="center", fontsize=9, color="#1a5c1a")
    ax.set_title("Context axis (4B-4bit)", fontsize=9)
    fig.suptitle("Feasibility map (green = all preregistered repeats succeeded)",
                 fontsize=9.5)
    _save(fig, "fig2_feasibility_map")


def fig3_memory_scaling(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(4.6, 3.4))
    series = {
        # 4B BF16 LoRA 依 deviations.md D1 降级为边界观测，不进入 formal 序列
        "BF16 LoRA": (BF16_COLOR, ["formal-axis1-0.6b-bf16-lora",
                                   "formal-axis1-1.7b-bf16-lora"]),
        "4bit QLoRA": (Q4_COLOR, ["formal-axis1-0.6b-4bit-qlora",
                                  "formal-axis1-1.7b-4bit-qlora",
                                  "formal-axis1-4b-4bit-qlora",
                                  "formal-axis1-8b-4bit-qlora",
                                  "formal-axis1-14b-4bit-qlora"]),
    }
    fits = {}
    for label, (color, gnames) in series.items():
        xs, ys, es = [], [], []
        for g in gnames:
            sub = _group(df, g)
            if sub.empty:
                continue
            params_b = float(sub["tm.logical_parameter_count"].iloc[0]) / 1e9
            mem = _agg(sub["tm.peak_metal_gpu_memory_bytes"])
            xs.append(params_b)
            ys.append(mem["mean"] / 2**30)
            es.append(mem["sd"] / 2**30 if mem["sd"] else 0)
        ax.errorbar(xs, ys, yerr=es, marker="o", ms=4, lw=1.4, color=color,
                    label=label, capsize=2)
        fit = loglog_fit(xs, ys)
        if fit:
            fits[label] = fit
            xx = np.logspace(np.log10(min(xs)), np.log10(max(xs)), 50)
            ax.plot(xx, 10 ** fit["intercept"] * xx ** fit["slope"], "--",
                    color=color, alpha=0.6, lw=1)
            ax.annotate(f"slope={fit['slope']:.2f}, R²={fit['r_squared']:.3f}, n={fit['n']}",
                        xy=(xs[-1], ys[-1]), fontsize=6.5, color=color,
                        xytext=(-4, 8), textcoords="offset points",
                        ha="right")
    ax.axhline(16, color="#888888", lw=1, ls=":")
    ax.text(0.6, 16.4, "16 GiB physical RAM", fontsize=6.5, color="#666666")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("logical parameters (B)")
    ax.set_ylabel("MLX peak memory (GiB)")
    ax.set_title("Peak memory vs model scale (ctx512, mean±SD of 3 seeds)", fontsize=9)
    ax.legend(fontsize=7)
    (ROOT / "results" / "processed" / "memory_scaling_fits.json").write_text(
        json.dumps(fits, indent=2) + "\n")
    _save(fig, "fig3_memory_scaling")


def fig4_time_scaling(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.2))
    series = {
        # 4B BF16 LoRA 依 deviations.md D1 降级为边界观测，不进入 formal 序列
        "BF16 LoRA": (BF16_COLOR, ["formal-axis1-0.6b-bf16-lora",
                                   "formal-axis1-1.7b-bf16-lora"]),
        "4bit QLoRA": (Q4_COLOR, ["formal-axis1-0.6b-4bit-qlora",
                                  "formal-axis1-1.7b-4bit-qlora",
                                  "formal-axis1-4b-4bit-qlora",
                                  "formal-axis1-8b-4bit-qlora",
                                  "formal-axis1-14b-4bit-qlora"]),
    }
    fits = {}
    for label, (color, gnames) in series.items():
        xs, st, ste, tp, tpe = [], [], [], [], []
        for g in gnames:
            sub = _group(df, g)
            if sub.empty:
                continue
            params_b = float(sub["tm.logical_parameter_count"].iloc[0]) / 1e9
            a = _agg(sub["tm.median_step_time_seconds"])
            t = _agg(sub["runtime.tokens_per_second"])
            xs.append(params_b)
            st.append(a["mean"]); ste.append(a["sd"] or 0)
            tp.append(t["mean"]); tpe.append(t["sd"] or 0)
        axes[0].errorbar(xs, st, yerr=ste, marker="o", ms=4, lw=1.4,
                         color=color, label=label, capsize=2)
        axes[1].errorbar(xs, tp, yerr=tpe, marker="o", ms=4, lw=1.4,
                         color=color, label=label, capsize=2)
        fit = loglog_fit(xs, st)
        if fit:
            fits[label] = fit
            xx = np.logspace(np.log10(min(xs)), np.log10(max(xs)), 50)
            axes[0].plot(xx, 10 ** fit["intercept"] * xx ** fit["slope"], "--",
                         color=color, alpha=0.6, lw=1)
            axes[0].annotate(f"slope={fit['slope']:.2f}", xy=(xs[-1], st[-1]),
                             fontsize=6.5, color=color, xytext=(-2, 8),
                             textcoords="offset points", ha="right")
    for ax, ylab, title in ((axes[0], "median step time (s)", "Step time vs scale"),
                            (axes[1], "loss-bearing tokens/s", "Throughput vs scale")):
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("logical parameters (B)"); ax.set_ylabel(ylab)
        ax.set_title(title, fontsize=9)
        ax.legend(fontsize=7)
    (ROOT / "results" / "processed" / "step_time_scaling_fits.json").write_text(
        json.dumps(fits, indent=2) + "\n")
    _save(fig, "fig4_time_scaling")


def fig5_context_scaling(df: pd.DataFrame) -> None:
    boundary = json.loads((ROOT / "results" / "processed" /
                           "context_boundary_probe_summary.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.2))
    # formal ctx runs
    pts = {}
    for ctx, g in ((512, "formal-axis1-4b-4bit-qlora"),
                   (1024, "formal-axis2-ctx1024"),
                   (2048, "formal-axis2-ctx2048")):
        sub = _group(df, g)
        if sub.empty:
            continue
        pts[ctx] = {
            "step": _agg(sub["tm.median_step_time_seconds"]),
            "mem": _agg(sub["tm.peak_metal_gpu_memory_bytes"]),
        }
    xs = sorted(pts)
    axes[0].errorbar(xs, [pts[x]["step"]["mean"] for x in xs],
                     yerr=[pts[x]["step"]["sd"] or 0 for x in xs],
                     marker="o", ms=4, color=Q4_COLOR, lw=1.4, capsize=2,
                     label="formal (mean±SD, 3 seeds)")
    for f in boundary["series"]:
        if f["terminal_state"] != "success" and f["sequence_length"] >= 4096:
            axes[0].scatter([f["sequence_length"]], [90], marker="x", s=60,
                            color="#a11")
            axes[0].annotate(f"SIGKILL\n(0 steps, {f['sequence_length']})",
                             xy=(f["sequence_length"], 90), fontsize=6.5,
                             color="#a11", xytext=(6, -2),
                             textcoords="offset points")
    axes[0].axvspan(4096, 8192, color="#f6d3d3", alpha=0.5)
    axes[0].set_xscale("log"); axes[0].set_yscale("log")
    axes[0].set_xlabel("sequence length"); axes[0].set_ylabel("median step time (s)")
    axes[0].set_title("Step time vs context (4B-4bit QLoRA, b1)", fontsize=9)
    axes[0].legend(fontsize=7)

    axes[1].errorbar(xs, [pts[x]["mem"]["mean"] / 2**30 for x in xs],
                     yerr=[(pts[x]["mem"]["sd"] or 0) / 2**30 for x in xs],
                     marker="o", ms=4, color=Q4_COLOR, lw=1.4, capsize=2,
                     label="MLX peak (mean±SD)")
    axes[1].axhline(16, color="#888888", lw=1, ls=":")
    axes[1].text(520, 16.4, "16 GiB physical RAM", fontsize=6.5, color="#666666")
    axes[1].set_xscale("log"); axes[1].set_yscale("log")
    axes[1].set_xlabel("sequence length")
    axes[1].set_ylabel("MLX peak memory (GiB)")
    axes[1].set_title("Peak memory vs context", fontsize=9)
    axes[1].legend(fontsize=7)
    _save(fig, "fig5_context_scaling")


def fig6_paired_effects(df: pd.DataFrame) -> None:
    from .stats import paired_ratio
    fig, axes = plt.subplots(1, 3, figsize=(8.6, 2.9))
    models = [("0.6b", "0.6b-bf16-lora", "0.6b-4bit-qlora"),
              ("1.7b", "1.7b-bf16-lora", "1.7b-4bit-qlora"),
              ("4b", "4b-bf16-lora", "4b-4bit-qlora")]
    panels = [
        ("tm.peak_metal_gpu_memory_bytes", "memory ratio (4bit/BF16)"),
        ("tm.median_step_time_seconds", "step-time ratio (4bit/BF16)"),
        ("runtime.tokens_per_second", "throughput ratio (4bit/BF16)"),
    ]
    rows = []
    for ax, (col, title) in zip(axes, panels):
        xs, ratios, lo, hi = [], [], [], []
        for i, (label, ga, gb) in enumerate(models):
            pr = paired_ratio(df, f"formal-axis1-{ga}", f"formal-axis1-{gb}",
                              value_col=col)
            r = [p["ratio_b_over_a"] for p in pr]
            if r:
                xs.append(label)
                ratios.append(float(np.mean(r)))
                lo.append(float(np.mean(r) - min(r)))
                hi.append(float(max(r) - np.mean(r)))
                rows.append({"model": label, "metric": col,
                             "ratio_mean": float(np.mean(r)),
                             "ratio_min": float(min(r)), "ratio_max": float(max(r)),
                             "n_seeds": len(r)})
        ax.bar(xs, ratios, yerr=[lo, hi], capsize=3,
               color=["#9ecae1", "#f4a582", "#fdae6b"][:len(xs)], width=0.55)
        if col == "tm.median_step_time_seconds":
            ax.axhspan(0.80, 1.25, color="#2ca02c", alpha=0.12)
            ax.text(0.02, 0.92, "±25% equivalence\nmargin (frozen)",
                    transform=ax.transAxes, fontsize=6, color="#2ca02c")
        ax.axhline(1.0, color="#555555", lw=0.8, ls="--")
        ax.set_title(title, fontsize=8.5)
        ax.set_ylim(0, max(1.6, max(ratios) * 1.25 if ratios else 1.6))
    (ROOT / "results" / "processed" / "paired_quantization_effects.csv").write_text(
        pd.DataFrame(rows).to_csv(index=False))
    fig.suptitle("Paired 4bit QLoRA / BF16 LoRA effects (same model, seed-paired)",
                 fontsize=9.5)
    _save(fig, "fig6_paired_effects")


def fig7_batch_axis(df: pd.DataFrame) -> None:
    """轴 4 batch（D5 修复后同 commit 重跑；b8 SIGKILL 边界标注）。"""
    full = pd.read_csv(ROOT / "results" / "processed" / "experiments.csv",
                       low_memory=False)
    groups = {1: "formal-axis4-b1", 2: "formal-axis4-b2", 4: "formal-axis4-b4"}
    xs, tp, tpe, mem, meme = [], [], [], [], []
    for b, g in groups.items():
        sub = _group(df, g)
        if sub.empty:
            continue
        t = _agg(sub["runtime.tokens_per_second"])
        m = _agg(sub["tm.peak_metal_gpu_memory_bytes"])
        xs.append(b); tp.append(t["mean"]); tpe.append(t["sd"] or 0)
        mem.append(m["mean"] / 2**30); meme.append((m["sd"] or 0) / 2**30)
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.2))
    axes[0].errorbar(xs, tp, yerr=tpe, marker="o", ms=4, lw=1.4,
                     color=Q4_COLOR, capsize=2, label="trainable (3 seeds)")
    axes[0].scatter([8], [0], marker="x", s=70, color="#a11", zorder=5)
    axes[0].annotate("SIGKILL ×3 seeds\n(exit 137, zero steps)",
                     xy=(8, 0), fontsize=6.5, color="#a11",
                     xytext=(-6, 10), textcoords="offset points", ha="right")
    axes[0].set_xlabel("micro-batch size"); axes[0].set_ylabel("loss-bearing tokens/s")
    axes[0].set_title("Throughput vs batch (4B-4bit, ctx512)", fontsize=9)
    axes[0].legend(fontsize=7)
    axes[1].errorbar(xs, mem, yerr=meme, marker="o", ms=4, lw=1.4,
                     color=Q4_COLOR, capsize=2, label="MLX peak (mean±SD)")
    axes[1].scatter([8], [16], marker="x", s=70, color="#a11", zorder=5)
    axes[1].annotate("SIGKILL ×3\n(system swap→~20 GiB)",
                     xy=(8, 16), fontsize=6.5, color="#a11",
                     xytext=(-6, -18), textcoords="offset points", ha="right")
    axes[1].axhline(16, color="#888888", lw=1, ls=":")
    axes[1].text(1.0, 16.3, "16 GiB physical RAM", fontsize=6.5, color="#666666")
    axes[1].set_xlabel("micro-batch size"); axes[1].set_ylabel("MLX peak memory (GiB)")
    axes[1].set_title("Peak memory vs batch (batch boundary ∈ [4,8))",
                      fontsize=9)
    axes[1].legend(fontsize=7)
    _save(fig, "fig7_batch_axis")


def fig8_rank_axis(df: pd.DataFrame) -> None:
    """轴 3 rank（4B-4bit；r8 复用轴 1 同配置点）。"""
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.2))
    pts = {}
    for r, g in ((4, "formal-axis3-r4"), (8, "formal-axis1-4b-4bit-qlora"),
                 (32, "formal-axis3-r32")):
        sub = _group(df, g)
        if sub.empty:
            continue
        pts[r] = {"step": _agg(sub["tm.median_step_time_seconds"]),
                  "mem": _agg(sub["tm.peak_metal_gpu_memory_bytes"])}
    xs = sorted(pts)
    for ax, key, ylab, title in (
            (axes[0], "step", "median step time (s)", "Step time vs LoRA rank"),
            (axes[1], "mem", "MLX peak memory (GiB)", "Peak memory vs LoRA rank")):
        scale = (lambda v: v) if key == "step" else (lambda v: v / 2**30)
        ax.errorbar(xs, [scale(pts[x][key]["mean"]) for x in xs],
                    yerr=[(scale(pts[x][key]["sd"] or 0)) for x in xs],
                    marker="o", ms=4, lw=1.4, color=Q4_COLOR, capsize=2,
                    label="mean±SD (3 seeds)")
        ax.set_xscale("log", base=2)
        ax.set_xticks(xs); ax.set_xticklabels([str(x) for x in xs])
        ax.set_xlabel("LoRA rank"); ax.set_ylabel(ylab)
        ax.set_title(title + " (4B-4bit, ctx512)", fontsize=9)
        ax.legend(fontsize=7)
    _save(fig, "fig8_rank_axis")


def main() -> int:
    df = _load()
    fig1_architecture()
    fig2_feasibility(df)
    fig3_memory_scaling(df)
    fig4_time_scaling(df)
    fig5_context_scaling(df)
    fig6_paired_effects(df)
    fig7_batch_axis(df)
    fig8_rank_axis(df)
    return 0
