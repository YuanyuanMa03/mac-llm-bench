# Full Panel Review — Round 1（五席位模拟同行评审完整包）

- **对象**: `paper/main.tex`（How Far Can 16 GB Go? …，mac-llm-bench v1.0.0-rc1 稿）
- **评审日期**: 2026-09-16；**模式**: `academic-paper-reviewer` full（Phase 0 → Phase 1 五席位并行 → Phase 2 编辑综合）
- **裁决**: **Major Revision**（4/4 计分席位一致）
- 本文件为审稿独立产物；评审过程未修改稿件或仓库任何文件。

---

## 1. Editorial Decision（编辑决策信）

### Decision: **Major Revision**

数据层与工程层经独立抽查全部成立（17/17 引用经一手来源核验无一伪造；论文数字与 `results/processed/` 抽查约三十处一致；118 run 对账闭合），不构成 Reject 依据；但存在多处**可被稿件自身数据证伪的陈述**与**预注册透明度缺口**，且修复涉及摘要级声明改写与补充分析，必须复审。

### Reviewer Summary

| 席位 | 角色 | Recommendation | Confidence |
|---|---|---|---|
| Journal-Fit (EIC) | MLSys/系统评测资深领域主席 | Major Revision | 4 |
| Reviewer 1 | 基准方法论 + 统计（含独立重算） | Major Revision | 5 |
| Reviewer 2 | 高效微调领域（含 17/17 引用在库核验） | Major Revision | 4 |
| Reviewer 3 | OS/内存系统 | Major Revision | 4 |
| Devil's Advocate | 固定对抗席位 | 不投票（0 CRITICAL / 9 MAJOR / 4 MINOR） | 逐条 |

### DA CRITICAL 裁决（Iron Rule #4）

**本轮 DA CRITICAL 计数 = 0**，无需要逐条裁决的否决项。DA 自述理由：每条 MAJOR 单独成立时核心声明仍有原始 run 数据支撑且可修复，不满足"未修复即推翻核心声明"门槛。9 条 DA MAJOR 已全部并入下方 Required/Suggested Revisions 并标注来源。

### Blocking Issues（当前阻碍接受的 3 个问题簇）

| # | 阻碍项 | 来源席位 | 证据锚（摘要） |
|---|---|---|---|
| B1 | "statistically indistinguishable" 被自身 Table 2 数据证伪（0.6B 差 0.113 vs seed SD≈0.001–0.002，重算 t≈95；两 CI 完全不重叠） | R1-W1, R2-W1 | `text: §4.4 "statistically indistinguishable … (1.93 vs. 1.81)"` vs `table: Table 2 — 1.813±0.002 / 1.926±0.001` |
| B2 | 预注册透明度缺口：D2/D3 正文零描述；H2/H6 审计规则在结果落地后修订未在论文披露（`hypothesis_audit.json` `rule_revision` 载明 v1 锚 14B→v2 锚 8B） | EIC-W1, R1-W4/W11, DA-4 | `absence: 正文+附录 — expected D2/D3 描述; checked abstract/§3.7/§4/§5.4/附录A/B` + `dataset: hypothesis_audit.json H2.rule_revision` |
| B3 | Tier-B 自设规则的执行矛盾：① "every formal run exchanged >50 MB swap-in per step" 与 `experiments.csv` 重算矛盾（0.6B/1.7B 系列为 8.9–41.1 MB/步，按 D4 属 Tier-A）；② 4B 配对 step-time ratio 1.21 为跨窗口跨驻留 n=1 比较，违反 "not compared anywhere" 自设规则并进入摘要；③ `\efficient` 判定（8B 42.9 tok/s）使用的正是被宣布不可解释的 Tier-B 绝对值 | R1-W2/W3, DA-1/DA-2 | `text: §4.3 "every formal run exchanged $>$50\,MB"` vs `dataset: experiments.csv 重算`；`table: Table 3 — 4b ratio 1.21`（分母为 initSwap=0.0 GiB 的 D1 run） |

### 共识分析

