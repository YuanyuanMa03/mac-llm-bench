# Stage 4.5 — Final Integrity Verification Report

- **日期**: 2026-09-16；**模式**: Mode 2 (final-check, fresh from scratch per Anti-Pattern #6)
- **对象**: 修订后 `paper/main.tex`（14 页）+ bib 20 条 + 9 表 + 8 图 + processed JSON 链
- **执行**: 两个独立席位（引用席位 = Phase A/B 在线一手核验；数据席位 = Phase C/E + Mode 6 + 仓库规则，~290 项核对）+ 主会话修复轮 + 定向复检
- **上游**: Stage 3' Minor Revision（`reviews/2026-09-16-re-review-round2.md`）

## Verdict（终局）: **PASS WITH NOTES**

首轮 FAIL（1 SERIOUS 数据叙述 + 3 SERIOUS 引用 MISMATCH）→ 修复轮全部关闭 → 复检逐项验证通过。剩余为 MINOR/披露级 NOTE（下 §4），零 SERIOUS / 零 MEDIUM / 零 MAJOR_DISTORTION / 零 UNVERIFIABLE。

## 1. Phase A（引用，FRESH 全量 20 条）

- **17 VERIFIED / 3 MISMATCH / 0 NOT_FOUND**。三条 MISMATCH 为同一模式（arXiv v1 作者名单 + 正式 venue booktitle 混用，各多列 1–2 人）：ding2023ultrachat（9→8 人）、zheng2024llamafactory（7→5）、lv2024lomo（6→5）。
- **修复**：按 ACL Anthology 官方 `.bib` 逐字替换（WebFetch 一手拉取三份官方名单），补 pages 与 camera-ready note；头注释同步。
- **复检**：`Zheng, Zhi` 自 PDF 消失；三条作者数与官方一致。
- 风险点复核：LOMO 编号 2306.09782 独立确认（非 SiPM 论文 2402.12305）。
- 方法论注脚（席位自述）：其凭记忆给出的 4 个 arXiv ID 有 3 个错误、均被一手查询当场纠正——same-source hallucination 对策必要性的直接证明。

## 2. Phase B（引用语境 100%，26 处 \cite）

**26 VERIFIED / 0 distortion**。重点项逐词落实：QLoRA 三差异声明（摘要+ar5iv 双证据）、feng2025 page-faults 转述、ajayi encoder 定位、rajesh 五 runtime 逐字、baral Apple-Silicon+MLX 逐字、LOMO fused 逐字、applem4 的 4P+6E（Apple 官方正文逐字）。

## 3. Phase C/E（数据与声明，~290 项）

- **自动核对 162 项**（表 2/3/5/6/9 + 斜率/CI/ΔAIC/affine/val-loss 检验 vs processed JSON）：160 PASS + 2 合法舍入。
- **手工核对 ~120 项**（表 4/7/8、正文高频数字、附录 C/D/E、CSV 直源）：全部一致（修复后）。
- **JetsamEvent 附录 C**：9/9 字段与 `.ips` 原文吻合（含 SHA-256 sidecar 一致）。
- **Mode 6（Methods ↔ config）**：5 run × 15 字段全匹配；预注册 commit `3dc33d2`（16:57:05Z）早于首个 formal run（17:40:43Z），"frozen before any formal run" 成立。
- **仓库核心规则**：表格 9/9 + JSON 6/6 沙箱重生成**逐字节一致**；`results/raw/` 零改动；27 失败 run 全保留；118 对账闭合。

### 首轮发现并已修复的问题（错误链均为 deviations.md 手记 → audit → 论文，非管线产物）

| ID | 问题 | 修复 |
|---|---|---|
| SERIOUS S1 | 14B 第二次 formal 叙述（"50/100 步、27→86 s、stall@50"）与 raw stdout 矛盾——实测 **70 行 step、9.4–105.07 s、stall@70 后 ~23 min**（独立复核确认） | 正文/§6.2/附录改 70/100、9.4–105 s、mid-run peaked；`hypothesis_audit.py` 文字修正并重生成；deviations.md 加勘误注（原文不可变保留） |
| SERIOUS S1–S3 | 三条 bib 作者名单（见 §1） | 官方名单替换 |
| MEDIUM M1 | 8B "1,644–1,694 s"（手记）vs CSV 1642.9/1668.7/1693.3 | 改 1,643–1,693 |
| MEDIUM M2 | "26 minutes" vs wall 1627.4 s = 27.1 min | 全文三处改 27 minutes |
| MEDIUM M3 | fig4 caption "Absolute values are Tier-B" 为 D9 修复前残留，与混合分层矛盾 | 改 "window-specific (mixed Tier-A/Tier-B stratification)"；摘要同步 |
| MEDIUM M4 | "six runs lack manifests" 与机制不符（manifest 文件在；post-finalize log append 致 digest 失配，byte 级定性） | §5 与附录 D6 行改准确机制描述 |
| MINOR m1 | 0.34/4.6 "GiB" 实为 GB 误标（safetensors 0.312/4.291 GiB） | 改 0.31 / 4.29 GiB |
| MINOR m2 | 表 5 "231–339" vs 表 7 "230–339"（banker's vs 原值舍入） | 两生成器统一 half-up；两表现在均 231–339 |
| MINOR m3 | ctx1024 "6.6×"（应由未舍入值 6.544） | 改 6.5× |
| MINOR m4 | "60 measured steps" 实为 54（3×18 post-warm-up） | 改 54 并注明构成 |
| MINOR m5 | 附录 C "started 00:45:50" vs 实际 00:45:51 | 改 |

复检：以上每处经 PDF 文本 grep 验证在位（含旧值消失）；编译 0 error / 0 undefined / 0 bibtex warning，14 页，overfull 残余 4 处均 <8pt。

## 4. 剩余 NOTES（不阻塞，披露级）

1. `hu2022lora` venue（ICLR 2022）本轮仅二手印证（OpenReview/dblp/S2/Wikidata 通道全部受阻；arXiv 一手已确认标题/作者/年份，Wikipedia 一致且无矛盾证据）。
2. `mlxlm` year=2023：独立仓库 2025-03 才拆分创建，但保留的提交历史确凿始于 2023-12（可辩护）。
3. 正文将 `ultrachat_200k` 谱系引至原始 UltraChat 论文（HF 卡惯例一致）；未注明 HuggingFaceH4 过滤版（意义保真）。
4. 管线内并存口径：`key_numbers.json` 的 step-slope 0.9986 与 `step_time_scaling_fits.json` 0.9966（不同输入口径；论文统一引用后者，自洽）。
5. 措辞级观察（可辩）："roughly halves memory (0.54–0.73×)" 的 0.73 端、ctx2048 "swap near 20 GiB"（三 seed 峰 19.0/18.6/14.2，高驻留窗两次支撑）。

## 5. Phase D（原创性）——受限执行披露

WebSearch 配额耗尽，基于 web 的段落级原创性抽查（≥50%）**未执行**。替代覆盖：(a) 全部数字程序化生成且 9/9 表重生成逐字节一致（排除数据抄袭面）；(b) 20 条引用经一手核验且语境零失真；(c) 文本层与外部语料的相似性比对本轮缺失。**建议正式投稿前补一轮专业查重（Turnitin/iThenticate）**。

## 6. AI Research Failure Mode Checklist（7-mode）

| Mode | 首轮状态 | 处置 | 终局 |
|---|---|---|---|
| 1 Implementation bug | 历史案例（flatten Tier bug，Round-1 已修+D9）；本轮 S1 属同类（手记数字绕过管线） | 系统化核对 290 项 + 重生成逐字节一致；错误链切断 + 勘误注 | **CLEAR**（历史 D9 留痕） |
| 2 Hallucinated citation | 3 MISMATCH（作者版本混用） | Anthology 官方名单替换 + 复检 | **CLEAR**（修复后） |
| 3 Hallucinated result | **真实发生**（S1：叙述数字 ≠ raw stdout） | 修正为 raw 实测 + 独立复核 + 勘误 | **CLEAR**（修复后） |
| 4 Shortcut reliance | 不适用（系统基准，无泛化声明）+ DA So-what 已挑战并以 absence 声明回应 | — | **CLEAR** |
| 5 Bug-as-insight | 历史案例（Tier bug 输出曾成 "all Tier-B" 叙事，Round-1 揭露）；本轮确认无新惊喜叙事建于 bug 上（sublinear 已有界化） | D9 披露 | **CLEAR**（历史 D9 留痕） |
| 6 Methodology fabrication | 无 | 5 run × 15 字段全匹配 + 预注册时间戳验证 | **CLEAR** |
| 7 Frame-lock | 评审轮已系统挑战（Tier 叙事/8B 单窗/重跑不对称），论文以披露自纠而非固守 | — | **CLEAR** |

## 7. 结论

数据面 ~99% 核对项与不可变数据一致（修复后 100%）；引用面 20/20 一手核验通过（3 条修正后）；语境 26/26 忠实；方法学零失真；raw 全程零改动。**PASS WITH NOTES**——按协议，进入 Stage 5 FINALIZE 需要你在下述 MANDATORY checkpoint 上确认（PASS WITH NOTES 携带 §4 的 NOTE 列表进入，或先处理任意 NOTE）。

*本报告由 Stage 4.5 两独立席位产出 + 主会话修复轮与定向复检构成；修复轮由主会话执行并逐项 grep/PDF 验证，非席位自评。*
