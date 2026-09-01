# Repository Structure

本仓库用于研究和评估 **Apple Silicon 消费级设备上的大语言模型训练与参数高效微调能力**。

当前主要实验平台为 Apple Silicon Mac，实验框架以 MLX / MLX-LM 为核心。

项目的设计原则是：

* 实验配置与实验代码分离
* 原始实验数据不可修改
* 成功、OOM 和失败实验均保留
* 所有论文结果必须能够追溯到原始实验记录
* 不使用人工填写的 benchmark 数值
* 环境、模型、数据集和 Git revision 均需要记录
* validation、raw results、processed results 和 figures 严格分离

---

# 1. Repository Overview

```text
mac-llm-bench/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── uv.lock
├── .gitignore
│
├── configs/
│   ├── experiment.example.yaml
│   ├── models/
│   └── experiments/
│
├── docs/
│   ├── experiment_protocol.md
│   ├── result_schema.md
│   └── repository_structure.md
│
├── src/
│   ├── train/
│   ├── monitor/
│   ├── benchmark/
│   └── analysis/
│
├── scripts/
│   └── run_experiment.py
│
├── results/
│   ├── validation/
│   ├── raw/
│   ├── processed/
│   └── figures/
│
├── tests/
│
└── paper/
    ├── figures/
    └── tables/
```

> 注意：以上结构包含当前已经规划好的目录以及后续实验阶段预留目录。某些文件和模块可能尚未实现。

---

# 2. Root Files

## `AGENTS.md`

Codex 等 Coding Agent 的项目级工作规范。

主要负责约束：

* 禁止伪造实验数据
* 禁止使用未经执行的结果
* 实验必须具有可复现性
* raw result 不允许直接修改
* 所有实验必须保存环境和 Git provenance
* OOM / failure 必须作为实验结果保留
* 论文中的数字必须能够回溯到原始实验数据

该文件是 Agent 在仓库中工作的最高优先级项目规范之一。

---

## `README.md`

项目主页。

两个 README 各含一个自动镜像节（`prompt-log:begin/end` 标记内），
由 `scripts/prompt_log.py sync` 从 PROMPT.md 生成，禁止手工编辑；
其余部分（含语义状态表）手工维护。

后续主要包含：

* 项目简介
* Research Questions
* 支持的硬件
* 支持的模型
* 安装方法
* Benchmark 使用方法
* 实验结果
* Feasibility Map
* 数据集与论文链接
* Reproducibility Instructions

README 面向项目用户和外部研究者。

---

## `pyproject.toml`

Python 项目配置和依赖声明。

预计管理：

```text
Python
MLX
mlx-lm
huggingface_hub
PyYAML
数据分析相关依赖
测试依赖
```

项目优先使用 `uv` 管理 Python 环境和依赖。

---

## `uv.lock`

由 `uv` 生成的依赖锁文件。

用于固定：

* 精确依赖版本
* transitive dependencies
* 可复现 Python 环境

正式实验应尽可能基于固定的 lock file 运行。

---

# 3. `configs/`

实验配置目录。

原则：

> 实验逻辑写在代码中，实验变量写在配置中。

这样可以避免为了修改一个 context length 或 LoRA rank 就修改训练代码。

---

## `configs/experiment.example.yaml`

实验配置模板。

用于描述一个实验应该包含哪些字段，例如：

```yaml
experiment:

model:

dataset:

training:

monitoring:

output:
```

该文件主要用于说明 schema，不应该包含伪造的 benchmark 数据。

---

## `configs/models/`

后续保存不同模型的固定配置。

例如：

```text
configs/models/
├── qwen3-0.6b-base.yaml
├── qwen3-1.7b-base.yaml
├── qwen3-4b-base.yaml
└── ...
```

模型配置主要描述：

* Hugging Face model ID
* revision
* architecture
* dtype
* quantization
* tokenizer
* model metadata

模型 revision 应来自实际查询结果，不应该仅根据模型名称推断。

---

## `configs/experiments/`

保存正式实验配置。

例如：

```text
configs/experiments/
├── exp0_qwen3_0.6b_lora.yaml
├── model_scaling/
├── context_scaling/
├── lora_rank/
└── qlora/
```

后续每一个正式实验都应该能够通过配置文件完整复现。

---

# 4. `docs/`

研究协议和项目设计文档。

这部分主要回答：

> 我们为什么这样做，以及实验应该怎样做。

---

## `docs/experiment_protocol.md`

实验协议。

定义正式 benchmark 的实验规则，例如：

