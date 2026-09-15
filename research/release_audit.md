# Release Audit — v1.0.0-rc1（2026-09-16）

> 审查范围：论文、README、claim ledger、figures/tables、reproducibility
> audit、公开仓库卫生、复现链、新增交付物。Raw results 零修改，实验
> 结论零变更。本文件列全部 PASS / WARNING，不隐藏。

## A. 论文一致性

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| LaTeX 编译 | **PASS** | 8 页、0 error、0 undefined reference（pdflatex+bibtex×3） |
| 定量数字溯源 | **PASS** | 15 条 claim 全部展开 raw IDs（`claim_ledger.csv`）；正文关键数字抽查（0.54/0.73/0.57/1.00/9.19/42.9/89.5/66.4/34.6/6.19/10.04/16.98/23.9/1.93/1.81/1.63/1.55/4.44/1{,}644–1{,}694/451/118）全部命中 key_numbers/audit 派生值 |
| 过度 claim 扫描 | **PASS** | 禁用词 zero-cost / proves / maximum supported model / impossible / 14B practical / linear scaling：0 命中；14B 全部以 "boundary case / observed / suggests" 限定 |
| 缩写首现展开 | **PASS**（本轮修复 4 处） | SoC / RSS / SIGKILL(POSIX signal 9) / LM 首现均展开；MLX/LoRA/QLoRA 带 cite |
| 图表引用 | **PASS** | `\ref`/`\input`/`\includegraphics` 全解析（0 undefined）；fig3/5/7 + table1–6 嵌入 |
| 图表与论文口径一致 | **PASS** | tables/figures 由 `run_analysis.py` 与正文同一 processed 源生成（fig2 五级状态含 14B=state-dependent 紫） |

## B. 仓库卫生

| 检查 | 结果 | 证据 / 处置 |
| --- | --- | --- |
| 误入 Git 的临时/工具文件 | **PASS**（已清理） | `.video_agent/plugin_root`（工具 marker，内容为插件缓存路径）与 `paper/main.{aux,bbl,blg,log,out}` 已 `git rm --cached`；`.gitignore` 补规则 |
| staging 文件 | **PASS** | 3 个 `.staging` partial 均未跟踪（gitignore `*.staging/`），不属数据集 |
| 模型大文件 | **PASS** | `models/` 仅 `MANIFEST.md` 被跟踪；权重目录 ignored；tracked 最大文件为冻结数据集 `train.jsonl`（12 MB，有意发布） |
| 非 raw 文件的绝对本地路径 | **PASS**（已清理） | `docs/models_disk_usage.md`、`research/current_state.md` 已脱敏为 `<repo(-volume)>`；processed CSV 经 flatten 层 sanitize（0 本地路径，数字不变：8B 10.039 s / recon_ok=true，48 tests passed） |
| raw 证据中的本地路径与用户名 | **WARNING** | 289 个 raw 文件含本机路径（working_directory、环境快照等）——协议 §7 不可变要求下保留，属 provenance；公开发布时接受此披露 |
| 隐私（serial / machine id） | **PASS** | serial_number 字段采集时即 `[REDACTED]`；machine_id 恒 null（协议设计）；mac_model 为通用标识 `Mac16,10`；无序列号/主机名值 |
| git 历史残留 | **WARNING** | 早期误跟踪的 `.DS_Store`/pyc 仍在历史 blob 中（改写历史需 force-push，不做）；当前树干净 |
| 内部工作文档 | **WARNING**（无害保留） | `PROMPT.md`（prompt 工作台账）随库公开；无个人信息，保留以完整记录研究过程 |

## C. 复现链（干净环境）

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 命令引用有效性 | **PASS** | README Quickstart 与 paper appendix 引用的 11 个脚本/配置/数据路径全部存在 |
| 环境锁定 | **PASS** | `uv.lock`；Python 3.13.11 / mlx 0.32.2 / mlx-lm 0.31.3（raw 记录一致） |
| 一键重算 | **PASS** | `uv run python scripts/run_analysis.py` 从冻结 raw 重建全部 processed（本轮两次全删重建验证，对账不变） |
| 测试 | **PASS** | 48 passed（含 D5 padding 14 项回归） |
| 论文编译独立可复现 | **PASS** | pdflatex+bibtex 序列本轮多次执行成功 |
| 重跑实验（可选） | **WARNING** | 需自备 `models/`（git-ignored；MANIFEST 给出 8 个 HF revision 锚定）与 Apple Silicon 硬件；数字与冻结库对比需注意 Tier-B/系统状态（D4/D1） |

## D. 交付物补齐

| 项 | 结果 |
| --- | --- |
| `LICENSE` | **PASS**（MIT + 数据/模型 supplementary notices；如需其他协议可替换，数字与结论不受影响） |
| `CITATION.cff` | **PASS**（cff 1.2.0；version 1.0.0-rc1；freeze ID 作为 dataset identifier）。**WARNING**：`repository-code` 为占位 `https://github.com/anonymous/mac-llm-bench`，公开发布时替换真实地址 |
| `RELEASE_NOTES.md` | **PASS**（含 headline findings、known warnings、复现命令） |
| README Quickstart | **PASS**（最小复现 5 步） |
| README 状态表 | **PASS**（已更新至 freeze 终态；`README.zh-CN.md` 仍为旧版——**WARNING**，未在本轮同步） |

## E. 既有声明的承接（reproducibility_audit.md 已覆盖）

D6（5 manifest 缺失）、D4（全 Tier-B 时间数据）、supervisor dirty-patch 未实现、14B=D8 boundary case、3 个 staging partial——全部保持已登记状态，无新增问题。

## Git tag 建议（不自动执行、不发布）

```bash
git tag -a v1.0.0-rc1 -m "Release candidate 1: frozen dataset freeze-04f90a840b8ea8fb (118 finalized runs); paper 8pp; coverage 118=118; claim ledger 15; deviations D1-D8"
```

建议在上述 WARNING 中的两项可选修复（CITATION 占位 URL、README.zh-CN 同步）完成后打 tag；或接受现状直接打——两者均不阻塞 RC。

## 总体判定

**PASS with declared warnings**——可进入 RC。发布前唯一必改项：CITATION.cff
的真实仓库地址（占位符）。其余 WARNING 均为已声明、可接受的披露
（raw provenance 路径、git 历史残留、zh-CN README 未同步）。
