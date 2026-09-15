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

## D5 — 轴 4 implementation bug：变长 validation batching 崩溃 + padded mask 口径修正（2026-09-15 登记）

性质：**implementation deviation**（实现缺陷被 formal 矩阵暴露），非实验
失败本身的重新分类。历史失败 raw 不删除、不覆盖、不重分类。

- **发现日期**：2026-09-15（失败发生于 2026-09-12T01:00–01:02 UTC，
  trainer commit `7b4f304a07`）。
- **影响轴**：formal 轴 4 全部（b2/b4/b8 × 3 seeds = 9 run，零成功）。
- **受影响 experiment IDs**（全部保留，分类为 *implementation-invalid
  formal attempts*，不作为 OOM/硬件边界证据使用）：
  - `20260912T010039277561Z__mlx-community-qwen3-4b-4bit__qlora-q4__ctx512__b2-ga1__r8__s42__01a09321-77ed-781d-9525-c73e2f13f47c`
  - `20260912T010057032957Z__mlx-community-qwen3-4b-4bit__qlora-q4__ctx512__b2-ga1__r8__s123__01a09321-bd49-74c0-b8a1-0782b7750f54`
  - `20260912T010113537018Z__mlx-community-qwen3-4b-4bit__qlora-q4__ctx512__b2-ga1__r8__s2026__01a09321-fdc1-7318-9bb8-17062e743279`
  - `20260912T010129965737Z__mlx-community-qwen3-4b-4bit__qlora-q4__ctx512__b4-ga1__r8__s42__01a09322-3dee-714c-a8eb-64e1429d9826`
  - `20260912T010153968541Z__mlx-community-qwen3-4b-4bit__qlora-q4__ctx512__b4-ga1__r8__s123__01a09322-9b0b-754e-accc-539b548284ca`
  - `20260912T010221754536Z__mlx-community-qwen3-4b-4bit__qlora-q4__ctx512__b4-ga1__r8__s2026__01a09323-083a-7124-9f61-789f550b20ba`
  - `20260912T010247917130Z__mlx-community-qwen3-4b-4bit__qlora-q4__ctx512__b8-ga1__r8__s42__01a09323-6e6d-7bbc-a2c4-00d73e72c23c`
  - `20260912T010255423307Z__mlx-community-qwen3-4b-4bit__qlora-q4__ctx512__b8-ga1__r8__s123__01a09323-8bbf-760e-a3d8-f8a9763ccbc8`
  - `20260912T010259241894Z__mlx-community-qwen3-4b-4bit__qlora-q4__ctx512__b8-ga1__r8__s2026__01a09323-9aaa-7934-b499-d66e8245049e`
- **观测异常**（各 run stderr 一致）：
  `ValueError: Initialization encountered non-uniform length`，
  栈：`lora_smoke.py:177 run → :161 _eval_validation_loss → mx.array(chunk)`，
  即 step-0 训练前 validation eval 处崩溃（每 run 存活 ~10–20 s）。
- **根因证据**：
  1. validation 路径对变长 chunk 直接 `mx.array(chunk)`（未 pad）；训练路径
     同文件对 b>1 已实现右侧 pad + lengths mask。两条路径 batching 语义
     不一致，是单纯的实现缺陷。
  2. 触发条件 `micro_batch_size ≥ 2` 且批内长度不等：formal_sft_v1 的
     validation split 天然变长（`ids[:seq_len]` 截断是上限非下限）；
     b=1 时 chunk 为单条序列可构造成 2D 数组，故轴 1/2/3 的全部 b1 run
     不受影响（其 validation 计算路径相同但从未触发）。
- **计划修正**：抽取模块级共享 `_pad_batch(chunk, pad_id)`（右侧 pad 到
  批内最大长度 + 逐行有效 target 区间），训练循环与 validation 循环使用
  同一 helper，消除两套 batching 语义。
- **语义影响声明**：
  - 不改变：loss 定义、tokenizer、截断策略、optimizer/lr、LoRA 配置、
    dataset、formal 聚合口径。
  - 唯一刻意变更：padded batch 的 lengths 由 `[0, len(s)]` 收紧为
    `[0, len(s)−1]`（每样本恰好 `len(s)−1` 个真实 next-token target）。
    依据：`default_loss` 对 `targets=batch[:,1:]` 按 `steps∈[off,len]`
    mask；`[0,len]` 在 padded batch 中对非批内最长样本会多计入 1 个位置
    （input=真实末 token、target=pad token），即 padding 泄漏进有效 loss，
    与预注册 "全 token LM loss" 的定义不符，且使 b>1 与 b1 的
    loss-bearing token 口径不可比（预注册 §7 轴 4 明确要求 tokens 口径
    比较吞吐）。
  - **b=1 严格等价性**：单样本无 pad（M==L）时 targets 仅 L−1 列、steps
    最大 L−1，`[0,L]` 与 `[0,L−1]` 的 mask 完全相同 → 已有全部 b1 formal
    run（轴 1/1b/2/3）语义零影响；由 regression test 数值证明（新
    `tests/test_train_padding.py`：padded-batch loss ≡ 逐样本 token 加权、
    b1 新旧 lengths 语义 loss/tokens/mask 全等）。
  - 不存在受影响的已成功 b>1 run（b>1 formal 仅轴 4，全部失败，即本条
    所修对象）。
- **历史 raw 不可变性**：按协议 §7，9 个 runtime_error 目录原样保留；
  新 run 使用新 experiment ID（新 timestamp/UUID）；在 processed 层以本
  deviation 为机器可读依据将旧 9 个标记 implementation-invalid 并排除出
  聚合（failure taxonomy 保留其原始 runtime_error 终态）。
