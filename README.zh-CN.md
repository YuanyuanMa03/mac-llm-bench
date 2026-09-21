# mac-llm-bench

本仓库提供单台消费级 Apple Silicon 设备上内存高效大语言模型微调的可复现、包含失败运行的测量工件。

## 项目内容

本研究使用 Qwen3 0.6B 至 14B 模型，对比 BF16 LoRA 与 MLX 4-bit adapter fine-tuning。冻结语料包含 **118 个最终运行**，其中 **27 个失败运行**；**46 个运行**进入预注册聚合。仓库共同保留 raw 记录、processed 输出、图、配置、模型版本和 provenance。

## 硬件

所有报告数值来自单台配备 16 GiB 统一内存的 Apple M4 Mac。每个运行均记录硬件与软件版本。结果应解释为该机器及其已测机器状态下的观测。

## 方法

基准改变模型规模、最大序列长度上限、LoRA rank 和 micro-batch size。监督运行记录完整命令、Git commit、模型 revision、MLX 与 mlx-lm 版本、配置、环境、wall time、allocator peak、throughput、exit status，以及可用的逐步与系统状态轨迹。预注册和 D1-D12 偏离摘要位于 `research/`。

## 数据

- `results/raw/`：保留科研证据的公开成功与失败运行记录
- `results/processed/`：程序生成的表格与分析数据
- `results/figures/`：由 processed 与 raw 证据生成的图
- `data/formal_sft_v1/`：带校验和的冻结训练集与验证集
- `models/MANIFEST.md`：模型身份与固定 revision

## 主要观测

- 8B 4-bit 是本研究测试的最大配置，并在一个有利的已观测机器状态窗口内完成了预注册的三种子集合。
- 可行性随配置和机器内存状态共同变化。同一 4B BF16 配置在初始 swap residency 为零时完成训练，而在高 residency 条件下约 27 分钟未完成一个训练步。
- 在已测 4-bit 规模范围内，allocator peak memory 相对模型规模呈次线性变化（log-log slope 0.57 ± 0.05）。这是描述性缩放结果。
- 成对比较中，4-bit 运行的 allocator peak 为 BF16 LoRA 的 0.54-0.73 倍。步时比较采用修正后的 Tier-A/Tier-B 混合分层。
- 2048-cap workload 完成；首次观测失败来自单种子 synthetic 4096-cap probe。因此该结果是观测区间，不是物理或统计阈值。
- 有效的 2026-09-15 batch-8 三运行集合均在首个 optimizer step 完成前终止。D5 中较早的实现无效运行不作为该边界的正面证据。

## 复现

安装锁定环境并重新生成派生工件：

```bash
uv sync --locked
uv run python scripts/run_analysis.py
uv run python scripts/build_claim_ledger.py
uv run python scripts/audit_reproducibility.py
uv run python -m pytest tests/ -q
```

分析管线读取 `results/raw/`，重新生成 `results/processed/` 与 `results/figures/`。历史环境快照在公开发布前做了隐私脱敏，因此公开文件与保留的私有原件并非逐字节相同；benchmark 测量和科研字段保持不变，全部变化记录在 `release_sanitization_manifest.jsonl`。审计范围和已声明的完整性警告见 `research/reproducibility_public.md`。

## 局限

研究仅使用一台机器。时间和可行性受机器状态影响，系统级 swap 计数也不能把分页活动单独归因于训练进程。逐步时间动态、系统状态轨迹和内存分解中的部分分析属于事后探索。上下文上沿依赖单种子 synthetic probes。原有 6 个 D6 manifest warnings 与公开隐私脱敏分别记录。

## 论文

论文：arXiv 链接将在上传后补充。

## 许可与引用

见 `LICENSE` 与 `CITATION.cff`。
