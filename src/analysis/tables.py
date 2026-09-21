"""论文表格生成（全部从 processed 数据派生 → paper/submission/tables/*.tex；
该目录 git-ignored——论文成品只经 arXiv 发布，LaTeX 源码不进仓库）。

Table 1 hardware/software/model revisions（来自 formal run 的 raw provenance）
Table 2 formal matrix 汇总（mean±SD over 3 seeds）
Table 3 paired BF16 vs 4bit（含预注册 ±25% 等价判定）
Table 4 failure/boundary observations
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .stats import mean_sd_ci, paired_ratio

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "paper" / "submission" / "tables"


def _load() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "results" / "processed" / "experiments.csv",
                     low_memory=False)
    formal = df[df["experiment.comparison_group_id"].astype(str).str.startswith(
        ("formal-", "probe-8b-bf16", "probe-14b-4bit"))]
    from .flatten import retained
    return retained(formal)


def _agg_cell(sub: pd.DataFrame, col: str, digits: int = 3) -> str:
    a = mean_sd_ci([float(v) for v in sub[col]])
    if a is None:
        return "--"
    unit_scale = 1
    suffix = ""
    if col == "tm.peak_metal_gpu_memory_bytes":
        unit_scale = 2**30
        suffix = ""  # 单位由表头声明，不在每个单元格重复
    if a["sd"] is None:
        return f"{a['mean'] / unit_scale:.{digits}f}{suffix}"
    # 用数学模式 \pm（cmsy Type1）；字面 UTF-8 ± 会映射 TS1 文本伴随字体，
    # 缺 Type1 时 pdftex 回退为 Type3 位图字形
    return (f"{a['mean'] / unit_scale:.{digits}f}$\\pm$"
            f"{a['sd'] / unit_scale:.{digits}f}{suffix}")


def table1(df: pd.DataFrame) -> None:
    succ = df[df["status.terminal_state"] == "success"]
    mem_col = "hardware.unified_memory_bytes"
    mem_rows = succ[succ[mem_col].notna()]
    ref = (mem_rows if not mem_rows.empty else succ).iloc[-1]
    mem_gib = (float(ref[mem_col]) / 2**30
               if pd.notna(ref[mem_col]) else 16)
    rows = [
        ("Hardware", ""),
        ("\\quad Chip", f"{ref['hardware.apple_chip_model']}"),
        ("\\quad Memory", f"{mem_gib:.0f} GiB unified"),
        ("\\quad CPU cores",
         f"{ref['hardware.cpu_physical_cores']:.0f}-core (4P+6E, "
         f"{ref['hardware.cpu_logical_cores']:.0f} logical)"),
        ("OS", f"macOS {ref['software.macos_version']} "
               f"(build {ref['software.macos_build']})"),
        ("Python",
         f"{ref['software.python_version'].split()[0]} (uv-managed venv)"),
        ("MLX / mlx-lm",
         f"{ref['software.mlx_version']} / {ref['software.mlx_lm_version']}"),
        ("Training data", "ultrachat\\_200k@8049631c, frozen 2048/32 subset"),
    ]
    models = []
    seen = set()
    for _, r in df.iterrows():
        key = (r["model.id"], r["model.resolved_revision"])
        if key[0] in seen or pd.isna(r["model.resolved_revision"]):
            continue
        seen.add(key[0])
        short = (str(key[0]).replace("mlx-community/", "")
                 .replace("Qwen3-", "").replace("Qwen/", ""))
        if "4bit" not in short:
            short += "-BF16"
        models.append((short, str(key[1])[:8]))
    # 按规模升序、同规模 BF16 在前 4bit 在后，与 Table 2 行序一致
    def _sort_key(item):
        name = item[0]
        scale = "".join(ch for ch in name if ch.isdigit() or ch == ".")
        return (float(scale.rstrip(".") or 0), "4bit" in name)
    models.sort(key=_sort_key)
    lines = [
        "\\begin{table}[t]\\centering",
        "\\caption{Hardware, software, and model revisions "
        "(provenance from raw experiment records; covers the formal "
        "matrix---non-formal probes such as the timed-out 8B BF16 run "
        "are not listed, and carry the same provenance fields in their "
        "raw records).}",
        "\\label{tab:setup}",
        "\\footnotesize",
        "\\begin{tabular}{@{}p{1.9cm}p{3.6cm}@{}}", "\\toprule",
    ]
    for k, v in rows:
        lines.append(f"{k} & {v}\\\\")
    lines.append("\\midrule")
    lines.append("Qwen3 models & resolved revision (8-char prefix)\\\\")
    for name, rev in models:
        lines.append(f"\\quad \\texttt{{{name}}} & \\texttt{{{rev}}}\\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    TABLES.mkdir(parents=True, exist_ok=True)
    (TABLES / "table1_setup.tex").write_text("\n".join(lines) + "\n",
                                             encoding="utf-8")
    print("[table] table1_setup.tex")


def table2(df: pd.DataFrame) -> None:
    # 组名必须与 gen_formal_configs.py 的 comparison_group_id 完全一致：
    # formal-axis1-<model>-bf16-lora / -4bit-qlora / -0.6b-bf16-full
    lines = [
        "\\begin{table*}[t]\\centering",
        "\\caption{Formal benchmark at ctx512, b1-ga1, rank 8, lr 1e-4, "
        "100 steps, preregistered seeds \\{42,123,2026\\} (mean$\\pm$SD over "
        "completed seeds; memory is MLX allocator peak; $\\pm$0.00 marks "
        "bit-identical allocator peaks across seeds). Verdicts are derived "
        "programmatically from the completed-seed count and the frozen P2 "
        "median-step bound of 10\\,s; the system-wide P1 swap-growth "
        "criterion is confounded by background load "
        "(Sec.~\\ref{sec:whatenable}) and is reported "
        "(Table~\\ref{tab:sens}) but not gated (D11 and its "
        "counterfactual, App.~B). ``Boundary'' marks the "
        "D1/D8 system-state cells; ``Negative (diverged)'' is the frozen-lr "
        "full-FT divergence; alongside the four operational terms "
        "(Sec.~\\ref{sec:definitions}) these two auxiliary kinds complete the "
        "verdict vocabulary. Tok/s counts loss-bearing tokens "
        "(tokens contributing to the LM loss). 95\\% $t$-CIs in "
        "Table~\\ref{tab:ci}.}",
        "\\label{tab:matrix}", "\\footnotesize\\setlength{\\tabcolsep}{3pt}",
        "\\begin{tabular}{llrlrrrr}", "\\toprule",
        "Model & Method & Seeds & Verdict & Peak (GiB) & Med step (s) & "
        "Tok/s & Val loss\\\\", "\\midrule",
    ]
    order = [("0.6", "formal-axis1-0.6b-bf16-full", None),
             ("0.6", "formal-axis1-0.6b-bf16-lora", None),
             ("1.7", "formal-axis1-1.7b-bf16-lora", None),
             ("4", "formal-axis1-4b-bf16-lora", "D1"),
             ("0.6", "formal-axis1-0.6b-4bit-qlora", None),
             ("1.7", "formal-axis1-1.7b-4bit-qlora", None),
             ("4", "formal-axis1-4b-4bit-qlora", None),
             ("8", "formal-axis1-8b-4bit-qlora", None),
             ("14", "formal-axis1-14b-4bit-qlora", "D8")]
    nice = {"bf16-lora": "BF16 LoRA", "4bit-qlora": "4-bit QLoRA",
            "bf16-full": "Full FT"}
    n_prereg = 3  # 预注册每格 3 种子（research/preregistration.md）
    # 参数量优先取组内实测；全失败组（如 14B formal）回退到同模型的
    # probe run 实测值，二者都来自 tm.logical_parameter_count，不手填
    probe_fallback = {"14": "probe-14b-4bit-qlora"}
    for model, g, tag in order:
        method = g.rsplit("formal-axis1-", 1)[1].split("-", 1)[1]
        sub = df[(df["experiment.comparison_group_id"] == g)
                 & (df["status.terminal_state"] == "success")]
        n = len(sub)
        seeds = f"{n}/{n_prereg}" + (f" ({tag})" if tag else "")
        # 参数量取同模型任意可用行（14B formal 全失败时回退到 probe 实测）
        params_src = df[df["experiment.comparison_group_id"].isin(
            [g] + ([probe_fallback[model]] if model in probe_fallback
                   else []))]
        params_col = pd.to_numeric(
            params_src["tm.logical_parameter_count"], errors="coerce").dropna()
        params_txt = (f" ({params_col.iloc[0] / 1e9:.1f}B)"
                      if len(params_col) else "")
        # 判定口径：完成种子数 + 冻结 P2（10 s）；P1 被背景负载支配，只报告不门控
        med = _mean(sub, "tm.median_step_time_seconds")
        vl = _mean(sub, "metrics.validation_loss_final")
        if tag and n < n_prereg:
            verdict = f"Boundary ({tag})"
        elif "full" in g and vl is not None and vl > 2.5:
            verdict = "Negative (diverged)"
        elif n >= n_prereg and med is not None:
            verdict = ("\\textsc{Practical} (P2)" if med <= 10.0
                       else "\\textsc{Trainable} (P2 miss)")
        else:
            verdict = "see text"
        if sub.empty:
            lines.append(f"Qwen3-{model}b{params_txt} & {nice[method]} & "
                         f"{seeds} & {verdict} & -- & -- & -- & --\\\\")
        else:
            params = float(params_col.iloc[0]) / 1e9
            lines.append(
                f"Qwen3-{model}b ({params:.1f}B) & {nice[method]} & {seeds} & "
                f"{verdict} & "
                f"{_agg_cell(sub, 'tm.peak_metal_gpu_memory_bytes', 2)} & "
                f"{_agg_cell(sub, 'tm.median_step_time_seconds')} & "
                f"{_agg_cell(sub, 'runtime.tokens_per_second', 1)} & "
                f"{_agg_cell(sub, 'metrics.validation_loss_final', 3)}\\\\")
        if g.endswith("bf16-full") or g == "formal-axis1-4b-bf16-lora":
            lines.append("\\midrule")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    (TABLES / "table2_matrix.tex").write_text("\n".join(lines) + "\n",
                                              encoding="utf-8")
    print("[table] table2_matrix.tex")


def table3(df: pd.DataFrame) -> None:
    lines = [
        "\\begin{table}[t]\\centering",
        "\\caption{Paired quantization effects (same model/seed; ratios = "
        "4bit/BF16, mean [min--max over seed pairs], computed from "
        "unrounded per-seed values). Timing equivalence "
        "margin $\\pm$25\\% frozen before benchmark. $^\\dagger$The 4B "
        "step-time ratio is a single seed pair whose BF16 denominator is "
        "the zero-residency D1 rerun, i.e.\\ a cross-window comparison "
        "(Sec.~\\ref{sec:timingscale}); memory ratios are window-robust "
        "(allocator peaks are bit-stable across seeds).}",
        "\\label{tab:paired}", "\\footnotesize\\setlength{\\tabcolsep}{2.5pt}",
        "\\begin{tabular}{lrrr}", "\\toprule",
        "Model & Mem ratio & Step-time ratio & Tok/s ratio\\\\", "\\midrule",
    ]
    verdicts = {}
    for model in ("0.6b", "1.7b", "4b"):
        ga, gb = f"formal-axis1-{model}-bf16-lora", f"formal-axis1-{model}-4bit-qlora"
        cells = []
        step_ratios = []
        n_pairs = 0
        for col in ("tm.peak_metal_gpu_memory_bytes",
                    "tm.median_step_time_seconds", "runtime.tokens_per_second"):
            pr = paired_ratio(df, ga, gb, value_col=col)
            if not pr:
                cells.append("--")
                continue
            import numpy as np
            r = [p["ratio_b_over_a"] for p in pr]
            n_pairs = len(r)
            # min==max（如内存比值跨种子逐位一致）时省略范围
            cells.append(f"{np.mean(r):.2f}" if min(r) == max(r)
                         else f"{np.mean(r):.2f} [{min(r):.2f}--{max(r):.2f}]")
            if col == "tm.median_step_time_seconds":
                step_ratios = r
        verdict = ("within margin" if step_ratios
                   and all(0.80 <= x <= 1.25 for x in step_ratios)
                   else ("slower" if any(x > 1.25 for x in step_ratios)
                         else "faster"))
        verdicts[model] = {"step_ratios": step_ratios, "verdict": verdict,
                           "n_pairs": n_pairs}
        dag = "$^\\dagger$" if model == "4b" and n_pairs == 1 else ""
        pairs = f" ({n_pairs})" if n_pairs else ""
        lines.append(f"Qwen3-{model}{pairs}{dag} & {' & '.join(cells)}\\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (TABLES / "table3_paired.tex").write_text("\n".join(lines) + "\n",
                                              encoding="utf-8")
    (ROOT / "results" / "processed" / "paired_equivalence_verdicts.json").write_text(
        json.dumps({"margin": [0.80, 1.25], "verdicts": verdicts}, indent=2) + "\n")
    print("[table] table3_paired.tex")


def table4(df: pd.DataFrame) -> None:
    """失败分类学：类别聚合（类别判定只用退出证据，不改写 terminal_state）。

    类别规则（全部 evidence-based）：
    - runtime_error + SIGKILL/exit137 → OS kill（内存压力一致，但不自动等同 OOM）
    - timeout → 监督器超时
    - user_interrupted → 操作员中断（按 D1/D7 作为系统状态证据保留）
    - runtime_error + python traceback + formal-axis4（micro-batch>=2）→ D5 训练器
      实现缺陷（已在修复后 trainer 上整批重跑）
    - exp0-smoke 组 → 正式矩阵前的管线调试
    - 其余 → 未归因失败
    """
    taxonomy = json.loads((ROOT / "results" / "processed" /
                           "failure_taxonomy.json").read_text())
    full = pd.read_csv(ROOT / "results" / "processed" / "experiments.csv",
                       low_memory=False).set_index("experiment.id")

    def _esc(s: str) -> str:
        return str(s).replace("_", r"\_")

    def _config(eid: str, group: str) -> str:
        parts = eid.split("__")
        model = (parts[1].replace("mlx-community-", "")
                 .replace("qwen-qwen3-", "qwen3-") if len(parts) > 1 else group)
        model = model.replace("qwen3-0-6b", "qwen3-0.6b")
        # 方法段：4-bit 模型名已含 -4bit；BF16 LoRA 的模型名不带精度，补标注
        if len(parts) > 2 and "lora-qnone" in parts[2]:
            model += " (BF16)"
        cfg = model
        m = re.search(r"__ctx(\d+)__", eid)
        if m and m.group(1) != "512":
            cfg += f", ctx{m.group(1)}"
        m = re.search(r"__b(\d+)-ga\d+__", eid)
        if m and m.group(1) != "1":
            cfg += f", b{m.group(1)}"
        if group.startswith("probe-"):
            cfg += " [probe]"
        return cfg

    def _merge_cfgs(cfgs: dict) -> str:
        """同模型的多个变体合并为一个条目：model (v1, v2×n)。"""
        by_model: dict[str, list] = {}
        for k, n in sorted(cfgs.items()):
            model, _, variant = k.partition(", ")
            by_model.setdefault(model, []).append((variant, n))
        out = []
        for model, variants in by_model.items():
            if len(variants) == 1 and not variants[0][0]:
                n = variants[0][1]
                out.append(_esc(model) + (f"$\\times${n}" if n > 1 else ""))
                continue
            body = ", ".join(
                (_esc(v) if v else _esc(model))
                + (f"$\\times${n}" if n > 1 else "")
                for v, n in variants)
            out.append(f"{_esc(model)} ({body})")
        return "; ".join(out)

    CAT_OS_KILL = "External SIGKILL (memory pressure)"
    CAT_TIMEOUT = "Supervisor timeout"
    CAT_INTERRUPT = "Operator interrupt"
    CAT_D5 = "Trainer implementation bug (D5)"
    CAT_DEBUG = "Pre-formal pipeline debug"
    CAT_OTHER = "Unresolved failure"
    order = [CAT_OS_KILL, CAT_TIMEOUT, CAT_INTERRUPT, CAT_D5,
             CAT_DEBUG, CAT_OTHER]
    cats: dict[str, dict] = {c: {"n": 0, "cfgs": {}, "states": set(),
                                  "steps": [], "wall": []}
                             for c in order}
    for f in taxonomy["failures"]:
        eid = f["experiment_id"]
        meta = full.loc[eid] if eid in full.index else None
        group = (str(meta["experiment.comparison_group_id"])
                 if meta is not None else "?")
        killed = f["signal"] == "SIGKILL" or f["exit_code"] == 137
        labels = set(f["evidence_labels"])
        if f["terminal_state"] == "runtime_error" and killed:
            cat = CAT_OS_KILL
        elif f["terminal_state"] == "timeout":
            cat = CAT_TIMEOUT
        elif f["terminal_state"] == "user_interrupted":
            cat = CAT_INTERRUPT
        elif (f["terminal_state"] == "runtime_error"
              and "stderr:python_traceback" in labels
              and group.startswith("formal-axis4")):
            cat = CAT_D5
        elif group == "exp0-smoke":
            cat = CAT_DEBUG
        else:
            cat = CAT_OTHER
        c = cats[cat]
        c["n"] += 1
        if meta is not None:
            s = pd.to_numeric(pd.Series([meta.get("runtime.successful_steps")]),
                              errors="coerce").iloc[0]
            if pd.notna(s):
                c["steps"].append(int(s))
            w = pd.to_numeric(pd.Series([meta.get("runtime.wall_clock_seconds")]),
                              errors="coerce").iloc[0]
            if pd.notna(w):
                c["wall"].append(float(w))
        cfg = _config(eid, group)
        c["cfgs"][cfg] = c["cfgs"].get(cfg, 0) + 1
        state = f["terminal_state"] + (f" ({f['signal']})" if f["signal"] else "")
        c["states"].add(state)

    def _steps_txt(c: dict) -> str:
        if c["steps"] and max(c["steps"]) == 0:
            return "0 completed steps"
        if c["steps"]:
            return f"{min(c['steps'])}--{max(c['steps'])} completed steps"
        return "steps not recorded"

    def _wall_txt(c: dict) -> str:
        if not c["wall"]:
            return ""
        lo, hi = min(c["wall"]), max(c["wall"])
        return (f"{lo:.0f}" if lo == hi else f"{lo:.0f}--{hi:.0f}") + "\\,s"

    evidence = {
        CAT_OS_KILL: lambda c: "exit 137 / SIGKILL, " + _steps_txt(c)
                     + "; kernel JetsamEvent confirms one b8 kill "
                     "(App.~\\ref{app:jetsam}); rest SIGKILL-consistent only, "
                     "not reclassified as OOM",
        CAT_TIMEOUT: lambda c: "killed at the configured supervisor "
                     + ("limit " + _wall_txt(c) if c["wall"] else "limit")
                     + " under multi-GiB swap residency",
        CAT_INTERRUPT: lambda c: "operator halt after "
                     + (_wall_txt(c) if c["wall"] else "partial run")
                     + "; retained as system-state evidence (D1/D7)",
        CAT_D5: lambda c: "python traceback in variable-length validation "
                "batching (micro-batch $\\ge$2); rerun on the fixed trainer",
        CAT_DEBUG: lambda c: "python traceback before the formal matrix "
                 "was frozen",
        CAT_OTHER: lambda c: "no specific pattern in exit evidence"
                + ((" " + _steps_txt(c)) if c["steps"] else "")
                + "; 14B attempt attributed to operator KeyboardInterrupt "
                  "per D8",
    }
    n_total = sum(c["n"] for c in cats.values())
    lines = [
        "\\begin{table*}[t]\\centering",
        "\\caption{Failure taxonomy over all " + str(n_total) +
        " failed runs (terminal states preserved verbatim; categories are "
        "evidence-based labels, never reclassifications).}",
        "\\label{tab:failures}", "\\footnotesize\\setlength{\\tabcolsep}{4pt}",
        "\\begin{tabular}{p{3.0cm}rp{3.4cm}p{7.0cm}}", "\\toprule",
        "Category & Runs & Configurations & Evidence\\\\", "\\midrule",
    ]
    for cat in order:
        c = cats[cat]
        if c["n"] == 0:
            continue
        cfgs = _merge_cfgs(c["cfgs"])
        # 终态去重：去掉同为其他状态前缀的项（如 runtime_error ⊂
        # runtime_error (SIGKILL)），避免重复罗列
        raw_states = sorted(c["states"])
        raw_states = [s for s in raw_states
                      if not any(t != s and t.startswith(s)
                                 for t in raw_states)]
        states = _esc("; ".join(raw_states))
        lines.append(f"{cat} & {c['n']} & {cfgs} & "
                     f"{evidence[cat](c)}; terminal state: {states}\\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    (TABLES / "table4_failures.tex").write_text("\n".join(lines) + "\n",
                                                encoding="utf-8")
    print("[table] table4_failures.tex")


def _swapin_range(sub: pd.DataFrame) -> str:
    """组内 whole-run swap-in/completed-step proxy 的 min–max。"""
    import math
    if "_swapin_per_step" not in sub.columns:
        return "--"
    vals = pd.to_numeric(sub["_swapin_per_step"], errors="coerce").dropna()
    vals = vals[~np.isinf(vals)]
    if vals.empty:
        return "--"
    lo = math.floor(float(vals.min()) + 0.5)
    hi = math.floor(float(vals.max()) + 0.5)
    return f"{lo}" if lo == hi else f"{lo}--{hi}"


def table5(df: pd.DataFrame) -> None:
    """轴 4 batch（D5 修复后同 commit 重跑；b8 SIGKILL 边界行）。"""
    lines = [
        "\\begin{table*}[t]\\centering",
        "\\caption{Batch axis (Qwen3-4B-4bit QLoRA, ctx512, r8, 20 steps, "
        "seeds \\{42,123,2026\\}, all cells rerun on the D5-fixed trainer in "
        "one window; mean$\\pm$SD; paging is the D4 whole-run swap-in "
        "delta normalized by completed training steps "
        "measure, all cells Tier-B; batch-8 kills recorded zero completed "
        "steps with empty stdout, so the MLX allocator peak is unavailable).}",
        "\\label{tab:batch}", "\\footnotesize\\setlength{\\tabcolsep}{2.8pt}",
        "\\begin{tabular}{rrrrrl}", "\\toprule",
        "Batch & Median step (s) & Tok/s & Peak mem (GiB) & "
        "Paging proxy (MB/completed step) & Status\\\\", "\\midrule",
    ]
    for b, g in ((1, "formal-axis4-b1"), (2, "formal-axis4-b2"),
                 (4, "formal-axis4-b4")):
        sub = df[(df["experiment.comparison_group_id"] == g)
                 & (df["status.terminal_state"] == "success")]
        if sub.empty:
            lines.append(f"{b} & -- & -- & -- & -- & missing\\\\")
            continue
        lines.append(
            f"{b} & {_agg_cell(sub, 'tm.median_step_time_seconds')} & "
            f"{_agg_cell(sub, 'runtime.tokens_per_second', 1)} & "
            f"{_agg_cell(sub, 'tm.peak_metal_gpu_memory_bytes', 2)} & "
            f"{_swapin_range(sub)} & success$\\times${len(sub)}\\\\")
    # b8 边界行：只认 exit-137 证据行（D5 修复后重跑系列），swap 取实测峰值
    full = pd.read_csv(ROOT / "results" / "processed" / "experiments.csv",
                       low_memory=False)
    b8 = full[(full["experiment.comparison_group_id"] == "formal-axis4-b8")
              & (full["status.exit_code"] == 137)
              & (full["status.terminal_state"] == "runtime_error")]
    if len(b8):
        swap_peak = pd.to_numeric(b8["runtime.peak_swap_bytes.value"],
                                  errors="coerce").max()
        swap_txt = (f"near {swap_peak / 2**30:.0f}\\,GiB"
                    if pd.notna(swap_peak) else "")
        lines.append(f"8 & -- & -- & -- & -- & "
                     f"SIGKILL$\\times${len(b8)} (exit 137; system swap "
                     f"{swap_txt})\\\\")
    else:
        lines.append("8 & -- & -- & -- & -- & "
                     "no exit-137 evidence rows\\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    (TABLES / "table5_batch_axis.tex").write_text("\n".join(lines) + "\n",
                                                  encoding="utf-8")
    print("[table] table5_batch_axis.tex")


def table6(df: pd.DataFrame) -> None:
    """轴 3 rank（r8 复用轴 1 点）。"""
    lines = [
        "\\begin{table}[t]\\centering",
        "\\caption{LoRA rank axis (Qwen3-4B-4bit QLoRA, ctx512, b1, 20 steps "
        "for r4/r32; r8 point reused from the 100-step axis-1 cell per "
        "preregistration; mean$\\pm$SD; all cells Tier-B).}",
        "\\label{tab:rank}", "\\footnotesize\\setlength{\\tabcolsep}{2pt}",
        "\\begin{tabular}{rrrrr}", "\\toprule",
        "Rank & Median step (s) & Tok/s & Peak mem (GiB) & "
        "Swap-in\\\\", "\\midrule",
    ]
    for r, g in ((4, "formal-axis3-r4"), (8, "formal-axis1-4b-4bit-qlora"),
                 (32, "formal-axis3-r32")):
        sub = df[(df["experiment.comparison_group_id"] == g)
                 & (df["status.terminal_state"] == "success")]
        if sub.empty:
            lines.append(f"{r} & -- & -- & -- & --\\\\")
            continue
        lines.append(
            f"{r} & {_agg_cell(sub, 'tm.median_step_time_seconds')} & "
            f"{_agg_cell(sub, 'runtime.tokens_per_second', 1)} & "
            f"{_agg_cell(sub, 'tm.peak_metal_gpu_memory_bytes', 2)} & "
            f"{_swapin_range(sub)}\\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (TABLES / "table6_rank_axis.tex").write_text("\n".join(lines) + "\n",
                                                 encoding="utf-8")
    print("[table] table6_rank_axis.tex")


def _mean(sub: pd.DataFrame, col: str) -> float | None:
    vals = pd.to_numeric(sub[col], errors="coerce").dropna()
    return float(vals.mean()) if len(vals) else None


def _latex_escape(s: str) -> str:
    s = s.replace("\\", "")
    s = s.replace("%", "\\%").replace("&", "\\&").replace("_", "\\_")
    s = s.replace("<=", "$\\le$").replace(">=", "$\\ge$")
    s = s.replace("->", "$\\to$").replace("+/-", "$\\pm$")
    s = s.replace("<", "$<$").replace(">", "$>$")
    return s


def table11(df: pd.DataFrame) -> None:
    """H1-H6 假设与当前审计计算；冻结/事后对照另表生成。

    数据源 results/processed/hypothesis_audit.json（由 hypothesis_audit.py
    从 raw 生成）；正文各处 "audit Hx" 均指向本表，规则原文不手改。
    """
    audit = json.loads((ROOT / "results" / "processed" /
                        "hypothesis_audit.json").read_text())
    status_nice = {"supported": "Supported",
                   "partially_supported": "Partially supported",
                   "unsupported": "Unsupported",
                   "insufficient": "Insufficient"}
    lines = [
        "\\begin{table*}[t]\\centering",
        "\\caption{Hypotheses H1--H6 with the current audit calculations "
        "(generated from raw-derived processed data). $^{\\dagger}$v2 rule: revised after "
        "results under D9 (App.~\\ref{app:deviations}), with the "
        "preregistration-era v1 rule and counterfactual verdict disclosed "
        "there. ``audit Hx'' mentions throughout the text refer to this "
        "table. H3's $n$=7 includes the cross-window 4B pair "
        "($\\dagger$, Table~\\ref{tab:paired}); the within-window count is "
        "6, and the verdict is unchanged either way.}",
        "\\label{tab:hyp}", "\\footnotesize\\setlength{\\tabcolsep}{3pt}",
        "\\begin{tabular}{@{}lp{4.0cm}p{5.8cm}rp{2.5cm}@{}}", "\\toprule",
        "ID & Hypothesis & Audit rule & $n$ & Verdict\\\\",
        "\\midrule",
    ]
    for hid, v in audit["hypotheses"].items():
        hyp = _latex_escape(v["hypothesis"].split(": ", 1)[1])
        rule = _latex_escape(v["rule"])
        v2 = v["rule"].startswith("v2")
        mark = "$^{\\dagger}$" if v2 else ""
        verdict = (status_nice.get(v["conclusion_status"],
                                   v["conclusion_status"]) +
                   (" (v2 rule)" if v2 else "") + mark)
        n = v["sample_size"]
        if isinstance(n, dict):
            n_txt = ", ".join(f"{k.rsplit('_', 1)[0]}={x}"
                              for k, x in n.items())
        else:
            n_txt = str(n)
        lines.append(f"{hid} & {hyp} & {rule}{mark} & {n_txt} & "
                     f"{verdict}\\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    TABLES.mkdir(parents=True, exist_ok=True)
    (TABLES / "table11_hypotheses.tex").write_text("\n".join(lines) + "\n",
                                                   encoding="utf-8")
    print("[table] table11_hypotheses.tex")


def table12(df: pd.DataFrame) -> None:
    """27 个失败运行的处置审计表（数据源 coverage_report.json，计数与命名均派生）。"""
    cov = json.loads((ROOT / "results" / "processed" /
                      "coverage_report.json").read_text())
    fails = {rid: v for rid, v in cov["per_run"].items()
             if v["state"] != "success"}
    disp = {}
    for v in fails.values():
        disp.setdefault(v["disposition"], []).append(v)
    dup = disp.get("excluded:duplicate", [])
    dup_states = ", ".join(
        f"{sum(1 for x in dup if x['state'] == st)}$\\times$ "
        f"{st.replace('_', '\\_')}"
        for st in sorted({x["state"] for x in dup}))
    dup_groups = ", ".join(sorted({x["group"].replace("formal-", "")
                                   for x in dup}))
    nf = (disp.get("non-formal:probe", []) +
          disp.get("non-formal:exp0-smoke", []) +
          disp.get("non-formal:calibration", []))
    from collections import Counter as _C
    _nfg = _C(x["group"].replace("probe-", "") for x in nf)
    nf_groups = ", ".join(f"{v}$\\times$ {k}" for k, v in sorted(_nfg.items()))
    rows = [
        ("Implementation-invalid (D5)",
         len(disp.get("excluded:implementation-invalid-d5", [])),
         "D5 trainer-bug signature (Table~\\ref{tab:failures} D5 row); "
         "rerun on the fixed trainer, preserved immutably."),
        ("Retained failure", len(disp.get("failed_retained_for_taxonomy", [])),
         "formal SIGKILL / timeout / operator-interrupt / unresolved runs "
         "retained as evidence."),
        ("Duplicate", len(dup),
         f"D2 dedup applied to failures ({dup_states}; groups: "
         f"{dup_groups}); see Sec.~"
         "\\ref{sec:failures} for the "
         "batch-8 ledger subtlety."),
        ("Non-formal (probe / exp0-smoke)", len(nf),
         f"pre-formal debug and probe runs outside the formal matrix "
         f"({nf_groups}); not formal cells."),
        ("Superseded", 0,
         "\\emph{no} failed run is superseded; all superseded rows are "
         "successful early runs (D2)."),
    ]
    lines = [
        "\\begin{table*}[t]\\centering",
        "\\caption{Audit disposition of the 27 failed runs, generated "
        "from the coverage report (abbreviating its machine-readable "
        "dispositions; evidence-level categories are in "
        "Table~\\ref{tab:failures}). The counts reconcile the failure "
        "taxonomy with the 118-run coverage audit.}",
        "\\label{tab:failedisposition}",
        "\\footnotesize\\setlength{\\tabcolsep}{5pt}",
        "\\begin{tabular}{@{}p{3.0cm}cp{8.0cm}@{}}", "\\toprule",
        "Coverage disposition & Runs & Meaning\\\\", "\\midrule",
    ]
    for name, cnt, meaning in rows:
        lines.append(f"{name} & {cnt} & {meaning}\\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    (TABLES / "table12_disposition.tex").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    print("[table] table12_disposition.tex")


def table13(df: pd.DataFrame) -> None:
    """Context axis (axis-2) 每格中位数（R2 建议的数据表，来源同 fig5）。"""
    groups = [("512 (reuse a1)", "formal-axis1-4b-4bit-qlora"),
              ("1024", "formal-axis2-ctx1024"),
              ("2048", "formal-axis2-ctx2048")]
    lines = [
        "\\begin{table}[t]\\centering",
        "\\caption{Maximum sequence-length-cap axis (Qwen3-4B-4bit QLoRA, 20 steps; cap512 "
        "reuses the axis-1 100-step cell per preregistration; mean$\\pm$SD "
        "over completed seeds; the ctx2048 s123 rerun completed in a "
        "lower-residency window than its peers, Sec.~\\ref{sec:ctx}). "
        "cap4096/8192 probes were SIGKILLed before any step and have no "
        "measurable medians. The non-monotonic medians (23.98 vs 20.66) reflect opposite window-state biases, not a context cliff (Sec.~\\ref{sec:ctx}).}",
        "\\label{tab:ctx}", "\\footnotesize\\setlength{\\tabcolsep}{3pt}",
        "\\begin{tabular}{lrrr}", "\\toprule",
        "Cap & Med step (s) & Peak (GiB) & Seeds\\\\", "\\midrule",
    ]
    for label, g in groups:
        sub = df[(df["experiment.comparison_group_id"] == g)
                 & (df["status.terminal_state"] == "success")]
        if sub.empty:
            lines.append(f"{label} & -- & -- & 0/3\\\\"); continue
        lines.append(f"{label} & "
                     f"{_agg_cell(sub, 'tm.median_step_time_seconds')} & "
                     f"{_agg_cell(sub, 'tm.peak_metal_gpu_memory_bytes', 2)} & "
                     f"{len(sub)}/3\\\\")
    lines += ["4096 [probe] & \\multicolumn{3}{l}{SIGKILL, 0 steps "
             "(single seed)}\\\\",
             "8192 [probe] & \\multicolumn{3}{l}{SIGKILL, 0 steps "
             "(single seed)}\\\\",
             "\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (TABLES / "table13_context.tex").write_text("\n".join(lines) + "\n",
                                                encoding="utf-8")
    print("[table] table13_context.tex")


def main() -> int:
    df = _load()
    table1(df)
    table2(df)
    table3(df)
    table4(df)
    table5(df)
    table6(df)
    table11(df)
    table12(df)
    table13(df)
    return 0
