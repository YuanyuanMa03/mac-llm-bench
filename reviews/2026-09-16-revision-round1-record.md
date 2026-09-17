# Revision Round 1 — Record（adjudication · R→改动映射 · apply report）

- **日期**: 2026-09-16；**上游**: `reviews/2026-09-16-panel-review-round1.md`（五席位评审，Major Revision）
- **模式**: `academic-paper` revision（#390 patch 协议的手工等效执行：anchorize/apply 脚本在本环境不可用，全部改动经精确锚定替换完成，blast radius 限于 roadmap 覆盖块）
- **编译终态**: pdflatex+bibtex 干净（0 error / 0 undefined citation），14 页；overfull 残余均 <8pt。
- **数字生成纪律**: 论文全部新数字由 `src/analysis/revision_round1.py` 与修复后的 `src/analysis/flatten.py` / `tables.py` / `figures.py` 从 `results/raw/` 全量重算（`scripts/run_analysis.py`），无手打。

## 1. Author Adjudication（14 项全部 will_address）

| 项 | 处置 | 路径选择 |
|---|---|---|
| R1 | will_address | 撤回统计措辞 + 配对 t/Welch 检验程序化（`val_loss_tests.json`） |
| R2 | will_address | 附录偏差表 D1–D9 + git 冻结证据（`3dc33d2`）+ deviations.md 追加 D9 |
| R3 | will_address | (a)(b)(d) 文本+数据修正；(c) 选 Tier-B 限定措辞路径（未跑 8B 轻载 probe） |
| R4 | will_address | 敏感性表 + t-CI 表 + 每对比值范围 + 幂律 vs affine + 斜率 CI |
| R5 | will_address | 跨窗口 53% 漂移例证化（3.66 vs 5.62 s）+ Table 5/6 paging 列 + 删除 0.22/3.66 例证 |
| R6 | will_address | **取证成功**：kernel JetsamEvent（b8 run3）入附录 C；其余 5 kill 中性标注 |
| R7 | will_address | 协议操作化小节（§6.2）；vm_stat 快照已含 compressor（披露）；1 Hz compressor 轨迹与 per-process footprint 未加采（协议 v2 讨论路径） |
| R8 | will_address | §3.5 "QLoRA semantics on MLX" 段 + §2.3 paged optimizer 对照 |
| R9 | will_address | 标题/贡献 (i)/摘要收窄为单机定位；第二配置锚点未跑（收窄路径） |
| S1 | will_address | 补引 3 篇（一手核验；**LOMO 编号 2306.09782 系复核纠正，评审稿的 2402.12305 为误引**） |
| S2 | will_address | R² 0.99→0.985、14B residency 统一为 CSV 口径、manifest 5→6、fig2 ctx512 "reuse a1"、Table 4 对齐 D8 |
| S3 | will_address | MIT license、10-core (4P+6E)、模型命名、±0.00 注、bib 卷号/URL/年份。（Round-2 更正：14B 参数量回填**未成立**——processed 数据中 14B formal 与 probe 均未落盘 `tm.logical_parameter_count`，按不补猜测值规则 Table 2 的 14B 行保持无参数量，模型规格引用 yang2025qwen3） |
| S4 | will_address | 8B 首试 timeout + 单窗口限定 + CP 下限 0.29 + ctx2048 s123 首试披露 + 重跑不对称声明（§6.4）+ timeout 敏感性声明 |
| S5 | **部分**（consider 级） | 未单独成段；终端用户运营变量（温度/SSD 写入/磁盘预算）未展开，遗留为 known gap |

## 2. R→改动映射

