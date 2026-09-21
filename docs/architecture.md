# Repository architecture

`src/benchmark/` implements run identifiers, schemas, environment capture, monitoring, artifact finalization, and subprocess supervision. `src/train/` contains the MLX training workload. `src/analysis/` parses immutable run directories and produces aggregate statistics, audits, and figures.

`scripts/run_experiment.py` and `scripts/run_formal_batch.py` execute configured workloads. `scripts/run_analysis.py` is the single entry point for rebuilding processed outputs and figures. `scripts/build_claim_ledger.py` maps public claims to processed files and raw experiment IDs. `scripts/audit_reproducibility.py` checks the public raw-to-claim chain.

`configs/` contains declared experiment inputs. `data/formal_sft_v1/` contains the frozen dataset and checksums. `models/MANIFEST.md` pins model identities and revisions. `results/raw/` is append-only evidence; `results/processed/` and `results/figures/` are generated artifacts.

`docs/` defines methodology and data semantics. `research/` contains preregistration, freeze identity, normalized deviations, the claim ledger, and public reproducibility records.
