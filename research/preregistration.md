# Pre-registration — Formal Benchmark (mac-llm-bench)

冻结日期：2026-09-11（本文件所在 commit 即冻结 commit；正式 benchmark 数据采集
开始于其后的 commit）。冻结后**不得**为迎合结果修改定义；如需偏离，必须在
论文中作为 deviation 如实报告，并在 `research/` 下以新文件记录修订。

研究问题（冻结）：

> Under a fixed consumer-grade 16 GB Apple Silicon unified-memory budget, what is
> the real feasibility boundary for LLM fine-tuning, and how does quantization
> change that boundary?

RQ1 规模↑时 BF16 LoRA vs 4bit QLoRA 的内存/步时/吞吐如何变化；
RQ2 4bit 把 Trainable 边界推多远；RQ3 context 边界在哪里；
RQ4 量化的内存收益是否伴随可测的时间代价；RQ5 "能启动" 与 "实用微调" 的差距。

---

## 1. Hardware（冻结）

Apple Mac mini（model_identifier 见 raw evidence `system_profiler`），
Apple M4，统一内存 17,179,869,184 B（16 GiB），10 物理 / 10 逻辑 CPU 核，
GPU 核心数未采集（无已验证来源）。macOS 26.5 (25F71)。
环境：uv 管理的 .venv，Python 3.13.11，mlx 0.32.2，mlx-lm 0.31.3。
软件版本如有升级，Upgrade 必须作为 deviation 记录并在同轴比较内保持一致。

隔离规则沿用 `docs/experiment_protocol.md` §5：单训练任务、AC 电源、
运行前后记录 swap/memory/power、`caffeinate -is` 防睡眠、禁 sudo/reboot。

## 2. Models（冻结）

沿用已哈希锚定的 Qwen3 家族（`models/MANIFEST.md`）：

| 用途 | 仓库 | revision |
| --- | --- | --- |
| BF16 LoRA / Full FT | Qwen/Qwen3-0.6B | `c1899de289a0…` |
| BF16 LoRA / Full FT | Qwen/Qwen3-1.7B | `70d244cc86cc…` |
| BF16 LoRA | Qwen/Qwen3-4B | `1cfa9a720891…` |
| BF16 边界探针（待获取） | Qwen/Qwen3-8B | 下载时实查并锚定 |
| 4bit QLoRA | mlx-community/Qwen3-{0.6B,1.7B,4B,8B,14B}-4bit | `73e3e38d… / 3b1b1768… / 4dcb3d10… / 545dc425… / a4d9b2df…` |

- 不中途更换模型家族；这些是 **instruct/chat 通用模型而非 Base** 模型，
  论文如实说明（训练目标是 LM loss，不代表 instruction-following 评测）。
- 参数量以训练进程内 `sum(array.size)` 实测为准（4bit 为打包存储元素口径，
  跨精度比较时以 BF16 版本参数量为准并注明）。

## 3. Methods（冻结）

- **BF16 LoRA**：rank 8 / alpha 16 / dropout 0 / target = q,k,v,o_proj；
- **4bit QLoRA**：同 LoRA 配置，权重为预量化 4bit（group 64）；
- **Full FT（探索性）**：仅 0.6B（唯一有先验可行性证据的最小模型），
  用于锚定 "PEFT 是否在小模型上仍是必要权衡"。
- 8B/14B 不跑 BF16 formal：8B BF16 仅做边界探针（预期 load/训练即失败）；
  14B BF16 权重体积已超物理内存，不做（declared out-of-budget，非观测）。

## 4. Fixed training controls（冻结）

| 控制项 | 值 |
| --- | --- |
| dataset | `data/formal_sft_v1/`（Phase 4 冻结；ultrachat_200k 固定子集 + MANIFEST + SHA256SUMS） |
| preprocessing | Qwen3 chat template（家族共享），tokenize 后截断至 sequence_length；loss = 全 token LM loss（default_loss，lengths=[0,len]），无 prompt masking（声明并统一） |
| optimizer | AdamW（mlx Adam），lr 1e-4，constant scheduler，warmup 0 |
| batch | micro 1 × grad-accum 1（除 batch-sensitivity 轴外） |
| steps/seed | 主矩阵 100 步；ctx 轴 20 步；4B 配对深潜 300 步；seeds {42, 123, 2026} |
| warmup exclusion | 100 步 → excluded_warmup_steps=5；20 步 → 2；300 步 → 10（预先声明） |
| 监控 | `sample_swap: true`（1 s cadence）+ before/after 快照；指标口径按 docs/measurement_validation.md §3 |
| 配置一致性 | 同一比较组内除声明变量外所有配置字段逐项相等（由 analysis pipeline 校验） |

seed 语义：`mx.random.seed(seed)` + python `random.Random(seed)`（影响数据循环顺序与
LoRA 初始化；dropout=0）。3 个 seed = 3 次独立重复，用于 mean±SD。

## 5. Operational definitions（冻结，机械可执行）

- **Loadable**：训练进程日志显示模型权重加载完成（`mlx_lm.load` 返回）。
  从 raw stdout/training_metrics 读取，无论后续成败。
- **Trainable**：`terminal_state == "success"` 且
  `successful_steps == requested_steps` 且 signal 为空。
  （即：完成全部预定优化器步，无 SIGKILL/timeout/异常退出。）
