# Measurement validation（测量体系验证）

版本：2026-09-11（Phase 2）。验证脚本：`scripts/validate_measurements.py`；
验证报告：`results/validation/measurements-20260911/report.json`。
本文回答一个唯一的问题：**哪些指标可以进入论文，哪些必须保持 null。**

## 1. 结论总表

| 指标 | 来源 | 单位 | scope | 同步要求 | 采样 | 开销 | 论文可用性 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| wall-clock time | supervisor `time.monotonic`（start→end，含模型加载） | s | 子进程全程 | 不适用 | 单次 | ≈0 | ✅ 可用（注明 scope） |
| per-step time | trainer：`perf_counter` 包裹 fwd+bwd+optimizer+`mx.eval` | s/step | 单优化器步 | **必须有 `mx.eval` 同步**（见 §2A） | 每步 | ≈0 | ✅ 可用 |
| tokens/s | trainer：measured loss-bearing tokens ÷ measured step-time 和 | tokens/s | measured 步区间 | 同上 | 派生 | — | ✅ 可用（口径见 §3） |
| completed steps | trainer step 计数 | count | 优化器步 | — | 每步 | ≈0 | ✅ 可用 |
| exit status / terminal state | supervisor 分类器（真实 returncode/signal/exception） | enum | 子进程 | — | 单次 | ≈0 | ✅ 可用 |
| MLX peak GPU memory | 训练进程 `mx.metal.get_peak_memory()`（=新 API `mx.get_peak_memory()`） | bytes | MLX 分配器 Metal buffer 高水位 | 须在 `mx.eval` 后读取（trainer 位于循环后）✅ | 每运行一次 | ≈0 | ✅ 可用，**必须声明口径**（见 §2B） |
| swap before/after | supervisor `sysctl vm.swapusage` 快照 | bytes | **系统级**（全体进程） | — | before/after | ≈0 | ✅ 可用作上下文（声明系统级） |
| swap peak（周期采样） | monitor 线程同源采样最大值 | bytes | 系统级 | — | 1 s（可配） | 0.2s 间隔实测 1.47% 单核（§2D）→ 1s 可忽略 | ✅ 可用（2026-09-11 起启用 `sample_swap: true`） |
| peak process RSS | `/usr/bin/time -l` | bytes | 进程 | — | 单次 | 未实测对 MLX 工作负载的影响 | ❌ 未验证 → null（见 §4） |
| peak system memory | 无已验证聚合定义 | — | — | — | — | — | ❌ null |
| page faults | `/usr/bin/time -l` 标签 | count | 进程 | — | 单次 | — | ❌ 语义未验证 → null |
| thermal / energy | 无可用可靠来源（powermetrics 需 root 且为估计值） | — | — | — | — | — | ❌ null |

## 2. 验证证据（2026-09-11 实测）

### A. MLX 异步执行对 step timing 的影响

同一 2048×2048 深链路工作负载（8 层 matmul+exp），60 次迭代：

- 无同步（只派发不 eval）：总时长 ≈ 同步模式的 **1/4571**
- 每迭代 `mx.eval`（trainer 实际模式，`src/train/lora_smoke.py:141`）：真实 GPU 时间

**结论**：无同步计时会把 step time 低报约三个数量级；我们的 collector 在每个
优化器步后调用 `mx.eval(model.parameters(), optimizer.state)` 并读取
`float(loss)`，同步点必要且已存在。✅ 通过。

### B. MLX peak memory 语义

请求分配 1 GiB（`mx.zeros(2^28, float32)`），`mx.reset_peak_memory()` 后测量：

- `get_active_memory` 增量 = 1,073,741,824 B（误差 < 1 MiB）✅
- `get_peak_memory` 增量 = 同上 ✅（先前未 reset 导致 peak 单调不回落——
  验证脚本已修正；**这同时证明 peak 是高水位口径**）
- deprecated `mx.metal.*` 读取值与 `mx.*` 新 API 完全一致 ✅（trainer 用旧 API，
  报告注明两者等价于本安装版 mlx 0.32.2）
- `clear_cache` 后 active 回落 → cache 不计入 active

**口径声明（论文必须原样使用）**：`peak_metal_gpu_memory_bytes` = MLX 分配器的
Metal buffer 高水位，**不是进程 RSS，不是系统内存占用**。在统一内存机器上，
当该值超过物理 RAM（如 ctx2048 probe 报告 23.19 GB > 16 GiB），超出部分由
macOS 换页承载，表现为严重 swap 与步时膨胀——此时该值仍如实反映 MLX 侧
峰值需求，但步时不再反映纯计算代价。

