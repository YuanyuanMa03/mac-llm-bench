# Final source audit — 2026-09-21

## Scope and source boundary

- Audited branch: `paperwriting`
- Audited HEAD before corrections: `f1b60766b099cdb1c84e2b50f2b7727e53e8e0f5`
- Latest manuscript source in this checkout: `paper/submission/main.tex` (not
  `paper/main.tex`). The corresponding generated PDF is
  `paper/submission/main.pdf`.
- The audit treats `results/raw/**`, `research/preregistration.md`, and existing
  deviation entries as immutable historical evidence.
- The public `master` revision named in the review prompt is not the current
  paper branch. All findings below were independently checked in this checkout.

`affects numbers` means that the issue changes a reported numerical result, not
merely its interpretation or provenance. `rerun` means a rerun is required to
retain the corrected claim; an optional targeted diagnostic is described where
appropriate.

## Findings

| ID | status | exact evidence | affected files | affects numbers | rerun | minimal correction |
|---|---|---|---|---|---|---|
| S01 | confirmed | `environment.py:28,199-215` redacts only serial/platform keys. A key-only scan found `provisioning_UDID` in all 118 historical `raw_environment.txt` files; values were not printed. Git history contains the key in 100 commits. | `src/benchmark/environment.py`, historical raw environment captures | no | no | Recursively redact normalized sensitive keys and fallback text in future collection; publish a separate history-remediation plan without force-pushing or copying values. |
| S02 | confirmed | `lora_smoke.py:200-218` constructs sequential `order`; shuffle occurs only after wrap. No formal run can consume 2,048 examples (`max_steps × micro_batch_size <= 300`). | trainer; all historical formal runs | no | no | Record fixed initial order in a processed audit; shuffle epoch 0 only in the bumped future protocol. |
| S03 | confirmed | Seed-42/123/2026 token-count sequences are identical within the 512/1024/2048-cap formal cells; preregistration says seed also affects data order. | preregistration interpretation; manuscript | no | no | Preserve preregistration; state that historical seeds varied initialization, not initial sample order. |
| S04 | confirmed | `build_formal_dataset.py:63-83` samples 2,080 indices, restores source-row order, then slices train 2,048 / validation 32. Verified `max(train.global_row) < min(validation.global_row)`. | dataset builder, MANIFEST description, validation interpretation | no | no | Preserve dataset; add a split audit and describe validation loss as descriptive. |
| S05 | confirmed | `lora_smoke.py:155-164` uses `ids[:seq_len]` without padding. | context-axis interpretation | no | no | Use “maximum sequence-length cap”; publish actual lengths. |
| S06 | confirmed | Recalculation from retained formal step records gives mean input lengths 500.10 / 916.05 / 1215.10 for caps 512 / 1024 / 2048. | context analysis and claims | yes, for workload summaries only | no | Generate a traceable length table; remove exact 4×-token interpretation. |
| S07 | confirmed | 4096/8192 are single-seed synthetic probes, while 2048 has formal and probe evidence. | context-boundary analysis and paper | no | no | Say “observed maximum-context bracket” and keep probe/formal evidence separate. |
| S08 | confirmed | Execution is model load → LoRA → initial validation (`lora_smoke.py:195-198`) → peak reset → loop; all three batch-8 stdout/stderr files are empty and exit 137. | batch-axis failure claim | no | optional targeted diagnostic only | State termination before first completed optimizer step and disclose phase ambiguity. |
| S09 | confirmed | `scripts/run_analysis.py` does not call `revision_round1.main`, although the paper inputs tables produced by that module. | analysis entry point, reproduction claim | no | no | Call every generator from the single entry point. |
| S10 | already_fixed | `summary.py:184-187` currently fits seed-group means, matching `figures.py`; the older `iloc[0]` mismatch is no longer present. Separate fit implementations/files remain. | summary, figures, hypothesis inputs | no in current checkout | no | Centralize the scaling series and fit, and test equality of consumers. |
| S11 | confirmed | D9 records post-result H2/H6 rule revisions; current hypothesis output foregrounds revised rules. | hypothesis audit and paper | no | no | Emit frozen and post-hoc rules/verdicts side by side. |
| S12 | confirmed | Frozen Practical is `Trainable AND P1 AND P2`; D11 and the discussion use P2-only. | hypothesis audit and paper | no | no | Report frozen and revised operational definitions side by side. |
| S13 | confirmed | Config declares `adamw`; `lora_smoke.py:189` instantiates MLX `Adam`. The manuscript already partly discloses this mismatch. | trainer metadata, paper | no | no | Keep historical config; machine-readably overlay declared AdamW versus effective Adam. |
| S14 | confirmed | `supervisor.py:205-208` copies input config to `effective_config.json`. | supervisor provenance | no | no | Future runs distinguish declared config from resolved runtime config; historical runs use an overlay. |
| S15 | confirmed | `schema.py:89` populates `training.optimizer` from declared config. | raw schema semantics | no | no | Do not rewrite raw; document via overlay and correct future schema population. |
| S16 | confirmed | `supervisor.py:588` hard-codes both raw validity flags false. | every historical result | no | no | Treat raw flags as v0 placeholders and generate a final inclusion audit. |
| S17 | confirmed | `supervisor.py:445` hard-codes `monitoring_overhead_validated=false`, contrary to the measurement validation record. | historical metadata | no | no | Preserve raw, correct future metadata, and disclose the historical placeholder. |
| S18 | confirmed | Among 46 aggregation-included successes: 9 clean, 33 dependency-dirty, 3 non-execution-artifact-only, and 1 source/config-dirty run. No historical patch artifact is present. | provenance and reproducibility claims | no | impossible for history | Publish classified provenance and disclose the unpreserved dirty state. |
| S19 | confirmed | `supervisor.py:368-374` stores null lockfile hash/size and null patch/package snapshot. | provenance | no | no | Future supervisor captures status, diffs, and dependency-file hashes. |
| S20 | confirmed | Current `reproducibility_audit.json` has `all_passed=false`. | release audit | no | no | Replace binary success semantics with disposition-aware status. |
| S21 | confirmed | `audit_reproducibility.py` requires three successful runs per formal group, including failure/boundary cells. | reproducibility audit | no | no | Audit observed evidence against declared cell disposition. |
| S22 | confirmed | Current raw count is 118; manifest verification is 112 true / 6 false. An older report says 113 / five missing, while later D6 records six digest/finalization warnings. | audit docs, README, paper appendix | no | no | Regenerate counts consistently; retain older deviation history. |
| S23 | confirmed | `lora_smoke.py:316-318` writes all step records only after the loop. | failed-run structured evidence | no | no | Stream and flush one record per completed step in future runs. |
| S24 | confirmed | Killed runs can have stdout step lines but null `successful_steps`; the 14B timeout is the demonstrated case. | failure-inclusive analysis | no | no | Parse immutable stdout into a processed overlay only. |
| S25 | confirmed | `flatten.py:130-158` computes whole-run swap-in delta divided by completed steps. | processed schema, tables, paper | no | no | Rename it to a whole-run normalized paging-intensity proxy. |
| S26 | confirmed | Historical step records use second-resolution `time.strftime` (`lora_smoke.py:240`). | D12 temporal analysis | no | impossible for history | Add a resolution caveat; use microseconds plus monotonic clocks in future. |
| S27 | confirmed | Monitor samples use microsecond wall timestamps (`monitor.py:36`) but no monotonic clock. | D12 alignment | no | no | Add monotonic timestamps to future monitor and step records. |
| S28 | confirmed | Peak reset precedes the loop, but periodic validation is inside the measured loop (`lora_smoke.py:207,244-248`). | memory metric definition | no | no | Call it the training-loop-workload allocator high-water mark including scheduled validation. |
| S29 | confirmed | `_validation_loss` uses `value_and_grad` (`lora_smoke.py:173-183`) despite “forward-only” wording. | trainer and method limitation | no | no | Future validation calls `default_loss` directly; do not speculate about historical lazy materialization. |
| S30 | confirmed | Batch-8 initial validation uses that same `value_and_grad` path and micro-batch. | batch-8 phase interpretation | no | optional targeted diagnostic only | Same conservative wording as S08; future phase markers. |
| S31 | confirmed | Collector requests `physicalMemory`; raw system-profiler data uses `physical_memory`; documented `sysctl hw.memsize` fallback is absent. GPU cores lack a verified source. | hardware collector | no | no | Prefer `hw.memsize`, accept verified profiler aliases, leave unknown GPU cores null. |
| S32 | confirmed | Scheduler, gradient accumulation, precision and checkpoint fields are largely declared schema values; the tested values make the current numerical effect minimal. | effective-config claim | no | no | Distinguish declared from resolved runtime semantics. |
| S33 | confirmed | `context_boundary.py:77+` sorts candidates and mechanically keeps the latest same-cap run. | context selection | potentially | no | Use explicit evidence IDs/selection priorities and emit selection provenance. |
| S34 | confirmed | Empirical p99 is computed from only 20 or 100 steps per run and is close to the sample maximum. | tail-latency claim | no | no | Say empirical p99 and report/qualify p95 and maximum. |
| S35 | confirmed | Memory decomposition uses stored/on-disk weights as a component. | decomposition figure/text | no | no | Label it a proxy and leave residual unallocated. |
| S36 | confirmed | Context, batch and scale are separate one-factor probes with different bases/windows, not one factorial binding-order experiment. | abstract/discussion/conclusion | no | no | Restrict claims to first observed failures in the separate probes. |
| S37 | confirmed | Only full tuning, LoRA, and 4-bit QLoRA were compared. | conclusion | no | no | Remove universal “default answer”; limit to tested methods. |
| S38 | confirmed | “First measurements/reference numbers” exceeds the demonstrated novelty scope. | related work/contribution | no | no | Claim failure-inclusive characterization on the pinned single-machine stack. |
| S39 | confirmed | PDF Figure 8(c) contains no batch-8 red trajectories although its caption describes three. `system_state.py:382` compares string `137` against CSV values formatted `137.0`, producing an empty selection. | figure generator, source data, paper | yes, plotted trajectories only | no | Use numeric exit-code filtering, export source data, and test trajectory count/range/caption values. |
| S40 | confirmed | Rank figure auto-scales a sub-2% effect, visually amplifying it. | rank-axis figure and caption | no | no | Plot relative change with an honest common baseline and explicit magnitude annotation. |
| S41 | confirmed | `pdfinfo paper/submission/main.pdf` reports the correct title but a blank Author field. | PDF metadata | no | no | Set `pdfauthor` to match the title block and recompile. |
| S42 | confirmed | Local `paperwriting` contains the newest paper/D12 work; remote/public `master` is not that fixed revision. | release provenance | no | no | Prepare a local readiness report only; do not push, tag, release, or submit. |

## No-rerun decision

None of S01–S42 requires rerunning the 118-run matrix. A three-seed,
instrumented batch-8 diagnostic could resolve S08/S30, but it would be
post-hoc evidence and is not required if the paper retains the conservative
“before completing the first optimizer step” wording.

## Audit-time invariants

- No file under `results/raw/` was modified.
- `research/preregistration.md` was not modified.
- Existing deviation entries were not rewritten.
- No benchmark was launched.
- No sensitive identifier value was printed into this audit.
