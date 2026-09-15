#!/usr/bin/env python3
"""生成 research/claim_ledger.csv：论文定量 claim → processed 来源 → raw IDs。

Claim 的位置/文本/来源字段为人工映射（本脚本内 CLAIMS 常量）；每个 claim
的支撑 raw experiment IDs 由 (group, seeds) 键从 results/processed/
experiments.csv 程序化展开，保证与冻结数据一致（freeze-04f90a840b8ea8fb）。
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "results" / "processed"

# (claim_id, paper_location, claim_text, processed_source, groups, seeds)
CLAIMS = [
    ("C1", "Abstract; Results/Quantization",
     "4-bit QLoRA peak memory is 0.54-0.73x of BF16 LoRA (paired, n=7)",
     "key_numbers.json:paired.*.tm.peak_metal_gpu_memory_bytes",
     ["formal-axis1-0.6b-bf16-lora", "formal-axis1-1.7b-bf16-lora",
      "formal-axis1-4b-bf16-lora", "formal-axis1-0.6b-4bit-qlora",
      "formal-axis1-1.7b-4bit-qlora", "formal-axis1-4b-4bit-qlora"], [42, 123, 2026]),
    ("C2", "Abstract; Results/Scale Feasibility",
     "8B 4-bit QLoRA is the highest reproducibly trainable scale: 3/3 seeds, "
     "1644-1694 s per 100-step run, 9.19 GiB peak",
     "key_numbers.json:scale_axis[formal-axis1-8b-4bit-qlora]",
     ["formal-axis1-8b-4bit-qlora"], [42, 123, 2026]),
    ("C3", "Abstract; Results/Quantization; Table 3",
     "All paired step-time ratios (1.10-1.23) fall within the preregistered "
     "+/-25% equivalence margin (n=7)",
     "key_numbers.json:paired.*.tm.median_step_time_seconds; "
     "paired_equivalence_verdicts.json",
     ["formal-axis1-0.6b-bf16-lora", "formal-axis1-1.7b-bf16-lora",
      "formal-axis1-4b-bf16-lora", "formal-axis1-0.6b-4bit-qlora",
      "formal-axis1-1.7b-4bit-qlora", "formal-axis1-4b-4bit-qlora"], [42, 123, 2026]),
    ("C4", "Abstract; Results/Memory Scaling (negative result)",
     "4-bit memory log-log slope 0.57+/-0.05 (R2=0.99, n=4): sublinear, "
     "linear hypothesis rejected (H4 unsupported)",
     "key_numbers.json:fits.4bit_qlora.memory",
     ["formal-axis1-0.6b-4bit-qlora", "formal-axis1-1.7b-4bit-qlora",
      "formal-axis1-4b-4bit-qlora", "formal-axis1-8b-4bit-qlora"], [42, 123, 2026]),
    ("C5", "Results/Training-Time Scaling",
     "4-bit step-time log-log slope 1.00+/-0.09 (R2=0.99): approximately "
     "linear, not sublinear (H5 partially supported; all Tier-B per D4)",
     "key_numbers.json:fits.4bit_qlora.step_time",
     ["formal-axis1-0.6b-4bit-qlora", "formal-axis1-1.7b-4bit-qlora",
      "formal-axis1-4b-4bit-qlora", "formal-axis1-8b-4bit-qlora"], [42, 123, 2026]),
    ("C6", "Results/Context Boundary",
     "ctx1024: 24.0 s/step, 11.16 GiB; ctx2048: 20.7 s/step, 23.88 GiB peak "
     "(4B 4-bit; 3 seeds each; Tier-B window)",
     "key_numbers.json:context_axis",
     ["formal-axis1-4b-4bit-qlora", "formal-axis2-ctx1024",
      "formal-axis2-ctx2048"], [42, 123, 2026]),
    ("C7", "Results/Context Boundary; Table 4",
     "Trainable context boundary is [2048,4096): ctx4096 and ctx8192 probes "
     "were SIGKILLed before completing any step",
     "context_boundary_probe_summary.json",
     ["probe-4b-4bit-qlora20-seed42", "probe-4b-4bit-ctx2048-qlora20-seed42",
      "probe-4b-4bit-ctx4096-qlora20-seed42",
      "probe-4b-4bit-ctx8192-qlora20-seed42"], [42]),
    ("C8", "Results/Batch and Rank; Table 5",
     "Batch axis throughput falls monotonically 89.5/66.4/34.6 tok/s at "
     "b1/b2/b4 while peak memory rises 6.19/10.04/16.98 GiB (3 seeds each)",
     "key_numbers.json:batch_axis",
     ["formal-axis4-b1", "formal-axis4-b2", "formal-axis4-b4"], [42, 123, 2026]),
    ("C9", "Results/Batch and Rank; Fig 7",
     "Batch-8 is SIGKILLed before any step in all 3 seeds (exit 137, zero "
     "stdout, system swap ~20 GiB): batch boundary in [4,8)",
     "key_numbers.json:batch_axis['8']; coverage_report.json",
     ["formal-axis4-b8"], [42, 123, 2026]),
    ("C10", "Results/Batch and Rank; Table 6",
     "LoRA rank is nearly free: ranks 4/8/32 change step time <2% and peak "
     "memory by 0.24 GiB (4B 4-bit)",
     "key_numbers.json:rank_axis",
     ["formal-axis3-r4", "formal-axis1-4b-4bit-qlora", "formal-axis3-r32"],
     [42, 123, 2026]),
    ("C11", "Results/Boundary Behavior at 14B (D8)",
     "14B 4-bit boundary case: probe entered training (0.68 s/step at 2.7 GiB "
     "swap); formal attempts: 24-min zero-step interrupt (7.1 GiB) and "
     "50/100-step timeout with ~40-min load (3.7 GiB start)",
     "results/raw logs (probe + 2 formal); deviations.md D8",
     ["probe-14b-4bit-qlora20-seed42", "formal-axis1-14b-4bit-qlora"], [42, 123]),
    ("C12", "Results/Scale Feasibility (D1)",
     "4B BF16 regime dependence: 451 s (3.03 s/step) at zero residency vs "
     "zero completed steps in 26 min at 6 GiB residency",
     "deviations.md D1 + D1 addendum; key_numbers scale_axis",
     ["formal-axis1-4b-bf16-lora"], [42]),
    ("C13", "Results/Scale Feasibility; Table 2",
     "Full fine-tuning of 0.6B completes but diverges at frozen lr 1e-4 "
     "(final val loss 4.44 vs 1.93 for 4-bit QLoRA) - retained negative result",
     "key_numbers.json:scale_axis[formal-axis1-0.6b-bf16-full]",
     ["formal-axis1-0.6b-bf16-full", "formal-axis1-0.6b-4bit-qlora"],
     [42, 123, 2026]),
    ("C14", "Failure Analysis",
     "118 finalized runs: 27 failures retained; 9 formal attempts "
     "implementation-invalid (D5) excluded from aggregation by error "
     "signature; 46/46 aggregated runs manifest-verified; 118=118 "
     "coverage reconciliation",
     "coverage_report.json; failure_taxonomy.json",
     [], []),  # corpus-level claim: resolved via coverage_report per_run
    ("C15", "Results/Training Effectiveness",
     "Validation loss comparable across precisions after 100 steps "
     "(0.6B: 1.93 vs 1.81; 1.7B: 1.63 vs 1.55)",
     "key_numbers.json:scale_axis[*].val_loss_final",
     ["formal-axis1-0.6b-bf16-lora", "formal-axis1-0.6b-4bit-qlora",
      "formal-axis1-1.7b-bf16-lora", "formal-axis1-1.7b-4bit-qlora"],
     [42, 123, 2026]),
]


def main() -> int:
    df = pd.read_csv(PROC / "experiments.csv", low_memory=False)
    out = ROOT / "research" / "claim_ledger.csv"
    rows = []
    for cid, loc, text, source, groups, seeds in CLAIMS:
        sub = df[df["experiment.comparison_group_id"].isin(groups)]
        sub = sub[sub["training.seed"].isin(seeds)]
        # 只保留成功或对应声明所需的行：boundary/失败类 claim 需要 non-success 行
        if cid in ("C9", "C11", "C12"):
            ids = sorted(sub["experiment.id"])
        else:
            ids = sorted(sub[sub["status.terminal_state"] == "success"]
                         ["experiment.id"])
        rows.append({
            "claim_id": cid,
            "paper_location": loc,
            "claim_text": text,
            "processed_source": source,
            "n_raw_runs": len(ids),
            "raw_experiment_ids": ";".join(ids),
            "freeze": "freeze-04f90a840b8ea8fb",
        })
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"[claim_ledger] {len(rows)} claims -> {out.relative_to(ROOT)}")
    for r in rows:
        print(f"  {r['claim_id']:4s} n={r['n_raw_runs']:3d}  {r['claim_text'][:60]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
