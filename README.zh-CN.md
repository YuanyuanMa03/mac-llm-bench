# mac-llm-bench

[English](README.md) | 中文

在消费级 16 GB 统一内存 Apple Silicon Mac 上，对大语言模型微调（full / LoRA / QLoRA）进行可复现基准测试的研究仓库，基于 [MLX](https://ml-explore.github.io/mlx/) 与 MLX-LM 构建。

本仓库处于**研究进行中**状态。目前不存在任何 benchmark 数值——这是设计使然：将来出现在这里的每一个数字都必须能追溯到原始实验记录（见 [AGENTS.md](AGENTS.md)）。

## 研究问题

> 在固定的消费级 Apple Silicon 统一内存预算下，大语言模型训练与参数高效微调的真实可行边界在哪里？

项目要测绘的边界（见 [docs/repository_structure.md](docs/repository_structure.md)）：

```text
Loadable（可加载）→ Trainable（可训练）→ Practical（实用）→ Efficient（高效）
```

`success`、`oom`，以及（在可可靠测量时的）`严重 swap / 吞吐不可用` 都是同等重要的实验结果。OOM 运行是有效观测，永不删除。

计划的实验轴：模型规模（Qwen3-0.6B → 1.7B → 4B → …）、上下文长度、batch size、LoRA rank 扫描、full vs LoRA vs QLoRA、多随机种子重复。

## 当前状态

| 方面 | 状态 |
| --- | --- |
| 实验协议与结果 schema | ✅ 完成 — [docs/experiment_protocol.md](docs/experiment_protocol.md)、[docs/result_schema.md](docs/result_schema.md)（commit `6720bcb`） |
| 示例配置 | ✅ 完成 — [configs/experiment.example.yaml](configs/experiment.example.yaml) |
| Python 环境（uv 锁定） | ✅ 完成并验证 — [pyproject.toml](pyproject.toml) + [uv.lock](uv.lock) |
| Qwen3 模型下载 | ✅ 完成 — 4 个仓库，已按字节校验（见[模型](#模型)） |
| Experiment Supervisor | ✅ v0 已实现 — 8/8 测试通过，3 个验证运行见 [results/validation/supervisor-v0/](results/validation/supervisor-v0) |
| 训练运行 | 🔄 冒烟+校准+首个规模对比完成 — 0.6B vs 1.7B（各 3×100-step）：71.2ms → 161.2ms/步（2.27×），峰值 GPU 1.34 → 3.64 GB；更大模型与扫描待做 |
| Feasibility map、图表、论文 | ⬜ 未开始 |

## 硬件

- 目标平台：Apple Silicon Mac（arm64），16 GB 统一内存，macOS。
- 确切硬件元数据（芯片、核心数、内存）由协议**逐实验**采集记录；不从机器名称推断任何信息。

## 模型

Qwen3 系列，固定到 2026-08-31 经 Hub API 实际核验的 revision：

| 本地路径 | HF 仓库 | Revision | 磁盘体积 |
| --- | --- | --- | --- |
| `models/Qwen3-0.6B` | `Qwen/Qwen3-0.6B` | `c1899de289a0` | ≈1.52 GB |
| `models/Qwen3-1.7B` | `Qwen/Qwen3-1.7B` | `70d244cc86cc` | ≈4.08 GB |
| `models/Qwen3-0.6B-4bit` | `mlx-community/Qwen3-0.6B-4bit` | `73e3e38d9813` | ≈0.35 GB |
| `models/Qwen3-1.7B-4bit` | `mlx-community/Qwen3-1.7B-4bit` | `3b1b1768f8f8` | ≈0.98 GB |

`models/` 已加入 git-ignore。模型 revision 永远不从名称推断——来自真实 Hub 查询，并记录于 `models/MANIFEST.md`。

## 安装

需要 [uv](https://docs.astral.sh/uv/) 与 arm64 macOS 主机。

```bash
uv sync          # 创建 .venv 并按 uv.lock 精确安装
uv run python -c "import mlx.core as mx; print(mx.metal.is_available())"  # 自检
```

当前开发机的已验证环境（2026-08-31）：

| 组件 | 版本 |
| --- | --- |
| Python | CPython 3.13.11（uv 托管） |
| mlx | 0.32.2（Metal 可用） |
| mlx-lm | 0.31.3 |
| huggingface-hub | 1.29.0 |
| pyyaml | 6.0.3 |
| macOS | 26.5（arm64） |

## 使用方法

所有训练任务经由 Experiment Supervisor（`src/benchmark/`）启动：

```bash
uv run python scripts/run_experiment.py \
  --config configs/experiments/exp0_qwen3_0.6b_lora.yaml \
  [--timeout 3600] -- <精确命令 argv...>
```

Supervisor 负责验证配置、生成 experiment ID、采集环境 provenance（git、macOS、Python、MLX、硬件、运行前内存/swap）、监督子进程并完整保留 stdout/stderr、分类终态（`success` / `timeout` / `runtime_error` / …；OOM 仅在可可靠识别时记录），最后原子 finalize 出带 SHA-256 manifest 的不可变 raw result。失败同样产出完整结果——不丢弃任何观测。实验变量写在 `configs/experiments/` 的配置里，实验逻辑写在代码里。

## 实验结果

暂无。将来存在时：

```text
results/validation/   环境与模型 smoke test（非正式 benchmark）
results/raw/          不可变的原始记录，每个实验一个目录
results/processed/    由分析流水线重新生成
results/figures/      从原始结果程序化生成
```

论文图表将由 `src/analysis/` 从 `results/raw/` 生成——绝不手工填写。

## 可复现性政策

核心规则（完整清单见 [AGENTS.md](AGENTS.md)）：

1. 严禁伪造 benchmark 结果；严禁用估计值顶替缺失测量。
2. 所有报告的数字必须来自原始实验日志。
3. 实验结束后 raw result 不可修改；修正必须通过新实验。
4. 每个实验记录：git commit、模型与 revision、MLX/mlx-lm 版本、macOS 版本、硬件、训练方法、量化、batch size、序列长度、LoRA rank、种子、wall-clock 时间、峰值内存、吞吐、退出状态。
5. 失败/OOM 实验作为有效结果保留。
6. 缺失值为 `null`——绝不是 `0`，绝不估计。

## Prompt 台账

[PROMPT.md](PROMPT.md) 的自动镜像——标记区内请勿手工编辑。

<!-- prompt-log:begin: 由 scripts/prompt_log.py 自动生成，请勿手工编辑 -->
| Prompt | 日期 | 状态 | 提交 |
| --- | --- | --- | --- |
| [prompt01](PROMPT.md#prompt01) | 2026-08-30 | ✅ 已完成 | `6720bcb` |
| [prompt02](PROMPT.md#prompt02) | 2026-08-30 | ⬜ 未完成 | `bab6ac4`（补提交） |
| [prompt03](PROMPT.md#prompt03) | 2026-08-31 | ✅ 已完成 | `bab6ac4`（补提交） |
| [prompt04](PROMPT.md#prompt04) | 2026-08-31 | ✅ 已完成 | `d0e36d3` |
| [prompt05](PROMPT.md#prompt05) | 2026-08-31 | ✅ 已完成 | `f8f41f7` |
| [prompt06](PROMPT.md#prompt06) | 2026-09-01 | ✅ 已完成 | `a5cb5f2` |
| [prompt07](PROMPT.md#prompt07) | 2026-09-07 | ✅ 已完成 | `df008bf` |
| [prompt08](PROMPT.md#prompt08) | 2026-09-07 | ✅ 已完成 | `bb2a941` |
| [prompt09](PROMPT.md#prompt09) | 2026-09-07 | 🔄 进行中 | （进行中） |
<!-- prompt-log:end -->

## 文档

- [AGENTS.md](AGENTS.md) — 对 agent 与人类均有约束力的工作规范
- [docs/experiment_protocol.md](docs/experiment_protocol.md) — 每个实验必须记录什么；什么才算有效 benchmark
- [docs/result_schema.md](docs/result_schema.md) — 机器可读的结果结构（`null` 而非 `0` 原则）
- [docs/repository_structure.md](docs/repository_structure.md) — 目录职责与数据流
- [PROMPT.md](PROMPT.md) — 每条任务 prompt 及其结果的带日期记录
