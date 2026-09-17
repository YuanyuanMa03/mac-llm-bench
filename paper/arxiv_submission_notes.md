# arXiv 投稿材料清单（v1.0.0-rc1，2026-09-17）

## 仓库边界（2026-09-17 用户定调）

- **GitHub 仓库 = 实验过程**（代码、raw 结果、分析管线、审计与评审记录）；
  **论文文字成果只经 arXiv 发布，LaTeX 源码不进仓库**（`paper/main.tex`
  等已从 git 删除；git 历史中的旧版本属于过程记录，已经 D10 隐私改写审计）。
- 论文源码目录 `paper/submission/` 与 tarball 均为 git-ignored 可再生物；
  `scripts/run_analysis.py` 重算后 figures/tables 直接写入 `paper/submission/`。
- 注意：arXiv deposited source 默认对公众开放下载（论文源码经 arXiv 仍公开，
  只是托管地不同）；arXiv 不可撤稿，只能以新版本迭代。

## 交付物

| 文件 | 说明 |
|---|---|
| `paper/mac-llm-bench-arxiv-v1.0.0-rc1.tar.gz` | arXiv 上传源码包（829,120 B；SHA-256 `fbeadee0eabb78835760d33475a2953a8fb3e2823272f3edb11c4ca4d6597f30`） |
| `paper/submission/` | 与 tarball 内容一一对应的源码目录（编译产物 main.pdf/aux/log 不上传） |

包内结构（main.tex 位于根，figures/ tables/ 为一级子目录，符合 arXiv 要求）：

```
main.tex  references.bib  main.bbl
figures/  fig1_architecture.png（作者手绘，1471×609，已裁除图内标题/说明带；
          约 210 dpi @ 7in，若绘图源文件可导出 2× 分辨率更佳）
          fig2..fig8 .pdf（脚本生成，TrueType 全内嵌）
tables/   table1..table10 .tex（脚本生成，由 main.tex \input）
          + main.tex 内联 2 表（失败处置审计表等）
```

规模：**16 页、8 figures、13 tables（12 生成 + 1 附录偏差摘要引用台账）、bib 20 条**。
版式：**IEEE 会议风格**（Times 正文 + CM 数学/真小型大写 + 罗马节号 + run-in Abstract/Index Terms，纯本地宏包实现于导言区，无外部 .cls 依赖——arXiv 自包含）。
编译门：err=0 / undefined=0 / overfull=0 / Type3=0（首次全绿；此前版本带有被 nonstopmode 吞掉的表格下划线与列定义错误，已根治）。

## 提交表单元数据（可直接粘贴）

- **Title**: How Far Can 16 GB Go? Characterizing Memory-Efficient LLM Fine-Tuning on Consumer Apple Silicon
- **Abstract**: 见 main.tex abstract（提交时从 PDF 复制）
- **建议分类**: 主分类 `cs.LG`；交叉 `cs.PF`（性能）、`cs.AR`（硬件架构）
- **Comments 草稿**: 15 pages, 8 figures, 12 tables; preregistered failure-inclusive benchmark; all numbers regenerated from immutable raw results by committed scripts (code and raw data at github.com/YuanyuanMa03/mac-llm-bench)
  - 仓库当前 **PRIVATE**：Comments 引用仓库 URL 的前提是先转 public
    （`gh repo edit YuanyuanMa03/mac-llm-bench --visibility public`），
    转公开与上传的先后由用户控制。

## 提交前可选项

- **作者块已填写**（`\author{Yuanyuan Ma}`，马远远）。如需补充单位/邮箱，改
  `paper/submission/main.tex` 后按下方命令重编译重打包：
  ```
  cd paper/submission
  pdflatex main && bibtex main && pdflatex main && pdflatex main
  cd .. && tar -czf mac-llm-bench-arxiv-v1.0.0-rc1.tar.gz -C submission main.tex references.bib main.bbl figures tables
  ```
- 投稿前建议补 Turnitin/iThenticate 查重（Stage 4.5 Phase D 当年未做 web 抽查）。
- 若后续投双盲评审的会议/期刊，实名仓库与 arXiv 版本会破坏匿名性，时序由用户控制。

## 已验证项（2026-09-17 本轮全部复验）

- [x] fig1 换作者手绘版：裁除图内自带的标题带与说明文字带（避免与 LaTeX
      caption 重复），main.tex 引用改为 .png；重编译 15 页/0/0；第 4 页
      渲染视觉验收（无内部标题、无裁切、无重叠）；
      `figures.py _save` 已加防回写保护（重跑管线不会把 matplotlib 版
      fig1 带回论文目录）
- [x] tarball 抽取独立构建：pdflatex ×2（包内 main.bbl，无 bibtex）exit 0，
      **17 页**，0 Overfull、0 undefined（产出 1,145,180 B，与
      `paper/submission/` 本地构建报告尺寸一致）
- [x] figures 与 `results/figures/`（2026-09-17 二轮重绘版）逐字节一致
- [x] 本轮新增内容隐私扫描（main.tex/全部 tables/分析脚本）：本地路径、
      用户名、机器标识 0 命中；唯一机器相关引用为 JetsamEvent 文件名取证
      引用（.ips 原件不在仓库与历史）
- [x] 表格/图全部由 `scripts/run_analysis.py` 程序化生成（tables.py 输出
      `paper/submission/tables/`），无手写数字
- [x] bib 20 条此前全部一手核验（台账 `research/literature_ledger.csv`），
      本轮未改动参考文献
- [x] 旧 SHA 全部作废：`c99976ca…`、`2aceb876…`、`8c35316e…`、
      `046d373a…` → 现行 `fbeadee0…`
- 字体全内嵌/0 Type 3 继承前轮验证；如 PDF 再变，重跑 `pdffonts` 复检

## 复验命令

```bash
# 从 tarball 完整复验
tar -xzf paper/mac-llm-bench-arxiv-v1.0.0-rc1.tar.gz -C /tmp/v && cd /tmp/v
pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex
# 期望：exit 0；15 pages；main.log 中 0 Overfull、0 undefined

# 仓库内全链路再生成（figures/tables 直接写入 paper/submission/，
# 之后在 paper/submission/ 重跑 pdflatex+bibtex 并按上方命令重打包）
uv run python scripts/run_analysis.py
```