* 环境要求
* hardware metadata
* software metadata
* model metadata
* dataset metadata
* training configuration
* runtime metrics
* failure classification
* benchmark isolation
* warm-up policy
* repeated runs
* raw-result immutability

该文件决定什么样的实验可以被认为是有效 benchmark。

---

## `docs/result_schema.md`

定义实验结果的数据结构。

主要描述：

```text
experiment
hardware
software
model
dataset
training
runtime
metrics
status
artifacts
```

并明确：

```text
missing != 0
unknown != 0
failed measurement != 0
```

无法获得的数据使用：

```json
null
```

而不是人工估计。

---

## `docs/repository_structure.md`

即当前文件。

用于说明整个仓库：

* 每个目录的职责
* 数据如何流动
* 哪些文件允许修改
* 哪些数据属于正式实验结果

---

# 5. `src/`

核心 Python 实现。

原则：

> `src/` 中放可复用模块，`scripts/` 中放命令行入口。

---

# 5.1 `src/train/`

训练相关代码。

后续可能包含：

```text
src/train/
├── lora.py
├── qlora.py
├── full_finetune.py
└── common.py
```

主要负责：

* MLX model loading
* LoRA
* QLoRA
* Full Fine-Tuning
* training configuration
* checkpoint / adapter handling

训练代码本身不负责生成论文数据表。

---

# 5.2 `src/monitor/`

macOS / Apple Silicon 系统监控。

后续可能负责采集：

* process memory
* system memory
* swap
* page faults
* thermal information
* energy information

注意：

只有经过验证的 measurement 才允许进入正式论文指标。

目前无法可靠获取的指标应保持：

```text
null
```

同时保留原始 measurement evidence。

---

# 5.3 `src/benchmark/`

Benchmark 的核心控制层。

预计负责：

```text
配置
 ↓
preflight
 ↓
environment metadata
 ↓
experiment process
 ↓
monitoring
 ↓
status classification
 ↓
raw result
```

后续 Experiment Supervisor / Runner 应主要位于该模块。

可能包含：

```text
src/benchmark/
├── environment.py
├── experiment.py
├── supervisor.py
├── schema.py
├── ids.py
└── artifacts.py
```

具体文件应根据实现过程确定，不提前假设已经存在。

---

# 5.4 `src/analysis/`

实验完成后的数据分析。

该目录只能读取：

```text
results/raw/
```

不能修改 raw results。

后续负责：

* flatten JSON
* aggregate runs
* statistics
* confidence intervals
* failure analysis
* feasibility boundary
* table generation
* figure data preparation

---

# 6. `scripts/`

用户直接运行的 CLI / command entrypoint。

例如：

```text
scripts/run_experiment.py
scripts/prompt_log.py
```

`scripts/prompt_log.py` 是正式任务 prompt 的台账 harness（已实现，含测试）：

```text
begin   登记正式 prompt：原文逐字入账 + 元数据表加行 + 提交
finish  终结：状态/产出（须附真实验证 evidence）+ 任务全部产出一次提交
sync    重建两个 README 中的自动镜像节（--check 核对漂移，--init 首次插入）
```

规则见 `.claude/skills/prompt-log/SKILL.md`；元数据表与镜像节不允许手工编辑。

后续可能增加：

```text
scripts/validate_environment.py
scripts/run_sweep.py
scripts/analyze_results.py
```

原则是：

> scripts 尽量薄，核心逻辑放在 `src/`。

例如：

```bash
uv run python scripts/run_experiment.py \
  --config configs/experiments/exp0_qwen3_0.6b_lora.yaml
```

---

# 7. `results/`

实验数据目录。

这是整个项目中最重要的目录之一。

数据流应该严格遵循：

```text
Validation
     │
     ▼
results/validation/

Formal Experiment
     │
     ▼
results/raw/
     │
     ▼
analysis
     │
     ▼
results/processed/
     │
     ▼
results/figures/
```

---

# 7.1 `results/validation/`

保存环境验证和 smoke test。

例如：

```text
results/validation/
├── environment/
└── model/
```

包括：

* Python environment
* MLX environment
* model download
* model revision
* tokenizer load
* model load
* inference smoke test

这里的数据：

> 不属于正式 benchmark。

---

# 7.2 `results/raw/`

正式实验原始数据。

这是项目最严格保护的目录。

原则：

> Raw results are immutable.

每个实验应该具有独立目录，例如：

```text
results/raw/
└── qwen3-0.6b_lora_ctx512_b1_r8_seed42_.../
    ├── result.json
    ├── config.yaml
    ├── stdout.log
    ├── stderr.log
    ├── environment.json
    ├── command.txt
    └── manifest.sha256
```

