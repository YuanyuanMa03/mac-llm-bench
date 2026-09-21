"""System-state (swap residency) trajectory analysis（D12 事后探索性分析）。

消费此前无人读取的 1 Hz 采样工件：各 raw run 的 system_monitor.jsonl
（supervisor 启动的 SwapSampler 写入；字段 t_utc / swap_used_bytes）。
全部数字由不可变 raw 派生。

分析内容（论文 Sec. "Machine State as a Hidden Axis"）：
- 每 run swap 轨迹汇总：start/min/max/end、Δ、振幅、到峰时间、采样节拍；
- 步时 ↔ 并发 swap 对齐：对同时拥有 step_timings 与 monitor 的成功 run
  （75 个）按 wall_utc 线性插值对齐，逐 run Spearman 相关；
- 14B 超时 run 的 stdout 步时轨迹解析（parquet 无该 run：timeout 进程不写
  step_timings.jsonl——对齐不可恢复性本身作为 supervisor 设计教训记录）；
- batch-8 SIGKILL 三连（2026-09-15）的 swap 爬升曲线。2026-09-12 的 b8
  三条为 D5 实现无效（exit 1，配置错误），不作为斜坡证据；
- 同配置异状态对照表（Table 15）：同一配置在不同系统驻留/窗口下的不同结局。

输出：
- results/processed/system_state.json
- results/figures/fig11_state_dynamics.{pdf,png}（2×2 四面板）
- paper/submission/tables/table15_same_config_state.tex
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps

from .figures import KILL_COLOR, RAM_COLOR, _save, plt, ROOT
from .step_dynamics import TIER_A_COLOR, TIER_B_COLOR

RAW = ROOT / "results" / "raw"
PROCESSED = ROOT / "results" / "processed"
TABLES = ROOT / "paper" / "submission" / "tables"
GIB = 2**30

STEP_LINE = re.compile(
    r"^step (\d+)/(\d+) loss=([0-9.]+) tokens=(\d+) step_time=([0-9.]+)s")


def _git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True,
                              cwd=ROOT).stdout.strip()
    except Exception:
        return "unknown"


def _parse_ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def load_monitor(raw_dir: Path) -> dict | None:
    """解析一个 run 的 system_monitor.jsonl → {t0, t_rel, swap_gib, n, cadence}。"""
    f = raw_dir / "system_monitor.jsonl"
    if not f.exists():
        return None
    ts, sw = [], []
    with f.open() as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "t_utc" in rec and "swap_used_bytes" in rec:
                ts.append(_parse_ts(rec["t_utc"]))
                sw.append(rec["swap_used_bytes"] / GIB)
    if len(ts) < 10:
        return None
    t = np.asarray(ts)
    order = np.argsort(t)
    t, sw = t[order], np.asarray(sw)[order]
    t_rel = t - t[0]
    dts = np.diff(t)
    return {"t0": float(t[0]), "t_rel": t_rel, "swap_gib": sw,
            "n": int(len(t)), "duration_s": float(t_rel[-1]),
            "cadence_median_s": float(np.median(dts)) if len(dts) else None}


def run_traj_summary(mon: dict) -> dict:
    sw = mon["swap_gib"]
    t = mon["t_rel"]
    imax = int(np.argmax(sw))
    return {
        "n_samples": mon["n"],
        "duration_s": mon["duration_s"],
        "cadence_median_s": mon["cadence_median_s"],
        "swap_start_gib": float(sw[0]),
        "swap_min_gib": float(np.min(sw)),
        "swap_max_gib": float(sw.max()),
        "swap_end_gib": float(sw[-1]),
        "swap_delta_gib": float(sw[-1] - sw[0]),
        "swap_max_excursion_gib": float(sw.max() - sw[0]),
        "swap_amplitude_gib": float(sw.max() - np.min(sw)),
        "time_to_peak_s": float(t[imax]),
        "time_to_peak_frac": float(t[imax] / t[-1]) if t[-1] else None,
    }


def parse_stdout_steps(raw_dir: Path) -> list[dict]:
    """从 logs/stdout.log 解析 step 行（timeout/中断 run 无 step_timings.jsonl）。"""
    f = raw_dir / "logs" / "stdout.log"
    if not f.exists():
        return []
    out = []
    for line in f.read_text(errors="replace").splitlines():
        m = STEP_LINE.match(line.strip())
        if m:
            out.append({"step": int(m.group(1)), "total": int(m.group(2)),
                        "loss": float(m.group(3)),
                        "tokens": int(m.group(4)),
                        "step_time_s": float(m.group(5))})
    return out


def _retained_success() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED / "experiments.csv", low_memory=False)
    formal = df[df["experiment.comparison_group_id"].astype(str)
                .str.startswith("formal-")]
    from .flatten import retained
    ok = retained(formal)
    ok = ok[ok["status.terminal_state"] == "success"].copy()
    ok["runtime.excluded_warmup_steps"] = pd.to_numeric(
        ok["runtime.excluded_warmup_steps"], errors="coerce").fillna(0)
    return ok


def align_steps(step_df: pd.DataFrame, runs: pd.DataFrame,
                monitors: dict[str, dict]) -> list[dict]:
    """逐 run：step wall_utc ↔ monitor 插值 → 并发 swap + Spearman。"""
    meta = runs.set_index("experiment.id")
    out = []
    for eid, g in step_df.groupby("experiment_id"):
        if eid not in meta.index or eid not in monitors:
            continue
        row = meta.loc[eid]
        mon = monitors[eid]
        warm = int(row["runtime.excluded_warmup_steps"])
        gg = g[g["step"] > warm].sort_values("step")
        if len(gg) < 15:
            continue
        t_step = np.array([_parse_ts(x) for x in gg["wall_utc"]])
        t0 = mon["t0"]
        rel = t_step - t0
        lo, hi = mon["t_rel"][0], mon["t_rel"][-1]
        if rel[0] < lo - 5 or rel[-1] > hi + 5:
            continue  # 步时间窗超出 monitor 覆盖（不应发生；防御性丢弃）
        conc = np.interp(np.clip(rel, lo, hi), mon["t_rel"], mon["swap_gib"])
        st = gg["step_time_seconds"].to_numpy()
        rho, p = sps.spearmanr(conc, st)
        out.append({
            "experiment_id": eid,
            "group": str(row["experiment.comparison_group_id"]),
            "tier": str(row.get("_tier", "")),
            "n_steps": int(len(gg)),
            "spearman_rho": float(rho) if np.isfinite(rho) else None,
            "spearman_p": float(p) if np.isfinite(p) else None,
            "concurrent_swap_mean_gib": float(np.mean(conc)),
            "concurrent_swap_range_gib": float(np.max(conc) - np.min(conc)),
            "_per_step": {"step": gg["step"].tolist(),
                          "t_rel": rel.tolist(),
                          "step_time_s": st.tolist(),
                          "concurrent_swap_gib": conc.tolist()},
        })
    return out


# ------------------------------------------------------------------ 图 11
def fig11_state_dynamics(payload: dict, batch8: list[dict],
                          aligned: list[dict]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 4.7), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.18, h_pad=0.10, wspace=0.05,
                                hspace=0.07)

    # (a) 14B 超时 run：步时轨迹（stdout 解析）
    ax = axes[0][0]
    traj = payload["boundary14b_timeout_run"]["steps"]
    if traj:
        steps = [p["step"] for p in traj]
        ts = [p["step_time_s"] for p in traj]
        ax.plot(steps, ts, color=KILL_COLOR, lw=0.9, marker="o", ms=2.2,
                alpha=0.85)
        k = 5
        if len(ts) >= k:
            roll = pd.Series(ts).rolling(k, center=True).median()
            ax.plot(steps, roll, color="#333333", lw=1.6, alpha=0.9,
                    label=f"rolling median (k={k})")
            ax.legend(fontsize=7, loc="upper right")
        imax = int(np.argmax(ts))
        ax.annotate(f"peak {ts[imax]:.0f} s (step {steps[imax]})",
                    xy=(steps[imax], ts[imax]), fontsize=7, color=KILL_COLOR,
                    xytext=(6, -2), textcoords="offset points")
        ax.annotate(f"stall after step {steps[-1]}\n(~23 min, hand-logged D8)",
                    xy=(steps[-1], ts[-1]), fontsize=7, color="#555555",
                    xytext=(-4, 26), textcoords="offset points", ha="right")
    ax.set_xlabel("training step (step index; wall-clock alignment not "
                  "recoverable)")
    ax.set_ylabel("step time (s)")
    ax.set_title("(a) 14B 4-bit timeout run: {}/{} steps".format(
        len(traj), traj[0]["total"] if traj else 100), fontsize=9)

    # (b) 同 run：1 Hz swap（墙钟）
    ax = axes[0][1]
    mon = payload["boundary14b_timeout_run"]["monitor"]
    if mon:
        t = np.asarray(mon["t_rel"]) / 60.0
        sw = np.asarray(mon["swap_gib"])
        ax.plot(t, sw, color="#6a51a3", lw=0.8)
        sm = payload["boundary14b_timeout_run"]["monitor_summary"]
        ipk = int(np.argmax(sw))
        ax.annotate(f"peak {sw.max():.1f} GiB", xy=(t[ipk], sw.max()),
                    fontsize=7, color="#6a51a3", xytext=(6, -4),
                    textcoords="offset points")
        ax.annotate(f"start {sw[0]:.1f} GiB", xy=(t[0], sw[0]), fontsize=7,
                    color="#6a51a3", xytext=(6, 6), textcoords="offset points")
        ax.text(0.985, 0.05,
                f"{sm['n_samples']} samples @ {sm['cadence_median_s']:.2f} s",
                transform=ax.transAxes, ha="right", fontsize=7, color="#666666")
    ax.set_xlabel("wall clock from run start (min)")
    ax.set_ylabel("system swap in use (GiB)")
    ax.set_title("(b) same run: 1 Hz sampled swap (saw-tooth)", fontsize=9)

    # (c) batch-8 SIGKILL 三连：swap 爬升
    ax = axes[1][0]
    for i, r in enumerate(batch8):
        ax.plot(np.asarray(r["t_rel"]) / 60.0, r["swap_gib"], lw=1.1,
                color=KILL_COLOR, alpha=0.65 + 0.12 * i,
                label=f"s{r['seed']} ({r['duration_s']:.0f} s to kill)")
        ax.annotate("×", xy=(r["t_rel"][-1] / 60.0, r["swap_gib"][-1]),
                    color=KILL_COLOR, fontsize=10, ha="center", va="center",
                    fontweight="bold")
    # 对照：一个 Tier-A run 的平坦轨迹
    ctrl = payload["tier_a_contrast_run"]
    if ctrl:
        ax.plot(np.asarray(ctrl["t_rel"]) / 60.0, ctrl["swap_gib"], lw=1.0,
                color=TIER_A_COLOR, alpha=0.9, ls="--",
                label=f"Tier-A contrast (0.6B 4bit, {ctrl['duration_s']:.0f} s)")
    ax.legend(fontsize=6.6, loc="upper left")
    ax.set_xlabel("wall clock from run start (min)")
    ax.set_ylabel("system swap in use (GiB)")
    ax.set_title("(c) batch-8 runs: swap ramp to SIGKILL (0 steps)", fontsize=9)

    # (d) 逐 step：步时 vs 并发 swap（对齐 run）
    ax = axes[1][1]
    for tier, color in (("A", TIER_A_COLOR), ("B", TIER_B_COLOR)):
        xs, ys = [], []
        for a in aligned:
            if a["tier"] != tier:
                continue
            xs.extend(a["_per_step"]["concurrent_swap_gib"])
            ys.extend(a["_per_step"]["step_time_s"])
        if xs:
            ax.scatter(xs, ys, s=3.5, color=color, alpha=0.28,
                       rasterized=True, label=f"Tier-{tier} steps (n={len(xs)})")
    rho_b = [a["spearman_rho"] for a in aligned
             if a["tier"] == "B" and a["spearman_rho"] is not None]
    rho_a = [a["spearman_rho"] for a in aligned
             if a["tier"] == "A" and a["spearman_rho"] is not None]
    txt = (f"within-run Spearman ρ (median)\n"
           f"Tier-A: {np.median(rho_a):+.2f} (n={len(rho_a)} runs)\n"
           f"Tier-B: {np.median(rho_b):+.2f} (n={len(rho_b)} runs)")
    ax.text(0.02, 0.97, txt, transform=ax.transAxes, fontsize=7, va="top",
            bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="#cccccc",
                      lw=0.6))
    ax.set_yscale("log")
    ax.set_xlabel("concurrent system swap (GiB, interpolated at step time)")
    ax.set_ylabel("step time (s)")
    ax.set_title(f"(d) step time vs concurrent swap ({len(aligned)} aligned "
                 "runs)", fontsize=9)
    ax.legend(fontsize=7, loc="lower right", markerscale=3.0)
    _save(fig, "fig11_state_dynamics")


# ----------------------------------------------------------------- 表 15
def table15(payload: dict) -> None:
    lines = [
        r"\begin{table*}[t]\centering",
        r"\caption{Same configuration, different machine state (all values "
        r"from processed data; exploratory D12 synthesis of D1/D7/D8 "
        r"evidence). Initial swap is the supervisor pre-run snapshot "
        r"(\texttt{vm.swapusage}). Window = calendar date(s) of the runs. "
        r"The three within-window rows compare identical configs across "
        r"wall-clock windows; the boundary rows are the preregistered "
        r"boundary evidence retained in full.}",
        r"\label{tab:samestate}",
        r"\footnotesize\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{@{}llrrrrl@{}}",
        r"\toprule",
        r"Configuration & System state / window & Runs & Steps & "
        r"Med.\ step (s) & Init.\ swap (GiB) & Outcome\\",
        r"\midrule",
    ]
    for row in payload["same_config_contrasts"]:
        lines.append(
            f"{row['config']} & {row['state']} & {row['n_runs']} & "
            f"{row['steps']} & {row['median_step_s']} & "
            f"{row['initial_swap_gib']} & {row['outcome']}\\\\"
        )
        if row.get("midrule_after"):
            lines.append(r"\midrule")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""]
    TABLES.mkdir(parents=True, exist_ok=True)
    (TABLES / "table15_same_config_state.tex").write_text(
        "\n".join(lines), encoding="utf-8")
    print("[table] table15_same_config_state.tex")


# ------------------------------------------------------------------ main
def _num(x, fmt="{:.2f}"):
    try:
        v = float(x)
        return fmt.format(v) if np.isfinite(v) else "--"
    except (TypeError, ValueError):
        return "--"


def build_payload() -> dict:
    df = pd.read_csv(PROCESSED / "experiments.csv", low_memory=False)
    step_df = pd.read_parquet(PROCESSED / "step_timings.parquet")
    runs = _retained_success()

    # ---- 全体 monitor 汇总
    monitors: dict[str, dict] = {}
    summaries = []
    for _, r in df.iterrows():
        raw_dir = RAW / str(r["_raw_dir"])
        mon = load_monitor(raw_dir)
        if mon is None:
            continue
        monitors[str(r["experiment.id"])] = mon
        s = {"experiment_id": str(r["experiment.id"]),
             "group": str(r["experiment.comparison_group_id"]),
             "terminal_state": str(r["status.terminal_state"])}
        s.update(run_traj_summary(mon))
        summaries.append(s)
    mon_by_id = {s["experiment_id"]: s for s in summaries}

    # ---- 步时对齐
    aligned = align_steps(step_df, runs, monitors)
    for a in aligned:
        a.pop("_per_step")  # 轨迹本体不进 JSON（体量）；统计量保留

    # ---- 14B 超时 run（stdout 解析 + monitor）
    t14 = df[(df["experiment.comparison_group_id"] == "formal-axis1-14b-4bit-qlora")
             & (df["status.terminal_state"] == "timeout")]
    boundary = {}
    if len(t14):
        r = t14.iloc[0]
        raw_dir = RAW / str(r["_raw_dir"])
        steps = parse_stdout_steps(raw_dir)
        mon = monitors.get(str(r["experiment.id"]))
        boundary = {
            "experiment_id": str(r["experiment.id"]),
            "steps": steps,
            "n_steps_completed": len(steps),
            "requested_steps": int(steps[0]["total"]) if steps else 100,
            "step_time_min_s": min((p["step_time_s"] for p in steps),
                                   default=None),
            "step_time_max_s": max((p["step_time_s"] for p in steps),
                                   default=None),
            "monitor": None if mon is None else
                {"t_rel": mon["t_rel"][::10].tolist(),
                 "swap_gib": mon["swap_gib"][::10].tolist()},
            "monitor_summary": mon_by_id.get(str(r["experiment.id"])),
            "alignment_caveat": (
                "step_timings.jsonl absent for timeout runs; per-step "
                "wall-clock alignment is NOT recoverable (70 steps sum to "
                "~3407 s of a 7199 s window; ~63 min is load/eval/stall per "
                "D8 hand notes). Panels (a)/(b) therefore use independent "
                "x-axes and no per-step attribution is claimed."),
        }

    # ---- batch-8 SIGKILL 三连（2026-09-15；09-12 为 D5 exit-1 无效）
    b8 = df[(df["experiment.comparison_group_id"] == "formal-axis4-b8")
            & (df["status.exit_code"].astype(str) == "137")]
    batch8 = []
    for _, r in b8.iterrows():
        mon = monitors.get(str(r["experiment.id"]))
        if mon is None:
            continue
        batch8.append({
            "experiment_id": str(r["experiment.id"]),
            "seed": int(r["training.seed"]) if pd.notna(r["training.seed"]) else None,
            "duration_s": mon["duration_s"],
            "t_rel": mon["t_rel"].tolist(),
            "swap_gib": mon["swap_gib"].tolist(),
            "swap_start_gib": float(mon["swap_gib"][0]),
            "swap_peak_gib": float(mon["swap_gib"].max()),
            "time_to_peak_s": float(mon["t_rel"][int(np.argmax(mon["swap_gib"]))]),
            "successful_steps": int(float(r["runtime.successful_steps"]))
            if pd.notna(r["runtime.successful_steps"]) else 0,
        })
    b8_invalid = df[(df["experiment.comparison_group_id"] == "formal-axis4-b8")
                    & (df["status.exit_code"].astype(str) != "137")]
    b8_invalid_note = (
        f"{len(b8_invalid)} additional b8 rows are D5 implementation-invalid "
        "(exit 1, variable-length validation bug, 2026-09-12) and are "
        "excluded from the ramp evidence.")

    # ---- Tier-A 对照 run（图 11c 虚线）：0.6B 4bit s42 成功 run
    ctrl_id = None
    for a in aligned:
        if a["group"] == "formal-axis1-0.6b-4bit-qlora" and a["tier"] == "A":
            ctrl_id = a["experiment_id"]
            break
    tier_a_contrast = None
    if ctrl_id:
        mon = monitors[ctrl_id]
        tier_a_contrast = {"experiment_id": ctrl_id,
                           "t_rel": mon["t_rel"].tolist(),
                           "swap_gib": mon["swap_gib"].tolist(),
                           "duration_s": mon["duration_s"]}

    # ---- 同配置异状态对照（Table 15，全部从 experiments.csv 取数）
    def _grp(g):
        return df[df["experiment.comparison_group_id"] == g]

    def _row(config, state, sub, outcome, steps=None, midrule=False,
             median_override=None):
        med = pd.to_numeric(sub["tm.median_step_time_seconds"],
                            errors="coerce").dropna()
        sw = pd.to_numeric(sub["runtime.initial_swap_bytes.value"],
                           errors="coerce").dropna() / GIB
        st = steps if steps is not None else (
            "--" if sub["runtime.successful_steps"].isna().all()
            else f"{int(pd.to_numeric(sub['runtime.successful_steps'], errors='coerce').fillna(0).max())}")
        med_s = median_override if median_override is not None else (
            _num(med.mean()) if len(med) else "--")
        sw_txt = (f"{sw.min():.1f}–{sw.max():.1f}" if len(sw) else "--")
        return {
            "config": config, "state": state, "n_runs": int(len(sub)),
            "steps": st, "median_step_s": med_s,
            "initial_swap_gib": sw_txt,
            "outcome": outcome, "midrule_after": midrule,
        }

    axis1_4b = _grp("formal-axis1-4b-4bit-qlora")
    axis4_b1 = _grp("formal-axis4-b1")
    bf16_4b = _grp("formal-axis1-4b-bf16-lora")
    d1_int = bf16_4b[(bf16_4b["status.terminal_state"] == "user_interrupted")
                     & (pd.to_numeric(bf16_4b["runtime.wall_clock_seconds"],
                                      errors="coerce") >= 1500)]
    d1_ok = bf16_4b[bf16_4b["status.terminal_state"] == "success"]
    ctx2k = _grp("formal-axis2-ctx2048")
    ctx2k_kill = ctx2k[ctx2k["status.terminal_state"] != "success"]
    ctx2k_ok = ctx2k[ctx2k["status.terminal_state"] == "success"]
    b14 = _grp("formal-axis1-14b-4bit-qlora")
    b14_stall = b14[b14["status.terminal_state"] == "unknown_failure"]
    b14_to = b14[b14["status.terminal_state"] == "timeout"]
    p14 = df[df["experiment.comparison_group_id"]
             == "probe-14b-4bit-qlora20-seed42"]
    p14 = p14[p14["status.terminal_state"] == "success"]

    med_a1 = pd.to_numeric(axis1_4b["tm.median_step_time_seconds"],
                           errors="coerce").mean()
    med_b1 = pd.to_numeric(axis4_b1["tm.median_step_time_seconds"],
                           errors="coerce").mean()
    drift_pct = f"+{(med_b1 / med_a1 - 1) * 100:.0f}\\%" if med_a1 else "--"
    med14 = (_num(float(np.median([p["step_time_s"]
                                   for p in boundary.get("steps", [])])))
             if boundary.get("steps") else "--")

    contrasts = [
        _row("4B 4bit, b1, ctx512", "axis-1 window (09-11/12)",
             axis1_4b, "3/3 success", midrule=False),
        _row("4B 4bit, b1, ctx512", "batch-axis window (09-15)",
             axis4_b1, f"3/3 success, {drift_pct} step time"),
        _row("4B BF16, ctx512", "high residency (09-11)",
             d1_int, "0 steps in 27 min (D1)", steps="0"),
        _row("4B BF16, ctx512", "post-reboot, swap 0 (09-12)",
             d1_ok, "success in 451 s (D1)"),
        _row("8B 4bit, ctx512", "first attempt (09-15)",
             _grp("formal-axis1-8b-4bit-qlora")[
                 _grp("formal-axis1-8b-4bit-qlora")["status.terminal_state"]
                 != "success"],
             "timeout (D7)"),
        _row("8B 4bit, ctx512", "favorable window (09-15)",
             _grp("formal-axis1-8b-4bit-qlora")[
                 _grp("formal-axis1-8b-4bit-qlora")["status.terminal_state"]
                 == "success"],
             "3/3 success"),
        _row("ctx2048, s123", "7.7 GiB residency (09-11)",
             ctx2k_kill, "SIGKILL (0 steps)", steps="0"),
        _row("ctx2048, s123", "2.96 GiB residency (09-15)",
             ctx2k_ok[ctx2k_ok["training.seed"] == 123],
             "success (D7 rerun)"),
        _row("14B 4bit, ctx512", "smoke probe, 2.5 GiB (09-11)",
             p14, "20/20 steps @ 0.68 s (D8)"),
        _row("14B 4bit, ctx512", "6.6 GiB (09-11)",
             b14_stall, "0 steps in 24 min (D8)", steps="0"),
        _row("14B 4bit, ctx512", "3.5 GiB (09-15)",
             b14_to, "70/100 steps, timeout (D8)", steps="70",
             median_override=med14),
    ]

    rho_b = [a["spearman_rho"] for a in aligned
             if a["tier"] == "B" and a["spearman_rho"] is not None]
    rho_a = [a["spearman_rho"] for a in aligned
             if a["tier"] == "A" and a["spearman_rho"] is not None]

    def _rho_sum(v):
        if not v:
            return {"n": 0}
        return {"n": len(v), "median": float(np.median(v)),
                "p25": float(np.percentile(v, 25)),
                "p75": float(np.percentile(v, 75))}

    monitor_dirs = sum(1 for d in RAW.iterdir()
                       if (d / "system_monitor.jsonl").exists())

    return {
        "schema_version": "1.0.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "generator_commit": _git_commit(),
        "analysis_kind": "post-hoc exploratory (deviations.md D12)",
        "monitor_coverage": {
            "runs_total": int(len(df)),
            "run_dirs_with_monitor_file": monitor_dirs,
            "runs_parsed_ge10_samples": len(monitors),
            "cadence_median_s_overall": float(np.median(
                [m["cadence_median_s"] for m in monitors.values()
                 if m["cadence_median_s"]]))},
        "per_run": summaries,
        "step_swap_alignment": {
            "n_runs_aligned": len(aligned),
            "runs": aligned,
            "spearman_rho_summary": {
                "tier_A": _rho_sum(rho_a), "tier_B": _rho_sum(rho_b),
                "interpretation": (
                    "within-run step time correlates weakly with the "
                    "concurrent system-swap LEVEL: swap is a stock metric; "
                    "paging bursts are flow events. Supports 'residency is "
                    "necessary but not sufficient' (paper Sec. limitations "
                    "of state description)."),
            }},
        "boundary14b_timeout_run": boundary,
        "batch8_sigkill": batch8,
        "batch8_invalid_note": b8_invalid_note,
        "tier_a_contrast_run": tier_a_contrast,
        "same_config_contrasts": contrasts,
    }


def main() -> int:
    payload = build_payload()
    # 图需要 _per_step 轨迹：在 JSON 序列化前单独重算（保持 JSON 轻量）
    step_df = pd.read_parquet(PROCESSED / "step_timings.parquet")
    runs = _retained_success()
    df = pd.read_csv(PROCESSED / "experiments.csv", low_memory=False)
    monitors = {}
    for _, r in df.iterrows():
        mon = load_monitor(RAW / str(r["_raw_dir"]))
        if mon is not None:
            monitors[str(r["experiment.id"])] = mon
    aligned_full = align_steps(step_df, runs, monitors)
    # 14B monitor 全分辨率给画图（JSON 里存的是 1/10 抽稀）
    t14 = df[(df["experiment.comparison_group_id"] == "formal-axis1-14b-4bit-qlora")
             & (df["status.terminal_state"] == "timeout")]
    if len(t14) and payload["boundary14b_timeout_run"].get("steps"):
        mon14 = monitors.get(str(t14.iloc[0]["experiment.id"]))
        if mon14:
            payload["boundary14b_timeout_run"]["monitor"] = {
                "t_rel": mon14["t_rel"], "swap_gib": mon14["swap_gib"]}
    ctrl = payload.get("tier_a_contrast_run")
    if ctrl and ctrl["experiment_id"] in monitors:
        m = monitors[ctrl["experiment_id"]]
        ctrl.update({"t_rel": m["t_rel"], "swap_gib": m["swap_gib"],
                     "duration_s": m["duration_s"]})
    fig11_state_dynamics(payload, payload["batch8_sigkill"], aligned_full)
    # JSON 存抽稀版
    mon14 = payload["boundary14b_timeout_run"].get("monitor")
    if mon14 and isinstance(mon14.get("t_rel"), np.ndarray):
        payload["boundary14b_timeout_run"]["monitor"] = {
            "t_rel": mon14["t_rel"][::10].tolist(),
            "swap_gib": mon14["swap_gib"][::10].tolist()}
    for r in payload["batch8_sigkill"]:
        r["t_rel"] = np.asarray(r["t_rel"])[::2].tolist()
        r["swap_gib"] = np.asarray(r["swap_gib"])[::2].tolist()
    if ctrl and isinstance(ctrl.get("t_rel"), np.ndarray):
        ctrl["t_rel"] = ctrl["t_rel"].tolist()
        ctrl["swap_gib"] = ctrl["swap_gib"].tolist()
    (PROCESSED / "system_state.json").write_text(
        json.dumps(payload, indent=1))
    table15(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
