"""Step-time dynamics and loss trajectories（D12 事后探索性分析）。

消费此前无人读取的逐 step 工件 `results/processed/step_timings.parquet`
（由 trainer 写入各 raw run 的 step_timings.jsonl，flatten 汇入；仅成功 run
有此文件）+ experiments.csv。全部数字由不可变 raw 派生，禁止手工输入。

分析内容（论文 Sec. "Step-Time Dynamics" 与 "Training Effectiveness"）：
- 每 run 步时分布：p10/p50/p90/p99、mean/SD、变异系数 cv、p99/p50 尾比、
  run 内漂移（后半段中位数 / 前半段中位数）；
- 按组聚合（3 seeds mean±SD）+ Tier 标注（flatten.retained() 的 D4 规则）；
- 逐 step 训练 loss 曲线（seed 均值±min-max 带）与 3 点验证 loss 轨迹；
- warmup 排除与 trainer 口径一致（runtime.excluded_warmup_steps，逐 run）。

输出：
- results/processed/step_dynamics.json
- results/figures/fig9_step_dynamics.{pdf,png}（ECDF + cv-vs-median 散点）
- results/figures/fig10_loss_trajectories.{pdf,png}
- paper/submission/tables/table14_step_dynamics.tex
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .figures import BF16_COLOR, Q4_COLOR, plt, _save, ROOT

PROCESSED = ROOT / "results" / "processed"
TABLES = ROOT / "paper" / "submission" / "tables"

# axis1 展示顺序（图/表）：按规模 × 精度
AXIS1_ORDER = [
    "formal-axis1-0.6b-bf16-lora",
    "formal-axis1-1.7b-bf16-lora",
    "formal-axis1-4b-bf16-lora",
    "formal-axis1-0.6b-4bit-qlora",
    "formal-axis1-1.7b-4bit-qlora",
    "formal-axis1-4b-4bit-qlora",
    "formal-axis1-8b-4bit-qlora",
    "formal-axis1-0.6b-bf16-full",
]
GROUP_LABEL = {
    "formal-axis1-0.6b-bf16-lora": "0.6B BF16 LoRA",
    "formal-axis1-1.7b-bf16-lora": "1.7B BF16 LoRA",
    "formal-axis1-4b-bf16-lora": "4B BF16 LoRA",
    "formal-axis1-0.6b-4bit-qlora": "0.6B 4bit QLoRA",
    "formal-axis1-1.7b-4bit-qlora": "1.7B 4bit QLoRA",
    "formal-axis1-4b-4bit-qlora": "4B 4bit QLoRA",
    "formal-axis1-8b-4bit-qlora": "8B 4bit QLoRA",
    "formal-axis1-0.6b-bf16-full": "0.6B BF16 full FT",
}
TIER_A_COLOR, TIER_B_COLOR = "#1a9850", "#d73027"


def _git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True,
                              cwd=ROOT).stdout.strip()
    except Exception:
        return "unknown"


def _retained_success() -> pd.DataFrame:
    """formal retained success 视图（与 figures._load 同口径）+ _tier。"""
    df = pd.read_csv(PROCESSED / "experiments.csv", low_memory=False)
    formal = df[df["experiment.comparison_group_id"].astype(str)
                .str.startswith("formal-")]
    from .flatten import retained
    ok = retained(formal)
    ok = ok[ok["status.terminal_state"] == "success"].copy()
    ok["runtime.excluded_warmup_steps"] = pd.to_numeric(
        ok["runtime.excluded_warmup_steps"], errors="coerce").fillna(0)
    return ok


def per_run_stats(step_df: pd.DataFrame, runs: pd.DataFrame) -> list[dict]:
    out = []
    meta = runs.set_index("experiment.id")
    for eid, g in step_df.groupby("experiment_id"):
        if eid not in meta.index:
            continue  # 非 formal-retained（probe / 早期调试 / 去重前）
        row = meta.loc[eid]
        warm = int(row["runtime.excluded_warmup_steps"])
        t = g[g["step"] > warm]["step_time_seconds"].to_numpy()
        if len(t) < 10:
            continue
        p10, p50, p90, p99 = np.percentile(t, [10, 50, 90, 99])
        half = len(t) // 2
        first, second = np.median(t[:half]), np.median(t[half:])
        out.append({
            "experiment_id": eid,
            "group": str(row["experiment.comparison_group_id"]),
            "seed": int(row["training.seed"]) if pd.notna(row["training.seed"]) else None,
            "tier": str(row.get("_tier", "")),
            "n_steps": int(len(t)),
            "p10_s": float(p10), "p50_s": float(p50),
            "p90_s": float(p90), "p99_s": float(p99),
            "mean_s": float(np.mean(t)), "sd_s": float(np.std(t, ddof=1)),
            "cv": float(np.std(t, ddof=1) / np.mean(t)),
            "p99_over_p50": float(p99 / p50),
            "drift_second_first": float(second / first) if first > 0 else None,
        })
    return out


def _agg(values: list[float]) -> dict:
    vals = [v for v in values if v is not None]
    if not vals:
        return {"n": 0}
    return {"n": len(vals), "mean": float(np.mean(vals)),
            "sd": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0}


def per_group(stats: list[dict]) -> dict:
    by_group: dict[str, list[dict]] = {}
    for s in stats:
        by_group.setdefault(s["group"], []).append(s)
    out = {}
    for g, rows in by_group.items():
        out[g] = {
            "n_runs": len(rows),
            "tiers": sorted({r["tier"] for r in rows}),
            "p50_s": _agg([r["p50_s"] for r in rows]),
            "p90_s": _agg([r["p90_s"] for r in rows]),
            "p99_s": _agg([r["p99_s"] for r in rows]),
            "cv": _agg([r["cv"] for r in rows]),
            "p99_over_p50": _agg([r["p99_over_p50"] for r in rows]),
            "drift": _agg([r["drift_second_first"] for r in rows]),
        }
    return out


# ---------------------------------------------------------------- 图 9：分布
def fig9_step_dynamics(step_df: pd.DataFrame, runs: pd.DataFrame,
                       stats: list[dict]) -> None:
    # 单栏竖排双面板（减少全宽浮动体数量，缓解两栏排版拥堵）
    fig, axes = plt.subplots(2, 1, figsize=(3.35, 4.7), layout="constrained")
    fig.get_layout_engine().set(h_pad=0.14, hspace=0.06)
    meta = runs.set_index("experiment.id")

    # 上：每组池化 ECDF（log-x）。4bit 蓝系 / BF16 橙系，线型按规模区分
    ax = axes[0]
    shades4 = ["#93c5fd", "#60a5fa", "#2563eb", "#1e40af"]  # 0.6/1.7/4/8B
    shadesB = ["#fdba74", "#f97316"]                          # 0.6/1.7B
    ecdf_series = [
        ("formal-axis1-0.6b-4bit-qlora", shades4[0], "-"),
        ("formal-axis1-1.7b-4bit-qlora", shades4[1], "-"),
        ("formal-axis1-4b-4bit-qlora", shades4[2], "-"),
        ("formal-axis1-8b-4bit-qlora", shades4[3], "-"),
        ("formal-axis1-0.6b-bf16-lora", shadesB[0], "--"),
        ("formal-axis1-1.7b-bf16-lora", shadesB[1], "--"),
    ]
    pooled_by_group: dict[str, np.ndarray] = {}
    for gname, color, ls in ecdf_series:
        eids = [e for e in runs[runs["experiment.comparison_group_id"] == gname]
                ["experiment.id"] if e in set(step_df["experiment_id"])]
        if not eids:
            continue
        pool = []
        for e in eids:
            warm = int(meta.loc[e, "runtime.excluded_warmup_steps"])
            gg = step_df[(step_df["experiment_id"] == e)
                         & (step_df["step"] > warm)]["step_time_seconds"]
            pool.extend(gg.tolist())
        if not pool:
            continue
        v = np.sort(np.asarray(pool))
        pooled_by_group[gname] = v
        ax.step(np.concatenate([v, [v[-1]]]),
                np.arange(1, len(v) + 2) / (len(v) + 1), where="post",
                color=color, ls=ls, lw=1.3,
                label=GROUP_LABEL.get(gname, gname).replace(" LoRA", ""))
    ax.set_xscale("log")
    ax.set_xlabel("step time (s)")
    ax.set_ylabel("ECDF")
    ax.set_title("Step-time distributions (pooled seeds, warmup excl.)",
                 fontsize=8.5)
    ax.legend(fontsize=6.4, loc="lower right", handlelength=1.5)

    # 下：cv vs 中位步时（每 run 一点，Tier 着色）
    ax = axes[1]
    for tier, color, label in ((("A",), TIER_A_COLOR, "Tier-A (<50 MB/step)"),
                               (("B",), TIER_B_COLOR, "Tier-B (paging)")):
        xs = [s["p50_s"] for s in stats if s["tier"] in tier]
        ys = [s["cv"] for s in stats if s["tier"] in tier]
        ax.scatter(xs, ys, s=14, color=color, alpha=0.75, label=label, zorder=3)
    mx = max(stats, key=lambda s: s["cv"])
    ax.annotate(GROUP_LABEL.get(mx["group"], mx["group"]).replace(" QLoRA", ""),
                xy=(mx["p50_s"], mx["cv"]), fontsize=6.5,
                xytext=(4, 2), textcoords="offset points")
    ax.set_xscale("log")
    ax.set_xlabel("median step time (s, per run)")
    ax.set_ylabel("coefficient of variation")
    ax.set_title("Predictability splits by paging tier", fontsize=8.5)
    ax.legend(fontsize=6.8, loc="upper left")
    _save(fig, "fig9_step_dynamics")


# ------------------------------------------------------------- 图 10：loss
def fig10_loss_trajectories(step_df: pd.DataFrame, runs: pd.DataFrame) -> None:
    # 单栏竖排双面板（减少全宽浮动体数量）
    fig, axes = plt.subplots(2, 1, figsize=(3.35, 4.7), layout="constrained")
    fig.get_layout_engine().set(h_pad=0.14, hspace=0.06)
    meta = runs.set_index("experiment.id")

    series = [
        ("formal-axis1-0.6b-4bit-qlora", "#93c5fd", "-"),
        ("formal-axis1-1.7b-4bit-qlora", "#60a5fa", "-"),
        ("formal-axis1-4b-4bit-qlora", "#2563eb", "-"),
        ("formal-axis1-8b-4bit-qlora", "#1e40af", "-"),
        ("formal-axis1-0.6b-bf16-lora", "#fdba74", "--"),
        ("formal-axis1-1.7b-bf16-lora", "#f97316", "--"),
        ("formal-axis1-0.6b-bf16-full", "#b2182b", ":"),
    ]
    ax = axes[0]
    for gname, color, ls in series:
        eids = [e for e in runs[runs["experiment.comparison_group_id"] == gname]
                ["experiment.id"] if e in set(step_df["experiment_id"])]
        curves = []
        for e in eids:
            warm = int(meta.loc[e, "runtime.excluded_warmup_steps"])
            gg = step_df[(step_df["experiment_id"] == e)
                         & (step_df["step"] > warm)].sort_values("step")
            curves.append(gg.set_index("step")["loss"])
        if not curves:
            continue
        mat = pd.concat(curves, axis=1)
        mean = mat.mean(axis=1)
        ax.plot(mean.index, mean.values, color=color, ls=ls, lw=1.3,
                label=GROUP_LABEL.get(gname, gname))
        ax.fill_between(mean.index, mat.min(axis=1), mat.max(axis=1),
                        color=color, alpha=0.15, lw=0)
    ax.set_xlabel("training step (warmup excluded)")
    ax.set_ylabel("training LM loss")
    ax.set_title("Training loss (seed mean, band min–max)",
                 fontsize=8.5)
    ax.legend(fontsize=6.0, ncol=2, loc="upper right")

    # 右：验证 loss 轨迹（steps 0/50/100）
    ax = axes[1]
    for gname, color, ls in series:
        sub = runs[runs["experiment.comparison_group_id"] == gname]
        trajs = []
        for _, r in sub.iterrows():
            raw = r.get("tm.validation_loss_trajectory")
            if not isinstance(raw, str) or not raw:
                continue
            try:
                t = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(t, list) and t:
                trajs.append(([(p["step"], p["loss"]) for p in t
                               if isinstance(p, dict) and "step" in p]))
        if not trajs:
            continue
        steps = [p[0] for p in trajs[0]]
        vals = np.array([[p[1] for p in t] for t in trajs])
        ax.plot(steps, vals.mean(axis=0), color=color, ls=ls, lw=1.3,
                marker="o", ms=3.5,
                label=GROUP_LABEL.get(gname, gname))
        ax.fill_between(steps, vals.min(axis=0), vals.max(axis=0),
                        color=color, alpha=0.15, lw=0)
    ax.set_xlabel("validation point (step)")
    ax.set_ylabel("validation LM loss")
    ax.set_title("Validation loss (3 evals, n=32)", fontsize=8.5)
    ax.set_xticks([0, 50, 100])
    _save(fig, "fig10_loss_trajectories")


# ----------------------------------------------------------------- 表 14
def table14(groups: dict) -> None:
    lines = [
        r"\begin{table*}[t]\centering",
        r"\caption{Step-time distribution statistics per group "
        r"(post-hoc exploratory analysis, D12; per-run percentiles after "
        r"trainer warmup exclusion---5 steps for 100-step runs, 2 for "
        r"20-step runs, per the trainer's measured-interval "
        r"convention---aggregated as mean$\pm$SD over seeds; times in "
        r"seconds). "
        r"cv = SD/mean within a run; tail = p99/p50; drift = median(second "
        r"half)/median(first half). Tier per D4 rule. The 4B BF16 row is "
        r"the single-seed D1 boundary observation; b1 on the batch axis "
        r"reuses the axis-1 4B 4-bit cell.}",
        r"\label{tab:stepdyn}",
        r"\footnotesize\setlength{\tabcolsep}{5pt}",
        r"\begin{tabular}{@{}lrrrrrr@{}}",
        r"\toprule",
        r"Group & p50 (s) & p90 (s) & p99 (s) & cv & tail & drift\\",
        r"\midrule",
    ]

    def cell(v):
        return f"{v['mean']:.2f}" if isinstance(v, dict) and v.get("n") else "--"

    def cell_pm(v, dec=2):
        if not (isinstance(v, dict) and v.get("n")):
            return "--"
        if v.get("sd"):
            return f"${v['mean']:.{dec}f}\\pm{v['sd']:.{dec}f}$"
        return f"${v['mean']:.{dec}f}$"

    compact = {
        "formal-axis1-0.6b-bf16-lora": "0.6B BF16 LoRA",
        "formal-axis1-1.7b-bf16-lora": "1.7B BF16 LoRA",
        "formal-axis1-4b-bf16-lora": "4B BF16 LoRA",
        "formal-axis1-0.6b-4bit-qlora": "0.6B 4bit",
        "formal-axis1-1.7b-4bit-qlora": "1.7B 4bit",
        "formal-axis1-4b-4bit-qlora": "4B 4bit",
        "formal-axis1-8b-4bit-qlora": "8B 4bit",
        "formal-axis1-0.6b-bf16-full": "0.6B full FT",
        # 轴 2/4 与 300-step 重复组（正文动力学叙述引用的第二块）
        "formal-axis2-ctx1024": "ctx1024 (4B 4bit)",
        "formal-axis2-ctx2048": "ctx2048 (4B 4bit)",
        "formal-axis1b-4b-4bit-qlora": "4B 4bit, 300-step (D2)",
        "formal-axis4-b2": "batch 2 (4B 4bit)",
        "formal-axis4-b4": "batch 4 (4B 4bit)",
    }
    extra_order = ["formal-axis2-ctx1024", "formal-axis2-ctx2048",
                   "formal-axis1b-4b-4bit-qlora", "formal-axis4-b2",
                   "formal-axis4-b4"]

    def _emit(glist, midrule_first=False):
        for g in glist:
            if g not in groups:
                continue
            d = groups[g]
            tiers = "/".join(t or "?" for t in d["tiers"])
            lines.append(
                f"{compact.get(g, GROUP_LABEL.get(g, g))} ({tiers}) & "
                f"{cell(d['p50_s'])} & {cell(d['p90_s'])} & {cell(d['p99_s'])} & "
                f"{cell_pm(d['cv'])} & {cell_pm(d['p99_over_p50'])} & "
                f"{cell_pm(d['drift'])}\\\\"
            )

    _emit(AXIS1_ORDER)
    lines.append(r"\midrule")
    _emit(extra_order)
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""]
    TABLES.mkdir(parents=True, exist_ok=True)
    (TABLES / "table14_step_dynamics.tex").write_text(
        "\n".join(lines), encoding="utf-8")
    print("[table] table14_step_dynamics.tex")


# ------------------------------------------------------------------ main
def main() -> int:
    step_df = pd.read_parquet(PROCESSED / "step_timings.parquet")
    runs = _retained_success()
    stats = per_run_stats(step_df, runs)
    groups = per_group(stats)
    payload = {
        "schema_version": "1.0.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "generator_commit": _git_commit(),
        "analysis_kind": "post-hoc exploratory (deviations.md D12)",
        "warmup_exclusion": "per-run runtime.excluded_warmup_steps (trainer "
                            "measured-interval convention)",
        "inputs": ["results/processed/step_timings.parquet",
                   "results/processed/experiments.csv"],
        "per_run": stats,
        "per_group": groups,
    }
    (PROCESSED / "step_dynamics.json").write_text(json.dumps(payload, indent=1))
    fig9_step_dynamics(step_df, runs, stats)
    fig10_loss_trajectories(step_df, runs)
    table14(groups)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
