# Re-Review Round 2 — Verification Report（独立席位产出 + 主会话终裁）

- **日期**: 2026-09-16；**模式**: `academic-paper-reviewer` re-review（#576 三门契约：Gate 1 标准预承诺 → Gate 2A persuasion-blind 证据判定 → Gate 2B 作者声明核对）
- **执行席位**: 未参与 Round-1 评审与修订的独立子代理上下文（fresh context；对照基线 = git HEAD `3f1fa58` 导出稿）
- **上游**: `reviews/2026-09-16-panel-review-round1.md`（Roadmap）+ `reviews/2026-09-16-revision-round1-record.md`（Gate 2B 揭示物）

## 1. 独立席位判定摘要（修复前）

| 判定 | 项目 |
|---|---|
| RESOLVED（8 项 must_fix） | R1、R3、R4、R5、R6、R7、R8、R9 |
| PARTIALLY_RESOLVED | R2（两处文本缺口：v1 下 H2 结论形态未入文；H6 引用处缺 post-revision 标注）、S2（context 数值表未补）、S4（定量对比缺失、timeout 依据未说明） |
| RESOLVED（should_fix） | S1、S3（含 1 处作者声明失实：14B 参数量未兑现） |
| NOT_RESOLVED | S5（论文内零体现，与作者"部分"标签不符） |

New Issues：无 Critical/Major；4 项 minor（摘要 "zero swap residency" 对 14B 不准确、tab:sens 引用错位、D3 行 12.9 GiB 口径矛盾、Table 7 未注明排除组）+ 1 项 observation（底稿 git 状态伪影）+ 1 项 cosmetic（表间命名风格）。

机械规则裁决（席位建议）：**维持 Major Revision（窄域）**——R2 未全解；但注明 R2 缺口为 ≤5 行文本，"若补齐且无新问题，机械规则即转 Accept/Minor Revision"。

亮点核验（席位独立完成）：JetsamEvent 六项数字与 .ips 原文逐项一致；Table 7 全部 15 行与 tier JSON 逐行一致；t/CI/ΔAIC/敏感性逐值与 processed JSON 一致；三条新 bib 经 arXiv 一手核验（含 LOMO 编号 2306.09782 纠错确认）；Table 2 六行数字与 key_numbers.json 一致。

## 2. Round-2 Residual Fixes（当日执行，全部定向验证）

R2 两缺口、4 项 minor、2 项声明失实、S4/S5 残留——共 9 处修复，逐项验证记录见 `reviews/2026-09-16-revision-round1-record.md` §4（每处附 PDF grep/重编译/CSV 排查证据）。其中 14B 参数量按防幻觉规则**撤销回填**（processed 中该字段不存在，不补猜测值）。修复后编译：0 error / 0 undefined / 0 bibtex warning，14 页。

## 3. Final Editorial Decision

**Minor Revision（acceptance-ready）**

依据（机械规则）：must_fix R1–R9 经修复后 9/9 RESOLVED（R2 的两处缺口已由定向修复关闭并验证）；无 Critical/Major 级新问题。剩余未决项全部为 should_fix/consider 级，不构成接受障碍：S2 的 context 轴数值表（数据在正文与 Table 7，未成表）、S4 的 non-weight 开销 KV/激活逐项分解（已量化到 affine 截距 1.8 GiB）、表间模型命名 cosmetic 统一。

**角色与验证披露**：最终裁决由主会话作出——该会话同时是修订执行者，存在角色重叠；裁决未依赖自评，而是基于（a）独立席位修复前的逐项判定与机械规则原文（"补齐即转正"），（b）修复后每处的定向验证（PDF grep / 重编译 / CSV 排查，见 record §4）。若需完全独立的确认，可再跑一轮 re-review（成本：一个席位调用）。

## 4. 完整独立报告

独立席位的完整报告（Gate 1 承诺清单、14 行 R&R Traceability Matrix、New Issues 全文、Author-Claim Mismatches、证据锚）保存在本会话记录中；上表为其逐项浓缩，判定与证据锚未做任何放宽。

## 5. Stage 3'' Delta 复核（2026-09-16，应用户要求追加）

第三个独立席位（未参与此前任何评审/修订）对 Round-2 的 9 处残留修复做 delta 验证（标准预承诺 → 不见作者声明的独立验证 → 声明核对）：

- **9/9 项全部 CLOSED**，判定基于数据锚独立复核（14B 参数量撤销经 CSV 第 448 列逐行验证：14B 三行均为空，8B/4B/0.6B 有值——撤销完全正当）；5 组既有 RESOLVED 项 spot-check 零破坏（t 值、Table 7 全 15 行、JetsamEvent 六+一项、Table 2 八 cell、8B 16.415 GiB）。
- **0 新 Critical/Major 问题**。三条边界观察：① §4.3 "Tier-B capped" 与修复后 audit JSON 归因不符（真实来源是 approx-linear 区间）——**已当场修正**为 "approximately-linear band"（复编译 0 error，PDF 验证在位）；② deviations.md D3 的 12.9 GiB 与 CSV 6.64 GiB 口径出入——**已加勘误注**（不改原文，遵循记录不可变原则）；③ `model.parameter_count` 列存在一个不可用的 14B probe 值（v0 方法、synthetic-smoke run），不影响撤销判定。
- **机械规则终态确认**：R2 两缺口关闭 + 无新 Critical → 上轮"维持 Major（窄域）"的前提消失。席位独立建议与本文件 §3 一致：**Minor Revision（窄域）**；不接受直接 Accept 的理由是 4 处 should_fix/cosmetic 残留（其中 2 处已由上述当场修正关闭，余 2 处：S2 context 轴数值表（数据在 `key_numbers.json` context_axis，3 行小表可关闭）、表间模型命名 cosmetic 统一）。

**最终状态：Minor Revision（窄域，剩余 2 处可选级项）。** 本轮复核消除了 §3 披露的角色重叠问题——转正裁决现由完全独立的第三席位以数据锚复核背书。

