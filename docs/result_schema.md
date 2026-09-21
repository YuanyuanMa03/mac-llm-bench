# Result schema

Each `results/raw/<experiment-id>/` directory is a finalized experiment record. Core files are:

- `result.json`: schema version, experiment identity, provenance, declared configuration, measured summaries, terminal state, and artifact inventory.
- `config.yaml`: declared input configuration.
- `effective_config.json`: historical configuration copy; corrected semantic overlays are in `results/processed/effective_runtime_config.*`.
- `command.txt`: exact execution command.
- `environment/`: hardware, software, and pre/post system snapshots.
- `logs/`: stdout and stderr.
- `training_metrics.json`: successful training summary when emitted.
- `step_timings.jsonl`: per-step records when emitted.
- `system_monitor.jsonl`: sampled system state when available.
- `manifest.sha256`: digest list when finalization produced a verifiable manifest.

Missing values mean unavailable measurements and are never replaced with estimates. A non-success terminal state is retained as a result. `results/processed/coverage_report.json` assigns every raw run a disposition and reconciles raw and processed totals.

The frozen historical schema and the current collector differ in some fields. Processed overlays document corrected semantics without mutating raw evidence. See `docs/experiment_protocol.md` and `research/reproducibility_public.md`.
