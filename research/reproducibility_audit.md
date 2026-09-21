# Reproducibility Audit — 2026-09-21 final correction

> 审计对象：冻结数据集（`research/experiment_freeze.md`）派生的全部
> processed 产物、图表、论文定量声明与引用。程序化检查由
> `scripts/audit_reproducibility.py` 与 `src/analysis/coverage.py` 执行；
> 本文档汇总 PASS / WARNING / unresolved limitation，不隐藏任何信号。

## 1. 程序化检查结果

| 检查 | 结果 | 说明 |
| --- | --- | --- |
| Coverage reconciliation | **PASS** | raw 118 == processed 118；每行机器可读 disposition（`coverage_report.json`，`reconciliation_ok=true`） |
| All-raw manifests | **WARNING** | 112/118 digest 复算通过；6 个 run 的 manifest 在位但与 finalized 后日志不匹配（D6 及其勘误；零聚合影响；不回写 raw） |
| Formal disposition | **PASS** | 19/19 formal groups 均有机器可读 success/failure/stopped disposition；failure-inclusive benchmark 不再要求每组必须 3/3 success |
| Dataset SHA-256 | **PASS** | formal_sft_v1 两个文件 hash 一致（n_files=2） |
| Model revisions | **PASS** | raw results 与 models/MANIFEST.md 无冲突 |
| key_numbers traceability | **PASS** | 全部关键数字可回溯 raw |
| Claim ledger | **PASS** | 15 条定量 claim 全部展开到 raw experiment IDs（`research/claim_ledger.csv`，claim → processed source → raw IDs → freeze ID） |
| Citations | **PASS** | main.tex 引用 14 = references.bib 14，全部在 literature_ledger（16 行含验证日期与引用理由）；无 uncited bib 条目 |
| Reproducibility script | **PASS WITH DECLARED WARNINGS** | `overall_status=PASS_WITH_DECLARED_WARNINGS`；唯一 warning 为上述 6 个 manifest digest |

## 2. 图表输入与生成链

- 全部 figures（fig1–fig12）/ tables / key_numbers / coverage /
  hypothesis audit / final semantic overlays 由 `scripts/run_analysis.py` 从冻结 raw
  一键重生成（generator commit `5c8675d` 之后），旧 processed 已删除
  重建（非增量）。
- 论文 PDF 只 include `results/figures/*.pdf` 与 `paper/tables/*.tex`
  （两者均程序生成）；正文数字以 `key_numbers.json` /
  `hypothesis_audit.json` 为源（claim ledger 记录映射）。

## 3. Git / 环境溯源

- Freeze 点 commit：`dcf84db`（数据）/ 冻结文档提交 `5c8675d`。
- 46 个 aggregation-included run 的分类为：9 clean、33
  dirty_dependency_files、3 dirty_nonexecution_artifact_only、1
  dirty_source_code；supervisor v0 未存 patch artifact（见 §4 WARNING）。
- 软件版本锁定：uv lock（Python 3.13.11 / mlx 0.32.2 / mlx-lm 0.31.3）。

## 4. Unresolved limitations（如实列出）

1. **Dirty-tree formal runs 无 patch artifact**：supervisor v0 的
   `git_patch` 恒 null（schema 要求 dirty run 附 patch 未实现）。
   缓解：trainer 演进链由 D5 commit 边界显式声明；影响评估有限但
   未消除。**WARNING，未解决**。
2. **Paging 指标是 whole-run proxy**：before/after swap-in 增量除以完成步数，
   含 load/validation/background，不是 optimizer-step paging rate。**已声明限制**。
3. **14B 为 boundary case 而非 3-seed formal cell**（D8 停止决策）。
   **已声明决策**，见 `paper` §Boundary Behavior at 14B。
4. **6 个 raw manifest digest warning**（D6 及勘误）。**已登记，不回写**
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
