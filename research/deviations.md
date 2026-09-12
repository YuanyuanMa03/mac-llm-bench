# Deviations from preregistration（预注册偏离记录）

规则：预注册冻结后如需偏离，必须在此记录（论文如实报告），禁止静默修改。

## D1 — formal 轴 1 的 4B BF16 LoRA 格降级为边界观测（2026-09-12）

- 预注册值：4B BF16 LoRA @ ctx512、100 步、3 seeds（formal）。
- 偏离：该格不作为 100-step formal 运行报告，降级为 boundary observation。
- 依据（raw evidence）：
  - `results/raw/20260911T193038681059Z__qwen-qwen3-4b__lora-qnone__ctx512…`
    （terminal_state=user_interrupted，由操作者主动中断）：
    预注册配置 + swap 闸门通过（起始 swap 6.54 GiB ≤ 8.5 GiB）条件下，
    训练进程 **26 分钟未完成任何单个训练步**（stdout 零步输出），
    期间系统 swap 从 6.24 GiB 上升到峰值 11.93 GiB（1 Hz 采样轨迹
    system_monitor.jsonl，n=1608）。外推 100 步 ≥ 43 小时。
  - 对照：同模型同方法的 20-step 探针（2026-09-07，
    `20260907T040620496121Z`，~200-token 短样本、起始 swap 6.79 GiB）
    以 median 0.335 s/步完成。
  - 归因（interpretation，非 OOM 断言）：formal 数据集样本为完整 511-token
    （探针为 ~200-token），激活与工作集显著增大；在统一内存驻留 swap 6+ GiB
    的现实条件下工作集越界导致持续换页（measured swap-in/out deltas）。
- 处置：4B BF16 LoRA 在 Table 2 / Figure 3 / Figure 4 中报告为
  "boundary observation（user_interrupted after 26 min, 0 steps; see D1）"，
  不进入 formal 统计聚合；3 seeds 不再消耗机器时间。
- 结论措辞约束：可写 "not trainable in practice under the tested conditions"；
  不得写 "OOM"（无内核证据）；不得写 "4B BF16 is not trainable"（探针证据
  表明轻载条件下可训练——Trainable 判定本身依赖系统状态，这正是 RQ5 的核心）。

### D1 补充（2026-09-12 16:45，机器重启后重检验）

用户重启机器（swap 0.00 MiB）后，同配置（4B BF16 LoRA、ctx512、100 步、
seed 42）重试 **成功**：
`results/raw/20260912T…`（batch10）——451 s 完成，median 3.03 s/步，
MLX peak 11.54 GiB，起始 swap 0 GiB。

修正后的结论：**4B BF16 LoRA 的 Trainable 状态依赖系统内存驻留状态**——
swap 驻留 ≥6 GiB 时 26 分钟无法完成一步（越界换页），swap=0 时可训练
（步时仍受边界效应影响，为 compute-bound 速度的数倍）。D1 的原始
user_interrupted 运行保留为"高驻留状态下的边界观测"；成功运行作为
"低驻留状态下的 formal 观测"进入矩阵。该对照本身成为 RQ5 的关键证据：
**Trainable 不是模型的固有属性，而是模型×系统状态的联合属性。**

## D2 — runner 配置去重与重复运行（2026-09-12）

- 期间发现 runner 的 config hash 与 supervisor 的 schema.config_sha256 不一致
  （分隔符 + 内部排序键污染），导致 0.6B/1.7B 部分组被重复运行（同配置
  最多 3 次）。修复后：分析管线按 (group, seed) 保留最早 retained success，
  重复运行保留于 results/raw（不可变），在 evidence_ledger 中可见。
- 该偏离不影响数据有效性：重复运行的步时一致性（同组 CV<1%）作为
  运行间可靠性的额外证据。

## D3 — swap 闸门（预注册隔离规则的补强，非偏离）

预注册 §1 沿用协议 §5 隔离规则但未量化"内存可比性"。2026-09-12 深夜事件
（swap 基线 12.9 GiB 时 14B-4bit 24 分钟零步；见
`20260911T182218892057Z`）后，runner 加入正式闸门：每个 run 开始前
vm.swapusage used ≤ 8.5 GiB 方可启动（等待上限 1 小时）。
全部 formal run 的 swap_before 已逐 run 记录，可在分析中核验。

## D4 — 时间类指标的 Tier 分层规则（2026-09-12 04:40 预先冻结）

背景：闸门 8.5 GiB 下，4B-4bit formal run 仍出现 ~280 MB/步的 swap-in
流量（如 axis3-r4 三次运行 median 3.55–3.66 s/步，对照探针 0.22 s/步），
时间/吞吐类指标在高档位 swap 驻留下被 paging 混淆；内存类指标
（MLX allocator 峰值）不受影响。

预先冻结的机械化规则（在重跑 axis1 之前声明，防止事后挑选）：

- 每个 run 计算 paging 强度 `swapins_delta_per_step = (vm_stat swapins Δ) ×
  page_size / successful_steps`（所有测量量均已存在于 raw result）。
- **Tier-A**：swapins_delta_per_step < 50 MB/步 —— 视为 compute-bound，
  可用于 step-time / throughput 的主要 scaling 分析。
- **Tier-B**：其余 —— 保留全部数据，仅作描述性报告并标注 paging 强度。
- 同一 (group, seed) 有多个 run 时，优先取 Tier-A run；并列取最早。
- 内存类（peak memory）、feasibility 状态、loss 轨迹不受此分层影响，
  全部 run 均可使用。

依据：4B-4bit 工作集 ~4.5 GiB 在 ~7 GiB 可用内存下应无 swap-in 服务；
>50 MB/步 的 swap-in 只能来自工作集越界的活跃换页。
