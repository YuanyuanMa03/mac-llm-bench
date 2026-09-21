# mac-llm-bench

Reproducible, failure-inclusive measurements of memory-efficient LLM fine-tuning on one consumer Apple Silicon system.

## What

This artifact evaluates Qwen3 models from 0.6B to 14B with BF16 LoRA and MLX 4-bit adapter fine-tuning. The frozen corpus contains **118 finalized runs**, including **27 failures**; **46 runs** are included in the preregistered aggregations. Raw records, processed outputs, figures, configs, model revisions, and provenance are retained together.

## Hardware

All reported measurements come from a single Apple M4 Mac with 16 GiB unified memory. Hardware and software versions are recorded per run. Results should be read as observations from this machine and its measured state.

## Methods

The benchmark varies model scale, maximum sequence-length cap, LoRA rank, and micro-batch size. Runs are supervised and record the exact command, git commit, model revision, MLX and mlx-lm versions, configuration, environment, wall time, allocator peak, throughput, exit status, and available step and system-state traces. The preregistration and D1-D12 deviation summary are in `research/`.

## Data

- `results/raw/`: immutable run records, successes and failures
- `results/processed/`: programmatically derived tables and analysis data
- `results/figures/`: figures generated from processed and raw evidence
- `data/formal_sft_v1/`: frozen training and validation splits with checksums
- `models/MANIFEST.md`: model identities and pinned revisions

## Key observations

- 8B 4-bit was the largest tested configuration with a completed three-seed preregistered set within one favorable observed machine-state window.
- Observed feasibility varied with both configuration and machine memory state. The same 4B BF16 setup completed at zero initial swap residency and made no completed-step progress during a roughly 27-minute high-residency observation.
- Across the measured 4-bit scale range, allocator peak memory scaled sublinearly with model size (log-log slope 0.57 ± 0.05). This is a descriptive scaling result.
- Paired 4-bit runs used 0.54-0.73× the BF16 LoRA allocator peak. Step-time comparisons are stratified by the corrected mixed Tier-A/Tier-B paging classification.
- The 2048-cap workload completed. The first observed failure was a single-seed synthetic 4096-cap probe, so this is an observed bracket rather than a physical or statistical threshold.
- The valid 2026-09-15 batch-8 set terminated before the first completed optimizer step in all three seeds. Earlier D5 implementation-invalid rows are excluded from this boundary evidence.

## Reproduce

Install the locked environment and regenerate all derived artifacts:

```bash
uv sync --locked
uv run python scripts/run_analysis.py
uv run python scripts/build_claim_ledger.py
uv run python scripts/audit_reproducibility.py
uv run python -m pytest tests/ -q
```

The analysis pipeline reads `results/raw/` and rewrites `results/processed/` and `results/figures/`. Audit scope and known integrity warnings are documented in `research/reproducibility_public.md`.

## Limitations

The study uses one machine. Timing and feasibility depend on machine state, while system-wide swap counters cannot attribute paging to the training process alone. Some analyses of step-time dynamics, system-state trajectories, and memory decomposition are post-hoc. The context upper edge uses single-seed synthetic probes. Historical collection limitations and six declared manifest digest warnings are preserved in the public audit.

## Paper

Paper: arXiv link forthcoming.

## License and citation

See `LICENSE` and `CITATION.cff`.
