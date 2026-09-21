#!/usr/bin/env python3
"""Generate the public claim ledger from canonical processed and raw evidence."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "results" / "processed"
RAW = ROOT / "results" / "raw"
FREEZE = "freeze-04f90a840b8ea8fb"
FIELDS = [
    "claim_id", "claim_text", "processed_source", "raw_source_ids",
    "analysis_status", "evidence_grade", "paper_section_label_optional",
]


def _load(name: str):
    return json.loads((PROC / name).read_text(encoding="utf-8"))


def _fmt(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def main() -> int:
    df = pd.read_csv(PROC / "experiments.csv", low_memory=False)
    coverage = _load("coverage_report.json")
    key = _load("key_numbers.json")
    context = _load("context_boundary_probe_summary.json")
    state = _load("system_state.json")
    val = _load("val_loss_tests.json")
    batch8 = _load("figure8c_batch8_source.json")
    memory = _load("memory_decomposition.json")

    dispositions = {k: v["disposition"] for k, v in coverage["per_run"].items()}

    def ids_for(groups=(), *, included=False, terminal=None):
        sub = df[df["experiment.comparison_group_id"].isin(groups)] if groups else df
        if included:
            sub = sub[sub["experiment.id"].map(dispositions) == "aggregation_included"]
        if terminal is not None:
            sub = sub[sub["status.terminal_state"].isin(terminal)]
        return sorted(set(sub["experiment.id"].astype(str)))

    def joined(ids):
        return ";".join(sorted(set(ids)))

    paired_groups = [
        "formal-axis1-0.6b-bf16-lora", "formal-axis1-0.6b-4bit-qlora",
        "formal-axis1-1.7b-bf16-lora", "formal-axis1-1.7b-4bit-qlora",
        "formal-axis1-4b-bf16-lora", "formal-axis1-4b-4bit-qlora",
    ]
    scale_4bit = [
        "formal-axis1-0.6b-4bit-qlora", "formal-axis1-1.7b-4bit-qlora",
        "formal-axis1-4b-4bit-qlora", "formal-axis1-8b-4bit-qlora",
    ]
    context_groups = ["formal-axis1-4b-4bit-qlora", "formal-axis2-ctx1024", "formal-axis2-ctx2048"]
    batch_groups = ["formal-axis4-b1", "formal-axis4-b2", "formal-axis4-b4"]
    rank_groups = ["formal-axis3-r4", "formal-axis1-4b-4bit-qlora", "formal-axis3-r32"]

    paired_ids = ids_for(paired_groups, included=True)
    scale_ids = ids_for(scale_4bit, included=True)
    context_ids = ids_for(context_groups, included=True)
    batch_ids = ids_for(batch_groups, included=True)
    rank_ids = ids_for(rank_groups, included=True)
    all_raw_ids = sorted(coverage["per_run"])
    success_ids = ids_for(terminal={"success"})
    alignment_ids = [r["experiment_id"] for r in state["step_swap_alignment"]["runs"]]
    memory_groups = [c["group"] for c in memory["cells"]]
    memory_ids = ids_for(memory_groups, included=True)

    eight = key["scale_axis"]["formal-axis1-8b-4bit-qlora"]
    eight_rows = df[df["experiment.id"].isin(ids_for(["formal-axis1-8b-4bit-qlora"], included=True))]
    wall = sorted(float(x) for x in eight_rows["runtime.wall_clock_seconds"].dropna())
    fit_mem = key["fits"]["4bit_qlora"]["memory"]
    fit_time = key["fits"]["4bit_qlora"]["step_time"]
    c1024, c2048 = key["context_axis"]["1024"], key["context_axis"]["2048"]
    b = key["batch_axis"]
    r = key["rank_axis"]
    boundary14 = state["boundary14b_timeout_run"]
    same = state["same_config_contrasts"]
    d1_high = next(x for x in same if x["config"] == "4B BF16, ctx512" and "high" in x["state"])
    d1_low = next(x for x in same if x["config"] == "4B BF16, ctx512" and "swap 0" in x["state"])

    def row(cid, text, sources, ids, status, grade, section):
        return {
            "claim_id": cid,
            "claim_text": text,
            "processed_source": ";".join(sources),
            "raw_source_ids": joined(ids),
            "analysis_status": status,
            "evidence_grade": grade,
            "paper_section_label_optional": section,
        }

    rows = [
        row("C1", "Paired 4-bit QLoRA allocator peaks were 0.54-0.73x the BF16 LoRA peaks across seven observed seed pairs.",
            ["results/processed/key_numbers.json#paired"], paired_ids, "confirmatory descriptive", "paired raw measurements", "Quantization effects"),
        row("C2", f"8B 4-bit was the largest tested configuration with a completed three-seed preregistered set within one favorable observed machine-state window; runs took {_fmt(min(wall),0)}-{_fmt(max(wall),0)} s and allocator peak averaged {_fmt(eight['peak_mem_gib']['mean'])} GiB.",
            ["results/processed/key_numbers.json#scale_axis", "results/processed/system_state.json#same_config_contrasts"], ids_for(["formal-axis1-8b-4bit-qlora"], included=True), "confirmatory with window scope", "three seeds in one window", "Scale feasibility"),
        row("C3", "Within the two fully paired three-seed scales, observed 4-bit/BF16 step-time ratios were 1.10-1.23 and fell inside the preregistered +/-25% margin; the 4B single cross-window pair is descriptive only.",
            ["results/processed/paired_equivalence_verdicts.json", "results/processed/key_numbers.json#paired"], paired_ids, "confirmatory for 0.6B and 1.7B; descriptive for 4B", "paired measurements with stated exclusion", "Quantization effects"),
        row("C4", f"Across the measured 4-bit scale range, allocator peak memory had log-log slope {_fmt(fit_mem['slope'])} +/- {_fmt(fit_mem['stderr_slope'])} (R2={_fmt(fit_mem['r_squared'])}, four group means), which is sublinear over the measured range.",
            ["results/processed/memory_scaling_fits.json", "results/processed/key_numbers.json#fits"], scale_ids, "confirmatory scaling analysis", "four group means", "Memory scaling"),
        row("C5", f"The 4-bit step-time log-log slope was {_fmt(fit_time['slope'])} +/- {_fmt(fit_time['stderr_slope'])} (R2={_fmt(fit_time['r_squared'])}); corrected paging strata are mixed, so absolute timing remains window- and tier-scoped.",
            ["results/processed/step_time_scaling_fits.json", "results/processed/tier_classification.json"], scale_ids, "confirmatory scaling analysis with corrected stratification", "mixed paging strata", "Step-time scaling"),
        row("C6", f"For 4B 4-bit, the 1024-cap group averaged {_fmt(c1024['median_step_s']['mean'],1)} s/step and {_fmt(c1024['peak_mem_gib']['mean'])} GiB peak; the 2048-cap group averaged {_fmt(c2048['median_step_s']['mean'],1)} s/step and {_fmt(c2048['peak_mem_gib']['mean'])} GiB peak.",
            ["results/processed/key_numbers.json#context_axis", "results/processed/context_actual_lengths.json"], context_ids, "confirmatory descriptive", "three seeds per formal cap", "Context axis"),
        row("C7", "Observed maximum-context bracket: the 2048-cap workload completed; the first observed failure was a single-seed synthetic 4096-cap probe. This is not a statistical or physical trainability threshold.",
            ["results/processed/context_boundary_probe_summary.json"], [x["experiment_id"] for x in context["series"]], "boundary observation", "single-seed synthetic upper-edge probe", "Context axis"),
        row("C8", f"In the valid batch-axis set, throughput decreased from {_fmt(b['1']['tokens_per_s']['mean'],1)} to {_fmt(b['2']['tokens_per_s']['mean'],1)} to {_fmt(b['4']['tokens_per_s']['mean'],1)} token/s for b1/b2/b4 while allocator peak rose from {_fmt(b['1']['peak_mem_gib']['mean'])} to {_fmt(b['2']['peak_mem_gib']['mean'])} to {_fmt(b['4']['peak_mem_gib']['mean'])} GiB.",
            ["results/processed/key_numbers.json#batch_axis"], batch_ids, "confirmatory descriptive", "three valid seeds per completed batch", "Batch axis"),
        row("C9", f"All three valid 2026-09-15 batch-8 runs terminated before the first completed optimizer step; swap peaks spanned {_fmt(batch8['swap_peak_gib_min'],1)}-{_fmt(batch8['swap_peak_gib_max'],1)} GiB. D5-invalid 2026-09-12 rows do not support this claim.",
            ["results/processed/figure8c_batch8_source.json", "results/processed/system_state.json#batch8_sigkill"], batch8["experiment_ids"], "boundary observation", "three valid runs; one has withheld kernel corroboration", "Batch axis"),
        row("C10", f"For 4B 4-bit, ranks 4/8/32 changed mean step time by less than 2% around the shared rank-8 baseline, while the measured peak range was {_fmt(max(r[x]['peak_mem_gib']['mean'] for x in r)-min(r[x]['peak_mem_gib']['mean'] for x in r))} GiB.",
            ["results/processed/rank_relative_effects.csv", "results/processed/key_numbers.json#rank_axis"], rank_ids, "confirmatory descriptive", "three seeds per rank", "Rank axis"),
        row("C11", f"The 14B 4-bit boundary evidence includes a completed 20-step probe, a roughly 24-minute zero-step formal observation, and a timeout after {boundary14['n_steps_completed']}/{boundary14['requested_steps']} steps with observed step times {_fmt(boundary14['step_time_min_s'],1)}-{_fmt(boundary14['step_time_max_s'],1)} s and swap {_fmt(boundary14['monitor_summary']['swap_min_gib'],1)}-{_fmt(boundary14['monitor_summary']['swap_max_gib'],1)} GiB.",
            ["results/processed/system_state.json#boundary14b_timeout_run", "results/processed/failure_progress.json"], ids_for(["probe-14b-4bit-qlora20-seed42", "formal-axis1-14b-4bit-qlora"]), "boundary observation", "probe plus two formal observations", "14B boundary"),
        row("C12", f"For the same 4B BF16 configuration, the high-residency observation made {d1_high['steps']} completed-step progress in about 27 minutes, while the zero-residency rerun completed in {d1_low['outcome'].split(' ')[2]} s with median step time {d1_low['median_step_s']} s.",
            ["results/processed/system_state.json#same_config_contrasts", "results/processed/key_numbers.json#scale_axis"], ids_for(["formal-axis1-4b-bf16-lora"]), "boundary observation", "same configuration across two state windows", "Machine state"),
        row("C13", f"At the frozen learning rate, 0.6B full fine-tuning ended at mean validation loss {_fmt(key['scale_axis']['formal-axis1-0.6b-bf16-full']['val_loss_final']['mean'])}, versus {_fmt(key['scale_axis']['formal-axis1-0.6b-4bit-qlora']['val_loss_final']['mean'])} for 4-bit QLoRA; the full-fine-tuning outcome is retained as a negative result.",
            ["results/processed/key_numbers.json#scale_axis"], ids_for(["formal-axis1-0.6b-bf16-full", "formal-axis1-0.6b-4bit-qlora"], included=True), "negative result", "three seeds per group", "Scale feasibility"),
        row("C14", f"The corpus contains {coverage['raw_total']} finalized runs and 27 failures; 9 D5 implementation-invalid attempts are excluded by signature, {coverage['dispositions']['aggregation_included']} runs enter aggregation, and raw-to-processed reconciliation is complete.",
            ["results/processed/coverage_report.json", "results/processed/failure_taxonomy.json"], all_raw_ids, "corpus audit", "complete raw census", "Failure accounting"),
        row("C15", f"After the 100-step benchmark, observed 4-bit minus BF16 final validation-loss differences were {_fmt(val['0.6b']['diff_4bit_minus_bf16_mean'],4)} at 0.6B and {_fmt(val['1.7b']['diff_4bit_minus_bf16_mean'],4)} at 1.7B; no converged-quality equivalence is claimed.",
            ["results/processed/val_loss_tests.json"], ids_for(["formal-axis1-0.6b-bf16-lora", "formal-axis1-0.6b-4bit-qlora", "formal-axis1-1.7b-bf16-lora", "formal-axis1-1.7b-4bit-qlora"], included=True), "descriptive", "paired three-seed short-run losses", "Training effectiveness"),
        row("C16", "Among completed runs, group-mean within-run drift stayed near 1 while step-time dispersion rose in heavier paging regimes; this describes burstiness without establishing a causal mechanism.",
            ["results/processed/step_dynamics.json"], success_ids, "post-hoc exploratory", "91 successful runs with available summaries", "Step-time dynamics"),
        row("C17", "The 8B median step time was 10.039 s and its empirical p99 was about 3.1 times the median; the tail metric is descriptive and window-specific.",
            ["results/processed/step_dynamics.json", "results/processed/key_numbers.json#scale_axis"], ids_for(["formal-axis1-8b-4bit-qlora"], included=True), "post-hoc exploratory", "three runs in one window", "Step-time dynamics"),
        row("C18", f"The 14B timeout completed {boundary14['n_steps_completed']}/{boundary14['requested_steps']} steps and showed an oscillating {_fmt(boundary14['monitor_summary']['swap_min_gib'],1)}-{_fmt(boundary14['monitor_summary']['swap_max_gib'],1)} GiB swap trace; step-level wall-clock alignment is unavailable for the timeout.",
            ["results/processed/system_state.json#boundary14b_timeout_run"], [boundary14["experiment_id"]], "post-hoc exploratory", "single boundary trajectory", "Machine state"),
        row("C19", f"The valid batch-8 trio rose by {_fmt(batch8['swap_ramp_gib_min'],1)}-{_fmt(batch8['swap_ramp_gib_max'],1)} GiB before termination, reaching peaks of {_fmt(batch8['swap_peak_gib_min'],1)}-{_fmt(batch8['swap_peak_gib_max'],1)} GiB with zero completed steps.",
            ["results/processed/figure8c_batch8_source.json", "results/processed/system_state.json#batch8_sigkill"], batch8["experiment_ids"], "post-hoc exploratory", "three valid trajectories", "Machine state"),
        row("C20", "Concurrent system swap level had median within-run Spearman rho about +0.22 in Tier-A and +0.10 in Tier-B aligned runs; this is descriptive co-variation under second-resolution and attribution limits.",
            ["results/processed/system_state.json#step_swap_alignment"], alignment_ids, "post-hoc exploratory", "aligned subset with explicit caveats", "Machine state"),
        row("C21", "Memory accounting leaves an unallocated residual for adapter runs; the reported affine slope decomposition is an arithmetic partition of stored-weight and residual slopes, not causal proof of an overhead mechanism.",
            ["results/processed/memory_decomposition.json", "models/MANIFEST.md"], memory_ids, "post-hoc exploratory", "measured allocator peaks plus model manifest", "Memory decomposition"),
    ]

    # Validate every source and raw ID before writing.
    for item in rows:
        for source in item["processed_source"].split(";"):
            rel = source.split("#", 1)[0]
            if not (ROOT / rel).exists():
                raise FileNotFoundError(f"{item['claim_id']}: missing source {rel}")
        for exp_id in filter(None, item["raw_source_ids"].split(";")):
            if not (RAW / exp_id).is_dir():
                raise FileNotFoundError(f"{item['claim_id']}: missing raw experiment {exp_id}")

    out = ROOT / "research" / "claim_ledger.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"[claim_ledger] {len(rows)} public claims -> {out.relative_to(ROOT)} ({FREEZE})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