- **重跑策略**（code-revision confounder 控制）：在修复 commit 上重跑完整
  batch 轴 **b∈{1,2,4,8} × 3 seeds = 12 runs**（预注册原文"b1 复用轴 1"
  为跨步数口径复用；为保证轴 4 内部同 commit、同步数（20 步）、同
  warmup 排除（2 步）的严格可比性，新增 `formal-axis4-b1` 组作为
  same-commit control。轴 1 的 b1 100-step run 继续按预注册用于跨轴复用；
  轴 4 分析报告将同时呈现两者以供交叉核验）。

  **重跑结果（2026-09-15，batch11，trainer commit f381ffc，12/12 有效观测）**：
  b1/b2/b4 × 3 seeds 全部 success（b1 ~350s、b2 ~9.8min、b4 ~31min/run，
  含换页状态下的慢退出）；**b8 × 3 seeds 一致 exit 137（SIGKILL）**、
  stdout/stderr 空、peak_swap 19.5–20.4 GiB——batch 可行性边界落在
  [4, 8)（4B-4bit、ctx512、swap_before 3–4 GiB 基线）。b8 三个 run
  保留为 boundary evidence（SIGKILL-consistent，非 OOM 断言），
  preflight 可比性声明见各 run 的 initial_swap_bytes。

## D6 — 5 个失败/中断 run 的 finalize 缺少 manifest.sha256（2026-09-15 登记）

- 现象：flatten 的 manifest 复算显示 5 个 run 目录无 `manifest.sha256`
  （supervisor 对 timeout/user_interrupted 类 run 的 finalize 路径未写出
  manifest）：
  - `20260911T191618034713Z__qwen-qwen3-0-6b__lora-qnone__…`（user_interrupted）
  - `20260911T203648798393Z__mlx-community-qwen3-4b-4bit__…`（user_interrupted）
  - `20260912T032808727860Z__qwen-qwen3-8b__lora-qnone__…`（timeout，probe）
  - `20260912T050812117342Z__mlx-community-qwen3-8b-4bit__…`（timeout）
  - `20260912T084135321518Z__qwen-qwen3-4b__lora-qnone__…`（timeout）
- 处置：按协议 §7 不事后补写（finalize 后目录不可变；事后补写的
  manifest 无防伪价值）。这些 run 的 result.json/logs 原样可用，仅
  evidence 质量降级（`_manifest_verified=False`，experiments.csv 与
  coverage_report.json 可见）。
- 影响评估：**零聚合影响**——coverage audit（2026-09-15）确认全部 42 个
  `aggregation_included` run 的 manifest 复算通过；上述 5 个均处
  failed_retained_for_taxonomy / non-formal:probe 处置，不进入任何
  性能聚合。
- supervisor 根因修复（对失败路径同样写出 manifest）不在本轮执行：
  避免在补实验窗口引入 supervisor code-revision confounder；
  其缺陷仅影响失败 run 的证据完整性，成功 run 的 manifest 一直正常。

## D7 — 14B-4bit formal 在当前内存驻留下不可完成（timeout），剩余 seeds 推迟低驻留窗口（2026-09-16 登记）

- 事件（batch12，2026-09-16 02:40–04:40 CST）：
  - 8B-4bit 3 seeds **全部 success**（1644/1670/1694 s，100 步）——确认
    2026-09-12 旧 timeout（swap_before 17.6 GiB）为环境归因而非规模极限。
  - ctx2048 s123 重跑 **success**（1301 s）——axis2 ctx2048 达成 3/3 seeds
    （旧失败为 peak_swap 19.9 GiB 下的 step-20-validation SIGKILL，保留）。
  - **14B-4bit s42 timeout**（7201 s 被杀；stdout 证据：模型加载 ~40 min，
    训练推进至 50/100 步，step_time 27–86 s 波动、末端 >10 min 停滞于
    step 50；training_metrics 未落盘故 successful_steps=null，步数证据
    在 raw logs/stdout.log）。起始 swap 3.7 GiB（闸门内），对照 probe
    （2026-09-07，swap 2.7 GiB）同配置 0.68 s/步 → 归因统一内存换页
    颠簸（model × system state，与 D1/D3 同构）。
- 处置（information-gain 原则，用户 P3 指令授权）：
  - s42 timeout 保留为 formal 负结果（system-state boundary 证据）；
  - 主动终止 batch 队列中 s123/s2026（预期各 ~2 h 重复 timeout，
    边际信息量低）；s123 被杀的 staging partial 留在磁盘不提交
    （recovery policy，同 28ed7fa 先例）；
  - 14B 剩余 formal seeds（s42 重跑/s123/s2026）与 P4（14B ctx2048
    boundary probe）**推迟至低驻留窗口**（swap≈0；D1 补充先例：重启后
    同类配置 451 s 成功；probe 证据下 14B 每	run 预计 ~5 min）。
    论文对 14B 报告为 "system-state-dependent boundary"：低驻留 probe
    success + 当前驻留 formal timeout，不宣称 14B 不可训练。
  - H2 判定以 8B-4bit 3/3 formal success 为主证据（BF16 边界：8B probe
    timeout、4B regime-dependent、14B out-of-budget）。
- 备注：runner 的 [ok]/[FAIL] 只反映 supervisor 退出码，timeout run 亦
  打 [ok]——判读 run 成败必须读 result.json 的 terminal_state（本次
  即为例证）。

