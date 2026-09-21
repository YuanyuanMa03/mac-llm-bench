# Public release policy

The release tree is allowlisted. A tracked file must belong to one of the categories below and must have a reproducibility purpose.

## PUBLIC_CORE

Scientific artifacts required to inspect or reproduce the reported results: source code, scripts, tests, locked dependencies, experiment configurations, frozen dataset files, model manifest, raw results, processed outputs, figures, license, citation metadata, and concise project entry points. These files are retained unless a privacy remediation requires a separately reviewed transformation.

## PUBLIC_SUPPORTING

Explanatory records that help a reader interpret the artifact: methodology, measurement definitions, result schema, architecture, preregistration, freeze identity, normalized deviation summary, claim ledger, dataset split note, and repository reproducibility audit. These files are published only after stale claims, machine-specific details, and work-process language are removed.

## PRIVATE_INTERNAL

Research-governance and work-process records: assistant instructions, prompts, review transcripts, draft notes, obsolete release notes, debugging diaries, working ledgers, private diagnostic reports, history-remediation records, and development-only validation captures. They are preserved locally under the ignored `.private/` directory and are absent from the public Git tree.

## Allowlist

The public root is limited to `README.md`, `README.zh-CN.md`, `LICENSE`, `CITATION.cff`, `pyproject.toml`, `uv.lock`, and the directories `src/`, `scripts/`, `tests/`, `configs/`, `data/formal_sft_v1/`, `models/MANIFEST.md`, `results/raw/`, `results/processed/`, `results/figures/`, `docs/`, and the approved records under `research/`.

New tracked paths require an inventory entry and an explicit reproducibility reason. Being present in an earlier commit is not sufficient.
