# Current state（Phase 0 审计产出）

> 本文只陈述可由仓库 evidence 支持的事实。每条事实给出可定位来源。
> 推断与事实明确分开；推断一律标注 [推断]。
> 生成日期：2026-09-11。审计人：ZCode agent（prompt15 会话）。

## 1. 审计结论总览

- `results/raw/` 共 **19 个实验目录**，全部含 finalized `result.json`。
- **19/19 manifest SHA-256 校验通过**（`scripts/build_evidence_ledger.py` 逐文件复算，
  2026-09-11 运行，输出见 `research/evidence_ledger.csv` 的 `manifest_verified` 列）。
- 19/19 含完整 git commit；9 个 `git_dirty=true`（prompt06–09 早期运行），
  10 个 clean。无 manifest 不一致项，**无需停用任何实验**。
- 测试套件 `uv run python -m pytest tests/ -q`：**24 passed**（2026-09-11 实际运行）。
- 软件环境（实机查询）：macOS 26.5 (25F71)、Python 3.13.11（uv .venv）、
  mlx 0.32.2、mlx-lm 0.31.3、Apple M4、17179869184 B 统一内存、10 CPU 核。
- prompt14（ctx 边界探针）**未闭环**：ctx2048 与 ctx8192 两个 raw result 已 finalize
  但未提交（当时 `git status` untracked）；无 processed 对比分析；台账状态"进行中"。

## 2. 硬件与机器状态（审计时点）

| 项 | 值 | 来源 |
| --- | --- | --- |
| 芯片 | Apple M4 | `sysctl machdep.cpu.brand_string` |
| 统一内存 | 17,179,869,184 B（16 GiB） | `sysctl hw.memsize` |
| CPU 核 | 10 物理 / 10 逻辑 | `sysctl hw.physicalcpu/hw.logicalcpu` |
| GPU 核 | 未采集（无已验证来源键） | `src/benchmark/environment.py` 设计如此 |
| 磁盘 | <repo-volume> 已用 11%，可用 ≈613 GB（df -kP 1024B 块） | 2026-09-11 查询 |
| 当前 swap | used = 4846.50 MB（2026-09-11 查询；系统长期驻留 swap，非本次实验污染） | `sysctl vm.swapusage` |

注意：本机 `system_profiler` 的 GPU 核心数与 thermal/energy 均无已验证采集路径，
所有 raw result 中对应字段为 `null`/`unresolved`（协议 §4 的既定决定，非遗漏）。

## 3. 模型清单（models/MANIFEST.md + raw result resolved_revision 交叉核对）

8 个本地仓库，revision 均为 Hub API 实查并逐文件哈希锚定；与 raw result 中
`model.resolved_revision`（来自训练时本地缓存/sidecar 读取）一致：

| 模型 | revision（短） | BF16 磁盘 |
| --- | --- | --- |
| Qwen/Qwen3-0.6B | `c1899de289a0` | 1.503 GB |
| Qwen/Qwen3-1.7B | `70d244cc86cc` | 4.064 GB |
| Qwen/Qwen3-4B | `1cfa9a720891` | 8.045 GB |
| mlx-community/Qwen3-0.6B-4bit | `73e3e38d9813` | 0.335 GB |
| mlx-community/Qwen3-1.7B-4bit | `3b1b1768f8f8` | 0.968 GB |
| mlx-community/Qwen3-4B-4bit | `4dcb3d101c2a` | 2.263 GB |
| mlx-community/Qwen3-8B-4bit | `545dc4251c05` | 4.608 GB |
| mlx-community/Qwen3-14B-4bit | `a4d9b2df59d2` | 8.308 GB |

raw result 与 MANIFEST 无 revision 冲突。两处 raw result 的 `resolved_revision=null`
均为训练进程在写出 metrics 前失败所致（两条 prompt06 早期 smoke 失败 + ctx8192 SIGKILL），
不是 provenance 缺陷；对应实验的模型身份由 config.yaml 锚定。

## 4. 已有实验证据全景（19 个 raw result，全部为 probe/非 formal）

汇总见 `research/evidence_ledger.csv`（程序化生成）。关键分组事实：

### 4.1 冒烟与校准（prompt06–08，git dirty 期）
- exp0-smoke：0.6B LoRA ctx512 20 步。前 2 次 `runtime_error`（exit 1，保留），
  后 2 次 success：median step 0.067–0.068 s，peak GPU 1.337 GB。
- calibration-0.6b（100 步 ×3 seed42 重复）：median 0.071–0.073 s，peak GPU ≈1.338 GB，
  重复间步时 CV 极小（<2%）；final loss 0.4217（3 次一致）。