具体结构以后以 Experiment Supervisor 实际实现为准。

成功、OOM 和 runtime failure 都应该保留。

禁止因为实验失败而删除结果。

---

# 7.3 `results/processed/`

由 analysis pipeline 自动生成。

例如：

```text
results/processed/
├── experiments.csv
├── steps.parquet
├── feasibility.csv
└── summary.csv
```

这里的数据允许重新生成。

任何 processed result 都必须能够追溯到：

```text
results/raw/
```

---

# 7.4 `results/figures/`

自动生成的 benchmark 图。

例如后续可能包含：

```text
model_scaling.pdf
context_scaling.pdf
memory_boundary.pdf
throughput.pdf
feasibility_map.pdf
```

论文 Figure 不允许手工填写 benchmark 数字。

正确流程：

```text
raw JSON
   ↓
analysis code
   ↓
processed data
   ↓
figure
```

---

# 8. `tests/`

自动化测试。

现有：

```text
tests/test_prompt_log.py   台账 harness（begin/finish/sync，临时 git 仓库集成测试）
tests/test_supervisor.py   Experiment Supervisor v0（配置验证/ID/provenance/子进程/manifest/防覆盖）
```

主要验证：

* config parsing
* result schema
* experiment ID
* JSON serialization
* metadata collection
* failure handling
* subprocess supervisor
* result finalization
* hash manifest

注意：

测试可以使用 mock 验证软件行为。

但是：

> mock 数据不能作为研究 benchmark 数据。

---

# 9. `paper/`

论文相关资源。

```text
paper/
├── figures/
└── tables/
```

后续可能扩展为：

```text
paper/
├── main.tex
├── references.bib
├── sections/
├── figures/
└── tables/
```

论文中的 Table / Figure 应尽可能通过 analysis pipeline 自动生成。

例如：

```text
results/raw
    ↓
src/analysis
    ↓
paper/tables/table_2.tex
```

这样可以避免论文里的数字和真实实验结果不一致。

---

# 10. Experiment Data Flow

整个实验的数据流设计如下：

```text
Experiment YAML
      │
      ▼
Configuration Validation
      │
      ▼
Environment Collection
      │
      ▼
Experiment Supervisor
      │
      ├───────────────┐
      ▼               ▼
Training Process    Monitoring
      │               │
      └───────┬───────┘
              ▼
        Runtime Evidence
              │
              ▼
          result.json
              │
              ▼
        results/raw/
              │
              ▼
       Analysis Pipeline
              │
              ▼
      results/processed/
              │
        ┌─────┴─────┐
        ▼           ▼
     Figures       Tables
        │           │
        └─────┬─────┘
              ▼
            Paper
```

---

# 11. Planned Experiment Progression

当前研究计划按逐步扩大实验规模的方式进行。

```text
Stage 0
Repository + Protocol
        │
        ▼
Stage 1
Environment Validation
        │
        ▼
Qwen3-0.6B-Base
Model Load Test
        │
        ▼
Experiment 0
20-step LoRA Smoke Test
        │
        ▼
Calibration
100-step / short runs
        │
        ▼
Model Scaling
0.6B → 1.7B → 4B → 8B → larger models
        │
        ▼
Context Scaling
        │
        ▼
LoRA / QLoRA / Full FT
        │
        ▼
Memory Boundary
        │
        ▼
Downstream Evaluation
        │
        ▼
Statistical Analysis
        │
        ▼
Paper
```

其中模型规模和实际实验配置只有在前一级实验验证通过后才继续扩大。

---

# 12. Core Research Artifact

本仓库最终不仅需要产生训练代码。

真正的核心研究资产是：

```text
Reproducible Experiment Framework
             +
Apple Silicon Measurements
             +
Fine-Tuning Feasibility Boundary
             +
Raw Benchmark Dataset
             +
Analysis Pipeline
             +
Research Paper
```

核心研究问题可以概括为：

> 在固定的消费级 Apple Silicon 统一内存预算下，大语言模型训练和参数高效微调能够达到怎样的可行边界？

因此：

```text
success
```

是实验结果。

```text
OOM
```

同样是实验结果。

```text
severe swap / impractical throughput
```

如果能够可靠测量，同样属于实验结果。

项目目标不是强迫所有模型成功训练，而是通过可复现实验确定：

```text
Loadable
   ↓
Trainable
   ↓
Practical
   ↓
Efficient
```

之间的真实边界。