**CONSENSUS-4（四计分席位全部 + DA 印证）**
1. **Major Revision**：全部四席位；理由结构一致——数据链可信（不 Reject）vs 报告层/透明度实质缺陷（非 Minor）。
2. **统计措辞越界**：R1-W1 与 R2-W1 独立发现同一矛盾（R1 给出重算 t≈95；R2 从领域角度补充"100-step LM loss 不能外推 QLoRA 收敛质量结论"）。
3. **偏差与规则修订须入论文**：EIC-W1、R1-W11（D2/D3 缺失）+ R1-W4/DA-4（H2/H6 事后修订）。
4. **跨窗口/跨表数字未调和**：EIC-W4（吞吐 137.2 vs 89.5）、R1-W8（步时 3.665 vs 5.620，差 53%）、DA-12（并排无警示）——同一 run 对的三个侧面。

**CONSENSUS-3**
5. **8B 阈值/敏感性**：EIC-W5（10.039>10 被 "sits at the threshold" 掩盖）、R1-W5（承诺的 ±2× 敏感性/每对 SD/t-CI 全部未执行）、DA Observations-6 印证。
6. **单机泛化 vs 类级标题**：EIC-W3（Major）、DA-13（Minor，因 Limitations 已披露）；R2 在 Criterion 表中同记"跨 M 代际外推性未知"。
7. **SIGKILL 机制归因**：R3-W1（Major：无 kernel 证据、与 supervisor 自身 SIGKILL 无判别）+ DA Ignored-Alternative 1（Metal working set/wired limit 替代机制）。

**分歧与裁决**
- **新颖性/增量**：R2-S2 判 Originality MEETS（arXiv 检索确认 "preregistered feasibility map" 空白属实）vs DA-9（发现层面无与既有认知的差异对比，So-what 未证）。**裁决：两者同时成立**——方法学空白为真（R2 在线核验），但发现层增量对比缺失（DA-9 的 absence 锚成立）。处置：并入 S4（对比讨论），不升级为 must_fix。
- **sublinear 内存结论**：R1-W6 仅要求补报告（CI/df/p、R² 更正），未否认结论；DA-5 质疑 "reject the linear-memory hypothesis" 措辞与 affine（peak≈wN+c）替代模型的竞争解释。**裁决：合并**——保留结论但必须补 CI + 幂律 vs affine 模型比较 + 软化 "reject/naive" 措辞（并入 R4）。

### Decision Rationale

四席位独立得出同一裁决且理由结构互补：EIC 从就绪度（偏差披露不可核验、gap 对话面窄、单机泛化）、R1 从执行层（统计陈述被数据证伪、分层规则自违、承诺分析缺位——全部经独立重算）、R2 从领域层（引用全真但质量声明越界、QLoRA 语义披露不足）、R3 从系统层（kill 归因无 kernel 证据、residency 单指标）。DA 的不对称认识论指控（对失败严格、对成功宽松：8B/ctx2048 的首次失败被重跑成功静默替换，而 4B BF16 1/3 被升格为 boundary 案例并成为亮点）与 R1-W13、R1 独立发现的 run 时间线证据交叉印证，是本轮最实质的挑战，已转化为 R3/R4/S4 的具体修订项。选择 Major 而非 Minor：B1–B3 均为事实性错误或透明度缺口而非呈现瑕疵，且摘要级声明需要改写；选择 Major 而非 Reject：核心测量（118 runs、失败包容、数字-数据一致性、引用真实性）经三席位独立抽查全部成立。

---

## 2. Required Revisions（must_fix，按主题；R<n> 为传递引用非工作顺序）

