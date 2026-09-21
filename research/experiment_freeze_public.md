# Public experiment freeze record

## Identity

- Freeze ID: `freeze-04f90a840b8ea8fb`
- Freeze manifest: `research/experiment_freeze_manifest.sha256`
- Freeze manifest SHA-256: `04f90a840b8ea8fb3e60c3ccb18df88e6596e23e431d5be354a8b35a553532e5`
- Preregistration commit: `8db9c13`

The manifest preserves the identity of the finalized run set. It must be interpreted together with the current processed coverage report because six historical finalization records now produce declared digest warnings. All 46 aggregation-included runs re-verify.

## Reconciled corpus

The canonical coverage report accounts for 118 raw runs: 91 successes and 27 failures. Forty-six runs are aggregation-included. Nine D5 implementation-invalid formal attempts remain in raw evidence and are excluded from performance and boundary aggregation. The public deviation record explains later corrections without changing the freeze identity or raw numerical measurements.

## Current references

- `results/processed/coverage_report.json`
- `research/deviations_public.md`
- `research/reproducibility_public.md`
- `research/claim_ledger.csv`
