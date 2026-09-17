"""Round-1 revision analyses (panel review R1–R9, 2026-09-16).

Every number is derived programmatically from results/processed/experiments.csv
and existing processed JSONs. Outputs:
  - results/processed/tier_classification.json      (R3a/R3d: per-run paging + Tier)
  - results/processed/val_loss_tests.json           (R1: paired t / Welch on val loss)
  - results/processed/threshold_sensitivity.json    (R4: ±2x threshold sensitivity)
  - results/processed/scaling_model_comparison.json (R4/DA-5: power vs affine)
  - results/processed/slope_confidence_intervals.json (R4: slope CI/df/p)
  - paper/tables/table7_tier.tex                    (appendix: per-run paging table)
  - paper/tables/table8_sensitivity.tex             (appendix: threshold sensitivity)
  - paper/tables/table9_axis1_ci.tex                (appendix: axis-1 95% t-CIs)

Tier rule (D4, frozen 2026-09-12 04:40):
  swapins_delta_per_step = (vm_stat swapins after - before) * page_size
                           / successful_steps
  Tier-A < 50 MB/step (compute-bound); Tier-B otherwise.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "results" / "processed"
TABLES = ROOT / "paper" / "tables"

SW_IN_B = "runtime.system_vm_counters_before.value.counters_pages.swapins"
SW_OUT_B = "runtime.system_vm_counters_before.value.counters_pages.swapouts"
SW_IN_A = "runtime.system_vm_counters_after.value.counters_pages.swapins"
PS = "runtime.system_vm_counters_before.value.page_size_bytes"
STEPS = "runtime.successful_steps"


def _load_full() -> pd.DataFrame:
    return pd.read_csv(PROC / "experiments.csv", low_memory=False)


def _load_aggregated() -> pd.DataFrame:
    """与 tables.py 相同的聚合集合（retained formal/probe 行）。"""
    df = _load_full()
    formal = df[df["experiment.comparison_group_id"].astype(str).str.startswith(
        ("formal-", "probe-8b-bf16", "probe-14b-4bit"))]
    from .flatten import retained
    return retained(formal)


def _num(series: pd.Series) -> float:
    return pd.to_numeric(series, errors="coerce")


def tier_table() -> dict:
    """使用 flatten.retained() 输出的 _swapin_per_step/_tier 列（D4 权威口径）。

    retained()（flatten.py）已按 D2/D4 去重：未 supersede + 同
    (group, seed, state) 优先 Tier-A、并列取最早。
    """
    df = _load_aggregated()
    if "_swapin_per_step" not in df.columns:
        raise SystemExit("retained() output missing _swapin_per_step column")
    rows = []
    for _, r in df.iterrows():
        group = str(r.get("experiment.comparison_group_id", ""))
        state = str(r.get("status.terminal_state", ""))
        mb_step = pd.to_numeric(pd.Series([r.get("_swapin_per_step")]),
                                 errors="coerce").iloc[0]
        steps = pd.to_numeric(pd.Series([r.get(STEPS)]), errors="coerce").iloc[0]
        if (not group.startswith("formal-")
                or pd.isna(mb_step) or (pd.isna(steps) or steps <= 0)):
            continue
        init_swap = float(r.get("runtime.initial_swap_bytes.value", 0) or 0) / 2**30
        rows.append({
            "experiment_id": str(r.get("experiment.id", "")),
            "group": group,
            "seed": int(pd.to_numeric(r.get("training.seed"), errors="coerce")),
            "terminal_state": state,
            "successful_steps": int(steps),
            "median_step_s": float(r.get("tm.median_step_time_seconds")),
            "swapins_mb_per_step": round(float(mb_step), 1),
            "tier": str(r.get("_tier")),
            "initial_swap_gib": round(init_swap, 2),
        })
    rows.sort(key=lambda x: (x["group"], x["seed"]))
    per_group = {}
    for x in rows:
        g = per_group.setdefault(x["group"], {"runs": 0, "tier_a": 0, "tier_b": 0,
                                              "mb_step_min": math.inf,
                                              "mb_step_max": -math.inf,
                                              "init_swap_min": math.inf,
                                              "init_swap_max": -math.inf})
        g["runs"] += 1
        g[f"tier_{x['tier'].lower()}"] += 1
        g["mb_step_min"] = min(g["mb_step_min"], x["swapins_mb_per_step"])
        g["mb_step_max"] = max(g["mb_step_max"], x["swapins_mb_per_step"])
        g["init_swap_min"] = min(g["init_swap_min"], x["initial_swap_gib"])
        g["init_swap_max"] = max(g["init_swap_max"], x["initial_swap_gib"])
    for g in per_group.values():
        for k in ("mb_step_min", "mb_step_max", "init_swap_min", "init_swap_max"):
            if math.isinf(g[k]):
                g[k] = None
    out = {
        "rule": "D4 frozen 2026-09-12: swapins_delta_per_step "
                "= (vm_stat swapins delta) * page_size / successful_steps; "
                "Tier-A < 50 MB/step",
        "n_runs_with_paging": len(rows),
        "per_run": rows,
        "per_group": per_group,
    }
    (PROC / "tier_classification.json").write_text(
        json.dumps(out, indent=2) + "\n")

    # Appendix table: axis-1 + axis-2/3/4 groups, one row per group
    keep = [g for g in per_group
            if g.startswith("formal-axis1-") and "14b" not in g
            or g in ("formal-axis2-ctx1024", "formal-axis2-ctx2048",
                     "formal-axis3-r4", "formal-axis3-r32",
                     "formal-axis4-b1", "formal-axis4-b2", "formal-axis4-b4")]
    lines = [
        "\\begin{table*}[t]\\centering",
        "\\caption{Per-group paging stratification for the aggregated "
        "groups (D4 rule, computed from the frozen \\texttt{vm\\_stat} "
        "snapshots in each raw record): "
        "Tier-A $=$ swap-in $<$50\\,MB/step (compute-bound), Tier-B otherwise. "
        "Residency is the pre-run system swap level. The axis1b 300-step "
        "duplicate-retention group (D2) is excluded from the aggregated "
        "matrix and hence here.}",
        "\\label{tab:tier}", "\\footnotesize\\setlength{\\tabcolsep}{4pt}",
        "\\begin{tabular}{lrrrrr}", "\\toprule",
        "Group & Runs & Tier-A & Tier-B & Swap-in (MB/step) & "
        "Residency (GiB)\\\\", "\\midrule",
    ]
    def _esc(s: str) -> str:
        return s.replace("_", r"\_")
    import math as _m
    for g in sorted(keep):
        d = per_group[g]
        nice = _esc(g.replace("formal-axis1-", "a1: ").replace(
            "formal-axis2-", "a2: ").replace("formal-axis3-", "a3: ").replace(
            "formal-axis4-", "a4: "))
        lo = _m.floor(d["mb_step_min"] + 0.5)
        hi = _m.floor(d["mb_step_max"] + 0.5)
        lines.append(
            f"{nice} & {d['runs']} & {d['tier_a']} & {d['tier_b']} & "
            f"{lo}--{hi} & "
            f"{d['init_swap_min']:.1f}--{d['init_swap_max']:.1f}\\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    (TABLES / "table7_tier.tex").write_text("\n".join(lines) + "\n",
                                            encoding="utf-8")
    print("[rev1] tier_classification.json + table7_tier.tex")
    return out


def val_loss_tests() -> dict:
    df = _load_full()
    out = {}
    for model in ("0.6b", "1.7b"):
        cells = {}
        for prec, g in (("bf16", f"formal-axis1-{model}-bf16-lora"),
                        ("4bit", f"formal-axis1-{model}-4bit-qlora")):
            sub = df[(df["experiment.comparison_group_id"] == g)
                     & (df["status.terminal_state"] == "success")]
            vals = pd.to_numeric(sub["metrics.validation_loss_final"],
                                 errors="coerce").dropna().tolist()
            seeds = pd.to_numeric(sub["training.seed"], errors="coerce").tolist()
            cells[prec] = dict(zip(seeds, vals))
        common = sorted(set(cells["bf16"]) & set(cells["4bit"]))
        a = np.array([cells["bf16"][s] for s in common], dtype=float)
        b = np.array([cells["4bit"][s] for s in common], dtype=float)
        t_pair = sps.ttest_rel(b, a)
        t_welch = sps.ttest_ind(b, a, equal_var=False)

        def ci(x: np.ndarray) -> list[float]:
            m, sd, n = float(x.mean()), float(x.std(ddof=1)), len(x)
            tq = float(sps.t.ppf(0.975, n - 1))
            return [round(m - tq * sd / math.sqrt(n), 4),
                    round(m + tq * sd / math.sqrt(n), 4)]

        d = b - a
        dq = float(sps.t.ppf(0.975, len(d) - 1))
        out[model] = {
            "n_pairs": len(common),
            "seeds": common,
            "bf16_mean_sd": [round(float(a.mean()), 4), round(float(a.std(ddof=1)), 4)],
            "4bit_mean_sd": [round(float(b.mean()), 4), round(float(b.std(ddof=1)), 4)],
            "bf16_ci95": ci(a), "4bit_ci95": ci(b),
            "diff_4bit_minus_bf16_mean": round(float(d.mean()), 4),
            "diff_ci95": [round(float(d.mean() - dq * float(d.std(ddof=1)) / math.sqrt(len(d))), 4),
                          round(float(d.mean() + dq * float(d.std(ddof=1)) / math.sqrt(len(d))), 4)],
            "paired_t": round(float(t_pair.statistic), 2),
            "paired_t_p": float(t_pair.pvalue),
            "paired_t_df": len(d) - 1,
            "welch_t": round(float(t_welch.statistic), 2),
            "welch_p": float(t_welch.pvalue),
        }
    (PROC / "val_loss_tests.json").write_text(json.dumps(out, indent=2) + "\n")
    print("[rev1] val_loss_tests.json")
    return out


def threshold_sensitivity() -> dict:
    df = _load_aggregated()
    df = df[df["status.terminal_state"] == "success"]
    rows = []
    p2_grid = (5.0, 10.0, 20.0)
    p1_grid = (2.0, 4.0, 8.0)
    eff_grid = (50.0, 100.0, 200.0)
    order = ["formal-axis1-0.6b-4bit-qlora", "formal-axis1-1.7b-4bit-qlora",
             "formal-axis1-4b-4bit-qlora", "formal-axis1-8b-4bit-qlora",
             "formal-axis1-0.6b-bf16-lora", "formal-axis1-1.7b-bf16-lora",
             "formal-axis1-4b-bf16-lora"]
    nice = {"formal-axis1-": "Qwen3-"}
    for g in order:
        sub = df[df["experiment.comparison_group_id"] == g]
        if sub.empty:
            continue
        med = pd.to_numeric(sub["tm.median_step_time_seconds"],
                            errors="coerce").dropna()
        tok = pd.to_numeric(sub["runtime.tokens_per_second"],
                            errors="coerce").dropna()
        sw = (pd.to_numeric(sub["runtime.peak_swap_bytes.value"], errors="coerce")
              - pd.to_numeric(sub["runtime.initial_swap_bytes.value"], errors="coerce")).dropna()
        med_m = float(med.mean()) if len(med) else None
        tok_m = float(tok.mean()) if len(tok) else None
        sw_m = float(sw.mean()) if len(sw) else None
        row = {
            "group": g, "n_seeds": int(len(sub)),
            "median_step_s_mean": round(med_m, 3) if med_m else None,
            "swap_delta_gib_mean": round(sw_m / 2**30, 2) if sw_m is not None else None,
            "tokens_per_s_mean": round(tok_m, 1) if tok_m else None,
            "P2_pass_at_5_10_20": [bool(med_m and med_m <= t) for t in p2_grid],
            "P1_pass_at_2_4_8": [bool(sw_m is not None and sw_m / 2**30 <= t)
                                 for t in p1_grid],
            "eff_pass_at_50_100_200": [bool(tok_m and tok_m >= t) for t in eff_grid],
        }
        rows.append(row)
    out = {"p2_grid_s": list(p2_grid), "p1_grid_gib": list(p1_grid),
           "eff_grid_tps": list(eff_grid), "cells": rows}
    (PROC / "threshold_sensitivity.json").write_text(
        json.dumps(out, indent=2) + "\n")
    lines = [
        "\\begin{table}[t]\\centering",
        "\\caption{Threshold sensitivity (preregistration \\S5: \\emph{results "
        "must be shown if conclusions flip under $\\pm 2\\times$ threshold "
        "changes}). Pass/fail of the frozen \\practical{} criteria P1 (swap "
        "growth $\\le$4\\,GiB), P2 (median step $\\le$10\\,s) and the "
        "exploratory \\efficient{} criterion ($\\ge$100 loss-bearing "
        "tokens/s) at $0.5\\times$/$1\\times$/$2\\times$ the frozen values.}",
        "\\label{tab:sens}", "\\footnotesize\\setlength{\\tabcolsep}{3pt}",
        "\\begin{tabular}{lccc}", "\\toprule",
        "Cell & P1 (2/4/8\\,GiB) & P2 (5/10/20\\,s) & Eff.\\ (50/100/200)\\\\",
        "\\midrule",
    ]
    for r in rows:
        cell = (r["group"].replace("formal-axis1-", "")
                .replace("-4bit-qlora", " 4bit").replace("-bf16-lora", " BF16"))
        p1 = "/".join("Y" if x else "n" for x in r["P1_pass_at_2_4_8"])
        p2 = "/".join("Y" if x else "n" for x in r["P2_pass_at_5_10_20"])
        ef = "/".join("Y" if x else "n" for x in r["eff_pass_at_50_100_200"])
        lines.append(f"\\texttt{{{cell.replace('_', '-')}}} & {p1} & {p2} & {ef}\\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (TABLES / "table8_sensitivity.tex").write_text("\n".join(lines) + "\n",
                                                   encoding="utf-8")
    print("[rev1] threshold_sensitivity.json + table8_sensitivity.tex")
    return out


def scaling_model_comparison() -> dict:
    """Power law vs affine (peak = w*params + c) on identical points."""
    df = _load_aggregated()
    df = df[df["status.terminal_state"] == "success"]
    out = {}
    for prec, groups in (
            ("4bit QLoRA", ["formal-axis1-0.6b-4bit-qlora",
                            "formal-axis1-1.7b-4bit-qlora",
                            "formal-axis1-4b-4bit-qlora",
                            "formal-axis1-8b-4bit-qlora"]),
            ("BF16 LoRA", ["formal-axis1-0.6b-bf16-lora",
                           "formal-axis1-1.7b-bf16-lora",
                           "formal-axis1-4b-bf16-lora"])):
        xs, ys = [], []
        for g in groups:
            sub = df[df["experiment.comparison_group_id"] == g]
            if sub.empty:
                continue
            x = float(pd.to_numeric(sub["tm.logical_parameter_count"],
                                    errors="coerce").dropna().mean())
            y = float(pd.to_numeric(sub["tm.peak_metal_gpu_memory_bytes"],
                                    errors="coerce").dropna().mean()) / 2**30
            xs.append(x / 1e9)
            ys.append(y)
        x, y = np.array(xs), np.array(ys)
        # power law (2 params) fitted in log space, evaluated in raw space
        lx, ly = np.log10(x), np.log10(y)
        slope, intercept, *_ = sps.linregress(lx, ly)
        y_power = 10 ** (slope * lx + intercept)
        # affine (2 params) in raw space
        w, c = np.polyfit(x, y, 1)
        y_affine = w * x + c
        n, k = len(y), 2

        def aic(yhat: np.ndarray) -> float:
            sse = float(((y - yhat) ** 2).sum())
            return n * math.log(sse / n) + 2 * k, sse

        aic_p, sse_p = aic(y_power)
        aic_a, sse_a = aic(y_affine)
        # R^2 in raw space for both
        sst = float(((y - y.mean()) ** 2).sum())
        out[prec] = {
            "n_points": n,
            "params_B": [round(v, 2) for v in x.tolist()],
            "peak_gib": [round(v, 2) for v in y.tolist()],
            "power_law": {"slope_loglog": round(float(slope), 4),
                          "sse_gib2": round(sse_p, 4),
                          "r2_raw": round(1 - sse_p / sst, 4),
                          "aic": round(aic_p, 2)},
            "affine": {"slope_gib_per_B": round(float(w), 4),
                       "intercept_gib": round(float(c), 4),
                       "sse_gib2": round(sse_a, 4),
                       "r2_raw": round(1 - sse_a / sst, 4),
                       "aic": round(aic_a, 2)},
            "delta_aic_affine_minus_power": round(aic_a - aic_p, 2),
            "weight_at_8b": round(float(w * 8.2 + c), 2),
        }
    (PROC / "scaling_model_comparison.json").write_text(
        json.dumps(out, indent=2) + "\n")
    print("[rev1] scaling_model_comparison.json")
    return out


def slope_confidence_intervals() -> dict:
    out = {}
    for fname, key in (("memory_scaling_fits.json", "memory"),
                       ("step_time_scaling_fits.json", "step_time")):
        fits = json.loads((PROC / fname).read_text())
        sec = {}
        for series, d in fits.items():
            n, se, slope = d["n"], d["stderr_slope"], d["slope"]
            dfree = n - 2
            tq = float(sps.t.ppf(0.975, dfree))
            sec[series] = {
                "n": n, "df": dfree, "slope": round(slope, 4),
                "stderr": round(se, 4),
                "ci95": [round(slope - tq * se, 3), round(slope + tq * se, 3)],
                "p_value": d.get("p_value"),
                "r_squared": round(d.get("r_squared", float("nan")), 4),
                "ci_contains_1": bool(slope - tq * se <= 1.0 <= slope + tq * se),
            }
        out[key] = sec
    (PROC / "slope_confidence_intervals.json").write_text(
        json.dumps(out, indent=2) + "\n")

    # Appendix table: axis-1 95% t-CIs (median step + val loss + tok/s)
    df = _load_aggregated()
    df = df[df["status.terminal_state"] == "success"]
    lines = [
        "\\begin{table}[t]\\centering",
        "\\caption{Axis-1 cells, mean [95\\% $t$-CI] "
        "(preregistration \\S9: wide intervals reported honestly; "
        "CI $= t_{0.975,n-1}\\,\\mathrm{SD}/\\sqrt{n}$; per-seed SD in "
        "Table~\\ref{tab:matrix}).}",
        "\\label{tab:ci}", "\\footnotesize\\setlength{\\tabcolsep}{3pt}",
        "\\begin{tabular}{lrrr}", "\\toprule",
        "Cell & Median step (s) & Tok/s & Val loss\\\\", "\\midrule",
    ]
    order = ["formal-axis1-0.6b-4bit-qlora", "formal-axis1-1.7b-4bit-qlora",
             "formal-axis1-4b-4bit-qlora", "formal-axis1-8b-4bit-qlora",
             "formal-axis1-0.6b-bf16-lora", "formal-axis1-1.7b-bf16-lora",
             "formal-axis1-0.6b-bf16-full"]

    def cell_txt(sub: pd.DataFrame, col: str, digits: int) -> str:
        vals = pd.to_numeric(sub[col], errors="coerce").dropna().tolist()
        if not vals:
            return "--"
        m = float(np.mean(vals))
        if len(vals) < 2:
            return f"{m:.{digits}f}"
        sd = float(np.std(vals, ddof=1))
        tq = float(sps.t.ppf(0.975, len(vals) - 1))
        half = tq * sd / math.sqrt(len(vals))
        scale = 2**30 if "memory" in col else 1
        m, half = m / scale, half / scale
        return (f"{m:.{digits}f} [{m - half:.{digits}f},"
                f"{m + half:.{digits}f}]")

    for g in order:
        sub = df[df["experiment.comparison_group_id"] == g]
        if sub.empty:
            continue
        cell = (g.replace("formal-axis1-", "").replace("-4bit-qlora", " 4bit")
                .replace("-bf16-lora", " BF16").replace("-bf16-full", " fullFT"))
        lines.append(f"\\texttt{{{cell}}} & "
                     f"{cell_txt(sub, 'tm.median_step_time_seconds', 2)} & "
                     f"{cell_txt(sub, 'runtime.tokens_per_second', 0)} & "
                     f"{cell_txt(sub, 'metrics.validation_loss_final', 2)}\\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (TABLES / "table9_axis1_ci.tex").write_text("\n".join(lines) + "\n",
                                                encoding="utf-8")
    print("[rev1] slope_confidence_intervals.json + table9_axis1_ci.tex")
    return out


def main() -> int:
    tier_table()
    val_loss_tests()
    threshold_sensitivity()
    scaling_model_comparison()
    slope_confidence_intervals()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