| Ref | 修订项 | 来源 | 严重度 | 验收标准（单行） |
|---|---|---|---|---|
| R1 | 撤回或正式化 §4.4 质量统计声明：删除 "statistically indistinguishable" 或补预注册 loss 等价 margin + TOST/配对检验；写明 100-step LM loss 与 QLoRA 原论文收敛结论不可比 | R1-W1, R2-W1 | major | 正文不再含未被检验支持的"统计不可区分"表述，且差值 0.113/0.085 被如实报告并讨论 |
| R2 | 预注册全量入文：附录 D1–D8 汇总表（含 D2/D3 一句话定义）；H2/H6 判定规则修订（v1 锚 14B→v2 锚 8B）作为新偏差（D9）披露含时间线与 v1 下结论形态；注明 preregistration.md 冻结证据（git 时间戳） | EIC-W1, R1-W4/W11, DA-4 | major | 论文内可完整核对 8+1 项偏差；H2/H6 引用处标注 post-revision rule |
| R3 | Tier-B 一致性修复（四子项）：(a) 逐 run 报告 paging 强度与 Tier 判定，修正 "all timing figures are Tier-B" 全称断言；(b) 4B step-time ratio 标注跨窗口 n=1 或移出等价性声明，摘要 "all three paired scales" 改两尺度；(c) 8B "not \efficient" 判定加 Tier-B 限定或补 8B 轻载 probe；(d) 给出 ">50 MB swap-in per step" 的定义、推导与适用步长 | R1-W2/W3, R3-W2c, DA-1/DA-2 | major | 论文中不再存在与 experiments.csv 重算或自设比较规则矛盾的陈述 |
| R4 | 补齐承诺分析：±2× 阈值敏感性表（8B Practical 判定在 10.039 vs 10 s 处必须如实呈现翻转）；Table 3 每对比值 SD；Table 2 t-CI（ci95 已在 processed 数据中）；斜率 CI/df/p + 幂律 vs affine 模型比较；软化 "reject the linear-memory hypothesis" 与 "Contrary to the naive" 措辞 | R1-W5/W6, EIC-W5, DA-5, DA-8 | major | §3.7 承诺的敏感性、全部 CI/SD 出现在正文或附录；R² 与 processed JSON 一致 |
| R5 | 跨表基线调和：拆解 4B-4bit b1 的 3.665 s（Table 2）vs 5.620 s（Table 5）与吞吐 137.2 vs 89.5 的来源（trainer commit/窗口/协议）；Table 5/6 加 paging 强度列；重写或删除 0.22 vs 3.66 s/step 例证（probe 为 ~19 token/步 vs formal ~489 token/步，workload 不可比） | R1-W7/W8, EIC-W4, DA-12 | major | 同一配置不再在两表并排出现未解释的 53% 差异；Tier-B 例证不再混入 workload 差异 |
| R6 | SIGKILL 归因降级或取证：检索 unified log 的 kernel/memorystatus(jetsam) 记录（若保留期内）作为 Appendix 证据；supervisor 记录 kill 来源判别（elapsed vs timeout 上限）；在此之前将 "OS kill under memory pressure" 改为中性标签（如 "external SIGKILL under high sampled swap (mechanism unverified)"），摘要与 §5.3 的 "the OS terminates/kills" 同步弱化 | R3-W1, DA-Alt1 | major | 机制归因陈述的证据等级与持有证据匹配，或已附 kernel 取证 |
| R7 | Residency 测量与协议操作化：supervisor 增加 `vm_stat`（compressor pages、pageins/outs）与 per-process footprint 采样（或声明为协议 v2 并讨论局限）；"mandatory residency field" 建议给出字段集/频率/基线的具体协议，并讨论 "measure vs control(fresh-boot)" 两条路线及 D8 的选择理由 | R3-W2/W3 | major | 论文对 "residency state" 的刻画不再依赖单一系统级 swap 计数且建议可被第三方执行 |
| R8 | QLoRA 实现语义披露：§3.5 写明 MLX 路径 = group-wise 4-bit（group size 64）量化基座 + 常规 AdamW，非 NF4、无 double quantization、无 paged optimizer；讨论 paged optimizer（GPU 侧可控分页）vs 本文 OS 级不可控 thrashing 的对照 | R2-W2 | major | 读者可判断本文数字与 QLoRA 文献的可比边界 |
| R9 | 范围收窄或加固：标题/贡献 (i) 改为 16 GiB M4 case study 定位（"a transferable protocol + one-point deep map"），泛化列为 future work；或补第二配置锚点复测 2–3 个 cell | EIC-W3, DA-13 | major | 类级声称（"Consumer Apple Silicon"）与证据面匹配 |

