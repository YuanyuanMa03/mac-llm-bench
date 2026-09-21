# Final release audit — 2026-09-21 (prompt18 evidence-preserving final correction)

## Scope

This audit closes the regeneration contract of the 2026-09-21 final correction
(prompt18). Audited branch: `paperwriting`. The full per-issue evidence table
is [research/final_source_audit_20260921.md](final_source_audit_20260921.md);
this document records the executed fixes, the verification commands actually
run with their verbatim outcomes, and what remains open.

Invariants held throughout: no file under `results/raw/**` was modified,
`research/preregistration.md` was not modified, existing deviation entries
were not rewritten, no benchmark was launched, and no sensitive identifier
value was copied into any report, test, commit message, or terminal output.

## Commit decomposition (local only; nothing pushed)

| Commit | Content |
|---|---|
| `34697c0` | prompt-log harness tolerates finalized legacy summary rows (pre-task fix; 15 regression tests) |
| `f1b6076` | prompt18 begin (verbatim prompt ledgered) |
| `a3d3083` | audit-only: `research/final_source_audit_20260921.md` (S01–S42 independently verified) |
| `2972dfc` | future collectors: privacy redaction (`environment.py`), resolved-vs-declared config split, phase markers, per-step streaming, µs+monotonic timestamps, dirty-state capture (`supervisor.py`), forward-only validation + epoch-0 shuffle under a bumped protocol (`lora_smoke.py`, `monitor.py`, `schema.py`); audits: `dataset_split_audit.md`, `privacy_remediation_plan_20260921.md` |
| `f63ecff` | historical semantic overlays + single analysis entry point: 20 new/updated processed artifacts (context actual lengths, data order, effective runtime, final validity, git provenance, failure progress, figure8c source, rule comparison, group-mean scaling), `run_analysis.py` now calls every generator, disposition-aware `audit_reproducibility.py`, new analysis tests |
| (this wave) | terminology-corrected figures/tables (maximum sequence-length cap, whole-run paging proxy), frozen-vs-post-hoc rule table (table17), README/audit doc alignment, this release audit |

Paper-side artifacts (`paper/submission/**`) are intentionally untracked in
this repository; they were regenerated and recompiled during this task:
`main.tex` (claim corrections), all `tables/*.tex` (regenerated 2026-09-21),
`figures/*` (synced from `results/figures`), `main.pdf` (20 pp, clean).

## S01–S42 final status

Legend: **fixed-future** = source fixed for future collection only (history
untouched); **overlay** = machine-readable processed overlay; **paper** =
wording/claim corrected in the manuscript; **plan** = remediation plan
documented, execution deferred to the owner.

| IDs | Resolution |
|---|---|
| S01 | fixed-future + plan. Collector now recursively redacts `provisioning_UDID` and normalized sensitive keys (tests included). Value-aware scan (2026-09-21): real value present only in 137 environment captures (118 `results/raw` + 19 `results/validation`); no non-environment file contains it. History remediation requires owner decision (make private, archive, sanitize, re-publish) — see the plan; nothing force-pushed. |
| S02, S03 | overlay + paper. `data_order_audit.json` proves no formal run traversed the 2,048-example set; paper states seeds varied MLX/LoRA initialization with a fixed initial sample order. Future trainer shuffles at epoch 0 under protocol bump only. |
| S04 | overlay + paper. `dataset_split_audit.md` documents the sort-then-tail-32 semantics; validation loss reported as descriptive evidence only. |
| S05, S06 | overlay + paper. `context_actual_lengths.json` + generated table give per-cap step token statistics (means 500.10 / 916.05 / 1215.10); all "context length" wording replaced by maximum sequence-length cap; no 4×-token interpretation remains. |
| S07 | paper. Bracket wording now separates the completed 2048-cap formal workload from the single-seed 4096/8192 synthetic-probe failures. |
| S08, S30 | paper. Batch-8 claims restricted to "terminated before completing the first optimizer step"; phase ambiguity disclosed; kernel jetsam record for one kill appended as evidence. Optional post-hoc instrumented rerun proposed below, not executed. |
| S09 | fixed. `run_analysis.py` now invokes every generator (revision_round1 included); one-command rebuild verified end-to-end and byte-identical on re-run. |
| S10 | fixed. Single group-mean scaling source consumed by key numbers, fits, figures, and tables; cross-consistency test added (67-test suite). |
| S11, S12 | overlay + paper. `hypothesis_rule_comparison.json` + table17 report frozen vs post-hoc rules and verdicts side by side; the paper foregrounds the frozen confirmatory definition and labels the revised one post-hoc operational. |
| S13–S15 | overlay + fixed-future. `effective_runtime_config.{json,csv}` overlays declared-AdamW vs effective-Adam per run; future supervisor separates declared from resolved config; raw untouched. |
| S16, S17 | overlay. `final_validity_audit.csv` supersedes the supervisor-v0 placeholder flags; README/paper explain that inclusion is represented by the audit, not by rewriting raw. |
| S18, S19 | overlay + fixed-future. `git_provenance_audit.csv` classifies the 46 included runs (9 clean / 33 dependency-dirty / 3 non-execution-artifact / 1 source-dirty); limitation disclosed; future supervisor captures status, diffs, and dependency hashes. |
| S20, S21 | fixed. `audit_reproducibility.py` is disposition-aware; `overall_status=PASS_WITH_DECLARED_WARNINGS` with the six declared manifest-digest warnings as the sole warning. |
| S22 | fixed. Counts unified at 118 raw / 112 verified / 6 declared warnings across README, audit docs, and the regenerated report. |
| S23, S24 | fixed-future + overlay. Future trainer streams one flushed JSONL record per completed step with phase markers; `failure_progress.json` parses immutable stdout for historical killed runs (8 parsed). |
| S25 | fixed. Metric renamed/aliased `whole_run_swapin_mb_per_completed_step`; tables and paper call it a whole-run system-wide paging-intensity proxy, not per-step paging. |
| S26, S27 | paper + fixed-future. Second-resolution caveat added to the temporal analysis; future records use µs wall time plus monotonic clocks. |
| S28 | paper. Metric defined as the MLX allocator high-water mark during the measured training-loop workload including scheduled validation. |
| S29 | fixed-future. Future validation is forward-only; historical lazy semantics left as a disclosed limitation without speculation. |
| S31 | fixed-future. Collector prefers `sysctl hw.memsize`, accepts verified profiler aliases, leaves GPU cores null; historical values documented by source. |
| S32 | overlay. Declared-vs-resolved semantics carried in `effective_runtime_config`; ga=1/constant scheduler noted as the effective historical regime. |
| S33 | fixed. Context boundary selection emits explicit evidence IDs and selection provenance. |
| S34 | paper. Reported as empirical p99 with p95/max qualification. |
| S35 | paper. Weight component labelled stored/on-disk proxy; residual left unallocated. |
| S36 | paper. Axis claims restricted to separate one-factor probes on the tested bases. |
| S37 | paper. No universal "default answer"; restricted to the tested full/LoRA/4-bit comparison. |
| S38 | paper. Novelty narrowed to failure-inclusive characterization on the pinned single-machine stack. |
| S39 | fixed. Numeric exit-code filtering; Figure 8(c) now plots all three batch-8 trajectories from raw system monitors; source data exported (JSON/CSV); caption numbers generated as macros from that source (ramp 46–105 s, +16.3–17.1 GiB, peaks 19.5–20.4 GiB). |
| S40 | fixed. Rank effects reported as relative change with honest common baseline (rank_relative_effects.csv). |
| S41 | fixed. `pdfauthor` set; PDF metadata verified against the title block. |
| S42 | open by design. Local `paperwriting` holds the newest paper; fixing an `arxiv-v1` tag/push is deferred to the owner after the privacy hold (S01) is resolved. |

