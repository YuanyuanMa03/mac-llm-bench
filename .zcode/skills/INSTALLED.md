# Installed Skills — Provenance

| Skill | Version source | Installed | Purpose |
| --- | --- | --- | --- |
| `arxiv-paper-writer` | https://github.com/appautomaton/latex-arxiv-SKILL.git @ `b5b058350796bd6c9df7725a5d2e1607a9d45b2a` | 2026-09-16 | arXiv-style ML/AI review-paper harness (IEEEtran scaffold, plan/issues pipeline, arXiv discovery with SQLite cache, citation verification, compile gate) |
| `latex-rhythm-refiner` | same upstream commit | 2026-09-16 | Prose post-processing (varied sentence/paragraph rhythm); declared dependency of `arxiv-paper-writer`'s refinement stage |

Notes:

- Only these two skills from the upstream bundle were installed. The bundle's
  `collaborating-with-claude` / `collaborating-with-gemini` bridge skills were
  not installed (they target external CLI agents not used in this project).
- Scripts use the Python standard library only (verified by import scan);
  they do not touch this repository's `uv`-locked environment.
- Upstream layout is `.codex/skills/`; installed here under `.zcode/skills/`
  (this workspace's agent runtime convention) with file contents unmodified.
- Smoke test at install time: all 6 scripts parse; `bootstrap_ieee_review_paper.py --help` runs on system Python 3.9; SKILL.md frontmatter validated.
