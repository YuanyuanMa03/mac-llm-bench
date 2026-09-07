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
| [prompt10](#prompt10) | 2026-09-07 | 进行中 | （进行中） | 待补 |

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