### C. Raw result 算术一致性

16 个含 `step_timings.jsonl` 的 raw result 全部按其**各自声明的测量口径**重算：
`successful_steps` 计数、avg/median step time、tokens/s 全部一致（< 1e-6 相对误差）。✅

发现并修正检查器的两个初版误报，它们本身即是有价值的发现：

1. 校准 run（prompt07-08）声明 `excluded_warmup_steps=10`，summary 口径为
   排除后的 90 步——检查器初版未剔除 warmup。
2. **吞吐分母存在跨版本定义变化**：prompt06 时代 `throughput_interval_definition`
   = "仅训练循环"（分母含循环开销，`training_loop_seconds`）；prompt07 起 =
   "排除 warmup 后的 measured step-time 之和"。两版均在结果中如实声明了定义
   （schema 强制字段发挥了作用）。**论文只使用 prompt07+ 口径的吞吐数字**；
   prompt06 的 2 个 success run 的 tokens/s 如需引用必须换算或标注差异。

### D. Swap 周期采样器（2026-09-11 新增）

`src/benchmark/monitor.py`：daemon 线程按 interval 采样 `sysctl vm.swapusage`
（与 before/after 快照同一解析器），逐行写 `system_monitor.jsonl`。

- 开销实测：interval=0.2 s 连续 8 s，38 样本，全程 CPU 占单核 1.47%
  → 正式 interval=1.0 s 时 ≈0.3% 单核，对 GPU-bound 训练无可测影响
  （`results/validation/measurements-20260911/` 报告 + 上文终端输出）。
- 行为测试：`tests/test_supervisor.py` 3 项新测试（峰值追踪/受控停止/
  supervisor 集成：`sample_swap: true` → `peak_swap_bytes` measured + 产物落盘；
  缺省关闭 → 保持 unresolved）。28+3=31 测试全过（见 §5 命令记录）。
- 局限：系统级指标，含其他进程贡献；采样可能错过瞬时峰；峰值是"最大观测值"
  而非真峰值。论文表述须为 "maximum sampled swap usage (1 s cadence)"。

### E. 本次验证未覆盖、已知保留事项

- supervisor `monitoring.interval_seconds` 在 v0 长期只是声明值（无采样器实现），
  2026-09-11 起 `sample_swap: true` 时真正生效；旧 raw result 不受影响，也不回填。
- `power_source`（pmset）解析仅区分 AC/Battery，作为上下文元数据可用，非性能指标。
- `/usr/bin/time -l` 的 RSS 计数对 MLX/Metal 统一内存分配的覆盖范围**未验证**：
  在验证完成前，正式 benchmark 不启用（保持 v0 决定）。

## 3. 正式 benchmark 采用的指标口径（冻结）

| 论文指标 | 定义 |
| --- | --- |
| Step time | measured 区间内每优化器步墙钟（含 fwd+bwd+optimizer+sync），warmup 步排除并在结果中声明 |
| Throughput | measured loss-bearing tokens ÷ measured step-time 总和（prompt07+ 口径） |
| Peak memory | `peak_metal_gpu_memory_bytes`（MLX 分配器口径，逐运行读取） |
| Swap | before / after / sampled peak（1 s cadence，系统级，声明口径） |
| Training loss | 每步 loss-bearing 交叉熵（`default_loss`），最后有限值 + 全轨迹（step_timings.jsonl） |

## 4. 保持 null 的指标与理由（不补估算）

`peak_process_memory_bytes`（/usr/bin/time 语义未验证）、`peak_system_memory_bytes`
（无已验证聚合定义）、`process_page_faults`（语义未验证）、`energy_joules`
（无校准计量）、`thermal_state_*`（Foundation helper 未实现验证）。

## 5. 验证命令记录（2026-09-11 实际运行）

```text
caffeinate -is uv run python scripts/validate_measurements.py
→ [A] async underreport factor: 4571.3x
→ [B] active/peak delta match alloc: True/True
→ [C] 16 raw results checked, all_consistent=True
→ results/validation/measurements-20260911/report.json

uv run python -m pytest tests/ -q → 31 passed（test_supervisor 14 + test_analysis 4 + test_prompt_log 13）
swap 采样开销实测（0.2s×8s）：38 样本，cpu_fraction=0.0147，errors=0
```