- calibration-1.7b（100 步 ×3）：median 0.158–0.165 s，peak GPU ≈3.640 GB，
  final loss 0.1959（3 次一致）。

### 4.2 规模探针（prompt09–13，git clean 期）
- 4B BF16 LoRA（ctx512, r8, 20 步）：2 次成功（其一 provenance 弱：dirty+rev null，
  属 REVISION sidecar 修复前），median 0.335–0.339 s，peak GPU 8.356 GB。
- 4B 4bit QLoRA（同 ctx/rank/seed）：2 次成功，median 0.219–0.225 s，peak GPU 2.566 GB。
- 8B 4bit QLoRA：success，median 0.389 s，peak GPU 4.980 GB。
- 14B 4bit QLoRA：success，median 0.679 s，peak GPU 8.789 GB。

### 4.3 Context 边界探针（prompt14，未闭环）
- ctx2048（4B-4bit QLoRA，synthetic long text）：**success**，20 步，
  median step 53.187 s（ctx512 基线 0.219 s 的 **243 倍**），tokens/s 31.6，
  peak GPU（MLX 口径）**23.19 GB > 16 GiB 物理内存**，swap before 3.24 GiB → after 4.68 GiB。
  [推断] 该运行处于重度 swap 颠簸区间：步时放大 243× 而上下文仅放大 4×，
  且 MLX 分配器峰值超过物理内存，唯一机制是统一内存换页。
- ctx8192（同系列）：**runtime_error**，子进程运行 87.3 s 后被 SIGKILL，
  stdout 为空、stderr 仅含 `mx.metal.reset_peak_memory` deprecation 警告、
  `successful_steps=null`（0 步完成）。
  stderr 警告出现在训练循环入口前 → [推断] 进程已通过模型加载与数据准备，
  在首个训练步完成前被杀。
  **confounder（raw evidence）**：swap before 4.64 GiB，swap after **23.77 GiB**
  （environment/raw_environment.txt，vm.swapusage used 字段）。
  不得写成"8192 OOM"或"8192 不可训练"；可陈述：该次 preflight 环境与配置下，
  子进程在完成任何训练步之前被 SIGKILL，伴随系统 swap 从 4.64 GiB 升至 23.77 GiB。

## 5. 测量体系现状（Phase 2 输入）

已在 raw result 中 `measured` 的指标：wall-clock（monotonic）、per-step time
（`mx.eval` 同步后计时，`src/train/lora_smoke.py:139-142`）、loss-bearing tokens、
tokens/s、samples/s、model load 秒数、initial swap（before/after 快照）、
power source、vm_stat 计数器、MLX GPU 侧峰值内存
（`mx.metal.get_peak_memory()`，训练进程自报）。

仍为 `unresolved`/null 的指标：peak process RSS（/usr/bin/time -l 未启用）、
peak system memory、peak swap（无周期采样）、page faults 语义、thermal、energy。
监控 interval_seconds=1.0 在配置中声明，但**当前 supervisor v0 并未实现周期采样器**
（`src/benchmark/supervisor.py` 仅 before/after 快照）→ 配置声明与实现不一致，
需在 Phase 2 修正或如实标注。

## 6. 代码与协议基线

- Supervisor v0：配置验证/ID/环境采集/子进程监督/终态分类/原子 finalize/manifest 齐备；
  `validity.protocol_valid` 恒为 False（最终验证器未实现）→ 所有 raw result 标注
  `exclusion_reasons=["v0：最终验证器未实现"]`。
- 训练器 `src/train/lora_smoke.py`：单文件 LoRA/QLoRA 冒烟训练器（无 validation split、
  无 checkpoint、无 eval 循环），text 字段直接 tokenize 截断。
- 配对比较 `src/analysis/paired_comparison.py`：仅支持"控制因子全等"的配对，
  **不支持 context-scaling 类比较**（sequence_length 在其 CONTROLLED_FACTORS 中）→
  Phase 1 需扩展。
- 协议/schema 版本均 0.1.0。

## 7. Phase 0 结论

1. 仓库 evidence 链完整可用：19/19 manifest 通过，provenance 可追溯，
   无伪造迹象；早期 dirty-git 运行如实保留并可按 evidence_quality 分级使用。
2. prompt14 未闭环是唯一阻塞项；两个未提交 raw result 内容完整合法。
3. ctx2048 的 53.9 s/步 + 23.19 GB MLX 峰值表明 **Trainable（可完成）与
   Practical（实用速度）在此已分离**——这是论文核心叙事的关键证据点，
   但需 formal 重复与更细 ctx 网格支撑。
4. 尚不存在 formal benchmark、重复实验矩阵（除校准 3 重复）、validation loss、
   analysis pipeline、图表、论文 —— 均为后续 Phase 工作。
