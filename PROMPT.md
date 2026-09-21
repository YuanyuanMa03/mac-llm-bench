# Prompt 记录

| Prompt | 日期 | 状态 | Git | 产出文件 |
| --- | --- | --- | --- | --- |
| [prompt01](#prompt01) | 2026-08-30 | 已完成 | `6720bcb` | [docs/experiment_protocol.md](docs/experiment_protocol.md)<br>[docs/result_schema.md](docs/result_schema.md)<br>[configs/experiment.example.yaml](configs/experiment.example.yaml) |
| [prompt02](#prompt02) | 2026-08-30 | 未完成 | `bab6ac4`（补提交） | [tests/test_supervisor.py](tests/test_supervisor.py)（仅测试，实现缺失） |
| [prompt03](#prompt03) | 2026-08-31 | 已完成 | `bab6ac4`（补提交） | [pyproject.toml](pyproject.toml)<br>[uv.lock](uv.lock)<br>[.gitignore](.gitignore)（修改）<br>models/（4 个 Qwen3 仓库，已校验，见 [models/MANIFEST.md](models/MANIFEST.md)，git-ignored） |
| [prompt04](#prompt04) | 2026-08-31 | 已完成 | `d0e36d3` | [docs/models_disk_usage.md](docs/models_disk_usage.md) |
| [prompt05](#prompt05) | 2026-08-31 | 已完成 | `f8f41f7` | [src/benchmark/__init__.py](src/benchmark/__init__.py)<br>[src/benchmark/ids.py](src/benchmark/ids.py)<br>[src/benchmark/environment.py](src/benchmark/environment.py)<br>[src/benchmark/schema.py](src/benchmark/schema.py)<br>[src/benchmark/artifacts.py](src/benchmark/artifacts.py)<br>[src/benchmark/supervisor.py](src/benchmark/supervisor.py)<br>[scripts/run_experiment.py](scripts/run_experiment.py)<br>[tests/test_supervisor.py](tests/test_supervisor.py)<br>[pyproject.toml](pyproject.toml)<br>[uv.lock](uv.lock)<br>[results/validation/supervisor-v0](results/validation/supervisor-v0) |
| [prompt06](#prompt06) | 2026-09-01 | 已完成 | `a5cb5f2` | [src/train/lora_smoke.py](src/train/lora_smoke.py)<br>[src/train/__init__.py](src/train/__init__.py)<br>[scripts/train_lora.py](scripts/train_lora.py)<br>[src/benchmark/supervisor.py](src/benchmark/supervisor.py)<br>[tests/test_supervisor.py](tests/test_supervisor.py)<br>[configs/experiments/exp0_qwen3_0.6b_lora.yaml](configs/experiments/exp0_qwen3_0.6b_lora.yaml)<br>[data/exp0_smoke.jsonl](data/exp0_smoke.jsonl)<br>[results/raw](results/raw) |
| [prompt07](#prompt07) | 2026-09-07 | 已完成 | `df008bf` | [src/train/lora_smoke.py](src/train/lora_smoke.py)<br>[configs/experiments/calib_qwen3_0.6b_lora_100step_r0.yaml](configs/experiments/calib_qwen3_0.6b_lora_100step_r0.yaml)<br>[configs/experiments/calib_qwen3_0.6b_lora_100step_r1.yaml](configs/experiments/calib_qwen3_0.6b_lora_100step_r1.yaml)<br>[configs/experiments/calib_qwen3_0.6b_lora_100step_r2.yaml](configs/experiments/calib_qwen3_0.6b_lora_100step_r2.yaml)<br>[results/raw](results/raw) |
| [prompt08](#prompt08) | 2026-09-07 | 已完成 | `bb2a941` | [configs/experiments/calib_qwen3_1.7b_lora_100step_r0.yaml](configs/experiments/calib_qwen3_1.7b_lora_100step_r0.yaml)<br>[configs/experiments/calib_qwen3_1.7b_lora_100step_r1.yaml](configs/experiments/calib_qwen3_1.7b_lora_100step_r1.yaml)<br>[configs/experiments/calib_qwen3_1.7b_lora_100step_r2.yaml](configs/experiments/calib_qwen3_1.7b_lora_100step_r2.yaml)<br>[results/raw](results/raw) |
| [prompt09](#prompt09) | 2026-09-07 | 已完成 | `099092c` | [models/MANIFEST.md](models/MANIFEST.md)<br>[configs/experiments/probe_qwen3_4b_bf16_lora_20step.yaml](configs/experiments/probe_qwen3_4b_bf16_lora_20step.yaml)<br>[src/benchmark/environment.py](src/benchmark/environment.py)<br>[src/train/lora_smoke.py](src/train/lora_smoke.py)<br>[tests/test_supervisor.py](tests/test_supervisor.py)<br>[results/raw](results/raw) |
| [prompt10](#prompt10) | 2026-09-07 | 已完成 | `72cc3ca` | [models/MANIFEST.md](models/MANIFEST.md)<br>[configs/experiments/probe_qwen3_4b_4bit_qlora_20step.yaml](configs/experiments/probe_qwen3_4b_4bit_qlora_20step.yaml)<br>[src/train/lora_smoke.py](src/train/lora_smoke.py)<br>[src/benchmark/supervisor.py](src/benchmark/supervisor.py)<br>[tests/test_supervisor.py](tests/test_supervisor.py)<br>[results/raw](results/raw) |
| [prompt11](#prompt11) | 2026-09-07 | 已完成 | `44c05bf` | [src/analysis/paired_comparison.py](src/analysis/paired_comparison.py)<br>[src/analysis/__init__.py](src/analysis/__init__.py)<br>[scripts/compare_probes.py](scripts/compare_probes.py)<br>[results/processed/comparison_paired_probe.json](results/processed/comparison_paired_probe.json)<br>[results/raw](results/raw) |
| [prompt12](#prompt12) | 2026-09-07 | 已完成 | `6ef789f` | [models/MANIFEST.md](models/MANIFEST.md)<br>[configs/experiments/probe_qwen3_8b_4bit_qlora_20step.yaml](configs/experiments/probe_qwen3_8b_4bit_qlora_20step.yaml)<br>[results/processed/comparison_8b_vs_4b_qlora.json](results/processed/comparison_8b_vs_4b_qlora.json)<br>[results/raw](results/raw) |
| [prompt13](#prompt13) | 2026-09-07 | 已完成 | `29a18b6` | [models/MANIFEST.md](models/MANIFEST.md)<br>[configs/experiments/probe_qwen3_14b_4bit_qlora_20step.yaml](configs/experiments/probe_qwen3_14b_4bit_qlora_20step.yaml)<br>[results/processed/comparison_14b_vs_8b_qlora.json](results/processed/comparison_14b_vs_8b_qlora.json)<br>[results/raw](results/raw) |
| [prompt14](#prompt14) | 2026-09-07 | 已完成 | `23dd83d` | [configs/experiments/probe_qwen3_4b_4bit_qlora20_ctx2048.yaml](configs/experiments/probe_qwen3_4b_4bit_qlora20_ctx2048.yaml)<br>[configs/experiments/probe_qwen3_4b_4bit_qlora20_ctx8192.yaml](configs/experiments/probe_qwen3_4b_4bit_qlora20_ctx8192.yaml)<br>[configs/experiments/probe_qwen3_4b_4bit_qlora20_ctx4096.yaml](configs/experiments/probe_qwen3_4b_4bit_qlora20_ctx4096.yaml)<br>[data/exp0_long_ctx2048.jsonl](data/exp0_long_ctx2048.jsonl)<br>[data/exp0_long_ctx8192.jsonl](data/exp0_long_ctx8192.jsonl)<br>[data/exp0_long_ctx4096.jsonl](data/exp0_long_ctx4096.jsonl)<br>[src/analysis/paired_comparison.py](src/analysis/paired_comparison.py)<br>[src/analysis/context_boundary.py](src/analysis/context_boundary.py)<br>[tests/test_analysis.py](tests/test_analysis.py)<br>[scripts/make_long_ctx_dataset.py](scripts/make_long_ctx_dataset.py)<br>[scripts/build_evidence_ledger.py](scripts/build_evidence_ledger.py)<br>[results/processed/comparison_4b4bit_ctx512_vs_ctx2048.json](results/processed/comparison_4b4bit_ctx512_vs_ctx2048.json)<br>[results/processed/context_boundary_probe_summary.json](results/processed/context_boundary_probe_summary.json)<br>[results/raw/20260907T110003248768Z__mlx-community-qwen3-4b-4bit__qlora-q4__ctx2048__b1-ga1__r8__s42__01a07b86-7030-7992-b5e9-e44c9960eb61](results/raw/20260907T110003248768Z__mlx-community-qwen3-4b-4bit__qlora-q4__ctx2048__b1-ga1__r8__s42__01a07b86-7030-7992-b5e9-e44c9960eb61)<br>[results/raw/20260907T111824441175Z__mlx-community-qwen3-4b-4bit__qlora-q4__ctx8192__b1-ga1__r8__s42__01a07b97-3db9-7873-b5b6-49cb74b618a0](results/raw/20260907T111824441175Z__mlx-community-qwen3-4b-4bit__qlora-q4__ctx8192__b1-ga1__r8__s42__01a07b97-3db9-7873-b5b6-49cb74b618a0)<br>[results/raw/20260911T164322546359Z__mlx-community-qwen3-4b-4bit__qlora-q4__ctx4096__b1-ga1__r8__s42__01a0915a-3232-7ce9-b2d0-3d9d674f7467](results/raw/20260911T164322546359Z__mlx-community-qwen3-4b-4bit__qlora-q4__ctx4096__b1-ga1__r8__s42__01a0915a-3232-7ce9-b2d0-3d9d674f7467)<br>[research/evidence_ledger.csv](research/evidence_ledger.csv)<br>[README.md](README.md)<br>[README.zh-CN.md](README.zh-CN.md) |
| [prompt15](#prompt15) | 2026-09-11 | 已完成 | `8db9c13` 等 | Phase 0 审计 / preregistration / dataset freeze / measurement validation / literature（见 [research/](research/)） |
| [prompt16](#prompt16) | 2026-09-12→16 | 已完成 | `877db81`→`b398076` | formal 矩阵战役 + D5 trainer 修复（axis4 闭环）+ D6/D7 + coverage 模块 + 8B/ctx2048 补齐 |
| [prompt17](#prompt17) | 2026-09-16 | 已完成 | `5c8675d`→ | D8 停止决策 + experiment freeze（`freeze-04f90a840b8ea8fb`）+ 全量重建 + H1-H6 audit + 论文终稿 + claim ledger + reproducibility audit |
| [prompt18](#prompt18) | 2026-09-21 | 进行中 | （进行中） | 待补 |

状态含义：

- 已完成 = 产出齐备且经实际验证（prompt01 三份产出已提交于 commit `6720bcb`；prompt03 环境经 import 实测、模型经字节数校验）
- 未完成 = 产出不完整（prompt02 会话仅交付测试文件、实现缺失；该实现后由 prompt05 补齐交付，prompt02 自身状态保留为历史记录）

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

---

# prompt05:

先读一下 AGENTS.md、docs/experiment_protocol.md、docs/result_schema.md、仓库结构文档，以及 models/MANIFEST.md。

环境和模型下载已经完成。现在开始补 Experiment Supervisor。

这一步先不要训练 Qwen，也不要运行 LoRA/QLoRA。我要先把实验执行和记录这一层做可靠。

请实现一个 Experiment Supervisor v0，让以后所有训练实验都必须通过它启动。

我希望它完成这些事情：

1. 读取并验证实验 YAML 配置。
2. 自动生成唯一的 experiment ID。
3. 在实验开始前记录真实环境：

   * Git commit
   * Git dirty status
   * macOS
   * Python
   * MLX / mlx-lm
   * 当前硬件信息
   * 实验开始前的内存和 swap 状态（仅限目前已经确认可以可靠获取的指标）。
4. 启动一个 subprocess，并保存：

   * exact command
   * stdout
   * stderr
   * start time
   * end time
   * wall time
   * exit code
5. 根据真实退出情况分类：

   * success
   * timeout
   * user_interrupted
   * configuration_error
   * dependency_error
   * model_load_error
   * runtime_error
   * unknown_failure
   * 如果能够可靠识别 OOM，则记录 oom；不能可靠识别时不要猜。
6. 即使 subprocess 失败，也必须产生完整 result，不允许因为失败而什么都不保存。
7. 最终结果严格按照 docs/result_schema.md 写入 results/raw/。
8. raw result 完成后原子 finalize，生成 SHA-256 manifest。
9. 已 finalize 的 raw result 不允许后续代码直接覆盖或修改。
10. 对暂时没有可靠 measurement 方法的字段继续使用 null，不要补估算值。

先不要接真正的训练命令。

先用三个最小 integration case 验证 Supervisor：

* 一个明确成功的命令，例如 `/usr/bin/true`
* 一个明确失败并返回非零 exit code 的命令
* 一个会超过 timeout 的命令

这三个 case 都必须真正执行，并分别产生对应的 raw result。

另外请补测试，至少覆盖：

* YAML config validation
* experiment ID generation
* Git provenance
* subprocess success
* subprocess failure
* timeout
* stdout/stderr preservation
* result JSON serialization
* atomic finalization
* SHA-256 manifest
* 已 finalize raw result 无法被普通流程覆盖

如果现有代码结构不适合，不要把所有逻辑都塞进 scripts/run_experiment.py。CLI 保持尽量薄，核心逻辑放进 src/benchmark/ 下。

完成后实际运行测试和三个 integration cases。

最后告诉我：

* 创建和修改了哪些文件
* 测试实际运行结果
* 三个 integration case 的 experiment ID
* 每个 case 的 terminal status 和 exit code
* raw result 实际保存在哪里
* manifest 是否校验通过
* Git commit 和 dirty status 是否成功进入 result
* 哪些 measurement 仍然保持 null，以及为什么

最后停下来。

不要继续做 Qwen 训练。

下一步我会让你把 Qwen3-0.6B-Base 接进 Supervisor，开始第一次 20-step LoRA Experiment 0。

---

# prompt06:

真实接入模型训练：把 Qwen3-0.6B-Base 接进 Supervisor，跑第一次 20-step LoRA Experiment 0

---

# prompt07:

100-step 校准运行.

---

# prompt08:

Model Scaling：0.6B → 1.7B，严格遵循AGENTS.md。

---

# prompt09:

先读取 AGENTS.md、实验协议、result schema、当前实验台账以及 prompt08 的全部结果。

prompt08 已完成，现在开始下一个正式边界探针。

这一步选择 4B BF16 路径，而不是先跑 4bit。

目标是回答一个非常具体的问题：

> 在当前 16GB Apple Silicon 机器上，Qwen3 4B 的 BF16 基础权重是否能够以 LoRA 方式完成真实训练步骤？

不要把之前估算的约 8.5GB 峰值内存当成事实。这个数字目前只是预估，本实验要获得真实 measurement。

先检查仓库中是否已经存在与当前实验系列一致的 Qwen3 4B 模型。

如果不存在，按照现有模型获取规范下载并固定准确的 Hugging Face repository 和 revision，更新 model manifest。不要根据模型名字推测 revision、参数量或 dtype。

保持与前面正式实验相同的模型系列和数据集定义，不要在这一轮同时更换数据集、训练模板或评价方法。

本轮配置先固定为：

- model: Qwen3 4B
- weight dtype: BF16
- method: LoRA
- batch size: 1
- sequence length: 512
- LoRA rank: 8
- seed: 42
- training steps: 20

除非当前已经固定的实验协议要求其他值，否则不要主动扩大 context、batch size 或 rank。

所有训练必须通过现有 Experiment Supervisor。

实验前先执行 preflight，检查：

- 当前 Git provenance
- 模型 revision
- 可用磁盘
- 当前 unified-memory 状态
- swap 状态
- 是否存在其他训练进程
- 当前配置是否符合 protocol

然后真正执行 20-step LoRA。

无论结果是：

- success
- oom
- runtime_error
- resource-related failure

都保留完整 raw result。

不要因为 OOM 而自动降低配置重新跑；如果失败，先把失败作为这一配置的真实 observation 保存下来。

本轮必须尽可能记录经过验证的：

- completed steps
- wall-clock time
- step time
- throughput
- peak memory
- swap
- stdout
- stderr
- exit code
- terminal state

未经验证可靠的 measurement 继续使用 null，不要估算。

实验完成后做一次结果完整性检查：

1. result 是否符合 result schema；
2. raw result 是否 immutable；
3. manifest 是否校验通过；
4. model revision 是否进入结果；
5. git commit / dirty status 是否进入结果；
6. 20 个 training steps 是否真实完成；
7. 是否发生 swap 或明显 memory pressure；
8. 是否存在任何人工填写、估算或推测值。

完成后停止。

不要自动运行：
- 4B 4bit
- QLoRA
- context 1024
- 更大的模型
- full fine-tuning

最后只报告这一次 4B BF16 probe 的真实 observation，并把它与前面同类实验做结构化对比。

如果成功，下一步候选应是：
同一个 4B 模型、相同 dataset / batch / context / rank / seed / steps，仅将 BF16 LoRA 替换为 4bit QLoRA，形成配对实验。

如果失败，也不要立即改变结论，先报告失败证据和最可能的失败类别。

---

# prompt10:

配对实验：同一 4B 模型、相同 dataset/batch/context/rank/seed/steps，仅将 BF16 LoRA 替换为 4bit QLoRA（mlx-community 4bit 权重已在本地，rev 4dcb3d10 待哈希锚定）——单变量对照，回答"量化把内存边界推开多少、代价多少吞吐"。

---

# prompt11:

先读 AGENTS.md、docs/experiment_protocol.md、docs/result_schema.md、当前实验台账、models/MANIFEST.md，以及已经完成的所有正式 probe 结果。

现在开始下一组 controlled probes。

这一步的目标不是做完整 benchmark，而是验证一个具体假设：

> 在相同训练条件下，4bit 量化是否能够显著降低 4B 模型的训练内存压力，同时保持可接受的训练速度，从而扩展 16GB Apple Silicon 上的可训练边界。

目前关于"峰值内存""量化几乎没有速度代价"等说法都只能视为待验证假设，不要把之前的估算写成实验事实。

## 第一部分：4B BF16 LoRA

先检查当前仓库是否已经有与现有 Qwen3 实验系列一致的 4B BF16 模型。

如果没有：

* 从 Hugging Face 获取正确模型；
* 查询并记录真实 repository revision / commit SHA；
* 按现有模型管理规范下载；
* 更新 models/MANIFEST.md；
* 完成模型文件校验；
* 不根据模型名称推断 revision、dtype 或参数量。

然后运行：

* model: Qwen3 4B
* weights: BF16
* method: LoRA
* batch size: 1
* sequence length: 512
* LoRA rank: 8
* seed: 42
* training steps: 20

数据集、prompt template、optimizer、learning rate、target modules 等其他条件必须尽量与之前同类正式实验保持一致。

如果必须改变任何条件，先在配置和结果里明确记录，不要静默修改。

所有训练必须通过现有 Experiment Supervisor 执行。

实验前执行 preflight，并记录：

* Git commit
* Git dirty status
* model revision
* 当前软件环境
* 当前 memory / swap 状态
* 是否存在其他训练进程
* 磁盘空间
* 配置是否符合 protocol

无论结果是 success、oom、runtime_error 或其他失败，都保留完整 raw result。

如果 BF16 实验失败，不要自动降低 context、rank 或 batch 重新跑。先保留这个配置对应的真实失败 observation。

## 第二部分：4B 4bit QLoRA

第一部分正式结束、raw result 已 finalize 并验证后，再运行配对实验。

使用同一个 4B 模型对应的 4bit MLX 权重。

配置保持：

* model scale: 4B
* weights: 4bit
* method: QLoRA
* batch size: 1
* sequence length: 512
* LoRA rank: 8
* seed: 42
* training steps: 20

除权重量化和由此必然产生的训练方式差异外，不要主动改变其他变量。

这组实验的目标是形成尽可能干净的 paired comparison：

BF16 LoRA
vs
4bit QLoRA

## Measurement

只记录当前已经验证可靠的真实 measurement。

至少保留：

* completed steps
* wall-clock time
* step timing
* throughput，如果当前方法已经通过验证
* process / system memory，如果当前 collector 已经通过验证
* swap，如果当前 collector 已经通过验证
* stdout
* stderr
* exit code
* terminal status

未经验证可靠的 measurement 继续使用 null。

不要为了生成完整表格而估算任何缺失数字。

## 配对检查

两次实验完成后，检查它们是否真正满足 controlled comparison。

生成一份机器可读的 comparison summary，但不要修改 raw results。

只比较真实观测值，例如：

* BF16 是否 trainable
* 4bit 是否 trainable
* peak memory difference
* wall-time difference
* step-time difference
* throughput difference
* swap behavior difference

如果某个 measurement 为 null，就明确写 unavailable，不要计算对应差值。

不要把单次 20-step probe 的结果描述为统计显著结论。

可以描述为：

* preliminary observation
* probe result
* evidence motivating the formal benchmark

不要描述为：

* proof
* zero-cost
* statistically significant
* general scaling law

除非后续正式重复实验真的支持这些结论。

## Validation

两组实验结束后实际检查：

1. 两个 result 是否符合 result schema；
2. raw results 是否 immutable；
3. manifest 是否校验通过；
4. Git provenance 是否完整；
5. model revision 是否完整；
6. 配置之间除了预定变量之外是否存在额外差异；
7. 是否存在人工填写或估算的 benchmark 数值；
8. 是否真的执行了 20 个 training steps；
9. failure/OOM 是否被完整保留；
10. comparison summary 是否完全来自 raw result。

## 完成后停止

不要自动继续：

* 8B
* context scaling
* batch-size sweep
* LoRA-rank sweep
* repeated seeds
* full fine-tuning
* 正式 Phase B benchmark

最后报告：

### 4B BF16 observation

只报告真实测量值。

### 4B 4bit observation

只报告真实测量值。

### Controlled comparison

明确区分 observation 和 interpretation。

### Files created or modified

列出真实路径。

### Validation evidence

列出实际运行的检查命令和相关输出。

### Unresolved measurements

说明哪些指标仍然不能可靠使用。

### Recommended next probe

根据这两个 probe 的真实结果，在以下两个方向中只推荐一个：

* 继续 scale 到 8B；
* 保持 4B，开始 context boundary probing。

说明推荐依据，但不要自动执行。

---

# prompt12:

继续 scale 到 8B（4bit QLoRA 探针）。

---

# prompt13:

14B-4bit 探针。

---

# prompt14:

按照你的计划继续。

---

# prompt18:

从当前公开 `master` 的训练器、Supervisor、分析代码、raw evidence、preregistration 和你最新论文里已经出现的结论一起看，问题已经可以分得比较清楚了。**核心实验不需要推倒重跑，但现在不能只润色论文。代码、分析链和论文表述要同步修一次。**

先处理一个与论文无关但优先级最高的问题：**公开仓库的 `raw_environment.txt` 里仍然包含未脱敏的设备 `provisioning_UDID`**。`src/benchmark/environment.py` 当前只脱敏 `serial_number`、`serial_number_system`、`platform_UUID`，没有覆盖 `provisioning_UDID`。建议先临时把仓库设为 private，处理完历史再重新公开。不要在公开 issue/commit message 里复制那个值。

## 一、我目前能确认的完整问题清单

下面“事实”都是我从当前公开 `master@aef0276f6cdbab1aac1bff754caeead7896621df` 源码或 raw evidence 直接确认的；“影响”是我的判断。

| ID  | 级别        | 问题                                                                             | 源码证据                                                                                                         | 对现有实验影响                                                                        | 是否重跑                                            |
| --- | --------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ | ----------------------------------------------- |
| S01 | **P0**    | 公开仓库泄露 `provisioning_UDID`                                                     | `src/benchmark/environment.py` 的 `_REDACTED_HARDWARE_KEYS` 未包含它；公开 `raw_environment.txt` 可见                  | 隐私问题，不是科研问题                                                                    | 否                                               |
| S02 | **P0**    | `shuffle: true` 实际没有在正式实验开始时 shuffle                                           | `lora_smoke.py:200-218`，只有遍历完 2048 samples 才 `rng.shuffle(order)`                                            | 论文不能说 seed 改变 data order                                                       | 否                                               |
| S03 | **P0**    | “3 seeds = 独立数据顺序重复”不成立                                                        | prereg `:69-70` 与训练器行为矛盾；三个 ctx2048 seed 的 token 序列完全相同                                                      | seed 主要改变 LoRA/MLX 初始化；统计解释需降级                                                 | 否                                               |
| S04 | **P0**    | formal dataset 的 train/val split 实现与 MANIFEST 描述不同                             | `build_formal_dataset.py` 先随机选 2080，随后按 `global_row` 排序，**再**取前2048/后32                                      | validation 是所选样本中 row index 最大的32条，不是 shuffled-order random validation         | 否，披露                                            |
| S05 | **P0**    | ctx512/1024/2048 不是固定长度 workload，而是 maximum truncation cap                     | `lora_smoke.py` 为 `ids[:seq_len]`；b1 不 pad 到 cap                                                             | “2048 context”不能解释成每步2048 tokens                                               | 否                                               |
| S06 | **P0**    | “512→2048 = 4× token count”不成立                                                 | raw 前20步平均实际 input ≈492 / 916 / 1215 tokens                                                                  | context scaling 的机制解释需要修改                                                      | 否                                               |
| S07 | **P0**    | `[2048,4096)` 容易被读成精确训练阈值                                                      | 4096/8192 是单 seed synthetic probe；2048 evidence又有 formal/probe 两种                                            | 只能叫 observed bracket / first observed failure                                  | 否                                               |
| S08 | **P0**    | batch=8 的失败阶段无法证明发生在训练 step                                                    | `lora_smoke.py:195-198` 在训练前先执行 validation；validation 使用同一 batch size；三个 b8 stdout 都是空文件                     | 只能证明 benchmark workload 在 first optimizer step 前失败，不能确定是 optimizer training 导致 | 可不重跑；若要强结论只需定向重跑 b8                             |
| S09 | **P0**    | `run_analysis.py` 并不能生成论文全部结果                                                  | 它没有调用 `revision_round1.main()`；但论文 `main.tex:794-796` 输入 table7/8/9，这三表由 `revision_round1.py` 生成             | “one command regenerates every figure/table”当前为假                               | 否                                               |
| S10 | **P0**    | scaling fit 存在两套实现、输入口径不一致                                                     | `summary.py` fit 使用每 cell `iloc[0]`；`figures.py:274/339` 使用 cell mean                                        | `key_numbers` 的 slope 与图的 slope 可不同；已有审计也承认 0.9986 vs 0.9966                   | 否                                               |
| S11 | **P0/P1** | H2/H6 判定规则结果后修改                                                                | `hypothesis_audit.py` + D9                                                                                   | 不能把 v2 当 preregistered confirmatory result                                     | 否                                               |
| S12 | **P0/P1** | Practical 从冻结的 `P1 ∧ P2` 改成最终 P2-only                                          | 你最新论文 D11                                                                                                    | final verdict 与 prereg definition 不一致                                          | 否，但必须并排报告 frozen 与 revised                      |
| S13 | **P1**    | config 写 AdamW，实际训练是 Adam                                                      | config `optimizer.name=adamw`；`lora_smoke.py:189 optimizer = Adam(...)`                                      | 方法描述必须写 effective Adam                                                         | 否                                               |
| S14 | **P1**    | `effective_config.json` 并不是 effective config                                   | `supervisor.py:206-207` 只是把输入 config dump 一份                                                                 | machine-readable provenance 会继续声称 AdamW/shuffle                                | 否                                               |
| S15 | **P1**    | raw `training.optimizer` 同样来自声明配置而非实际运行                                        | `schema.py:89`                                                                                               | raw 元数据错误表示 effective optimizer                                                | 否                                               |
| S16 | **P1**    | 所有 raw result 的 validity 默认被写成 false                                           | `supervisor.py:588` hardcode `protocol_valid=False, performance_valid=False`                                 | reviewer 打开正式 run 会看到“invalid”                                                 | 否                                               |
| S17 | **P1**    | `monitoring_overhead_validated` raw 中仍硬编码 false                                | Supervisor 与 `measurement_validation.md` 的验证结论不一致                                                            | machine-readable metadata stale                                                | 否                                               |
| S18 | **P1**    | 部分 formal run 在 dirty tree 上运行且没有保存 patch                                      | 一个 4B formal run明确显示 `pyproject.toml`、`uv.lock` modified；`git_patch=null`                                    | commit SHA 无法完全重建当时环境                                                          | 无法补造；披露                                         |
| S19 | **P1**    | `uv.lock` artifact 没保存 sha256/size，且无 package snapshot                         | `supervisor.py` 中 lockfile ref 的 hash/size 为 null                                                            | 加剧 S18 的 provenance 缺口                                                         | 历史无法补；未来修                                       |
| S20 | **P1**    | 当前 `reproducibility_audit.json` 自己是 `all_passed:false`                         | raw manifests / formal 3-seed check fail                                                                     | 公开 release 不应留下一个看起来“最终审计失败”的文件                                                | 否                                               |
| S21 | **P1**    | reproducibility audit 的“三 seed 都必须 success”规则本身不适合 failure-inclusive benchmark | `audit_reproducibility.py` 对所有成功 group 要求 count=3                                                            | 4B BF16 boundary 本来就允许 failure，却被脚本判 FAIL                                      | 否                                               |
| S22 | **P1**    | manifest 文档存在 stale/inconsistent 描述                                            | 较早 audit 写“5个缺 manifest”；后续 final-integrity 已改为 digest/finalize 机制                                           | 文档间有自相矛盾                                                                       | 否                                               |
| S23 | **P1**    | failed runs 的 step timing 不是流式保存                                               | `step_timings.jsonl` 在训练循环全部结束后一次性写文件                                                                        | SIGKILL/timeout 时结构化 step data 丢失；14B 才会靠 stdout 人工恢复70步                       | 历史无法补；未来修                                       |
| S24 | **P1**    | `successful_steps` 对 killed run 往往是 null，即使 stdout 已有 step                     | `training_metrics.json` 也是最后才写                                                                               | failure-inclusive 数据结构不完整                                                      | 用 processed parser补“observed_steps_from_stdout” |
| S25 | **P1**    | `_swapin_per_step` 不是训练 step 的 paging rate                                     | `flatten.py:130-158` = whole-run `vm_stat after-before / successful_steps`                                   | 包含 load/validation/background 等                                                | 否，重命名                                           |
| S26 | **P1**    | step timestamp 只有秒级                                                            | `lora_smoke.py:240`                                                                                          | D12 与 1Hz swap 对齐时，尤其 sub-second runs 有量化误差                                    | 不可回补；论文加 caveat                                 |
| S27 | **P1**    | monitor timestamp 却是微秒级                                                        | `monitor.py:36`                                                                                              | 与 S26 的时间分辨率不对称                                                                | 未来改 monotonic_ns                                |
| S28 | **P1**    | peak memory 的 scope 包含训练循环中的 periodic validation                               | reset peak 后进入循环，而 validation 在 step 50/100 等循环内部                                                            | `peak training memory` 严格说是 training-loop workload peak                        | 否，改定义                                           |
| S29 | **P1/P2** | validation 标为 forward-only，却调用 `value_and_grad`                                | `lora_smoke.py:173-183`                                                                                      | MLX lazy 下不能直接断言一定算 backward，但源码语义不干净                                          | 代码修，历史加限制                                       |
| S30 | **P1/P2** | batch8 pre-validation 也调用上述 `value_and_grad`                                   | 同 S08/S29                                                                                                    | 进一步使 b8 failure phase ambiguous                                                | 定向实验可解决                                         |
| S31 | **P2**    | `unified_memory_bytes` collector 实际经常为 null                                    | environment.py 查 `physicalMemory`，raw 实际键是 `physical_memory`；也没实现 docstring 所说的 `sysctl hw.memsize` fallback | 论文16GiB没错，但不是 result.json 直接支持的字段                                              | 未来修                                             |
| S32 | **P2**    | 若干 config 字段只是 schema 声明，没有真正被 trainer 执行                                      | gradient accumulation、scheduler、precision、checkpointing 等                                                    | 当前 ga=1、constant、false/null，所以当前实验影响极小；但“effective config”说法不准确                | 否                                               |
| S33 | **P2**    | context helper 同 ctx 多 run 时机械取“最新一次”                                          | `context_boundary.py:77`                                                                                     | 当前数据未必改变结论，但规则不是 prereg selection rule                                         | 修代码                                             |
| S34 | **P2**    | empirical p99 样本太小                                                             | 100步或20步里 p99 接近 max                                                                                         | 不能当稳定 tail percentile                                                          | 否                                               |
| S35 | **P2**    | memory decomposition 的 weight component 是 stored/on-disk proxy                 | 最新论文的分解逻辑                                                                                                    | 不能把 residual 精确解释成 activation/allocator 等                                      | 否                                               |
| S36 | **P2**    | `context → batch → scale` 被写得像普遍 binding order                                 | 三个轴不是统一 factorial experiment，且窗口不同                                                                           | 只能说 separate one-factor probes on tested bases                                 | 否                                               |
| S37 | **P2**    | “4-bit QLoRA is the default answer”范围过大                                        | 实际只比较 full/LoRA/4-bit QLoRA                                                                                  | 没比较其他低内存策略                                                                     | 否                                               |
| S38 | **P2**    | “first measurements/reference numbers” novelty 太宽                              | related-work wording                                                                                         | 容易被已有 Apple Silicon training 工作反驳                                              | 否                                               |
| S39 | **P2**    | Figure 8(c) 最新 PDF 的可视内容与 caption/body 描述不一致                                   | caption 说三条 b8 swap ramp 至约20GiB，PDF panel visually 没显示完整轨迹                                                  | 这是当前最明显的图证据 bug                                                                | 必须重新生成图                                         |
| S40 | **P2**    | Figure 11 narrow y-axis 放大 rank<2%的视觉差异                                        | 最新 PDF                                                                                                       | 视觉表达偏强                                                                         | 否                                               |
| S41 | **P2**    | PDF metadata 与正文 title/author 版本曾不一致                                           | 最新 PDF metadata Author 为空                                                                                    | arXiv 元数据质量问题                                                                  | 否                                               |
| S42 | **P2**    | 当前远程 `master` 不是最终 paper branch                                                | 远程只有 master，最新 paper 在你本地                                                                                    | arXiv code↔paper 无固定 revision                                                  | 提交前解决                                           |

其中我最担心的不是 Adam，而是 **S02/S03、S05/S06、S08、S09/S10 和 S01**。Adam 已经很容易披露；前面这些如果 reviewer 真正 clone 代码，是可以自己算出来的。

---

# 二、哪些东西不需要重跑

目前没有证据要求你重跑 118 个 experiments。

核心 model-scale 结果、4-bit/BF16 allocator peak、8B 三次完成、4B BF16 machine-state contrast、14B boundary case 都可以保留。

真正值得考虑的额外实验只有一个：

> **batch8 的 3 次 instrumented post-hoc rerun。**

目的不是改变结论，而是明确：

```text
model loading
↓
initial validation start
↓
initial validation end
↓
training step 1 start
```

究竟死在哪个 phase。

如果你不想再跑，论文直接改成：

> At micro-batch 8, all three benchmark runs terminated before completing the first optimizer step.

不要写：

> training at batch 8 caused...

这样就合法。

context 也不用重跑。直接从 raw 计算 actual token lengths，并把 `context length` 改成：

> maximum sequence-length cap

即可。

---

# 三、最重要的是让 Codex 不要“修旧数据”

你的项目最容易被 Coding Agent 搞坏的地方，是它看到不一致之后自动去“修复” `results/raw`、preregistration、deviation history。

**绝对不要允许。**

下面这份 prompt 可以直接交给你本地 Codex。建议在你**最新论文所在本地分支**上执行，不要在远程旧 master 上做。

```text id="0mjjyv"
你正在维护仓库 mac-llm-bench。

目标：
对当前“最新论文分支”执行一次 evidence-preserving final correction，
修复源码、分析链、论文表述和公开复现链中的已确认问题，
但绝不能篡改历史实验事实。

====================
0. NON-NEGOTIABLE RULES
====================

1. 禁止修改任何历史实验原始证据：
   - results/raw/** 中的研究数值、stdout/stderr、result.json、step timing、
     system monitor 不得为了让结果更好看而修改。
   - research/preregistration.md 作为冻结 preregistration，不得回改定义。
   - 已登记 deviation 的历史正文不得静默重写。
   - 禁止生成 fake/mock/placeholder benchmark data。
   - 不得重新分类 SIGKILL 为 OOM，除非有直接 kernel evidence。

2. 若因隐私泄漏必须制作公开脱敏版本：
   - 不得声称脱敏版本是 byte-identical immutable raw；
   - 原始 raw 应保存在 git 外的私有 archive；
   - 创建 machine-readable release_sanitization_manifest，
     记录 original_sha256、sanitized_sha256、被脱敏字段名，
     但绝不记录敏感字段原值。
   - 所有隐私历史重写必须单独提交/记录。
   - 不要自动 force-push，先给我报告。

3. 所有历史数据缺陷用以下方式处理：
   historical raw truth
       -> processed correction/overlay
       -> deviation/limitation disclosure
       -> paper wording
   绝不能反向修改 raw 来匹配论文。

4. 每完成一项修改必须：
   - 给出文件路径与行号；
   - 给出测试/检查命令；
   - 粘贴真实输出；
   - 若未执行，不得写“verified/passed”。

5. 不要大规模重构。
   采用最小修改原则。
   不进行新的正式 benchmark，除非最后单独提出建议。

====================
1. FIRST: AUDIT BEFORE EDIT
====================

先不要改文件。

检查当前分支、HEAD、git status，并确认它确实包含最新 paper/main.tex
和最新 D12 analysis。

建立：
research/final_source_audit_20260921.md

逐项核实下面 S01-S42。
每项写：
- status: confirmed / already_fixed / not_applicable / needs_evidence
- exact evidence
- affected files
- affects existing numerical results? yes/no
- requires rerun? yes/no
- proposed minimal fix

不得仅根据本 prompt 相信问题存在，必须从本地源码/raw 独立验证。

====================
2. P0 PRIVACY
====================

检查全仓库和 git 全历史是否存在：
- provisioning_UDID
- serial number
- platform UUID
- crashReporterKey
- 用户 home path
- 其它 device-specific persistent identifiers

已知 environment.py 的 redaction allowlist/denylist 可能漏掉
provisioning_UDID。

修复 future collector：
src/benchmark/environment.py

新增 regression tests：
- 所有 sensitive hardware keys 必须变为 [REDACTED]
- nested dict/list 同样脱敏
- raw fallback regex 也应覆盖
- 不在测试 fixture 中写任何真实 identifier

对于已经公开的历史：
只生成 privacy remediation plan 和待执行命令。
不要自动 force-push。

====================
3. TRAINER SEMANTICS
====================

检查并修复/记录：

A. DATA ORDER
当前 trainer 是否：
order = list(range(len(samples)))
只有 epoch wrap 时才 rng.shuffle(order)。

如果是：
- 不修改历史结果；
- 明确历史 formal runs 使用 fixed initial sample order；
- 计算每种 formal config 在 max_steps × batch_size 下是否曾触发 epoch wrap；
- 输出 results/processed/data_order_audit.json；
- 论文把 “seed affects data order” 删除；
- 改成：
  “Seeds vary MLX/LoRA initialization; the historical formal runs used a
   fixed initial sample order because no run traversed the full 2,048-example
   training set before termination/completion.”
- future trainer 才可以按 dataset.shuffle 在 epoch 0 开始前 shuffle，
  但必须设置 protocol version bump，不能用新 trainer 回填旧 experiments。

B. DATASET SPLIT
独立审计 scripts/build_formal_dataset.py。

验证是否存在：
randomly choose 2080 -> sort by global_row -> split first 2048/last32。

如果确认：
- 不重建 formal_sft_v1；
- 输出 actual semantics；
- 将 MANIFEST 的历史错误作为 deviation，而不是悄悄改成“原本就这么设计”；
- 创建 research/dataset_split_audit.md；
- 说明 validation set 是 selected 2080 中按 source row 排序后的 tail 32；
- validation-loss results 只作 descriptive evidence。

C. OPTIMIZER
验证：
config declares AdamW
trainer instantiates mlx.optimizers.Adam

历史数据：
- effective optimizer = Adam
- declared optimizer = adamw

不要修改历史 config。
新增 processed/effective runtime overlay，例如：
results/processed/effective_runtime_config.csv/json
字段：
experiment_id
optimizer_declared
optimizer_effective
shuffle_declared
initial_shuffle_effective
scheduler_declared
scheduler_effective
gradient_accumulation_effective
source_evidence

论文 Methods 必须写 actual Adam。
deviation 表注明 schema/config mismatch。

D. EFFECTIVE CONFIG
不要继续把 input config 的 JSON copy 称为 runtime effective config。
未来 supervisor 中：
- declared_config.json / config.yaml
- resolved_runtime_config.json
语义分离。

历史 run 用 processed overlay，不修改 raw。

====================
4. CONTEXT AXIS
====================

从 raw step_timings 重新计算每个 context cell 的真实：
- input tokens per step = loss_bearing_tokens + 1
- n
- min
- max
- mean
- median
- p10/p90
- fraction hitting sequence cap

至少覆盖：
ctx512
ctx1024
ctx2048

输出：
results/processed/context_actual_lengths.json
paper/tables/table_context_actual_lengths.tex

验证目前大致现象，但必须以本地 raw 重算为准：
ctx512 ≈ mean 492
ctx1024 ≈ mean 916
ctx2048 ≈ mean 1215
且 ctx2048 只有极少数 step 达到2048。

然后全仓库搜索以下措辞：
“4× tokens”
“4x tokens”
“context length 2048”
“[2048,4096)”
“context binds first”
“context-length boundary”

统一语义：

sequence_length = maximum sequence-length cap，
不是每个 step 的固定 token count。

禁止把 ctx512→2048 解释成 actual token workload 精确4×。

将 “[2048,4096)” 改成类似：
“observed maximum-context bracket: the 2048-cap workload completed,
whereas the first 4096-cap single-seed synthetic probe failed before
the first optimizer step.”

明确：
- 4096/8192 为 synthetic single-seed probes；
- 不是统计估计出的物理 threshold；
- formal 与 probe evidence 不混写。

====================
5. BATCH-8 FAILURE PHASE
====================

核查 trainer execution order：

model load
-> LoRA setup
-> initial validation
-> reset peak
-> training loop

核查 formal-axis4-b8 的三个 stdout 是否为空，
以及初始 validation 是否使用 micro_batch_size=8。

如果确认：
不得继续声称现有数据证明“training step at batch8 caused SIGKILL”。

论文改成：
“All three micro-batch-8 benchmark runs terminated before completing
the first optimizer step.”

并注明：
“The historical instrumentation does not distinguish whether termination
occurred during the initial validation workload or immediately before the
training loop.”

如果要保留更强的 batch-training claim：
只提出 post-hoc instrumented rerun plan，不自动执行。

future trainer:
- 每 phase 开始前立即 flush phase marker；
- validation_start / validation_end；
- train_step_start；
- structured phase field；
- failed run 能确定 error_phase。

====================
6. FAILURE EVIDENCE STREAMING
====================

修 future trainer：

当前 step_timings.jsonl 如果是 loop 完成后一次性写，
改为每个 completed optimizer step：
append one JSON line + flush。

同时 training progress 写：
training_progress.jsonl

这样 SIGKILL/timeout 时保留 partial structured evidence。

不要回填历史 raw。

对历史失败 run：
建立 parser：
src/analysis/failure_progress.py

仅从 immutable stdout 解析：
observed_completed_steps
observed_step_time_min/max
last_observed_step
source_artifact
parse_status

写：
results/processed/failure_progress.json

不得把 parsed value 写回 result.json。

====================
7. MEMORY/TIMING MEASUREMENT SEMANTICS
====================

A. PEAK MEMORY

验证 reset_peak_memory 与 periodic validation 的相对位置。

如果 peak counter 在训练 loop 前 reset，
但 validation 在 loop 内执行，
则论文统一称：
“MLX allocator high-water mark during the measured training-loop workload,
including scheduled validation evaluations”
或其他精确措辞。

不要无依据说 optimizer-step-only peak。

B. VALIDATION

当前 validation 若调用 value_and_grad：
- future trainer 改为 default_loss forward-only path；
- 增加 test，证明 validation 不更新参数/optimizer state；
- 如果无法证明历史 lazy evaluation 是否 materialize gradients，
  只写 limitation，不猜。

C. SWAP-IN METRIC

将：
_swapin_per_step

重命名/别名为：
whole_run_swapin_mb_per_completed_step

定义必须明确：
(vm_stat_after.swapins - vm_stat_before.swapins)
* page_size
/ completed_steps

论文/table 不叫 “per-step paging rate”。
叫：
“whole-run system swap-in normalized by completed training steps”
或 “paging-intensity proxy”。

D. TIMESTAMP

future step records 同时保存：
wall_utc with microseconds
monotonic_ns_start
monotonic_ns_end

历史 D12 correlation：
加入 caveat：
historical step timestamps are second-resolution while system swap was
sampled at ~1 Hz.

重新检查 Spearman calculation：
不得给予超过采样分辨率的时间因果解释。

====================
8. ANALYSIS PIPELINE SINGLE SOURCE OF TRUTH
====================

这是重点。

目前检查：
scripts/run_analysis.py
src/analysis/summary.py
src/analysis/figures.py
src/analysis/revision_round1.py
最新 D12 modules

目标：
ONE analysis entry point produces every:
- processed JSON/CSV
- figure
- table
- paper-generated quantitative artifact

run_analysis.py 必须显式调用全部 generators。

消除 duplicated scaling fit。

目前检查 summary.py 是否用每 cell iloc[0] 拟合，
figures.py 是否用 cell mean 拟合。

若确认：
建立一个唯一 helper，例如：
build_scaling_series(...)
fit_scaling_from_group_means(...)

所有：
key_numbers
figures
hypothesis audit
tables
CI
都读取同一结果。

严禁出现两个不同 slope 但都称同一 analysis。

新增 test：
同一 quantity 在 key_numbers / fit JSON / figure source / table source
数值完全一致。

====================
9. PREREGISTRATION / HYPOTHESIS STATUS
====================

research/preregistration.md 不修改。

H2/H6：
保留 frozen/original v1 verdict，
另列 revised post-hoc v2 verdict。

输出 table：
hypothesis
frozen_rule
frozen_verdict
posthoc_rule
posthoc_verdict
reason_for_revision
revision_date

论文不能仅显示 Supported(v2) 而让人以为 preregistered rule 支持。

Practical definition：
原始 frozen：
Trainable AND P1 AND P2

后续 revised：
Trainable AND P2

论文必须并排展示：
frozen_practical
revised_operational_practical

主 confirmatory statement 优先引用 frozen definition。
revised definition 明确叫 post-hoc / sensitivity interpretation。

====================
10. VALIDITY / REPRODUCIBILITY AUDIT
====================

历史 raw 中 protocol_valid=false / performance_valid=false 不修改。

新增：
results/processed/final_validity_audit.csv

字段至少：
experiment_id
raw_protocol_valid
raw_performance_valid
final_disposition
included_in_aggregation
evidence_grade
manifest_verified
deviation_ids
reason
auditor_version

在 README 和 paper 说明：
raw validity flags were supervisor-v0 placeholders;
final analytical inclusion is represented by the immutable coverage/validity
audit, not by rewriting historical raw.

重写 scripts/audit_reproducibility.py 的语义：

不要要求所有 formal groups 必须 3/3 success。

根据 prereg matrix 与 deviation ledger 分为：
- expected complete-success cells
- boundary/failure cells
- stopped cells
- exploratory cells

Audit success 的含义是：
“observed evidence matches declared expected/disclosed disposition”
而不是“训练必须成功”。

最终 audit 应输出：
overall_status = PASS / PASS_WITH_DECLARED_WARNINGS / FAIL

manifest integrity warning 必须与实际机制一致。
统一以下文档的 counts/wording：
research/reproducibility_audit.*
coverage_report
deviations
paper appendix
README

删除 stale contradiction。

====================
11. GIT PROVENANCE
====================

扫描所有 aggregation-included runs：
- git_commit
- git_dirty
- git status paths

生成：
results/processed/git_provenance_audit.csv

明确：
clean
dirty_nonexecution_artifact_only
dirty_dependency_files
dirty_source_code
unknown

不得把所有 dirty 简单视作同等级。

对于 dirty pyproject.toml / uv.lock 且 git_patch=null：
论文限制中说明 exact dirty lockfile state was not preserved。

未来 supervisor：
dirty=true 时自动保存：
git_status.txt
git_diff.patch
git_diff_cached.patch
uv.lock SHA256
pyproject.toml SHA256

====================
12. HARDWARE COLLECTOR
====================

修 environment.py：

- 正确解析 system_profiler 真实键；
- 优先使用 sysctl hw.memsize 获得 bytes；
- system_profiler 只作辅助 metadata；
- GPU cores 如果无验证来源继续 null；
- 增加 fixture tests。

不要回填历史 raw unified_memory_bytes。
历史论文硬件值注明来源。

====================
13. PAPER CLAIM CORRECTIONS
====================

对最新 paper/main.tex 全文做 claim audit。

必须处理：

A. title/abstract
- 不说 universal “default answer”
- 8B 限定为 tested machine/software/window
- context 改 maximum-sequence-length cap
- seed 不说改变 data order

B. novelty
将宽泛：
“first measurements”
收窄为：
failure-inclusive feasibility/machine-state characterization on a single
16-GiB Apple M4 under the pinned MLX stack.

C. axis order
不要：
“context, then batch, then scale” 作为普适结论。

改成：
“In separate one-factor probes around the tested base configurations,
the first observed failures occurred along context-cap and micro-batch
axes before the tested model-scale ceiling.”

D. memory decomposition
stored/on-disk weight bytes 必须叫 proxy。
residual 不归因到具体 mechanism。

E. p99
叫 empirical p99；
小样本同时报告 p95/max 或明确近似 sample maximum。

F. 8B
固定措辞：
“completed all three preregistered seeds within one favorable observed
machine-state window.”

G. 14B
不得说 impossible/OOM/stable。
保持 boundary case。

H. Figure 8(c)
从真实 raw system_monitor 重生成。
自动测试：
- 三个 b8 trajectories 都被加载；
- 数据 max 与 caption 中的 max 一致；
- y limits 覆盖所有 plotted values；
- figure source data 输出 JSON/CSV；
- caption 数字从 source data 自动生成，不手写。

I. Figure 11
避免窄轴夸大 <2% rank effect；
优先用相对变化或显式 annotation。

J. metadata
PDF title/author 与正文完全一致。

====================
14. REGENERATION CONTRACT
====================

完成后必须做到：

1. 从 clean generated-output state 重新运行：
   uv run python scripts/run_analysis.py

2. 再运行：
   uv run python scripts/audit_reproducibility.py
   uv run python -m pytest tests/ -q

3. 编译 paper。

4. 验证：
   - 无 undefined refs/citations
   - 无 stale generated tables
   - 所有论文 quantitative claims 能回溯 processed source
   - processed source 能回溯 raw experiment IDs
   - 不存在 paper-only handwritten quantitative result
   - privacy scan 为 0 sensitive identifiers
   - raw research evidence 没有被静默修改

5. 输出：
research/final_release_audit_20260921.md

其中列出：
- changed files
- every issue S01-S42 status
- commands actually run
- verbatim PASS/FAIL output
- remaining limitations
- whether any numerical headline changed
- whether any rerun is still recommended

====================
15. COMMIT STRATEGY
====================

不要一次巨型 commit。

建议本地拆成：
1. audit-only
2. privacy/future collectors
3. historical semantic overlays
4. analysis single-source-of-truth
5. paper claim corrections
6. figure/table regeneration
7. final audit/release

在最终报告前不要 push、不要 force-push、不要创建 release/tag。

最后停下来向我汇报，不自动提交 arXiv。
```

## 四、我建议 Codex 修改时采用的判断原则

最关键的是把问题分成三种，不要让 Codex 混在一起：

**历史实验事实错误**不能“修数据”，只能修解释。例如 shuffle、Adam、dataset split、second-resolution timestamps、dirty runs，这些已经发生了，只能建立 correction/overlay。

**分析代码错误**可以重新从 raw 计算。例如 context actual token lengths、scaling fit 单一来源、Figure 8、audit semantics、table generation，这些应该真正修掉并全部重生。

**未来采集器缺陷**可以改源码，但不能让新源码 retroactively 改变旧 experiment 的含义。例如 step streaming、microsecond timestamps、git patch、phase markers、initial shuffle、hardware collection。

这三层分开以后，你这篇文章其实会更强，因为最后能够明确告诉 reviewer：

> historical evidence was preserved; implementation mismatches were not retroactively corrected; all corrections were applied at the analysis and reporting layers with machine-readable provenance.

---

## 五、我会怎么决定是否重新实验

在 Codex 完成上述修复后，先看 final audit。

如果 headline 数字仍然是：

```text id="6rkdv2"
4-bit memory ratio ≈ 0.54–0.73×
8B = 3/3 completed in one favorable window
14B = boundary / not sustained formally
4B BF16 = strong machine-state contrast
```

那就**不要再重跑大矩阵**。

最多补一个很小的 post-hoc batch8 phase experiment，然后明确标为 post-hoc validation，不纳入 preregistered main matrix。

真正需要优先解决的是 **S01 的公开隐私泄漏**。其次再让 Codex 做 S02–S42 的 audit/fix。完成这轮后，这个仓库才适合固定 `arxiv-v1` tag。
