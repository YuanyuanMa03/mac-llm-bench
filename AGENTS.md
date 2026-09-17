# You are working on a reproducible ML systems research project.

## Core rules:

1. Never fabricate benchmark results.
2. Never replace missing measurements with estimates.
3. All reported numbers must originate from raw experiment logs.
4. Never modify raw result files after an experiment finishes.
5. Every experiment must record:
   - git commit
   - model
   - model revision
   - MLX version
   - mlx-lm version
   - macOS version
   - hardware
   - training method
   - quantization
   - batch size
   - sequence length
   - LoRA rank
   - seed
   - wall-clock time
   - peak memory
   - throughput
   - exit status
6. Failed/OOM experiments are valid results and must be retained.
7. Figures must be generated programmatically from raw results.
8. Never manually type benchmark numbers into paper tables.
9. Run tests before claiming an implementation works.
10. Preserve complete commands required to reproduce every experiment.
11. please answer me use Chinese.

## Bundled skills (`.agents/skills/`, AGENTS-driven; provenance in `.agents/skills/INSTALLED.md`):

When a task matches a bundled skill, read its `SKILL.md` first and follow it; prefer its scripts over ad-hoc commands.

- `arxiv-paper-writer/` — arXiv-style ML/AI review-paper harness (IEEEtran scaffold, plan gate, issues-CSV pipeline, arXiv discovery, citation verification, compile gate). Trigger: writing, planning, or continuing an arXiv review/survey paper, or validating/repairing citations in a LaTeX project.
- `latex-rhythm-refiner/` — LaTeX prose rhythm post-processing. Trigger: after drafting is complete, when sections read monotonous; also invoked by the writer skill's refinement stage.
- `academic-paper/` (symlink → Claude plugin `academic-research-skills` v3.22.0) — multi-agent academic paper writing pipeline (modes incl. full draft, revision roadmap, reviewer-comment parsing, rebuttal audit, citation check). Trigger: paper writing/revision/rebuttal requests beyond what the two project-local skills cover.
- `academic-pipeline/` (symlink, same plugin) — end-to-end research pipeline. Trigger: full research workflow requests (topic → literature → draft).
- `academic-paper-reviewer/` (symlink, same plugin) — paper review agent. Trigger: simulated peer review of a draft.
- `deep-research/` (symlink, same plugin) — deep research / literature review / fact-check pipeline. Trigger: systematic literature scans, meta-analysis, fact-checking.

Hard rules inherited from the writer skill's upstream workflow (apply whenever that skill is active):

- No prose before plan approval and a validated issues CSV exists (headings/bullets/seed citations only).
- Every citation must be verified against a live online source before entering `ref.bib`.
- The issues CSV is the execution contract; mark `DONE` only when its acceptance criteria are met; re-validate after edits.
- Delivery requires a clean `pdflatex`+`bibtex` build with zero undefined citations.

These skills are for new LaTeX writing projects; they never override the core rules above (raw results stay immutable; benchmark numbers stay script-generated).

The four `academic-*` / `deep-research` skills are symlinks into the user's Claude plugin cache (see INSTALLED.md notes); their workflows likewise never override the core rules above.
