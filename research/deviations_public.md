# Public preregistration deviation summary

The preregistration was frozen before formal execution. This record reports D1-D12 in a normalized scientific format. Public raw evidence preserves the scientific content; privacy-only transformations are explicitly mapped.

## D1

**Frozen plan:** Run the 4B BF16 LoRA cell at ctx512 for 100 steps and three seeds.

**Observed issue/event:** One high-residency attempt completed no optimizer step in roughly 27 minutes; a zero-residency rerun of the same configuration completed in 451 seconds.

**Disposition:** Report the cell as a machine-state-dependent boundary observation and include the completed low-residency run with its scope stated.

**Evidence:** `results/processed/system_state.json`; `results/processed/coverage_report.json`.

**Effect on reported results:** The matrix does not support a machine-state-independent 4B BF16 feasibility claim.

**Confirmatory/post-hoc status:** Deviation from the frozen cell execution; the contrast is descriptive.

## D2

**Frozen plan:** One retained run per formal group and seed.

**Observed issue/event:** A configuration-hash mismatch caused duplicate execution in several 0.6B and 1.7B groups.

**Disposition:** Preserve every raw run and apply the declared disposition rule when selecting aggregation inputs.

**Evidence:** `results/processed/coverage_report.json`; `results/processed/experiments.csv`.

**Effect on reported results:** Duplicate runs are excluded from aggregation; no raw observation is removed.

**Confirmatory/post-hoc status:** Processing deviation with a deterministic correction.

## D3

**Frozen plan:** Use the preregistered isolation procedure without a numeric pre-run swap threshold.

**Observed issue/event:** Large-model progress depended strongly on system memory residency.

**Disposition:** Add a pre-run system swap gate of 8.5 GiB for later formal execution while retaining all earlier observations.

**Evidence:** `results/processed/system_state.json`; per-run environment snapshots.

**Effect on reported results:** Later formal runs were restricted to the declared gate; the gate does not guarantee a favorable outcome.

**Confirmatory/post-hoc status:** Protocol strengthening after an observed stall.

## D4

**Frozen plan:** Compare timing measurements across retained runs.

**Observed issue/event:** Whole-run system paging intensity varied substantially across run windows.

**Disposition:** Freeze Tier-A as less than 50 MB whole-run swap-in per completed step and classify the remaining runs as Tier-B; restrict primary timing comparisons by window and tier.

**Evidence:** `results/processed/tier_classification.json`.

**Effect on reported results:** Timing claims use corrected mixed Tier-A/Tier-B stratification; memory and feasibility observations remain retained.

**Confirmatory/post-hoc status:** Stratification rule frozen before the affected axis-1 rerun.

## D5

**Frozen plan:** Execute micro-batches 1, 2, 4, and 8 with comparable validation semantics.

**Observed issue/event:** Variable-length validation batching caused nine micro-batch 2/4/8 attempts to fail before valid benchmark execution.

**Disposition:** Preserve the nine rows as implementation-invalid evidence, fix padding semantics, and rerun the complete batch axis. Only the valid 2026-09-15 set supports batch performance and boundary claims.

**Evidence:** `results/processed/coverage_report.json`; `results/processed/figure8c_batch8_source.json`.

**Effect on reported results:** Invalid rows appear in failure taxonomy but do not support the batch-8 ramp or boundary claim.

**Confirmatory/post-hoc status:** Implementation correction followed by a controlled rerun.

## D6

**Frozen plan:** Finalize every run with a verifiable manifest.

**Observed issue/event:** Six failure or interruption records contain manifest digest warnings after re-verification.

**Disposition:** Preserve the records and downgrade their integrity grade; do not reconstruct manifests after finalization.

**Evidence:** `results/processed/coverage_report.json`; `research/reproducibility_audit.json`.

**Effect on reported results:** No aggregation impact; all 46 aggregation-included runs re-verify.

**Confirmatory/post-hoc status:** Post-finalization integrity audit.

## D7

**Frozen plan:** Treat initial large-model failures as formal outcomes under the original execution schedule.

**Observed issue/event:** 8B and ctx2048 first attempts failed under less favorable residency, while later attempts completed; a 14B attempt progressed but timed out.

**Disposition:** Retain both outcomes and permit information-gain reruns under the stated gate.

**Evidence:** `results/processed/system_state.json`; `results/processed/coverage_report.json`.

**Effect on reported results:** 8B completion is scoped to one favorable observed window; 14B remains a boundary case.

**Confirmatory/post-hoc status:** Adaptive rerun decision after observed state dependence.

## D8

**Frozen plan:** Complete the 14B formal seed set when feasible.

**Observed issue/event:** The later 14B formal attempt reached 70 of 100 steps and timed out after two hours; another formal observation made no step progress for roughly 24 minutes.

**Disposition:** Stop further 14B formal execution and report 14B as a system-state-dependent boundary case.

**Evidence:** `results/processed/system_state.json`; `results/processed/failure_progress.json`.

**Effect on reported results:** No completed 14B formal seed set is claimed.

**Confirmatory/post-hoc status:** Post-preregistration stopping decision.

## D9

**Frozen plan:** Apply preregistered H2/H6 audit rules and the D4 paging classifier.

**Observed issue/event:** H2/H6 operational rules were revised after results, and a flattening defect initially labeled every run Tier-B.

**Disposition:** Publish frozen and revised rules side by side; correct the classifier from raw snapshots.

**Evidence:** `results/processed/hypothesis_rule_comparison.json`; `results/processed/tier_classification.json`.

**Effect on reported results:** The paging picture is mixed. Under the frozen H2 rule the extension claim is not supported; revised readings are labeled post-hoc.

**Confirmatory/post-hoc status:** Post-result rule revision and analysis defect correction.

## D10

**Frozen plan:** Publish a repository without persistent personal or device identifiers.

**Observed issue/event:** Source audit found a persistent device identifier in historical environment captures.

**Disposition:** Keep the repository under a publication hold until a separate evidence-preserving history remediation is completed and verified.

**Evidence:** Public release scan summary in `research/public_release_audit.md`.

**Effect on reported results:** Scientific numbers are unchanged; public history is not yet releasable.

**Confirmatory/post-hoc status:** Publication hygiene finding.

## D11

**Frozen plan:** Gate the Practical verdict on both swap-growth P1 and step-time P2.

**Observed issue/event:** Sensitivity analysis showed that P1 tracks system-wide background load rather than the training working set.

**Disposition:** Preserve the frozen P1-and-P2 verdict and report the P2-only operational reading separately.

**Evidence:** `results/processed/threshold_sensitivity.json`; `results/processed/hypothesis_rule_comparison.json`.

**Effect on reported results:** Counterfactual differences are explicit; the frozen definition remains visible.

**Confirmatory/post-hoc status:** Post-result operational rule change.

## D12

**Frozen plan:** Produce preregistered aggregate feasibility, memory, timing, and failure analyses.

**Observed issue/event:** Additional analyses were added over frozen evidence: step-time dynamics, system-state trajectories, and memory-accounting decomposition.

**Disposition:** Label all three modules post-hoc exploratory and generate them from immutable raw records. Exclude D5-invalid batch rows from ramp evidence.

**Evidence:** `results/processed/step_dynamics.json`; `results/processed/system_state.json`; `results/processed/memory_decomposition.json`.

**Effect on reported results:** New descriptive findings are added without changing frozen gates or raw evidence.

**Confirmatory/post-hoc status:** Post-hoc exploratory.
