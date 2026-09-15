# Reproducibility Audit — 2026-09-16（freeze-04f90a840b8ea8fb 之后）

> 审计对象：冻结数据集（`research/experiment_freeze.md`）派生的全部
> processed 产物、图表、论文定量声明与引用。程序化检查由
> `scripts/audit_reproducibility.py` 与 `src/analysis/coverage.py` 执行；
> 本文档汇总 PASS / WARNING / unresolved limitation，不隐藏任何信号。

## 1. 程序化检查结果

| 检查 | 结果 | 说明 |
| --- | --- | --- |
| Coverage reconciliation | **PASS** | raw 118 == processed 118；每行机器可读 disposition（`coverage_report.json`，`reconciliation_ok=true`） |
| Aggregated-run manifests | **PASS** | 46/46 `aggregation_included` run 的 SHA-256 manifest 复算通过 |
| All-raw manifests | **WARNING** | 113/118 通过；5 个 run 无 manifest（timeout/interrupted 类的 supervisor finalize 缺陷，deviation **D6**；全部处于 taxonomy/probe 处置，零聚合影响；按协议 §7 不事后补写） |
| Formal 3-seed completeness | **WARNING** | 15/16 组 3/3 success。`formal-axis1-4b-bf16-lora` 1/3（**D1**：1 success @零驻留 + 2 interrupted @高驻留，边界观测）；`formal-axis1-14b-4bit-qlora` 0/3（**D8**：probe success + interrupt + timeout，boundary case study——审计脚本的"3 seeds"规则不携带 D1/D8 语境，见 deviation ledger） |
| Dataset SHA-256 | **PASS** | formal_sft_v1 两个文件 hash 一致（n_files=2） |
| Model revisions | **PASS** | raw results 与 models/MANIFEST.md 无冲突 |
| key_numbers traceability | **PASS** | 全部关键数字可回溯 raw |
| Claim ledger | **PASS** | 15 条定量 claim 全部展开到 raw experiment IDs（`research/claim_ledger.csv`，claim → processed source → raw IDs → freeze ID） |
| Citations | **PASS** | main.tex 引用 14 = references.bib 14，全部在 literature_ledger（16 行含验证日期与引用理由）；无 uncited bib 条目 |
| LaTeX compile | **PASS** | pdflatex+bibtex 三轮：8 页，0 error，0 undefined reference |
| Tests | **PASS** | `uv run python -m pytest tests/ -q`：48 passed（含 D5 padding 14 项回归） |

## 2. 图表输入与生成链

- 全部 figures（fig1–fig8）/ tables（table1–table6）/ key_numbers /
  coverage / hypothesis_audit 由 `scripts/run_analysis.py` 从冻结 raw
  一键重生成（generator commit `f7fea5e` 之后），旧 processed 已删除
  重建（非增量）。
- 论文 PDF 只 include `results/figures/*.pdf` 与 `paper/tables/*.tex`
  （两者均程序生成）；正文数字以 `key_numbers.json` /
  `hypothesis_audit.json` 为源（claim ledger 记录映射）。

## 3. Git / 环境溯源

- Freeze 点 commit：`c5b9178`（数据）/ 冻结文档提交 `f7fea5e`。
- 每个 raw run 记录 git commit + dirty 状态（80/81 历史 formal run 为
  dirty，supervisor v0 未存 patch artifact——见 §4 WARNING）。
- 软件版本锁定：uv lock（Python 3.13.11 / mlx 0.32.2 / mlx-lm 0.31.3）。

## 4. Unresolved limitations（如实列出）

1. **Dirty-tree formal runs 无 patch artifact**：supervisor v0 的
   `git_patch` 恒 null（schema 要求 dirty run 附 patch 未实现）。
   缓解：trainer 演进链由 D5 commit 边界显式声明；影响评估有限但
   未消除。**WARNING，未解决**。
2. **全部时间类 formal 数据为 Tier-B**（D4：>50 MB swap-in/步）——绝对
   步时不可跨窗口比较；论文只报告窗口内比值。**已声明限制**。
3. **14B 为 boundary case 而非 3-seed formal cell**（D8 停止决策）。
   **已声明决策**，见 `paper` §Boundary Behavior at 14B。
4. **5 个 legacy run manifest 缺失**（D6）。**已登记，不可修复**
   （不可变原则），零聚合影响。
5. **staging partials ×3**（未 finalize，含 2026-09-15 14B s123 被杀
   partial）留磁盘未提交，不作为正式 result。**按协议处理**。
6. thermal / energy / 进程级峰值内存：无已验证采集路径，raw 中为
   null（协议 §4 既定）。
7. `system_profiler` GPU 核心数无已验证来源键（hardware.gpu_cores=null，
   设计如此，非遗漏）。

## 5. 结论

除上述已登记 deviations 与 inherent limitations 外，本仓库从
raw 不可变结果 → processed 派生 → 图表 → 论文数字的链路可一键复算、
可审计（claim ledger 逐条到 raw ID）；论文编译干净。**总体判定：
PASS with declared warnings（D1/D4/D5/D6/D8 均在 ledger 与论文中如实
呈现）**。
