# Release Notes — v1.0.0-rc1 (Release Candidate 1)

**Date**: 2026-09-16 · **Dataset freeze**: `freeze-04f90a840b8ea8fb`
(2026-09-15T22:17Z) · **Status**: release candidate — not yet published.

mac-llm-bench is a preregistered, failure-inclusive benchmark that maps the
fine-tuning feasibility boundary of a 16 GiB unified-memory Apple Silicon
Mac (Apple M4). This release freezes the experimental dataset and ships
the complete chain from immutable raw records to the compiled paper.

## What's in this release

- **118 finalized raw experiments** (97 formal / 11 probe / 10 calibration &
  smoke; 27 failures retained as first-class results), each with git
  provenance, model revision pinning, per-second swap sampling, complete
  logs, and (for 113/118) SHA-256 manifests. Freeze manifest:
  `research/experiment_freeze_manifest.sha256`.
- **Preregistered formal matrix** (axes: model scale, precision, context
  length 512–8192, LoRA rank 4–32, micro-batch 1–8) executed to its declared
  stopping points; eight logged deviations (D1–D8), including the D5 trainer
  fix (variable-length validation batching) with 14 regression tests and the
  D8 decision that stops 14B formal attempts and reports 14B as a
  system-state-dependent boundary case.
- **One-command analysis rebuild** (`uv run python scripts/run_analysis.py`):
  processed tables, coverage reconciliation (118 = 118 with machine-readable
  dispositions), key numbers, 8 figures, 6 LaTeX tables, and the H1–H6
  hypothesis audit.
- **Paper draft** (`paper/main.tex`, 8 pp, compiles with 0 errors and 0
  undefined references) with 15 quantitative claims traced to raw experiment
  IDs in `research/claim_ledger.csv`.
- **Audits**: `research/reproducibility_audit.md` (PASS with declared
  warnings), evidence/literature ledgers, coverage report.

## Headline findings

1. 4-bit QLoRA reduces peak training memory to 0.54–0.73× of BF16 LoRA at
   all paired scales, with step-time ratios inside the preregistered ±25%
   equivalence margin.
2. Highest reproducibly trainable configuration: 8B 4-bit QLoRA (3/3 formal
   seeds). 14B 4-bit is a system-state-dependent boundary case (probe
   completes at 2.7 GiB swap residency; formal runs stall/timeout under
   multi-GiB residency).
3. Memory scales sublinearly with model size (log-log slope 0.57 — a
   negative result vs the linear hypothesis); step time scales
   approximately linearly (slope 1.00).
4. Context length is the binding constraint (trainable boundary
   [2048, 4096)); micro-batching is counterproductive and fails outright at
   batch 8 (boundary [4, 8)).

## Known issues / warnings (deliberately not hidden)

- 5 legacy timeout/interrupted runs finalized without SHA-256 manifests
  (deviation D6); zero impact on aggregated results (46/46 aggregated runs
  manifest-verified).
- All timing data is Tier-B (paging-confounded, deviation D4): absolute
  step times are window-specific; the paper compares only within-window
  ratios.
- Supervisor v0 does not store patch artifacts for dirty-tree runs
  (`git_patch` is null); trainer lineage is instead anchored by declared
  commit boundaries (D5).
- Raw experiment records contain local filesystem paths as provenance
  (immutable by protocol); processed outputs are sanitized to `<repo>` /
  `<home>` placeholders.
- 3 unfinalized staging partials remain on disk, uncommitted, and are not
  part of the dataset.

## Reproduce

```bash
uv sync                                   # locked environment (Python 3.13, mlx 0.32.2)
uv run python -m pytest tests/ -q         # 48 tests
uv run python scripts/run_analysis.py     # rebuild all processed data/figures/tables
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```

Model weights are not bundled (git-ignored); see `models/MANIFEST.md` for the
pinned Hugging Face revisions and `README.md` for the quickstart.