### Suggested Revisions（should_fix / consider）

| Ref | 修订项 | 来源 | 义务 |
|---|---|---|---|
| S1 | 补引：Baral et al. 2026（arXiv:2606.31048，Apple Silicon MLX LoRA 实证）、MobileFineTuner（arXiv:2512.08211）、LOMO（arXiv:2402.12305）；软化 §2.1 "has so far focused on inference latency"；§2.1/§2.4 去重 | R2-W3/W4, EIC-W2 | should_fix |
| S2 | 口径更正：R² 0.99→0.98（与 JSON 0.9848 一致）；14B residency 引用口径（2.7/7.1/3.7 vs CSV 2.52/6.64/3.47 GiB）统一；manifest 缺失 5→6 并说明第 6 个（D7 14B timeout）；Table 4 "unknown_failure" 与正文 "operator interrupted" 对齐；fig2 右板 ctx512 "untested"→"reused (3/3)"；Table 4 的 ctx2048 OS-kill 与 §4.6 "completes all three seeds" 关系加注；context 轴补表 | R1-W6/W9, R1/R3 Minor | should_fix |
| S3 | 术语/格式：ultrachat_200k 许可改 "MIT license"（HF 卡证实）；Table 1 "10P/10L"→"10-core CPU (4P+6E)"（以环境快照为准）；Table 1/4 模型命名统一；Table 2 "±0.00" 加注；llamacpp URL 更新至 ggml-org；ajayi2025 年份信号统一；摘要压缩（发现(2)拆句）；摘要 peak memory 加 "(allocator high-water mark)" | R2-W5/W6, EIC/R2/DA Minor | should_fix |
| S4 | 叙事完整性：§5.2 补 8B 自身窗口对照（首次 timeout 16.4 GiB 驻留 vs 成功 3.6–4.8 GiB——论文普遍性主张的自证数据已在库）；披露重跑决策规则（ctx2048 s123、8B s42 首试失败被替换 vs 4B BF16 未补试——对齐两套标准或解释不对称）；3/3 的 Clopper-Pearson CI 一句话；14B timeout(7200 s) 选取依据与敏感性讨论；与既有定量认知的差异对比（回应 So-what）；non-weight 4.6 GiB 开销分解（面向 MLX 开发者） | R1-W10/W13, DA-3/6/7/9 | should_fix |
| S5 | 终端用户盲点：温度/风扇、SSD 写入量（~20 GiB swap 的页写出代价）、磁盘预算、长任务时间外推；或声明超出范围 | DA Missing Perspectives | consider |

### Revision Roadmap checklist（immutable source order）

- [ ] R1 — must_fix — 修正质量统计声明
- [ ] R2 — must_fix — 预注册偏差/规则修订全量入文
- [ ] R3 — must_fix — Tier-B 四子项一致性
- [ ] R4 — must_fix — 补齐承诺分析（敏感性/CI/SD/模型比较）
- [ ] R5 — must_fix — 跨表基线调和与例证重写
- [ ] R6 — must_fix — SIGKILL 归因取证或降级
- [ ] R7 — must_fix — residency 协议扩展与操作化
- [ ] R8 — must_fix — QLoRA 实现语义披露
- [ ] R9 — must_fix — 标题/贡献范围收窄或第二锚点
- [ ] S1 — should_fix — 补引三篇 + Related Work 修缮
- [ ] S2 — should_fix — 口径更正群
- [ ] S3 — should_fix — 术语/格式群
- [ ] S4 — should_fix — 叙事完整性群（含 DA 不对称认识论回应）
- [ ] S5 — consider — 终端用户运营变量

---

## 3. Panel Provenance（六轴如实披露）

