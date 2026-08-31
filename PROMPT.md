# Prompt 记录

| Prompt | 日期 | 状态 | Git | 产出文件 |
| --- | --- | --- | --- | --- |
| [prompt01](#prompt01) | 2026-08-30 | 已完成 | `6720bcb` | [docs/experiment_protocol.md](docs/experiment_protocol.md)<br>[docs/result_schema.md](docs/result_schema.md)<br>[configs/experiment.example.yaml](configs/experiment.example.yaml) |
| [prompt02](#prompt02) | 2026-08-30 | 未完成 | `bab6ac4`（补提交） | [tests/test_supervisor.py](tests/test_supervisor.py)（仅测试，实现缺失） |
| [prompt03](#prompt03) | 2026-08-31 | 已完成 | `bab6ac4`（补提交） | [pyproject.toml](pyproject.toml)<br>[uv.lock](uv.lock)<br>[.gitignore](.gitignore)（修改）<br>models/（4 个 Qwen3 仓库，已校验，见 [models/MANIFEST.md](models/MANIFEST.md)，git-ignored） |

| [prompt04](#prompt04) | 2026-08-31 | 已完成 | （见下一提交） | [docs/models_disk_usage.md](docs/models_disk_usage.md) |

状态含义：

- 已完成 = 产出齐备且经实际验证（prompt01 三份产出已提交于 commit `6720bcb`；prompt03 环境经 import 实测、模型经字节数校验）
- 未完成 = 产出不完整（prompt02 要求的 `benchmark/supervisor` 实现全库不存在，测试 import 目标缺失；`.pytest_cache/v/cache/lastfailed` 记录该测试文件上次运行失败）

日期来源：prompt01 取 commit `6720bcb` 提交时间（2026-08-30 21:52:52 +0800）；prompt02 取 `tests/test_supervisor.py` 文件修改时间（2026-08-30 21:58，据 mtime 推断）；prompt03 为任务执行日。自 2026-08-31 起由 `scripts/prompt_log.py` 自动登记。

---

# prompt01:
You are working inside a research repository for benchmarking LLM fine-tuning on a 16 GB Apple Silicon Mac.

Read `AGENTS.md` first and treat it as authoritative.

The repository skeleton has already been created.

Your task in this step is NOT to implement training.

Your task is to design the experimental protocol and result recording standard so that all later experiments are reproducible, auditable, and directly usable in a research paper.

## Goal

Create and complete:

- `docs/experiment_protocol.md`
- `docs/result_schema.md`
- `configs/experiment.example.yaml`

Do not implement the training runner yet.

---

## 1. Experimental protocol

In `docs/experiment_protocol.md`, define exactly what every experiment must record.

At minimum, include the following categories.

### Hardware

Record:

- Mac model
- Apple chip model
- total unified memory
- CPU core count
- GPU core count
- machine identifier if available
- storage type if relevant
- free disk space before experiment

Do not guess unavailable hardware fields.

Missing values must be recorded as `null`.

### Software

Record:

- macOS version
- Python version
- MLX version
- mlx-lm version
- package manager/environment information
- Git commit SHA
- Git dirty status
- model library versions if relevant

The protocol must preserve enough information to reproduce the software environment.

### Model

Record:

- model ID
- model provider/repository
- exact model revision or commit when available
- parameter count
- architecture
- quantization state before training
- model file size if measurable

Never infer parameter count or revision from the model name if it cannot be verified.

### Fine-tuning configuration

Record:

- method: full / LoRA / QLoRA
- quantization bits
- LoRA rank
- LoRA alpha
- LoRA dropout
- target modules
- number of trainable layers
- number of trainable parameters
- total parameters
- trainable parameter ratio
- batch size
- gradient accumulation
- effective batch size
- sequence length
- learning rate
- optimizer
- scheduler
- warmup
- number of steps
- number of epochs if applicable
- seed
- gradient checkpointing
- precision / dtype

### Dataset

Record:

- dataset name
- dataset source
- dataset revision/version
- train split size
- validation split size
- test split size
- preprocessing configuration
- tokenizer
- max sequence length

Dataset hashes should be recorded where practical.

### Runtime measurements

Record:

- experiment start time
- experiment end time
- wall-clock duration
- successful training steps
- average step time
- median step time if available
- tokens processed
- tokens per second
- samples per second
- peak process memory
- peak system memory
- initial swap usage
- peak swap usage
- page faults if reliably measurable
- energy consumption if reliably measurable
- thermal state if reliably measurable

Do NOT include a metric merely because it sounds useful.

For each system metric, explain:

1. how it will be measured on macOS
2. what command/API provides it
3. its units
4. its known limitations
5. whether it is reliable enough for publication

If a metric cannot be reliably measured, explicitly mark it as unresolved rather than inventing an implementation.

### Experiment outcome

Every run must have one terminal state:

- success
- oom
- timeout
- user_interrupted
- configuration_error
- dependency_error
- model_load_error
- runtime_error
- unknown_failure

Also record:

- process exit code
- error type
- error message
- stderr log path
- stdout log path

OOM experiments are valid experimental observations and MUST NOT be deleted.

---

## 2. Experimental isolation rules

Define rules to reduce confounding.

Include at minimum:

- do not run multiple ML training jobs simultaneously
- record whether the Mac is connected to power
- record thermal state before starting when possible
- record memory usage before training
- record swap usage before training
- close or document major background applications where possible
- use the same software versions across a comparison experiment
- use fixed random seeds for controlled comparisons
- repeat performance-sensitive experiments multiple times
- distinguish warm-up runs from measured runs
- never compare results collected under materially different conditions without documenting the difference

Explicitly define what constitutes a valid benchmark run.

---

## 3. Raw result immutability

Define a raw-results policy.

Requirements:

- raw results go under `results/raw/`
- one experiment produces one immutable result directory or file
- raw result files must never be edited after experiment completion
- corrections must generate a new experiment
- analysis code may only read raw results
- processed files belong in `results/processed/`
- figures belong in `results/figures/`

Every result must contain:

- experiment configuration
- exact command
- Git commit
- environment metadata
- measurements
- terminal status
- logs

---

## 4. Experiment ID

Design an experiment ID strategy.

It must be:

- unique
- human-readable enough for debugging
- safe as a filename
- stable
- programmatically generated

The ID should encode important experimental factors where practical, such as:

- model
- method
- quantization
- context length
- batch size
- LoRA rank
- seed

If a timestamp or hash is used, explain why.

---

## 5. Result schema

Create `docs/result_schema.md`.

Design a machine-readable JSON structure suitable for:

- later conversion to pandas DataFrame
- CSV export
- statistical analysis
- plotting
- automatic LaTeX table generation

Use nested JSON for raw results, but ensure important experimental dimensions can later be flattened cleanly.

A result should conceptually contain:
```json
{
  "experiment": {},
  "hardware": {},
  "software": {},
  "model": {},
  "dataset": {},
  "training": {},
  "runtime": {},
  "metrics": {},
  "status": {},
  "artifacts": {}
}
```

Define every field with:

- name
- type
- unit where applicable
- required or optional
- source of measurement
- meaning

Rules:

- missing measurement = `null`
- unknown is not zero
- unavailable is not zero
- failed measurement is not zero
- never insert estimated values into measured fields

If estimates are ever introduced later, they must live in a separate explicitly named `estimated_*` field.

---

## 6. Example config

Create:

`configs/experiment.example.yaml`

It should demonstrate a small LoRA experiment only.

Use symbolic or currently verified values.

Do not invent model revisions, hardware properties, benchmark measurements, or dataset sizes.

The configuration should include sections for:
```yaml
experiment:
model:
dataset:
training:
monitoring:
output:
```

The schema should be extensible enough to later support:

- Full fine-tuning
- LoRA
- QLoRA
- model-size sweep
- context-length sweep
- batch-size sweep
- LoRA-rank sweep
- repeated seeds

---

## 7. Reproducibility review

After creating the files, perform a critical review.

Ask:

- What information could still prevent another researcher from reproducing a run?
- Which metrics cannot currently be measured reliably on macOS?
- Which metrics may require elevated permissions?
- Which metrics may introduce excessive monitoring overhead?
- Which fields are redundant?
- Which fields are missing?
- What experimental variables could become confounders?
- Which measurements must be validated before they can appear in a paper?

Do not silently solve uncertainty by guessing.

Mark unresolved issues explicitly.

---

## 8. Scope restrictions

In this step, DO NOT:

- implement MLX training
- download a model
- run an experiment
- generate fake benchmark data
- create synthetic measurements
- populate example results with invented numbers
- implement plotting
- write the paper
- claim that any metric collection method works unless you verified the corresponding command/API behavior

You may inspect the local machine and repository if needed, but distinguish clearly between:

- observed information
- proposed design
- unresolved questions

---

## 9. Validation

Before finishing:

1. inspect all created files
2. check YAML syntax
3. check JSON examples if any
4. ensure no fabricated measurements exist
5. ensure all measurement units are explicit
6. ensure `null` is used for unavailable values
7. ensure raw-result immutability is documented
8. ensure failed/OOM experiments are retained
9. ensure the schema can represent both successful and failed runs

Report the exact validation commands you executed and their outputs.

Do not claim validation unless the commands were actually run.

---

## Final response

At the end, report only:

### Files created or modified

List exact paths.

### Key design decisions

Briefly explain the most important protocol/schema choices.

### Measurement risks

List macOS measurements that still require validation.

### Validation evidence

Show the commands actually executed and their relevant outputs.

### Next implementation task

Recommend exactly one next task.

The next task should most likely be implementing a minimal experiment runner and environment metadata collector, but base this recommendation on what you actually find in the repository.

---

# prompt02:

先读 `AGENTS.md`、`docs/experiment_protocol.md`、`docs/result_schema.md` 和 `configs/experiment.example.yaml`。

实验协议和结果格式已经确定了，现在开始实现实验基础设施。

先不要下载模型，也不要训练。

请先实现一个 Experiment Supervisor v0，目标是以后任何训练任务都必须通过它运行。

它至少需要做到：

1. 读取并验证 experiment YAML 配置。
2. 自动生成 experiment ID。
3. 记录当前 Git commit 和 dirty status。
4. 收集当前 Mac、macOS、Python、MLX 等能够可靠获取的环境信息。
5. 记录实验开始前的内存和 swap 状态。
6. 能够启动一个普通 subprocess，并完整保存 command、stdout、stderr、exit code、开始时间、结束时间和 wall time。
7. 根据退出情况写入 success / timeout / runtime_error 等状态。
8. 即使 subprocess 失败，也必须生成完整合法的结果。
9. 最终结果按照之前的 result schema 保存。
10. raw result 必须原子写入，完成后生成 SHA-256 manifest，并且不能被后续流程修改。

这一阶段不要接 MLX training。先用类似 `/usr/bin/true` 和一个故意失败的命令做测试，证明 success 和 failure 两种情况都能够正确保存结果。

对于 peak memory、swap、page fault、thermal、energy 等目前还没有验证可靠性的指标，不要自行猜测实现方式。可以先保留 null，并保存原始 evidence。

请补充对应的单元测试和集成测试，并实际运行。

完成后告诉我：

- 创建或修改了哪些文件
- 实际运行了哪些测试
- success case 产生了什么结果
- failure case 产生了什么结果
- 哪些 measurement 仍然没有解决
- Git provenance 是否已经正确写入结果

完成后停下来，不要开始模型下载或者 LoRA。

---

# prompt03:

先在项目根目录用 uv 创建 .venv，把 MLX、mlx-lm、huggingface_hub 和 pyyaml 作为项目依赖锁进 pyproject.toml/uv.lock。验证 Python 和各依赖的实际版本，并确认当前解释器来自项目 .venv。这一步完成后再开始下载 Qwen3，不要使用系统 Python。

---

# prompt04:

统计 models/ 目录下 4 个已下载 Qwen3 仓库的实际磁盘占用（含内部 .cache），连同各仓库的 revision 一起写入 docs/models_disk_usage.md，数据必须来自真实运行的命令输出。
