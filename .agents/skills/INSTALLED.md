# Installed Skills — Provenance

Integration model: **AGENTS-driven** (this project's convention). Skill
files live here as referenced resources; discovery and trigger rules are
registered in the repository root `AGENTS.md` ("Bundled skills" section).

| Skill | Version source | Installed | Purpose |
| --- | --- | --- | --- |
| `arxiv-paper-writer` | https://github.com/appautomaton/latex-arxiv-SKILL.git @ `b5b058350796bd6c9df7725a5d2e1607a9d45b2a` | 2026-09-16 | arXiv-style ML/AI review-paper harness (IEEEtran scaffold, plan gate, issues-CSV pipeline, arXiv discovery with SQLite cache, citation verification, compile gate) |
| `latex-rhythm-refiner` | same upstream commit | 2026-09-16 | LaTeX prose rhythm post-processing; declared dependency of the writer skill's refinement stage |
| `academic-paper` (symlink) | Claude plugin `academic-research-skills` v3.22.0 @ `~/.claude/plugins/cache/academic-research-skills/academic-research-skills/3.22.0/academic-paper` | 2026-09-16 | 12-agent academic paper writing pipeline (11 modes incl. revision/rebuttal/citation-check) |
| `academic-pipeline` (symlink) | same plugin v3.22.0 `/academic-pipeline` | 2026-09-16 | end-to-end academic research pipeline |
| `academic-paper-reviewer` (symlink) | same plugin v3.22.0 `/academic-paper-reviewer` | 2026-09-16 | paper review agent |
| `deep-research` (symlink) | same plugin v3.22.0 `/deep-research` | 2026-09-16 | 13-agent deep research / literature review / fact-check pipeline |

Notes:

- Only these skills are installed. The upstream bundle's
  `collaborating-with-claude` / `collaborating-with-gemini` bridge skills
  were not installed (external CLI agents, unused here).
- Scripts are Python-stdlib-only (import-verified): they do not touch this
  repository's `uv`-locked environment or the frozen dataset.
- Upstream layout is `.codex/skills/`; installed here under `.agents/skills/`
  with file contents unmodified. An earlier trial install under
  `.zcode/skills/` was removed per project convention (AGENTS.md only).
- Smoke test at install time: all 6 scripts parse;
  `bootstrap_ieee_review_paper.py --help` runs on system Python 3.9;
  SKILL.md frontmatter validated.
- The four `academic-*` / `deep-research` skills are **absolute symlinks**
  into the Claude plugin cache (user request, 2026-09-16): contents live
  outside this repo and are version-pinned to plugin v3.22.0 — a plugin
  update creates a new versioned cache dir and these links must be
  re-pointed. Cross-volume links (`<volume> → `/Users`) so
  relative links are not possible. Their scripts may have third-party
  dependencies (not stdlib-only); they never touch `results/raw/`.