| 轴 | 状态 | 说明 |
|---|---|---|
| role_separated | true | 五席位按 Phase 0 配置卡分角色执行 |
| fresh_context（席位内） | true | 每席位为独立 subagent 会话，各自重新读论文与模板 |
| blind_to_peer_outputs | true | 五席位并行发出，互不可见对方报告（含 Challenge/Scoring Plan 先盲后读的两步近似） |
| model_family_distinct | **false** | 五席位同一模型家族（GLM-5.3/ZCode 会话派生） |
| provider_distinct | **false** | 同一 provider |
| human_distinct | false | 无人类审稿人参与 |

**相关性误差披露（必读）**：五份报告来自同一模型家族的同一 provider，**不构成独立同行评审**；多席位对同一发现的交叉印证（如 R1-W1/R2-W1 的统计矛盾、R1-W3/DA-1 的跨窗口比率）应视为**共同证据源下的收敛**而非独立复现。两名席位（R1、R2、DA）访问了仓库 processed 数据与在线一手来源，发现含论文之外的证据；纯论文评审可能得出较宽松结论。本评审 NOT_CALIBRATED。

**契约近似声明**：v3.6.2 sprint contract 的两调用（paper-blind Phase 1 + paper-visible Phase 2）在本次执行中以"单席位内先盲写计划、后读论文"的顺序近似实现；`check_phase_conformance.py`/`check_panel_synthesis.py` 等运行时校验器未在本次环境执行，机械仲裁以人工综合替代并逐条溯源至席位报告。

---

## 4. 五席位发现索引（溯源用）

### EIC（Journal-Fit）— Major Revision, conf 4
- 优点 S1–S6：失败包容证据链、14B 三段式克制、四级操作定义、residency 字段建议、摘要-表格数字抽查一致、Tier-B 窗口纪律。
- W1(Major) D1–D8 未入文、D2/D3 零描述；W2(Major) gap 对话面窄（~3 篇）；W3(Major) 单机 vs 类级标题；W4(Minor) 89.5 vs 137.2 未调和；W5(Minor) 8B "sits at the threshold" 掩盖 10.039>10。
- Q1–Q4：D2/D3 内容；跨表差异归因；27 failures vs 118 disposition 逐类映射；8B wall-clock 与 100×step 差构成。

### R1（Methodology，含独立重算）— Major Revision, conf 5
- 优点 S1–S7：预注册/偏差体系深度、数字-数据抽查全部一致（~30 处）、测量口径验证、失败保守分类、D3/D4 规则预冻结、边界区间纪律、D5 处理范例。
- Major：W1 统计声明被证伪（t≈95）；W2 Tier-B 全称断言 vs CSV 重算（0.6B/1.7B 实为 Tier-A 8.9–41.1 MB/步；8B 在低驻留窗口计时）；W3 4B ratio 跨窗口 n=1 入摘要；W4 H2/H6 事后修订未披露；W5 敏感性/SD/CI 承诺未兑现 + 8B 阈值掩盖；W6 拟合报告不足（BF16 slope 95%CI [−0.22,1.65] 含 1；R²=0.99 vs 0.9848）；W7 0.22 vs 3.66 例证混淆 workload（19 vs 489 token/步）；W8 3.665 vs 5.620（53%）未调和、Table 5 无 paging 标注。
- Minor：W9 14B 口径三处不一致（residency 数值、unknown_failure vs interrupted、manifest 5≠6）；W10 3/3 CI；W11 D2/D3 缺失；W12 ctx 上界单 seed probe 证据等级；W13 8B 状态依赖未入叙事。

### R2（Domain，含 17/17 在库引用核验）— Major Revision, conf 4
- **Citation Verification Log 结论：17/17 verified，0 mismatch，0 unverifiable**（方法：arXiv export API / GitHub raw / ACL Anthology / PMLR / HF API 一手来源；WebSearch 配额耗尽改用一手途径）。带注 2 条：ajayi2025 年份信号（bib 2024 vs arXiv 2025-10）、mlxlm 标题措辞与现标语略异。
- 优点 S1–S4：引用全真、gap 定位经检索属实、QLoRA 转述与 mlx-lm 官方文档一致、主干文献五脉络覆盖得当。
- W1(Major) 统计声明矛盾 + 100-step loss 不能外推收敛质量；W2(Major) QLoRA 语义披露不足（无 NF4/double quant/paged optimizer；错失 paged optimizer 对照论证）；W3(Minor) 补引三篇；W4(Minor) "has so far focused" 过强；W5(Minor) ultrachat_200k 实为 MIT；W6(Minor) 10P/10L 歧义。

