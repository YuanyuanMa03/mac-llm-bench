"""论文图表生成（预注册 §9；全部从 processed/raw 派生，禁止手工数字）。

输出：results/figures/fig1..fig8 的 PDF+PNG（300 dpi），并将 fig2–fig8 的
PDF 同步到 paper/submission/figures/（论文源码目录，git-ignored——论文成品
只经 arXiv 发布，LaTeX 源码不进仓库）。fig1 例外：论文中使用作者手绘的
PNG（无数据数字的示意图），管线只输出生成版到 results/figures/。
数据源：results/processed/experiments.csv、step_timings.parquet、
context_boundary_probe_summary.json、failure_taxonomy.json。
任何 group 缺失时 fail loudly（不静默空图）。
尺寸约定：正文两栏版式 textwidth≈6.7in / columnwidth≈3.3in——
跨栏图 (7.0in) 配 figure*，单栏图 (3.35in) 配 figure，避免缩放导致字号过小。

视觉规范（顶会母版：GaLore Fig.4 / ZO-benchmark Fig.3 / Apple Silicon
Profiling Fig.4）：图例一律图外顶部横排或图内空白角 frameless；log 轴只标
数据点刻度且关闭 minor locator（先 set_xscale 再 set_xticks，否则被 log
locator 重置）；参考线文字只标线端；数值（slope 等）进图例/caption，
不与数据争夺图内空间；子图间距 constrained layout。
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import NullLocator

from .scaling import fit_scaling_from_group_means, write_scaling_source
from .stats import mean_sd_ci

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "results" / "figures"
PAPER_FIG = ROOT / "paper" / "submission" / "figures"

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 300, "font.size": 9,
    "axes.titlesize": 9.5, "axes.titleweight": "bold", "axes.labelsize": 9,
    "legend.fontsize": 8, "legend.frameon": False,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "axes.linewidth": 0.8, "axes.grid": True, "axes.grid.axis": "y",
    "grid.alpha": 0.35, "grid.linewidth": 0.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "errorbar.capsize": 2,
    "pdf.fonttype": 42,  # TrueType（Type 3 → 42：缩放清晰、文本可检索）
})
# Okabe–Ito 派生色板：蓝(4bit)/橙红(BF16)/砖红(失效)；灰为 RAM 参考线
Q4_COLOR, BF16_COLOR = "#2563eb", "#d55e00"
KILL_COLOR, RAM_COLOR = "#b2182b", "#555555"
GREEN_BG, PURPLE_BG, RED_BG, GRAY_BG = "#dcefdf", "#ece2f2", "#f7d9d9", "#f0f0f0"
GREEN_FG, PURPLE_FG, GRAY_FG = "#1a5c1a", "#6b3fa0", "#777777"


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
    # fig1 在论文中已换成作者手绘 PNG（零数据数字的示意图）：不再把
    # matplotlib 版 PDF 复制进 paper/submission/，避免旧图混入投稿包；
    # results/figures/ 中的生成版仍照常输出并入库
    if name != "fig1_architecture":
        PAPER_FIG.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(FIG / f"{name}.pdf", PAPER_FIG / f"{name}.pdf")
    plt.close(fig)
    print(f"[fig] {FIG / name}.pdf (+paper/submission/figures/ for fig2-8)")


def _model_label(group: str) -> str:
    # formal-axis1-<model>-<method>
    parts = group.split("-")
    idx = parts.index("axis1") if "axis1" in parts else 1
    return "-".join(parts[idx + 1:-1])


def _logx_ticks(ax, vals: list[float], base: int = 10) -> None:
    """log-x 只标数据点刻度。必须在 set_xscale 之后调用，否则手动刻度
    会被 log locator 重置、副刻度以科学计数挤成一团（fig3/fig4 的教训）。"""
    ax.set_xscale("log", base=base)
    ax.set_xticks(vals)
    ax.set_xticklabels([f"{v:g}" for v in vals])
    ax.xaxis.set_minor_locator(NullLocator())
    ax.margins(x=0.08)


def _ram_line(ax, y: float = 16.0, label: str = "16 GiB physical RAM",
              xfrac: float = 0.985, side: str = "right") -> None:
    """RAM 参考线 + 线端短标（Apple-Silicon 母版式：不进图例、不居中压数据）。"""
    ax.axhline(y, color=RAM_COLOR, lw=0.9, ls=(0, (4, 3)), zorder=1)
    lo, hi = ax.get_ylim()
    if ax.get_yscale() == "log":
        f = (np.log(y) - np.log(lo)) / (np.log(hi) - np.log(lo))
    else:
        f = (y - lo) / (hi - lo)
    x = xfrac if side == "right" else 1 - xfrac
    ax.text(x, min(f + 0.055, 0.97), label, transform=ax.transAxes,
            ha=side, va="bottom", fontsize=8, color=RAM_COLOR,
            bbox=dict(boxstyle="square,pad=0.12", fc="white", ec="none",
                      alpha=0.9))


def _legend_out(fig, entries: list, ncol: int) -> None:
    """图例整体外置顶部横排（GaLore/ZO 母版式；只出现一次）。

    entries 项为 (color, label) 或 (color, label, marker)；后者用于标记
    区分（如 BF16 用方点 vs 4bit 用圆点），灰度打印也保持可辨。
    """
    handles = []
    labels = []
    for e in entries:
        color, label = e[0], e[1]
        marker = e[2] if len(e) > 2 else "o"
        handles.append(Line2D([], [], color=color, marker=marker, ms=3.5,
                              lw=1.4))
        labels.append(label)
    fig.legend(handles, labels, loc="outside upper center",
               ncol=ncol, frameon=False, handletextpad=0.5, columnspacing=1.4)


def fig1_architecture() -> None:
    fig, ax = plt.subplots(figsize=(7.0, 2.2))
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
        ax.add_patch(Rectangle((xs[i] - 0.075, 0.35), 0.15, 0.42,
                               fc="#eaf1fd", ec=Q4_COLOR, lw=1.2))
        ax.text(xs[i], 0.60, b, ha="center", va="center", fontsize=8)
        ax.text(xs[i], 0.44, s, ha="center", va="center", fontsize=7,
                color="#555555")
        if i < len(boxes) - 1:
            ax.annotate("", xy=(xs[i + 1] - 0.078, 0.56),
                        xytext=(xs[i] + 0.078, 0.56),
                        arrowprops=dict(arrowstyle="->", lw=1.2, color=Q4_COLOR))
    ax.text(0.5, 0.12, "every number in the paper traces back to an immutable raw result",
            ha="center", fontsize=8, style="italic", color="#444444")
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
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.55), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.18, wspace=0.06)

    def cell(ax, x, y, bg, lines, fg="#333333", fs=7.5, weight="normal"):
        ax.add_patch(Rectangle((x - 0.5, y - 0.5), 1, 1, fc=bg,
                               ec="white", lw=1.6, zorder=1))
        ax.text(x, y, lines, ha="center", va="center", fontsize=fs, color=fg,
                fontweight=weight, linespacing=1.3, zorder=3)

    def strip(ax):
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.tick_params(length=0)

    ax = axes[0]
    models = ["0.6b", "1.7b", "4b", "8b", "14b"]
    methods = ["lora", "qlora", "full"]
    cell_data = {}
    for gname, sub in full.groupby("experiment.comparison_group_id"):
        if not str(gname).startswith("formal-axis1-"):
            continue
        label = str(gname).replace("formal-axis1-", "")
        model, method = label.rsplit("-", 1)
        mkey = model.replace("-bf16", "").replace("-4bit", "")
        n_ok = int((sub["status.terminal_state"] == "success").sum())
        n_all = len(sub)
        cell_data[(method, mkey)] = (n_ok, n_all, sub)
    # 状态分级（deviations D1/D8 的两层定位）：
    #   reproducible success（3/3 formal seeds）
    #   boundary / state-dependent（部分成功或失败均归因系统状态：4B-bf16 D1、14B D8）
    #   runtime failure（非系统状态归因的失败）
    #   untested / out-of-budget（从未运行 / 预注册声明不做）
    BOUNDARY = {("lora", "4b"), ("qlora", "14b")}  # D1 / D8
    OUT_OF_BUDGET = {("lora", "14b"), ("lora", "8b")}  # preregistration §3（8B 为 probe-only）
    probe8 = [p for p in probes["failures"] if "8b" in p["experiment_id"]
              and "qnone" in p["experiment_id"]]
    for i, method in enumerate(methods):
        for j, mkey in enumerate(models):
            n_ok, n_all, sub = cell_data.get((method, mkey), (0, 0, None))
            if (method, mkey) in OUT_OF_BUDGET and n_all == 0:
                txt = "probe:\ntimeout" if (mkey == "8b" and probe8) else "out-of\nbudget"
                cell(ax, j, i, GRAY_BG, txt, fg=GRAY_FG)
            elif n_all == 0:
                cell(ax, j, i, "white", "untested", fg=GRAY_FG)
            elif n_ok == n_all and n_ok >= 3:
                cell(ax, j, i, GREEN_BG, "✓ 3/3", fg=GREEN_FG, fs=8,
                     weight="bold")
            elif (method, mkey) in BOUNDARY:
                if n_ok:
                    cell(ax, j, i, PURPLE_BG, f"◐ {n_ok}/{n_all}\nstate-\ndep. (D1)",
                         fg=PURPLE_FG, fs=6.1, weight="bold")
                else:
                    cell(ax, j, i, PURPLE_BG, "◐ state-\ndep.\n(D8)",
                         fg=PURPLE_FG, fs=6.1, weight="bold")
            else:
                # 失败态单元格：状态名缩写为短码并按状态分行计数，避免长文本
                # 溢出单元格（缩写图例见 main.tex fig2 caption）
                abbr = {"success": "ok", "user_interrupted": "intr",
                        "timeout": "t/o", "runtime_error": "err"}
                counts = sub["status.terminal_state"].value_counts()
                parts = [f"{int(n)}×{abbr.get(str(s), str(s)[:4])}"
                         for s, n in counts.items()]
                cell(ax, j, i, RED_BG, "✗ " + "\n".join(parts),
                     fg=KILL_COLOR, fs=7)
    ax.set_xticks(range(len(models)), models)
    ax.set_yticks(range(len(methods)), ["BF16 LoRA", "4bit QLoRA", "Full FT"])
    ax.set_xlim(-0.5, len(models) - 0.5)
    ax.set_ylim(len(methods) - 0.5, -0.5)
    strip(ax)
    ax.set_title("Model-scale feasibility @ ctx512", fontsize=9.5)

    ax = axes[1]
    ctxs = ["512", "1024", "2048", "4096", "8192"]
    ok_groups = set(df["experiment.comparison_group_id"])
    for j, c in enumerate(ctxs):
        if c in ("4096", "8192"):
            cell(ax, j, 0, RED_BG, "✗ SIGKILL\n(probe)", fg=KILL_COLOR, fs=7)
        elif c == "512":
            # 预注册复用轴 1 的 4B-4bit cell（3/3 success），非 untested
            cell(ax, j, 0, GREEN_BG, "✓\n(reuse a1)", fg=GREEN_FG, fs=7)
        elif f"formal-axis2-ctx{c}" in ok_groups:
            cell(ax, j, 0, GREEN_BG, "✓", fg=GREEN_FG, fs=9.5, weight="bold")
        else:
            cell(ax, j, 0, "white", "untested", fg=GRAY_FG)
    ax.set_xticks(range(len(ctxs)), ctxs)
    ax.set_yticks([0], ["4B 4bit\nQLoRA"])
    ax.set_xlim(-0.5, len(ctxs) - 0.5)
    ax.set_ylim(0.5, -0.5)
    strip(ax)
    ax.set_title("Maximum sequence-length cap (4B-4bit)", fontsize=9.5)
    _save(fig, "fig2_feasibility_map")


def fig3_memory_scaling(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(3.35, 3.0), layout="constrained")
    # BF16 的 4B 点为 D1 边界观测（1/3 种子、零驻留窗口），以开口标记画出并
    # 计入拟合——与 summary.py / key_numbers.json 的 n=3 拟合口径一致
    # 值 = (color, marker)；BF16 用方点与 4bit 圆点区分（灰度打印也可辨）
    series = {
        "BF16 LoRA": (BF16_COLOR, "s",
                      ["formal-axis1-0.6b-bf16-lora",
                       "formal-axis1-1.7b-bf16-lora"],
                      ["formal-axis1-4b-bf16-lora"]),
        "4bit QLoRA": (Q4_COLOR, "o",
                       ["formal-axis1-0.6b-4bit-qlora",
                        "formal-axis1-1.7b-4bit-qlora",
                        "formal-axis1-4b-4bit-qlora",
                        "formal-axis1-8b-4bit-qlora"],
                       []),
    }
    fits = {}
    all_xs: set[float] = set()
    legend_entries = []
    for label, (color, marker, gnames, boundary_gnames) in series.items():
        xs, ys, es = [], [], []
        for g in gnames + boundary_gnames:
            sub = _group(df, g)
            if sub.empty:
                continue
            params_b = float(sub["tm.logical_parameter_count"].iloc[0]) / 1e9
            mem = _agg(sub["tm.peak_metal_gpu_memory_bytes"])
            xs.append(params_b)
            ys.append(mem["mean"] / 2**30)
            es.append(mem["sd"] / 2**30 if mem["sd"] else 0)
        all_xs.update(round(x, 2) for x in xs)
        n_formal = len(gnames)
        ax.errorbar(xs[:n_formal], ys[:n_formal], yerr=es[:n_formal],
                    marker=marker, ms=4, lw=1.4, color=color, capsize=2)
        if len(xs) > n_formal:
            ax.scatter(xs[n_formal:], ys[n_formal:], s=22, facecolors="none",
                       edgecolors=color, linewidths=1.4, zorder=5, marker=marker)
            ax.annotate("D1", xy=(xs[-1], ys[-1]), fontsize=7, color=color,
                        xytext=(6, -6), textcoords="offset points",
                        ha="left", va="top", fontweight="bold",
                        bbox=dict(boxstyle="square,pad=0.15", fc="white",
                                  ec="none", alpha=0.8))
            ax.plot(xs[n_formal - 1:], ys[n_formal - 1:], lw=1.0,
                    color=color, alpha=0.5)
        series_key = "bf16_lora" if label == "BF16 LoRA" else "4bit_qlora"
        fit = fit_scaling_from_group_means(
            df, series_key, "tm.peak_metal_gpu_memory_bytes", 2**30)
        if fit:
            fits[label] = fit
            xx = np.logspace(np.log10(min(xs)), np.log10(max(xs)), 50)
            ax.plot(xx, 10 ** fit["intercept"] * xx ** fit["slope"], "--",
                    color=color, alpha=0.6, lw=1)
            legend_entries.append((color, f"{label} (slope {fit['slope']:.2f})",
                                   marker))
        else:
            legend_entries.append((color, label, marker))
    # slope 数值进图例（GaLore 母版式），CI/R²/n 见 Table 9
    _legend_out(fig, legend_entries, ncol=1)
    ax.set_yscale("log")
    ax.set_ylim(1.0, 26)
    _logx_ticks(ax, sorted(all_xs))
    _ram_line(ax, 16, xfrac=0.985)
    ax.set_xlabel("logical parameters (B)")
    ax.set_ylabel("MLX peak memory (GiB)")
    ax.set_title("Peak memory vs model scale (ctx512)", fontsize=8)
    (ROOT / "results" / "processed" / "memory_scaling_fits.json").write_text(
        json.dumps(fits, indent=2) + "\n")
    _save(fig, "fig3_memory_scaling")


def fig4_time_scaling(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.2, wspace=0.06)
    # 同 fig3：BF16 的 4B 点为 D1 边界观测，开口标记并计入拟合（n=3）
    # 值 = (color, marker)；BF16 方点 vs 4bit 圆点（灰度可辨）
    series = {
        "BF16 LoRA": (BF16_COLOR, "s",
                      ["formal-axis1-0.6b-bf16-lora",
                       "formal-axis1-1.7b-bf16-lora"],
                      ["formal-axis1-4b-bf16-lora"]),
        "4bit QLoRA": (Q4_COLOR, "o",
                       ["formal-axis1-0.6b-4bit-qlora",
                        "formal-axis1-1.7b-4bit-qlora",
                        "formal-axis1-4b-4bit-qlora",
                        "formal-axis1-8b-4bit-qlora"],
                       []),
    }
    fits = {}
    all_xs4: set[float] = set()
    legend_entries = []
    for label, (color, marker, gnames, boundary_gnames) in series.items():
        xs, st, ste, tp, tpe = [], [], [], [], []
        for g in gnames + boundary_gnames:
            sub = _group(df, g)
            if sub.empty:
                continue
            params_b = float(sub["tm.logical_parameter_count"].iloc[0]) / 1e9
            a = _agg(sub["tm.median_step_time_seconds"])
            t = _agg(sub["runtime.tokens_per_second"])
            xs.append(params_b)
            st.append(a["mean"]); ste.append(a["sd"] or 0)
            tp.append(t["mean"]); tpe.append(t["sd"] or 0)
        all_xs4.update(round(x, 2) for x in xs)
        n_formal = len(gnames)
        for ax_i, ys_, es_ in ((axes[0], st, ste), (axes[1], tp, tpe)):
            ax_i.errorbar(xs[:n_formal], ys_[:n_formal], yerr=es_[:n_formal],
                          marker=marker, ms=4, lw=1.4, color=color, capsize=2)
        if len(xs) > n_formal:
            for ax_i, ys_ in ((axes[0], st), (axes[1], tp)):
                ax_i.scatter(xs[n_formal:], ys_[n_formal:], s=22,
                             facecolors="none", edgecolors=color,
                             linewidths=1.4, zorder=5, marker=marker)
                ax_i.plot(xs[n_formal - 1:], ys_[n_formal - 1:], lw=1.0,
                          color=color, alpha=0.5)
                axes[0].annotate("D1", xy=(xs[-1], st[-1]), fontsize=7,
                                 color=color, xytext=(6, -7),
                                 textcoords="offset points", ha="left",
                                 va="top", fontweight="bold")
        series_key = "bf16_lora" if label == "BF16 LoRA" else "4bit_qlora"
        fit = fit_scaling_from_group_means(
            df, series_key, "tm.median_step_time_seconds")
        if fit:
            fits[label] = fit
            xx = np.logspace(np.log10(min(xs)), np.log10(max(xs)), 50)
            axes[0].plot(xx, 10 ** fit["intercept"] * xx ** fit["slope"], "--",
                         color=color, alpha=0.6, lw=1)
            legend_entries.append((color, f"{label} (step-time slope "
                                          f"{fit['slope']:.2f})", marker))
        else:
            legend_entries.append((color, label, marker))
    # 图例只出现一次（ZO 母版式）：跨面板共享系列 + 步时拟合斜率
    _legend_out(fig, legend_entries, ncol=2)
    for ax, ylab, title in ((axes[0], "median step time (s)",
                             "Step time vs scale"),
                            (axes[1], "loss-bearing tokens/s",
                             "Throughput vs scale")):
        ax.set_yscale("log")
        _logx_ticks(ax, sorted(all_xs4))
        ax.set_xlabel("logical parameters (B)"); ax.set_ylabel(ylab)
        ax.set_title(title, fontsize=9.5)
    (ROOT / "results" / "processed" / "step_time_scaling_fits.json").write_text(
        json.dumps(fits, indent=2) + "\n")
    _save(fig, "fig4_time_scaling")


def fig5_context_scaling(df: pd.DataFrame) -> None:
    boundary = json.loads((ROOT / "results" / "processed" /
                           "context_boundary_probe_summary.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.2, wspace=0.06)
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
    ctx_ticks = [512, 1024, 2048, 4096, 8192]
    legend_entries = [(Q4_COLOR, "formal, mean±SD (3 seeds)")]

    axes[0].errorbar(xs, [pts[x]["step"]["mean"] for x in xs],
                     yerr=[pts[x]["step"]["sd"] or 0 for x in xs],
                     marker="o", ms=4, color=Q4_COLOR, lw=1.4, capsize=2)
    kills = [f for f in boundary["series"]
             if f["terminal_state"] != "success"
             and f["sequence_length"] >= 4096]
    # 失败标记放在数据带之上的固定高度，共用一条短标注（长说明留 caption）
    kill_y = 60
    if kills:
        kxs = [f["sequence_length"] for f in kills]
        axes[0].scatter(kxs, [kill_y] * len(kxs), marker="x", s=55,
                        color=KILL_COLOR, zorder=5)
        axes[0].annotate("SIGKILL (0 steps)",
                         xy=(float(np.mean(kxs)), kill_y), fontsize=8,
                         color=KILL_COLOR, xytext=(0, 9),
                         textcoords="offset points", ha="center",
                         fontweight="bold")
        legend_entries.append((KILL_COLOR, "SIGKILL before step 1 (cap≥4096, probe)"))
    axes[0].axvspan(4096, 8192, color="#f6d3d3", alpha=0.4, zorder=0)
    axes[0].set_yscale("log")
    axes[0].set_ylim(0.2, 300)
    _logx_ticks(axes[0], ctx_ticks)
    axes[0].set_xlim(400, 14000)
    axes[0].set_xlabel("maximum sequence-length cap"); axes[0].set_ylabel("median step time (s)")
    axes[0].set_title("Step time vs cap (4B-4bit QLoRA, b1)", fontsize=9.5)

    axes[1].errorbar(xs, [pts[x]["mem"]["mean"] / 2**30 for x in xs],
                     yerr=[(pts[x]["mem"]["sd"] or 0) / 2**30 for x in xs],
                     marker="o", ms=4, color=Q4_COLOR, lw=1.4, capsize=2)
    axes[1].axvspan(4096, 8192, color="#f6d3d3", alpha=0.4, zorder=0)
    axes[1].set_yscale("log")
    axes[1].set_ylim(10, 60)
    _logx_ticks(axes[1], ctx_ticks)
    axes[1].set_xlim(400, 14000)
    _ram_line(axes[1], 16, xfrac=0.985)
    axes[1].set_xlabel("maximum sequence-length cap")
    axes[1].set_ylabel("MLX peak memory (GiB)")
    axes[1].set_title("Peak memory vs cap", fontsize=9.5)
    _legend_out(fig, legend_entries, ncol=2)
    _save(fig, "fig5_context_scaling")


def fig6_paired_effects(df: pd.DataFrame) -> None:
    from .stats import paired_ratio
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.4), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.2, wspace=0.06)
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
               color=["#9ecae1", "#f4a582", "#fdae6b"][:len(xs)],
               hatch=["", "//", "xx"][:len(xs)], width=0.55)
        if col == "tm.median_step_time_seconds":
            ax.axhspan(0.80, 1.25, color="#2ca02c", alpha=0.12, zorder=0)
            ax.text(0.02, 0.90, "±25% equivalence margin (frozen)",
                    transform=ax.transAxes, fontsize=8, color="#2ca02c")
        ax.axhline(1.0, color="#555555", lw=0.8, ls="--")
        ax.set_title(title, fontsize=9.5)
        ax.set_ylim(0, max(1.6, max(ratios) * 1.25 if ratios else 1.6))
    (ROOT / "results" / "processed" / "paired_quantization_effects.csv").write_text(
        pd.DataFrame(rows).to_csv(index=False))
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
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.2, wspace=0.06)
    axes[0].errorbar(xs, tp, yerr=tpe, marker="o", ms=4, lw=1.4,
                     color=Q4_COLOR, capsize=2, label="trainable (3 seeds)")
    axes[0].scatter([8], [0], marker="x", s=70, color=KILL_COLOR, zorder=5)
    axes[0].annotate("SIGKILL ×3 seeds\n(exit 137, zero steps)",
                     xy=(8, 0), fontsize=8, color=KILL_COLOR,
                     xytext=(-10, 12), textcoords="offset points", ha="right",
                     bbox=dict(boxstyle="square,pad=0.18", fc="white",
                               ec="none", alpha=1.0))
    axes[0].set_xticks([1, 2, 4, 8])
    axes[0].set_ylim(0, max(tp) * 1.3)
    axes[0].set_xlabel("micro-batch size"); axes[0].set_ylabel("loss-bearing tokens/s")
    axes[0].set_title("Throughput vs batch (4B-4bit, ctx512)", fontsize=9.5)

    axes[1].errorbar(xs, mem, yerr=meme, marker="o", ms=4, lw=1.4,
                     color=Q4_COLOR, capsize=2)
    axes[1].scatter([8], [16], marker="x", s=70, color=KILL_COLOR, zorder=5)
    axes[1].annotate("SIGKILL ×3\n(system swap→~20 GiB)",
                     xy=(8, 16), fontsize=8, color=KILL_COLOR,
                     xytext=(-10, -20), textcoords="offset points", ha="right",
                     va="top",
                     bbox=dict(boxstyle="square,pad=0.18", fc="white",
                               ec="none", alpha=1.0))
    axes[1].set_xticks([1, 2, 4, 8])
    axes[1].set_ylim(0, 26)
    _ram_line(axes[1], 16, xfrac=0.985)
    axes[1].set_xlabel("micro-batch size"); axes[1].set_ylabel("MLX peak memory (GiB)")
    axes[1].set_title("Peak memory vs batch (batch boundary ∈ [4,8))",
                      fontsize=9.5)
    _legend_out(fig, [(Q4_COLOR, "trainable (3 seeds)", "o"),
                      (KILL_COLOR, "SIGKILL ×3 (probe)", "x")], ncol=2)
    _save(fig, "fig7_batch_axis")


def fig8_rank_axis(df: pd.DataFrame) -> None:
    """轴 3 rank：相对 r8 的百分比，避免窄绝对轴夸大微小差异。"""
    fig, axes = plt.subplots(2, 1, figsize=(3.35, 4.55), layout="constrained")
    fig.get_layout_engine().set(h_pad=0.14, hspace=0.06)
    pts = {}
    for r, g in ((4, "formal-axis3-r4"), (8, "formal-axis1-4b-4bit-qlora"),
                 (32, "formal-axis3-r32")):
        sub = _group(df, g)
        if sub.empty:
            continue
        pts[r] = {"step": _agg(sub["tm.median_step_time_seconds"]),
                  "mem": _agg(sub["tm.peak_metal_gpu_memory_bytes"])}
    xs = sorted(pts)
    source_rows = []
    for ax, key, ylab, title in (
            (axes[0], "step", "change from rank 8 (%)", "Step-time change vs rank 8"),
            (axes[1], "mem", "change from rank 8 (%)", "Peak-memory change vs rank 8")):
        scale = (lambda v: v) if key == "step" else (lambda v: v / 2**30)
        baseline = scale(pts[8][key]["mean"])
        means = [100 * (scale(pts[x][key]["mean"]) / baseline - 1) for x in xs]
        errors = [100 * scale(pts[x][key]["sd"] or 0) / baseline for x in xs]
        ax.errorbar(xs, means, yerr=errors,
                    marker="o", ms=4, lw=1.4, color=Q4_COLOR, capsize=2)
        ax.axhline(0, color="#555555", lw=0.8, ls="--")
        extent = max([abs(v) + e for v, e in zip(means, errors)] + [5.0])
        ax.set_ylim(-extent * 1.15, extent * 1.15)
        _logx_ticks(ax, xs, base=2)
        ax.set_ylabel(ylab)
        ax.set_title(title, fontsize=9.5)
        for rank, value, error in zip(xs, means, errors):
            source_rows.append({"rank": rank, "metric": key,
                                "relative_change_percent": value,
                                "relative_sd_percent": error})
        if ax is axes[1]:
            ax.set_xlabel("LoRA rank")
    pd.DataFrame(source_rows).to_csv(
        ROOT / "results" / "processed" / "rank_relative_effects.csv", index=False)
    _legend_out(fig, [(Q4_COLOR, "mean±SD (3 seeds)")], ncol=1)
    _save(fig, "fig8_rank_axis")


def main() -> int:
    df = _load()
    write_scaling_source(df)
    fig1_architecture()
    fig2_feasibility(df)
    fig3_memory_scaling(df)
    fig4_time_scaling(df)
    fig5_context_scaling(df)
    fig6_paired_effects(df)
    fig7_batch_axis(df)
    fig8_rank_axis(df)
    return 0
