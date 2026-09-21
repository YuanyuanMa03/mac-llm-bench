# Public release artifact audit

Date: 2026-09-21

## Public artifact scope

The curated tree is allowlisted to project entry points, locked dependencies, source, execution and analysis scripts, tests, configurations, the frozen formal dataset, model manifest, public sanitized raw evidence, processed evidence, figures, methodology documents, preregistration, freeze identity, normalized D1-D12 deviations, the generated claim ledger, and public audit records.

The public raw-to-claim chain reconciles 118 finalized runs, 27 retained failures, 46 aggregation-included runs, 6 original D6 manifest warnings, 12 deviations, and 21 generated claim-ledger rows. The valid batch-8 claim uses only the three 2026-09-15 runs.

## Privacy-preserving evidence

Historical environment captures were deterministically sanitized for public release. The private originals are retained separately. The 367-file original-to-public hash mapping is recorded in `release_sanitization_manifest.jsonl`; 365 tracked raw files changed only through approved identifier or path substitutions. Comparison against the private original checkout found 1,460 tracked raw files before and after, 118 unchanged experiment identities, and zero scientific semantic differences.

All current refs, including direct tree refs, were scanned after the local rewrite. Real persistent identifier values, personal paths, and custom volume paths each have zero findings in the current tree and all reachable objects. Historical experiment provenance SHA fields remain unchanged because they describe the repository state used when the experiments ran.

## Reproducibility verification

```text
[WARNING] original_raw_manifests_accounted n=118; verified=112; original_declared_integrity_warnings=6; public_privacy_sanitized_runs=118; counts={True: np.int64(112), False: np.int64(6)}
[PASS] public_privacy_sanitization_manifest n_mappings=367; current_raw_checked=365; mismatches=[]
[PASS] formal_groups_match_declared_disposition n_groups=19; unresolved=[]
[PASS] raw_processed_coverage_reconciled raw=118 processed=118
[PASS] formal_dataset_sha256 n_files=2
[PASS] model_revisions_consistent []
[PASS] key_numbers_traceable
[PASS] public_claim_ledger_schema n_claims=21
[PASS] public_claim_sources_exist processed_missing=[]; raw_missing=[]; duplicate_ids=[]
[audit] → research/reproducibility_audit.json
[audit] overall_status=PASS_WITH_DECLARED_WARNINGS
```

```text
....................................................                     [100%]
52 passed in 5.80s
```

## Status

`PRIVACY_HISTORY_REMEDIATED_LOCAL_ONLY`

No remote update was performed.