| Ref | 论文位置 | 改动 | 验证 |
|---|---|---|---|
| R1 | §4.4 重写 | 删除 "statistically indistinguishable"；改为如实报告差值 0.085–0.113 + 配对 t=70.4 (p=2e-4) / t=13.4 (p=0.006) + "100-step LM loss 不能建立质量等价"；§4.7 措辞同步 | `val_loss_tests.json`；PDF grep 确认旧措辞 0 次 |
| R2 | 附录 B 新增 | D1–D9 汇总表 + `3dc33d2` 冻结证据；`research/deviations.md` 追加 D9（H2/H6 规则修订 + tier 缺陷） | git log 时间戳可回溯 |
| R3 | §4.3 重写（`\label{sec:timingscale}`） | 真实混合分层（0.6B/1.7B-4bit 等 Tier-A 8–33.8 MB/步；4B/8B Tier-B 100–848）+ Table 7 + 缺陷披露（D9）+ ">50MB/step" 全称断言删除 + 4B ratio † 跨窗口标注（Table 3 + 摘要 "both fully paired scales"）+ 8B "not efficient" Tier-B 限定（§6.1） | `tier_classification.json`；audit `tier_a_runs: 6` |
| R4 | §4.2 重写、§4.3、表 8/9 | 斜率 CI（4bit mem [0.37,0.78] 不含 1；BF16 [-0.22,1.65] 无推断力）+ 幂律 vs affine（ΔAIC 3.2 / −8.7；affine intercept 1.8/1.3 GiB 量化固定开销）+ "reject/naive" 措辞撤回 + ±2× 敏感性表（8B P2 在 10 s fail、20 s pass 翻转如实呈现）+ 3/3 CP 下限 0.29 | `slope_confidence_intervals.json`、`scaling_model_comparison.json`、`threshold_sensitivity.json` |
| R5 | §4.3 + §4.5 + Table 5/6 | 3.665 vs 5.620 s（53% 窗口漂移）作 Tier-B 例证；0.22/3.66 probe 例证删除（workload 19 vs 489 tok/步不可比）；Table 5/6 加 swap-in 列（b4 达 13.1–13.6 GB/步） | CSV `_swapin_per_step` 权威列 |
| R6 | §4.5 + §5 + 附录 C + Table 4 | 类名 "External SIGKILL (memory pressure)"；附录 C 记录 `JetsamEvent-2026-09-16-004948.ips`（largestProcess=python3.13，驻留 23.5 GiB，compressor 12.5 GiB，free 59 MiB，24 进程被 jettison）；证据文件固化至 `research/evidence/` 带 SHA-256 | 一手 kernel 报告 + 时间窗对齐 run3 |
| R7 | §3.6 + §6.2 重写 | 采集范围披露（vm_stat 快照含 compressor；1 Hz 仅 swap）+ 采样局限三条入文；residency 必备字段的操作化协议（swap before/after/1 Hz 峰值 + vm_stat + footprint）+ clock-state 类比局限 + measure-vs-control 双路线及 D8 理由 | 正文/附录交叉引用 |
| R8 | §3.5 新段 + §2.3 | group-wise 4-bit ≠ NF4、无 double quantization、无 paged optimizer、常规 AdamW；与 QLoRA 文献可比边界声明；paged optimizer（GPU 框架可控分页）vs macOS OS 级全局分页对照 | mlx-lm 官方文档（R2 席位一手核验） |
| R9 | 标题/摘要/贡献 (i) | "on a Single Consumer Apple Silicon Mac"；贡献 (i) 加 "on a single M4/16 GiB machine"；摘要 "within one favorable residency window" | 标题/hypersetup 同步 |
| S1 | §2.1/§2.3/§2.4 + bib | baral2026distillation（2606.31048）、geng2025mobilefinetuner（2512.08211）、lv2024lomo（2306.09782）；"has so far focused" 软化；§2.1/§2.4 去重 | 三篇均经 arXiv 一手页面核验（含 LOMO 编号纠正） |
| S2 | 各处 | R²=0.985（与 `step_time_scaling_fits.json` 0.9848 一致）；14B residency 2.5/6.6/3.5 GiB（CSV `initial_swap_bytes`）；manifest "six runs"；Table 4 D8 KeyboardInterrupt 对齐；fig2 ctx512 → "✓ (reuse a1)"；Table 4 context-boundary 行删除（正文 §4.6 已有） | 表格重生成 + figures.py 重跑 |
| S3 | Table 1/2 + §6.5 + bib | "10-core (4P+6E, 10 logical)"；Table 2 caption ±0.00 语义 + 14B 参数量（probe 实测回填）；"MIT license"；`qwen3-0.6b` 命名；NeurIPS 卷号格式、llamacpp URL、ajayi 年份 | tables.py 派生 |
| S4 | §4.1/§4.6/§6.1/§6.2/§6.4 | 8B 首试 timeout（16.4 GiB）+ 三连成功窗口（3.6–4.8 GiB）；ctx2048 s123 首试 SIGKILL（7.66 GiB）→ 2.96 GiB 重跑；§6.4 显式声明重跑不对称（D7 information-gain vs D1/D8 定格）+ 14B timeout(7200 s) 敏感性未测声明 | coverage_report/CSV 双向核对 |
| S5 | —（部分） | 见 adjudication | — |

