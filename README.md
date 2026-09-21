# mac-llm-bench

English | [中文](README.zh-CN.md)

Reproducible benchmarks for fine-tuning large language models (full / LoRA / QLoRA) on a consumer 16 GB unified-memory Apple Silicon Mac, built on [MLX](https://ml-explore.github.io/mlx/) and MLX-LM.

> **Privacy hold (2026-09-21):** historical `raw_environment.txt` objects contain
> an unredacted persistent device identifier. Restrict public access until the
> reviewed history-remediation plan in
> [research/privacy_remediation_plan_20260921.md](research/privacy_remediation_plan_20260921.md)
> is completed. Do not copy identifier values into issues or commits.

**Experiment frozen 2026-09-15 (`freeze-04f90a840b8ea8fb`)**: 118 finalized raw experiments, preregistered formal matrix completed to its declared stopping points (deviations D1–D8 logged in [research/deviations.md](research/deviations.md)); every number in the paper traces to raw records via [research/claim_ledger.csv](research/claim_ledger.csv).

## Research Questions

> Under a fixed consumer-grade Apple Silicon unified-memory budget, what is the real feasibility boundary for LLM training and parameter-efficient fine-tuning?

The boundary being mapped (see [docs/repository_structure.md](docs/repository_structure.md)):

```text
Loadable → Trainable → Practical → Efficient
```

`success`, `oom`, and (when reliably measurable) `severe swap / impractical throughput` are all first-class experimental outcomes. OOM runs are valid observations and are never deleted.

## Headline results (from the frozen dataset)

- **Highest reproducibly trainable configuration**: 8B 4-bit QLoRA (3/3 formal seeds); 14B 4-bit is reported as a *system-state-dependent boundary case* (D8), not a completed formal cell.
- 4-bit QLoRA cuts peak memory to 0.54–0.73× of BF16 at all paired scales, with step-time ratios inside the preregistered ±25% equivalence margin.
- Memory scales **sublinearly** with model size (log-log slope 0.57) — fixed-overhead dilution; step time scales approximately linearly (slope 1.00).
- In separate one-factor probes, the 2048 maximum-sequence-length-cap workload completed before the first 4096-cap single-seed synthetic-probe failure; micro-batch 4 completed before batch 8 terminated without a completed optimizer step.
- Trainability is a joint property of model and system swap-residency state (D1/D3/D7/D8 case studies).

## Status

| Area | State |
| --- | --- |
| Experiment protocol & result schema | ✅ done — [docs/experiment_protocol.md](docs/experiment_protocol.md), [docs/result_schema.md](docs/result_schema.md) |
| Preregistration | ✅ frozen — [research/preregistration.md](research/preregistration.md) |
| Formal benchmark | ✅ **frozen** — 118 finalized runs; coverage reconciliation 118=118 ([results/processed/coverage_report.json](results/processed/coverage_report.json)); [research/experiment_freeze.md](research/experiment_freeze.md) |
| Deviation ledger | ✅ D1–D8 logged — [research/deviations.md](research/deviations.md) |
| Analysis pipeline | ✅ one-command rebuild — `uv run python scripts/run_analysis.py` (all processed overlays/tables/figures/key numbers/coverage/hypothesis audit) |
| Hypothesis audit (H1–H6) | ✅ [results/processed/hypothesis_audit.json](results/processed/hypothesis_audit.json) |
| Paper | ✅ 15 pp final draft; **LaTeX source intentionally not tracked here** — this repo hosts the experiment process only; the paper is deposited on arXiv (link to follow after upload) |
| Reproducibility audit | ✅ [research/reproducibility_audit.md](research/reproducibility_audit.md) |

## Quickstart (minimal reproduction)

```bash
# 1. Locked Python environment (uv required; Python 3.13, mlx 0.32.2, mlx-lm 0.31.3)
uv sync

# 2. Rebuild every derived artifact from the frozen raw records
#    (processed tables, coverage report, key numbers, figures, LaTeX tables,
#     hypothesis audit). Requires no model downloads and no GPU.
uv run python scripts/run_analysis.py

# 3. Verify the software layer
uv run python -m pytest tests/ -q

# 4. Recompute the audits
uv run python scripts/audit_reproducibility.py
uv run python scripts/build_claim_ledger.py

# 5. (paper) The LaTeX source is deliberately outside this repo. Generated
#    tables/figures are written to the git-ignored paper/submission/ for the
#    maintainer's local pdflatex+bibtex build; the paper itself is published
#    on arXiv.
```

Re-running experiments (optional) additionally requires the pinned model
weights under `models/` (see [Models](#models) and `models/MANIFEST.md`;
weights are git-ignored) and an Apple Silicon Mac; each run is launched via
`uv run python scripts/run_experiment.py --config <yaml> -- uv run python
scripts/train_lora.py <yaml>`.

## Hardware

- Target platform: Apple Silicon Mac (arm64), 16 GB unified memory, macOS.
- Exact hardware metadata (chip, core counts, memory) is recorded **per experiment** by the protocol; nothing is inferred from the machine name.

## Models

Qwen3 family, pinned to Hugging Face revisions verified via the Hub API on 2026-08-31:

| Local path | HF repository | Revision | Size on disk |
| --- | --- | --- | --- |
| `models/Qwen3-0.6B` | `Qwen/Qwen3-0.6B` | `c1899de289a0` | ≈1.52 GB |
| `models/Qwen3-1.7B` | `Qwen/Qwen3-1.7B` | `70d244cc86cc` | ≈4.08 GB |
| `models/Qwen3-0.6B-4bit` | `mlx-community/Qwen3-0.6B-4bit` | `73e3e38d9813` | ≈0.35 GB |
| `models/Qwen3-1.7B-4bit` | `mlx-community/Qwen3-1.7B-4bit` | `3b1b1768f8f8` | ≈0.98 GB |
| `models/Qwen3-4B` | `Qwen/Qwen3-4B` | `1cfa9a720891` | ≈8.05 GB |
| `models/Qwen3-4B-4bit` | `mlx-community/Qwen3-4B-4bit` | `4dcb3d101c2a` | ≈2.26 GB |
| `models/Qwen3-8B-4bit` | `mlx-community/Qwen3-8B-4bit` | `545dc4251c05` | ≈4.61 GB |
| `models/Qwen3-14B-4bit` | `mlx-community/Qwen3-14B-4bit` | `a4d9b2df59d2` | ≈8.31 GB |

`models/` is git-ignored. Model revisions are never inferred from names — they come from actual Hub queries and are recorded in `models/MANIFEST.md`.

## Installation

Requires [uv](https://docs.astral.sh/uv/) and an arm64 macOS host.

```bash
uv sync          # create .venv and install exactly what uv.lock pins
uv run python -c "import mlx.core as mx; print(mx.metal.is_available())"  # sanity check
```

Verified environment of the current development machine (2026-08-31):

| Component | Version |
| --- | --- |
| Python | CPython 3.13.11 (uv-managed) |
| mlx | 0.32.2 (Metal available) |
| mlx-lm | 0.31.3 |
| huggingface-hub | 1.29.0 |
| pyyaml | 6.0.3 |
| macOS | 26.5 (arm64) |

## Usage

Every training job goes through the Experiment Supervisor (`src/benchmark/`):

```bash
uv run python scripts/run_experiment.py \
  --config configs/experiments/exp0_qwen3_0.6b_lora.yaml \
  [--timeout 3600] -- <exact command argv...>
```

The supervisor validates the config, generates the experiment ID, captures environment provenance (git, macOS, Python, MLX, hardware, pre-run memory/swap), supervises the subprocess with full stdout/stderr retention, classifies the terminal state (`success` / `timeout` / `runtime_error` / …; OOM only when reliably identifiable), and atomically finalizes an immutable raw result with a SHA-256 manifest. Failures produce complete results too — nothing is discarded. Configs live in `configs/experiments/`; experiment logic lives in code, experiment variables live in configs.

## Results

None yet. When they exist:

```text
results/validation/   environment & model smoke tests (not formal benchmarks)
results/raw/          immutable raw records, one directory per experiment
results/processed/    regenerated by the analysis pipeline
results/figures/      generated programmatically from raw results
```

Paper figures and tables will be generated from `results/raw/` by `src/analysis/` — never typed by hand.

## Reproducibility policy

Core rules (full list in [AGENTS.md](AGENTS.md)):

1. Never fabricate benchmark results; never replace missing measurements with estimates.
2. Every reported number originates from raw experiment logs.
3. Raw results are immutable after an experiment finishes; corrections require a new experiment.
4. Every experiment records: git commit, model + revision, MLX/mlx-lm versions, macOS version, hardware, training method, quantization, batch size, sequence length, LoRA rank, seed, wall-clock time, peak memory, throughput, exit status.
5. Failed/OOM experiments are retained as valid results.
6. Missing values are `null` — never `0`, never estimated.

## Prompt log

Auto-generated mirror of [PROMPT.md](PROMPT.md) — do not edit inside the markers.

<!-- prompt-log:begin: 由 scripts/prompt_log.py 自动生成，请勿手工编辑 -->
| Prompt | Date | Status | Commit |
| --- | --- | --- | --- |
| [prompt01](PROMPT.md#prompt01) | 2026-08-30 | ✅ done | `6720bcb` |
| [prompt02](PROMPT.md#prompt02) | 2026-08-30 | ⬜ not done | `bab6ac4`（补提交） |
| [prompt03](PROMPT.md#prompt03) | 2026-08-31 | ✅ done | `bab6ac4`（补提交） |
| [prompt04](PROMPT.md#prompt04) | 2026-08-31 | ✅ done | `d0e36d3` |
| [prompt05](PROMPT.md#prompt05) | 2026-08-31 | ✅ done | `f8f41f7` |
| [prompt06](PROMPT.md#prompt06) | 2026-09-01 | ✅ done | `a5cb5f2` |
| [prompt07](PROMPT.md#prompt07) | 2026-09-07 | ✅ done | `df008bf` |
| [prompt08](PROMPT.md#prompt08) | 2026-09-07 | ✅ done | `bb2a941` |
| [prompt09](PROMPT.md#prompt09) | 2026-09-07 | ✅ done | `099092c` |
| [prompt10](PROMPT.md#prompt10) | 2026-09-07 | ✅ done | `72cc3ca` |
| [prompt11](PROMPT.md#prompt11) | 2026-09-07 | ✅ done | `44c05bf` |
| [prompt12](PROMPT.md#prompt12) | 2026-09-07 | ✅ done | `6ef789f` |
| [prompt13](PROMPT.md#prompt13) | 2026-09-07 | ✅ done | `29a18b6` |
| [prompt14](PROMPT.md#prompt14) | 2026-09-07 | ✅ done | `23dd83d` |
| [prompt15](PROMPT.md#prompt15) | 2026-09-11 | ✅ done | `8db9c13` 等 |
| [prompt16](PROMPT.md#prompt16) | 2026-09-12→16 | ✅ done | `877db81`→`b398076` |
| [prompt17](PROMPT.md#prompt17) | 2026-09-16 | ✅ done | `5c8675d`→ |
| [prompt18](PROMPT.md#prompt18) | 2026-09-21 | ✅ done | `044566c` |
| [prompt19](PROMPT.md#prompt19) | 2026-09-21 | ✅ done | `b0cfa33` |
| [prompt20](PROMPT.md#prompt20) | 2026-09-21 | 🔄 in progress | （进行中） |
<!-- prompt-log:end -->

## Documentation

- [AGENTS.md](AGENTS.md) — binding working rules for agents and humans
- [docs/experiment_protocol.md](docs/experiment_protocol.md) — what every experiment must record; what makes a run a valid benchmark
- [docs/result_schema.md](docs/result_schema.md) — machine-readable result structure (`null`-over-zero policy)
- [docs/repository_structure.md](docs/repository_structure.md) — directory responsibilities and data flow
- [PROMPT.md](PROMPT.md) — dated log of every task prompt and its outcome
