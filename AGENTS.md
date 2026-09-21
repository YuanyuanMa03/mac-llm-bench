# You are working on a reproducible ML systems research project.

> **Public note.** This file is the integrity charter that every AI coding
> assistant working in this repository must follow. It is published as part of
> the research artifact because these boundary rules are the mechanism behind
> the reproducibility and integrity claims of the study — see
> `docs/experiment_governance.md` for the full design. The companion tooling
> is published alongside it: the task-ledger harness `scripts/prompt_log.py`
> and its skill `.agents/skills/prompt-log/`. The recorded task texts
> themselves are maintainer-side working records and are not published.

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
11. Please answer in Chinese.

Note: the maintainer's local agent-skill bundle (`.agents/skills/`) is
workflow tooling; only the `prompt-log` skill is published with the artifact.
Everything else under `.agents/` stays local and git-ignored.
