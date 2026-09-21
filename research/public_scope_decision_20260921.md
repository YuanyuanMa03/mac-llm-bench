# Public repository scope decision — 2026-09-21 (prompt21)

## Decision

The public repository (https://github.com/YuanyuanMa03/mac-llm-bench) was
rescoped to publish **method and evidence artifacts only**, in line with
common practice in paper companion repositories (surveyed 2026-09-21:
tatsu-lab/stanford_alpaca, artidoro/qlora, microsoft/LoRA,
Lightning-AI/lit-gpt, mlcommons/training, mlcommons/inference — none
publish internal workflow records; they publish code, data
sheets/model cards, results, and integrity/consolidation docs).

This supersedes the 2026-09-17 boundary note (recorded in
`paper/arxiv_submission_notes.md`) that treated review records and the
prompt ledger as part of the public "experiment process". The owner
approved the change ("我听你的" following the survey-based proposal).

## Removed from the public lineage (history-level purge, filter-repo)

| Path | Reason |
|---|---|
| `PROMPT.md`, `scripts/prompt_log.py`, `tests/test_prompt_log.py` | internal task ledger + harness (verbatim prompt text, strategy discussion, private archive paths) |
| `reviews/**` (4 simulated peer-review records) | internal review process; superseded scope decision |
| `paper/arxiv_submission_notes.md` | submission operations checklist |
| `research/privacy_remediation_plan_20260921.md`, `research/privacy_remediation_execution_20260921.md` | privacy-incident runbooks (local paths, operational detail) |
| `research/final_source_audit_20260921.md`, `research/final_release_audit_20260921.md` | prompt18 internal audits (incident details, agent workflow) |
| `research/release_audit.md` | stale 2026-09-16 audit, superseded counts |
| `research/current_state.md` | internal state inventory |
| `research/history_rewrite_map.csv` | old→new sha map, meaningless in the public lineage |

## Retained in the public repository

Preregistration, deviations ledger, experiment freeze, claim/evidence/
literature ledgers, dataset split audit, reproducibility audit, docs/,
results/** (sanitized raw + processed), code, tests, configs,
`release_sanitization_manifest.jsonl`, sanitizer + tests, AGENTS.md
(research-integrity rules), CITATION.cff, RELEASE_NOTES.md.

All removed artifacts remain in this research repository and in the
private archives (`~/mac-llm-bench-private/archive/`, incl.
`mac-llm-bench-sanitized-pre-scope-purge.bundle`, SHA-256 logged).

## Coordinated edits (public lineage)

- `README.md` / `README.zh-CN.md`: prompt-log mirror sections removed;
  privacy note now points to the sanitization manifest and states that
  internal process artifacts live only in the maintainer archive.
- `docs/repository_structure.md`: `paper/` section replaced by a note that
  the paper is distributed via arXiv (LaTeX not in this repo); prompt-log
  sections marked as maintainer-internal; tree diagram updated.
- `research/evidence/README.md`: stale `release_audit.md` reference removed.
- `research/deviations.md` was NOT edited (frozen history); the README
  privacy note covers its references to now-private artifacts.

## Verification (public clone of the rewritten history)

- All 12 removed paths absent in a fresh clone; no other content changes.
- Full-history value scan: 2029 blobs, real identifier value hits = 0.
- README checks: mirror section gone, no PROMPT.md references, privacy
  note points to the manifest.
- Public test suite: 57 passed (research repo: 72 = 57 + 15 prompt_log
  tests that left with the harness — counts reconcile).
- `audit_reproducibility.py` inside the public clone:
  `overall_status=PASS_WITH_DECLARED_WARNINGS`, and the regenerated
  `research/reproducibility_audit.json` is byte-identical to the
  committed one (determinism holds on the public lineage).

## New workflow implications

Future ports to the sanitized public lineage must skip `PROMPT.md` and the
README mirror sections (the ledger now exists only in the research repo);
everything else ports as before. The sanitized checkout is
`~/mac-llm-bench-private/work/mac-llm-bench-sanitized-checkout`.

Remote state after this change: `master` = `daccebc` (forced update),
tag `v1.0.0-rc1` = `7e6767f` (forced update).
