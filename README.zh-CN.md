# mac-llm-bench

[English](README.md) | 中文

在消费级 16 GB 统一内存 Apple Silicon Mac 上，对大语言模型微调（full / LoRA / QLoRA）进行可复现基准测试的研究仓库，基于 [MLX](https://ml-explore.github.io/mlx/) 与 MLX-LM 构建。

> **隐私暂停（2026-09-21）**：历史 `raw_environment.txt` 对象含有未脱敏的
> 持久设备标识。在完成
> [research/privacy_remediation_plan_20260921.md](research/privacy_remediation_plan_20260921.md)
> 前应限制公开访问；不得把标识值复制进 issue 或 commit。

**实验已于 2026-09-15 冻结（`freeze-04f90a840b8ea8fb`）**：118 个 finalized 原始实验，预注册 formal 矩阵执行至声明的停止点（偏离 D1–D8 全部登记于 [research/deviations.md](research/deviations.md)）；论文中每个数字都经 [research/claim_ledger.csv](research/claim_ledger.csv) 追溯到原始记录。

## 研究问题

> 在固定的消费级 Apple Silicon 统一内存预算下，大语言模型训练与参数高效微调的真实可行边界在哪里？

项目要测绘的边界（见 [docs/repository_structure.md](docs/repository_structure.md)）：

```text
Loadable（可加载）→ Trainable（可训练）→ Practical（实用）→ Efficient（高效）
```

`success`、`oom`，以及（在可可靠测量时的）`严重 swap / 吞吐不可用` 都是同等重要的实验结果。OOM 运行是有效观测，永不删除。

## 主要结论（来自冻结数据集）

- **最高可复现训练配置**：8B 4-bit QLoRA（3/3 formal seeds）；14B 4-bit 作为 *system-state-dependent boundary case*（D8）报告，不作为已完成的 formal 格。
- 4-bit QLoRA 在全部配对规模上将峰值内存降至 BF16 的 0.54–0.73×，步时比值落在预注册 ±25% 等价边距内。
- 内存随模型规模**次线性**增长（log-log slope 0.57，固定开销稀释）；步时近似线性（slope 1.00）。
- 在相互独立的单因素探针中，2048 最大序列长度 cap 的 workload 完成，而首个 4096-cap 单 seed synthetic probe 失败；micro-batch 4 完成，batch 8 则在完成首个 optimizer step 前终止。
- 可训练性是模型×系统驻留状态的联合属性（D1/D3/D7/D8 案例链）。

## 最小复现

```bash
uv sync                                   # 锁定环境（Python 3.13, mlx 0.32.2）
uv run python -m pytest tests/ -q
uv run python scripts/run_analysis.py     # 从冻结 raw 一键重建全部派生产物
# 论文 LaTeX 源码有意不入库：生成的表格/图表写入 git-ignored 的
# paper/submission/ 供维护者本地编译；论文经 arXiv 发布
```

模型权重不入库（git-ignored），revision 锚定见 `models/MANIFEST.md`。

## 当前状态

| 方面 | 状态 |
| --- | --- |
| 实验协议与结果 schema | ✅ 完成 — [docs/experiment_protocol.md](docs/experiment_protocol.md)、[docs/result_schema.md](docs/result_schema.md)（commit `6720bcb`） |
| 示例配置 | ✅ 完成 — [configs/experiment.example.yaml](configs/experiment.example.yaml) |
| Python 环境（uv 锁定） | ✅ 完成并验证 — [pyproject.toml](pyproject.toml) + [uv.lock](uv.lock) |
| Qwen3 模型下载 | ✅ 完成 — 4 个仓库，已按字节校验（见[模型](#模型)） |
| Experiment Supervisor | ✅ future protocol v0.2 已修复 privacy/phase/streaming/provenance 采集；历史 v0 raw 保持不变 |
| 冻结实验 | ✅ 118 个 finalized runs；coverage 118=118；失败同样保留 |
| Feasibility map、图表、论文 | ✅ 一键重建；复现审计为 `PASS_WITH_DECLARED_WARNINGS` |

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
| `models/Qwen3-4B` | `Qwen/Qwen3-4B` | `1cfa9a720891` | ≈8.05 GB |
| `models/Qwen3-4B-4bit` | `mlx-community/Qwen3-4B-4bit` | `4dcb3d101c2a` | ≈2.26 GB |
| `models/Qwen3-8B-4bit` | `mlx-community/Qwen3-8B-4bit` | `545dc4251c05` | ≈4.61 GB |
| `models/Qwen3-14B-4bit` | `mlx-community/Qwen3-14B-4bit` | `a4d9b2df59d2` | ≈8.31 GB |

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
| [prompt09](PROMPT.md#prompt09) | 2026-09-07 | ✅ 已完成 | `099092c` |
| [prompt10](PROMPT.md#prompt10) | 2026-09-07 | ✅ 已完成 | `72cc3ca` |
| [prompt11](PROMPT.md#prompt11) | 2026-09-07 | ✅ 已完成 | `44c05bf` |
| [prompt12](PROMPT.md#prompt12) | 2026-09-07 | ✅ 已完成 | `6ef789f` |
| [prompt13](PROMPT.md#prompt13) | 2026-09-07 | ✅ 已完成 | `29a18b6` |
| [prompt14](PROMPT.md#prompt14) | 2026-09-07 | ✅ 已完成 | `23dd83d` |
| [prompt15](PROMPT.md#prompt15) | 2026-09-11 | ✅ 已完成 | `8db9c13` 等 |
| [prompt16](PROMPT.md#prompt16) | 2026-09-12→16 | ✅ 已完成 | `877db81`→`b398076` |
| [prompt17](PROMPT.md#prompt17) | 2026-09-16 | ✅ 已完成 | `5c8675d`→ |
| [prompt18](PROMPT.md#prompt18) | 2026-09-21 | ✅ 已完成 | `044566c` |
| [prompt19](PROMPT.md#prompt19) | 2026-09-21 | ✅ 已完成 | `b0cfa33` |
<!-- prompt-log:end -->

## 文档

- [AGENTS.md](AGENTS.md) — 对 agent 与人类均有约束力的工作规范
- [docs/experiment_protocol.md](docs/experiment_protocol.md) — 每个实验必须记录什么；什么才算有效 benchmark
- [docs/result_schema.md](docs/result_schema.md) — 机器可读的结果结构（`null` 而非 `0` 原则）
- [docs/repository_structure.md](docs/repository_structure.md) — 目录职责与数据流
- [PROMPT.md](PROMPT.md) — 每条任务 prompt 及其结果的带日期记录