- **Practical**：Trainable 且同时满足
  (P1) 采样峰值 swap ≤ 运行前 swap + 4 GiB；且
  (P2) median step time ≤ 10 s/step。
  依据：(P2) 在 b1-ga1、≈512 loss-bearing tokens/步 下对应单 Mtoken 训练
  ≤ ~3 小时量级，超过即偏离消费设备的可用性；(P1) 以系统 swap 增长限制
  工作集越界程度。两阈值在看到 formal 数据前冻结；论文报告阈值 ±2× 的
  敏感性（结论若随阈值翻转必须如实呈现）。
- **Efficient**（探索性，非 confirmatory）：Practical 且 measured tokens/s ≥ 100。
- **OOM**：不使用（无已验证识别器）。SIGKILL/exit 137 归入 failure taxonomy
  的 `SIGKILL-consistent`，不自动等同 OOM。
- **Probe vs Formal**：`formal_or_probe` 字段区分；probe 仅用于边界发现与
  矩阵设计，不进入主图表的统计聚合；formal = 本预注册矩阵内的运行。

## 6. Equivalence margin（RQ4，冻结）

"4bit 相对 BF16 无实质时间代价" 的判定：配对同配置下
`median_step_time(4bit) / median_step_time(bf16) ∈ [0.80, 1.25]`
→ 称 **practically equivalent timing**（预冻结 ±25% 边距）。
依据：同配置重复间 step-time CV 实测 ≈2–3%（0.6B/1.7B 校准三连），
±25% 远高于测量噪声，同时代表工程上有意义的差异界。
内存不做等价性声明，直接报告配对比值（内存是效果本体）。
论文措辞按预注册：区间内 → "no practically meaningful difference under the
preregistered ±25% margin"；区间外 → 如实描述方向与幅度。禁用 "zero-cost"。

## 7. Formal matrix（冻结）

轴 1 主矩阵（ctx512，100 步，3 seeds，`excluded_warmup=5`）：

| 模型 | 0.6B | 1.7B | 4B | 8B | 14B |
| --- | --- | --- | --- | --- | --- |
| BF16 LoRA | ✅ | ✅ | ✅ | 边界探针 | —（out-of-budget） |
| 4bit QLoRA | ✅ | ✅ | ✅ | ✅ | ✅ |
| Full FT | ✅（探索） | — | — | — | — |

轴 2 context（4B-4bit QLoRA，20 步，3 seeds，`excluded_warmup=2`）：
ctx ∈ {1024, 2048}；ctx512 复用轴 1；4096/8192 已有 probe 失败证据
（ctx4096 与 ctx8192 SIGKILL，见 results/raw/20260911… 与 20260907T1118…），
不重复。补充 1 次单点边界探针：14B-4bit ctx2048（20 步，seed42）。

轴 3 rank（4B-4bit QLoRA，ctx512，20 步，3 seeds）：rank ∈ {4, 8, 32}（r8 复用轴 1）。

轴 4 batch（4B-4bit QLoRA，ctx512，20 步，3 seeds）：micro-batch ∈ {1, 2, 4, 8}
（b1 复用轴 1；其余 loss-bearing tokens/步 相应放大，吞吐按 tokens 口径比较）。

轴 1b 配对深潜（4B，300 步，3 seeds，`excluded_warmup=10`）：
BF16 LoRA vs 4bit QLoRA，用于收敛轨迹对比（Phase 6），每 50 步记录 val loss。

预计机器时间（按探针步时推算）：轴 1 ≈30 min；轴 1b ≈6 min；轴 2 ≈1.2 h
（ctx2048 3×20×53.9s ≈ 54 min 主导）；轴 3 ≈10 min；轴 4 ≈30 min；
探针 ≈30 min。合计 ≈3–4 h，符合 machine-time policy。

## 8. Repetitions / validity（冻结）

- 主比较（轴 1 全部单元、轴 2 ctx2048、RQ4 配对）≥3 独立重复（3 seeds）；
- 每个 formal run 经 Supervisor v0.2（含 swap 采样器）+ manifest 校验 +
  Phase 7 的一致性审计（steps/公式/时间戳/哈希）后才计入 processed 数据；
- warmup 标记 excluded_warmup_steps，不入 timing 汇总；
- 失败/OOM/SIGKILL 原样保留并进入 failure taxonomy（Phase 9）；
- 禁止事后剔除不利重复；如需排除，必须记录不可变 exclusion-reason。

## 9. Analysis plan（冻结）

- 聚合：每单元报告 3 runs 全部点值 + mean ± SD；n=3 的 95% CI（t 分布，
  t₂,0.975=4.303）如实呈现为宽区间，不假装精确；
- Scaling fit：log-log 最小二乘 `memory ~ params`、`step_time ~ params`，
  报告 slope / R² / n / 残差图；仅当数据形态支持才使用 "approximately
  linear（in log-log）" 类措辞；不宣称 scaling law；
- RQ4：按 §6 边距做配对比值 + 每对差值的 SD；
- 边界：Trainable 边界报告为区间（如 [2048, 4096)），
  附 preflight 可比性说明与 confounder（swap before）记录；
- 所有数字从 raw results 经 `src/analysis/` 程序化生成，可一键重算。

## 10. 已知局限（冻结时点声明）

- 单机单卡（M4 16GB），结果不外推到其他芯片/内存；
- 20-step ctx 轴样本量限制步时分布刻画（但 3 seeds × 20 步 = 60 步样本）；
- loss 全 token 计（无 prompt masking），训练质量结论仅限此目标；
- swap 指标为系统级（含后台进程贡献）；机器长期驻留 baseline swap
  （审计时点 ≈4.6 GiB），比较使用 Δ 而非绝对值；
- MLX peak memory 口径见 docs/measurement_validation.md §2B。
