# Experiment protocol

## Historical frozen benchmark

The reported 118-run corpus used the protocol frozen before formal execution. Each supervised run records its command, declared YAML configuration, git commit, model identity and revision when resolved, MLX and mlx-lm versions, macOS and hardware metadata, training method, quantization, batch size, maximum sequence-length cap, LoRA rank, seed, wall-clock duration, available memory and throughput metrics, terminal state, logs, and a file manifest when finalization completed correctly.

Raw directories are immutable after finalization. Successes, timeouts, signals, runtime errors, and stopped observations remain in `results/raw/`. Aggregation inclusion is decided in the processed coverage audit; raw placeholder validity flags are not retroactively rewritten. Historical declared `adamw` configuration resolved to MLX Adam and is documented in `effective_runtime_config.*`.

Formal cells use seeds 42, 123, and 2026. Timing interpretation follows the frozen D4 whole-run paging stratification. The D5 invalid batch rows remain raw evidence but are excluded from boundary and performance aggregation. D1-D12 are summarized in `research/deviations_public.md`.

## Current collector behavior

Collector improvements made after the frozen corpus include clearer declared-versus-resolved configuration, stronger privacy redaction, explicit phase markers, streaming step records, finer timestamps, forward-only validation, and richer git-state capture. These requirements apply to future protocol versions. They must not be inferred to have been present in all historical runs.
