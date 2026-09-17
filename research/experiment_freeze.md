# Experiment Freeze — 2026-09-15T22:17:33Z

> 数据采集终止点。本文件之后，`results/raw/` 不再有新实验；后续全部
> 工作（analysis / paper）都从这一冻结版本派生。Raw 文件不修改。

## Freeze identity

| 项 | 值 |
| --- | --- |
| Freeze ID | `freeze-04f90a840b8ea8fb` |
| Freeze manifest | `research/experiment_freeze_manifest.sha256`（每个 finalized run 的 `manifest.sha256` 文件哈希清单；5 个 manifest 缺失 run 记为 `MISSING:<id>`，见 D6） |
| Freeze manifest SHA-256 | `04f90a840b8ea8fb3e60c3ccb18df88e6596e23e431d5be354a8b35a553532e5` |
| Git commit at freeze | `dcf84dbc9dfb770bc315cae26ccc047900233a6e` |
| Freeze timestamp (UTC) | 2026-09-15T22:17:33Z |

## Counts（全部来自 finalized `results/raw/*/result.json`，逐个读取）

| 计数 | 值 |
| --- | ---: |
| Finalized raw experiments | **118** |
| Formal runs | 97 |
| Probe runs | 11 |
| Other（calibration / exp0-smoke） | 10 |
| Failures（terminal_state ≠ success） | 27 |
| Implementation-invalid（D5 签名） | 9 |
| Valid formal successes（进入聚合的候选，去重前） | 75 |
| Validation/warmup 目录（results/validation/，不入 formal） | 18 |
| Unfinalized staging partials（保留磁盘，不作为正式 result） | 3（2026-09-12 8B s123、2026-09-12 4B-bf16 s123、2026-09-15 14B s123） |

## Highest reproducible formal model scale

**8B 4-bit QLoRA**（`formal-axis1-8b-4bit-qlora`，seeds {42,123,2026}
全部 success：1{,}644 / 1{,}670 / 1{,}694 s，100 步 @ctx512）。
这是本 benchmark 的 reproducible formal boundary（主论文模型规模
边界的主要证据）。

## 14B 的显式定位（D8 决策）

14B-4bit **不作为 missing formal cell，也不作为失败格**，定位为
**system-state-dependent boundary configuration**（boundary case
study / exploratory evidence）：

- 证据 1（favorable）：短程 probe（swap 2.7 GiB）0.68 s/步完成 20 步；
- 证据 2/3（formal 负载下）：24 min 零步（swap 7.1 GiB，操作者中断）、
  50/100 步后 timeout（加载 ~40 min，step_time 27–86 s，swap 3.7 GiB
  起始）；
- 解释约束：observed to enter training under favorable conditions,
  but not reproducibly sustained under the formal workload；
- 禁止表述：formally reproducible / stable / practical /
  impossible / OOM。

## Unresolved cells（显式清单）

| 格 | 状态 | 依据 |
| --- | --- | --- |
| 14B-4bit ctx512 formal 3 seeds | **停止（D8）**：1 timeout + 1 interrupted + 1 未启动；已有证据转 boundary case study | D8 |
| 14B-4bit ctx2048 probe | **取消（D8）**，从未执行 | D8 |
| 4B BF16 LoRA formal 3 seeds | D1 降级为边界观测（1 success @低驻留 + 2 interrupted @高驻留） | D1 |
| 8B BF16 formal | 预注册即仅 probe（timeout），非缺口 | preregistration §3 |
| 14B BF16 | declared out-of-budget（非观测） | preregistration §3 |

## Accounting invariant（freeze 时刻复核）

raw_total (118) == processed rows (118) == included + excluded
（机器可读 disposition 见 `results/processed/coverage_report.json`，
由 `src/analysis/coverage.py` 在 freeze 后的全量重建中生成并校验）。