## Verification commands actually run (this closing pass)

```
$ uv run python scripts/run_analysis.py
  … [analysis] 全部 processed/figures/tables 已从 raw results 重新生成
  # byte-identical on re-run: git diff stat unchanged (27 files, +100/−56),
  # results/raw and research/preregistration.md untouched (git status clean)

$ uv run python scripts/audit_reproducibility.py
  [WARNING] raw_manifests_accounted n=118; verified=112; declared_integrity_warnings=6
  [PASS] formal_groups_match_declared_disposition n_groups=19; unresolved=[]
  [PASS] raw_processed_coverage_reconciled raw=118 processed=118
  [PASS] formal_dataset_sha256 n_files=2
  [PASS] model_revisions_consistent []
  [PASS] key_numbers_traceable
  [audit] overall_status=PASS_WITH_DECLARED_WARNINGS

$ uv run python -m pytest tests/ -q
  67 passed in 7.74s

$ latexmk -pdf main.tex  (paper/submission)
  exit=0; 0 Overfull; no undefined references/citations; 20 pages;
  pdfinfo: Title and Author (Yuanyuan Ma) match the title block
```

Privacy scan (value-aware, values never printed): 118 `results/raw` + 19
`results/validation` environment captures contain the unredacted
`provisioning_UDID` value; zero occurrences in any other tracked file
(matches outside captures were the literal string `[REDACTED]`).
`<home> paths: zero occurrences in tracked files.

## Did any numerical headline change?

No. The feasibility map, 0.54–0.73× 4-bit memory ratio, step-time ratios,
8B 3/3 completion, 14B boundary status, and machine-state contrast are
unchanged. What changed is (a) the Figure 8(c) panel content (S39 — the
correct three batch-8 trajectories were absent from the old PDF), and
(b) descriptive workload summaries for the context axis (actual token
lengths now reported; means 500.10 / 916.05 / 1215.10), which previously
had no table at all.

## Remaining limitations / recommended follow-ups

1. **S01 privacy hold (blocking public release):** execute the owner-side
   remediation plan (restrict access → private archive → sanitized
   history or new public repo → manifest). Nothing was force-pushed.
2. **S42:** after the privacy decision, fix the paper revision (tag or
   branch) and only then publish the arXiv link.
3. **Optional post-hoc batch-8 diagnostic** (S08/S30): three instrumented
   reruns with phase markers would pin the failure phase. Not required if
   the conservative wording is retained; must be labelled post-hoc and kept
   outside the preregistered matrix.
4. Historical second-resolution step timestamps and unpreserved dirty
   dependency state remain immutable limitations, now disclosed in the
   paper; only future runs can improve them.

No rerun of the 118-run matrix is recommended or required.
