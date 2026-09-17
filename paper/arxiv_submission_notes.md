# arXiv 投稿材料清单（v1.0.0-rc1，2026-09-16）

## 交付物

| 文件 | 说明 |
|---|---|
| `paper/mac-llm-bench-arxiv-v1.0.0-rc1.tar.gz` | arXiv 上传源码包（158,952 B；SHA-256 `c99976ca07312e488fea2e6d9cb115f905c1e5c3b5583e68e603332e356e13b0`） |
| `paper/submission/` | 与 tarball 内容一一对应的目录（main.tex、references.bib、main.bbl、figures/×8、tables/×6） |
| `paper/main.pdf` | 本地编译产物（11 页，与 tarball 构建文本层逐字节一致） |

包内结构（main.tex 位于根，figures/ tables/ 为一级子目录，符合 arXiv 要求）：

```
main.tex  references.bib  main.bbl
figures/  fig1..fig8 .pdf（脚本生成，TrueType 全内嵌）
tables/   table1..table6 .tex（脚本生成，由 main.tex \input）
```

## 提交表单元数据（可直接粘贴）

- **Title**: How Far Can 16 GB Go? Characterizing Memory-Efficient LLM Fine-Tuning on Consumer Apple Silicon
- **Abstract**: 见 main.tex abstract（提交时从 PDF 复制或用下方摘要文本）
- **建议分类**: 主分类 `cs.LG`；交叉 `cs.PF`（性能）、`cs.AR`（硬件架构）
- **Comments 草稿**: 11 pages, 8 figures, 6 tables; preregistered failure-inclusive benchmark; all numbers regenerated from immutable raw results by committed scripts (code and raw data to be released)

## 提交前可选项

- **作者块已填写**（`\author{Yuanyuan Ma}`，马远远）。如需补充单位/邮箱，改 `submission/main.tex` 后按下方命令重编译重打包：
  ```
  cd paper/submission
  pdflatex main && bibtex main && pdflatex main && pdflatex main
  cd .. && tar -czf mac-llm-bench-arxiv-v1.0.0-rc1.tar.gz -C submission main.tex references.bib main.bbl figures tables
  ```
- Comments 草稿中的代码仓库 URL 目前是占位表述，公开仓库后补链接（或删去）。

## 已验证项（本次打包时全部复验）

- [x] 隔离目录独立构建：pdflatex ×2（无 bibtex，使用包内 main.bbl）exit 0，11 页
- [x] tarball 本体抽取再构建：exit 0，0 Overfull、0 undefined citation/reference
- [x] 无 `..` 外部路径引用（arXiv 自包含硬要求）
- [x] 字体全内嵌且全为 Type 1 矢量（0 个 Type 3；matplotlib 图 fonttype=42，正文 ±/圆点走 cmsy 数学字体）
- [x] 参考文献 17 条全部经在线核验（台账 `research/literature_ledger.csv`）
- [x] 表格/图全部由 `scripts/run_analysis.py` 从 raw 结果程序化生成，无手写数字
- [x] 全部图表在最终 PDF 逐页视觉验收通过

## 复验命令

```bash
# 从 tarball 完整复验
tar -xzf paper/mac-llm-bench-arxiv-v1.0.0-rc1.tar.gz -C /tmp/v && cd /tmp/v
pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex
# 期望：exit 0；11 pages；main.log 中 0 Overfull、0 undefined

# 仓库内全链路再生成（会同步 paper/figures/，之后需重新编译 + 重打包）
uv run python scripts/run_analysis.py
```
