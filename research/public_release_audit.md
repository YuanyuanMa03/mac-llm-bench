# Public release artifact audit

Date: 2026-09-21

## Public artifact scope

The curated tree is allowlisted to project entry points, locked dependencies, source, execution and analysis scripts, tests, configurations, the frozen formal dataset, model manifest, raw evidence, processed evidence, figures, methodology documents, preregistration, freeze identity, normalized D1-D12 deviations, the generated claim ledger, and public audit records.

The public raw-to-claim chain reconciles 118 finalized runs, 27 retained failures, 46 aggregation-included runs, 6 declared manifest digest warnings, 12 deviations, and 21 generated claim-ledger rows. The valid batch-8 claim uses only the three 2026-09-15 runs.

## Verification

Raw immutability comparison passed for 1,481 files under `results/raw/`. The allowlist scan found no path outside the approved public categories. Headline consistency checks passed across both README files, citation metadata, coverage, failure taxonomy, deviation summary, claim ledger, and reproducibility audit.

`uv run python scripts/audit_reproducibility.py`:

```text
[WARNING] raw_manifests_accounted n=118; verified=112; declared_integrity_warnings=6; counts={True: np.int64(112), False: np.int64(6)}
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

`uv run python -m pytest tests/ -q`:

```text
....................................................                     [100%]
52 passed in 5.61s
```

## Publication hold

A separate evidence-preserving privacy remediation remains required. Current verification found the persistent identifier key in 118 raw environment captures and machine-specific storage-device paths in 236 raw text or JSON files; the identifier key is reachable from 22 commits across current refs. No identifier value is reproduced here. Scientific raw bytes were unchanged during curation, and no history rewrite was performed.

## Status

`PUBLIC_RELEASE_READY_EXCEPT_PRIVACY_HISTORY`