### R3（Systems/OS）— Major Revision, conf 4
- 优点 S1–S5：peak memory 口径定义+实证、测量开销实测与 null 纪律、terminal-state 保守协议、D1/14B 自然实验、Tier-B 自我限缩。
- W1(Major) SIGKILL 归因（"OS kill under memory pressure" 嵌入两重未证实断言；与 supervisor timeout SIGKILL 无判别；unified log 取证可获得却未做；GPU 侧 working-set 违规未排除）；W2(Major) residency 单指标系统级（compressor 分量不可见；进程级 footprint 缺失故"驻留归因"不比"背景负载归因"更被支持；">50MB/step" 指标不在冻结清单）；W3(Major) mandatory-field 建议未操作化（clock-state 类比不严格：无跨机可比性）；W4(Minor) 23.9 GiB 解释缺 compressor/recommendedMaxWorkingSetSize/成功-失败非映射教学点。
- Q1–Q4：kernel 取证可行性；>50MB/step 推导；compressor 监测；ctx2048 Table4-vs-§4.6 关系与 context 轴表。

### Devil's Advocate — 0 CRITICAL / 9 MAJOR / 4 MINOR
- **最强反驳（不对称认识论）**：论文对失败用最严格系统状态怀疑主义、对成功用最宽松窗口内重复标准——Tier-B 豁免条款被摘要自己违反（4B 跨窗口比率）；`\efficient` 判定立于被豁免的绝对值；"reproducibly" = 单晚三连 + 被静默替换的首试失败；n=4 的 "reject"；事后修订的 H2/H6；timeout 界定的 14B "not sustained"。
- MAJOR：DA-1 跨窗口比率；DA-2 Tier-B/Efficient 矛盾；DA-3 单窗口 reproducible（CP 下限 0.29）；DA-4 H2/H6 修订；DA-5 n=4 reject + affine 竞争模型（外推预测 14B≈12.5 GiB 与自身观察相抵触）；DA-6 选择性报告（ctx2048 s123 SIGKILL→重跑成功不提首试；8B s42 timeout→重跑；4B BF16 未补试成 boundary——重跑机会分配方向一致偏向结论）；DA-7 14B 由 7200 s timeout 算术界定；DA-8 摘要/结论系统性高于 audit 一档 + "no measurable time cost" 与 1.10–1.23 自相矛盾；DA-9 So-what（无与既有认知差异对比）。
- MINOR：DA-10 practical/feasibility 无质量维度；DA-11 摘要省略 allocator 限定；DA-12 同配置 53% 并排无警示；DA-13 类级标题。
- **计划撤回（诚实记录）**：预设的"D1 边界点拉低 BF16 斜率以支持 sublinear"指控经数值检验**不成立**——纳入 4B 点实际抬升斜率（0.62/0.86 分段 → 0.71 整体），fig3 披露透明。14B 小节内部的呈现也被判定对称（成功/失败并列）——不对称问题在 8B/ctx2048 侧（DA-6）。

---

## 5. 下游衔接

- 修订执行：`academic-paper`（revision mode）——以上 Roadmap + `author-adjudication`（will_address / wont_address / not_on_point 逐项）。
- 修后复核：`academic-paper-reviewer`（re-review 模式，R&R Traceability Matrix 三门契约）。
- 需要更多文献侧证据：`deep-research`（R2 席位的引用核查方法可直接复用）。

*Generated by academic-paper-reviewer v1.11.1 full panel (5 seats + editorial synthesis), 2026-09-16. 评审只读：未修改 paper/ 或 results/ 任何文件。*
