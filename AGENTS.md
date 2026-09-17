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

Note: the maintainer's local agent-skill bundle (`.agents/skills/`) is
git-ignored; it is workflow tooling, not part of the research artifact.

