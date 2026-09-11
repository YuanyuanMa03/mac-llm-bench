"""论文表格生成（全部从 processed 数据派生 → paper/tables/*.tex）。

Table 1 hardware/software/model revisions（来自 formal run 的 raw provenance）
Table 2 formal matrix 汇总（mean±SD over 3 seeds）
Table 3 paired BF16 vs 4bit（含预注册 ±25% 等价判定）
Table 4 failure/boundary observations
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .stats import mean_sd_ci, paired_ratio

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "paper" / "tables"


def _load() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "results" / "processed" / "experiments.csv",
                     low_memory=False)
    formal = df[df["experiment.comparison_group_id"].astype(str).str.startswith(
        ("formal-", "probe-8b-bf16", "probe-14b-4bit"))]
    return formal


def _agg_cell(sub: pd.DataFrame, col: str, digits: int = 3) -> str:
    a = mean_sd_ci([float(v) for v in sub[col]])
    if a is None:
        return "--"
    unit_scale = 1
    suffix = ""
    if col == "tm.peak_metal_gpu_memory_bytes":
        unit_scale = 2**30
        suffix = " GiB"
    if a["sd"] is None:
        return f"{a['mean'] / unit_scale:.{digits}f}{suffix}"
    return (f"{a['mean'] / unit_scale:.{digits}f}±{a['sd'] / unit_scale:.{digits}f}"
            f"{suffix}")


def table1(df: pd.DataFrame) -> None:
    ref = df[df["status.terminal_state"] == "success"].iloc[-1]
    h = ref["hardware"]
    rows = [
        ("Hardware", ""),
        ("\\quad Chip", f"{h['apple_chip_model']}"),
        ("\\quad Memory", f"{h['unified_memory_bytes'] / 2**30:.0f} GiB unified"),
        ("\\quad CPU cores", f"{h['cpu_physical_cores']}P / {h['cpu_logical_cores']}L"),
        ("OS", f"macOS {ref['software']['macos_version']} (build {ref['software']['macos_build']})"),
        ("Python", f"{ref['software']['python_version'].split()[0]} (uv-managed venv)"),
        ("MLX / mlx-lm", f"{ref['software']['mlx_version']} / {ref['software']['mlx_lm_version']}"),
        ("Training data", "ultrachat\\_200k@8049631c, frozen 2048/32 subset"),
    ]
    models = []
    seen = set()
    for _, r in df.iterrows():
        key = (r["model.id"], r["model.resolved_revision"])
        if key[0] in seen or pd.isna(r["model.resolved_revision"]):
            continue
        seen.add(key[0])
        models.append((key[0], str(key[1])[:12]))
    lines = [
        "\\begin{table}[t]\\centering",
        "\\caption{Hardware, software, and model revisions "
        "(provenance from raw experiment records).}",
        "\\label{tab:setup}",
        "\\small",
        "\\begin{tabular}{ll}", "\\toprule",
    ]
    for k, v in rows:
        lines.append(f"{k} & {v}\\\\")
    lines.append("\\midrule")
    lines.append("Models & resolved revision\\\\")
    for name, rev in models:
        lines.append(f"\\quad \\texttt{{{name}}} & \\texttt{{{rev}}}...\\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    TABLES.mkdir(parents=True, exist_ok=True)
    (TABLES / "table1_setup.tex").write_text("\n".join(lines) + "\n",
                                             encoding="utf-8")
    print("[table] table1_setup.tex")


def table2(df: pd.DataFrame) -> None:
    lines = [
        "\\begin{table*}[t]\\centering",
        "\\caption{Formal benchmark at ctx=512, b1-ga1, rank 8, lr 1e-4, "
        "100 steps, seeds \\{42,123,2026\\} (mean$\\pm$SD; memory is MLX "
        "allocator peak).}",
        "\\label{tab:matrix}", "\\small",
        "\\begin{tabular}{llrrrr}", "\\toprule",
        "Model & Method & Peak mem (GiB) & Median step (s) & Tok/s & "
        "Val loss\\\\", "\\midrule",
    ]
    order = [("0.6b", "full"), ("0.6b", "lora"), ("1.7b", "lora"),
             ("4b", "lora"), ("0.6b", "qlora"), ("1.7b", "qlora"),
             ("4b", "qlora"), ("8b", "qlora"), ("14b", "qlora")]
    nice = {"lora": "BF16 LoRA", "qlora": "4bit QLoRA", "full": "Full FT"}
    for model, method in order:
        g = f"formal-axis1-{model}-{method if method != 'full' else 'full'}"
        sub = df[(df["experiment.comparison_group_id"] == g)
                 & (df["status.terminal_state"] == "success")]
        if sub.empty:
            lines.append(f"{model} & {nice[method]} & -- & -- & -- & --\\\\")
            continue
        params = float(sub["tm.logical_parameter_count"].iloc[0]) / 1e9
        lines.append(
            f"Qwen3-{model} ({params:.1f}B) & {nice[method]} & "
            f"{_agg_cell(sub, 'tm.peak_metal_gpu_memory_bytes', 2)} & "
            f"{_agg_cell(sub, 'tm.median_step_time_seconds')} & "
            f"{_agg_cell(sub, 'runtime.tokens_per_second', 1)} & "
            f"{_agg_cell(sub, 'metrics.validation_loss_final', 3)}\\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    (TABLES / "table2_matrix.tex").write_text("\n".join(lines) + "\n",
                                              encoding="utf-8")
    print("[table] table2_matrix.tex")


def table3(df: pd.DataFrame) -> None:
    lines = [
        "\\begin{table}[t]\\centering",
        "\\caption{Paired quantization effects (same model/seed; ratios = "
        "4bit/BF16). Timing equivalence margin $\\pm$25\\% frozen before "
        "benchmark.}",
        "\\label{tab:paired}", "\\small",
        "\\begin{tabular}{lrrr}", "\\toprule",
        "Model & Mem ratio & Step-time ratio & Tok/s ratio\\\\", "\\midrule",
    ]
    verdicts = {}
    for model in ("0.6b", "1.7b", "4b"):
        ga, gb = f"formal-axis1-{model}-bf16-lora", f"formal-axis1-{model}-4bit-qlora"
        cells = []
        step_ratios = []
        for col in ("tm.peak_metal_gpu_memory_bytes",
                    "tm.median_step_time_seconds", "runtime.tokens_per_second"):
            pr = paired_ratio(df, ga, gb, value_col=col)
            if not pr:
                cells.append("--")
                continue
            import numpy as np
            r = [p["ratio_b_over_a"] for p in pr]
            cells.append(f"{np.mean(r):.2f}")
            if col == "tm.median_step_time_seconds":
                step_ratios = r
        verdict = ("within margin" if step_ratios
                   and all(0.80 <= x <= 1.25 for x in step_ratios)
                   else ("slower" if any(x > 1.25 for x in step_ratios)
                         else "faster"))
        verdicts[model] = {"step_ratios": step_ratios, "verdict": verdict}
        lines.append(f"Qwen3-{model} & {' & '.join(cells)}\\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (TABLES / "table3_paired.tex").write_text("\n".join(lines) + "\n",
                                              encoding="utf-8")
    (ROOT / "results" / "processed" / "paired_equivalence_verdicts.json").write_text(
        json.dumps({"margin": [0.80, 1.25], "verdicts": verdicts}, indent=2) + "\n")
    print("[table] table3_paired.tex")


def table4(df: pd.DataFrame) -> None:
    taxonomy = json.loads((ROOT / "results" / "processed" /
                           "failure_taxonomy.json").read_text())
    boundary = json.loads((ROOT / "results" / "processed" /
                           "context_boundary_probe_summary.json").read_text())
    lines = [
        "\\begin{table}[t]\\centering",
        "\\caption{Failure and boundary observations (raw terminal states, "
        "never reclassified as OOM without direct evidence).}",
        "\\label{tab:failures}", "\\small",
        "\\begin{tabular}{p{3.4cm}ll}", "\\toprule",
        "Run & Status & Key observation\\\\", "\\midrule",
    ]
    for f in taxonomy["failures"]:
        steps = f["context_observations"]["completed_steps_observation"]
        key = f"{f['terminal_state']}"
        if f["signal"]:
            key += f" ({f['signal']})"
        lines.append(
            f"\\texttt{{{f['experiment_id'][:36]}}} & {key} & "
            f"steps={steps if steps is not None else 'n/a'}; "
            f"{'/'.join(f['evidence_labels'])}\\\\")
    b = boundary["boundary_interval"]
    lines.append("\\midrule")
    lines.append(
        f"\\multicolumn{{3}}{{p{{9cm}}}}{{Context boundary: "
        f"Trainable $\\in$ [{b['trainable_upper_bound_ctx']}, "
        f"{b['first_failure_ctx']}) under preflight-comparable conditions.}}\\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (TABLES / "table4_failures.tex").write_text("\n".join(lines) + "\n",
                                                encoding="utf-8")
    print("[table] table4_failures.tex")


def main() -> int:
    df = _load()
    table1(df)
    table2(df)
    table3(df)
    table4(df)
    return 0