## 3. Apply Report

- **编译**: 3×pdflatex+bibtex，0 error / 0 undefined；14 页。
- **数字一致性**: 论文↔processed 抽查通过（0.54–0.73、[0.37,0.78]、[0.62,1.37]、t=70.4/13.4、23.5 GiB、12.5 GiB、59 MiB、CP 0.29、16.4/2.96/7.66 GiB、13.1–13.6 GB、231–339 MB、3dc33d2、six manifests）；旧错误陈述 grep 0 次（"statistically indistinguishable"/"All timing figures"/"no measurable time cost"/"sits at the practical threshold"/"research-permitted"/"eight preregistration"/"the OS terminates"）。
- **零漂移确认**: 重算后核心聚合不变（8B 9.19 GiB/10.039 s/42.9 tok/s；4B 6.19/3.665/137.2；fits 斜率 0.5725/0.9966；H1–H6 判定不变）。
- **分析管线变更**: `flatten.py::_swapin_per_step` 兼展平列名（根因修复，正文以 D9 披露）；`tables.py`（T1/T2/T3/T4/T5/T6 增强）；`figures.py`（fig2 ctx512）；新增 `revision_round1.py`（5 个 JSON + 3 张新表）。
- **新产物**: `results/processed/{tier_classification,val_loss_tests,threshold_sensitivity,scaling_model_comparison,slope_confidence_intervals}.json`；`paper/tables/table{7,8,9}_*.tex`；`research/evidence/JetsamEvent-*.ips(+.sha256)`；deviations.md D9。
- **未做/降级**（诚实清单）: 8B 轻载 probe、第二配置锚点、1 Hz compressor 轨迹与 per-process footprint 加采、non-weight 开销的 KV/激活分解、S5 终端用户运营变量段——均按 roadmap 提供的文本替代路径处理或明示遗留。

## 4. Round-2 Residual Fixes（re-review 触发，2026-09-16）

独立 re-review（三门契约）判定 R1、R3–R9 共 8 项 must_fix RESOLVED、R2 PARTIALLY（两处文本缺口），另列 4 项 minor 新问题与 2 项声明失实。全部残留于当日修复：

| 来源 | 修复 | 验证 |
|---|---|---|
| R2 缺口① | 附录 B D9 行补 "under v1 the H2 verdict would read *not supported*" | PDF grep 1 |
| R2 缺口② | §4.6 H6 引用处加 "v2 rule; the preregistered-era v1 rule and its revision are disclosed as D9" | PDF grep 1 |
| New#1 | 摘要 "trains at zero swap residency" → "zero or low swap residency"（14B probe 实为 2.5 GiB） | PDF grep 1 |
| New#2 | §6.1 swap-growth 数字改标 "per-run peak-minus-initial swap in the processed data"（Table 8 只承载 pass/fail 模式） | PDF grep 1 |
| New#3 | 附录 D3 行删 12.9 GiB 口径（与 CSV 6.64 并存矛盾），改 "stalled 24 minutes under multi-GiB residency" | 重编译通过 |
| New#4 | Table 7 caption 注明排除 axis1b 重复保留组 | 重生成 |
| Mismatch#1（S5） | Limitations 加运营变量范围声明（thermal/SSD wear/磁盘/外推 out of scope）——按 Gate 1 预承诺（"显式声明超出范围即 RESOLVED"）转 RESOLVED | PDF 文本确认 |
| Mismatch#2（S3） | 14B 参数量回填撤销：数据源缺失，不补猜测值；本记录声明同步更正 | CSV 排查（formal+probe 均 NaN） |
| S4 残留 | §2.4 加 "no published quantitative boundary to compare against" 的检索性 absence 声明；§4.9 补 7,200 s 为 supervisor 全局配置上界（Table 4 证据）+ 敏感性未测声明 | PDF grep 各 1 |

修复后终态编译：0 error / 0 undefined / 0 bibtex warning，14 页；overfull 残余 <8pt。

## 5. 下游

修后复核走 `academic-paper-reviewer` re-review 模式（三门契约 + R&R Traceability Matrix，以本文件的 R→改动映射为核对基准）。
