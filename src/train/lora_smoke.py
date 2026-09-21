"""Experiment 0：Qwen3-0.6B + LoRA 20-step 冒烟训练。

由 Experiment Supervisor 以子进程启动；训练事实写入
$BENCH_EXPERIMENT_ARTIFACTS_DIR/training_metrics.json 与 step_timings.jsonl
（缺省回退当前目录）。所有数字来自真实计时/计数，不做估算。
所用 mlx-lm API 均经安装版（0.31.3）源码核实。
"""

from __future__ import annotations

import json
import os
import random
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
import mlx_lm
import yaml
from mlx.optimizers import Adam
from mlx_lm.tuner import linear_to_lora_layers
from mlx_lm.tuner.trainer import default_loss
from mlx.utils import tree_flatten


def _sum_tree_size(tree) -> int:
    """递归求和 mlx 参数树（dict/list/array）中的数组元素数。"""
    if isinstance(tree, dict):
        return sum(_sum_tree_size(v) for v in tree.values())
    if isinstance(tree, (list, tuple)):
        return sum(_sum_tree_size(v) for v in tree)
    return int(tree.size) if hasattr(tree, "size") else 0


def _pad_batch(chunk: list[list[int]],
               pad_id: int) -> tuple[list[list[int]], list[list[int]]]:
    """变长样本批构造（训练与 validation 共用同一 batching 语义）。

    右侧 pad 到批内最大长度；lengths=[0, len(s)-1] 给出每行有效 target
    区间（default_loss 按 steps∈[offset,len] 对 batch[:,1:] 逐行 mask），
    每样本恰好 len(s)-1 个真实 next-token target，pad 位置不参与 loss。
    单样本（无 pad 追加）时与旧实现 lengths=[0,len] 在 default_loss 下
    逐位等价（targets 仅 L-1 列，两种上界 mask 相同）——见
    tests/test_train_padding.py 与 research/deviations.md D5。
    """
    max_len = max(len(s) for s in chunk)
    batch_ids = [s + [pad_id] * (max_len - len(s)) for s in chunk]
    lengths = [[0, len(s) - 1] for s in chunk]
    return batch_ids, lengths


def _forward_validation_loss(model, batch, lengths):
    """Validation has no gradient or optimizer-update path."""
    return default_loss(model, batch, lengths)


def _logical_parameter_count(model: nn.Module) -> int:
    """逻辑参数量：量化层按 scales shape×group_size 还原 logical 形状计数。

    方法 = "weight/config inspection"（协议 §3.4）：QuantizedLinear/Embedding
    的 scales 形状为 (rows, in/group)，logical 元素数 = scales.size × group_size；
    非量化叶子模块（nn.Linear/Embedding/RMSNorm 等）按其参数树数组元素计数。
    叶子判定 = children() 为空（与 mlx leaf_modules 判据一致），
    保证每个数组恰好归属一个叶子模块，不重复计数。
    与打包存储口径（packed uint32 元素数）区分。
    """
    total = 0
    for _, mod in model.named_modules():
        if mod.children():
            continue
        if isinstance(mod, (nn.QuantizedLinear, nn.QuantizedEmbedding)):
            total += int(mod.scales.size * mod.group_size)
            bias = getattr(mod, "bias", None)
            if bias is not None:
                total += int(bias.size)
        else:
            total += _sum_tree_size(mod.parameters())
    return total


def _resolve_local_revision(model_dir: Path) -> tuple[str | None, str | None]:
    """从本地 hf 缓存 tree 元数据或 REVISION sidecar 读取已落盘 revision。"""
    trees = sorted((model_dir / ".cache" / "huggingface" / "trees").glob("*.json"))
    if len(trees) == 1:
        return trees[0].stem, "hf local cache trees/<sha>.json"
    if len(trees) > 1:
        return None, f"多个 tree 元数据（{len(trees)}），无法唯一定位"
    sidecar = model_dir / "REVISION"
    if sidecar.is_file():
        text = sidecar.read_text(encoding="utf-8").strip()
        if len(text) == 40 and all(c in "0123456789abcdef" for c in text):
            return text, "REVISION sidecar（见 models/MANIFEST.md 的哈希校验锚定）"
    return None, None


def run(config_path: Path) -> int:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    model_cfg = config["model"]
    train_cfg = config["training"]
    data_cfg = config["dataset"]

    artifacts_dir = Path(os.environ.get("BENCH_EXPERIMENT_ARTIFACTS_DIR", "."))
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    progress_path = artifacts_dir / "training_progress.jsonl"
    timing_path = artifacts_dir / "step_timings.jsonl"

    def _append_jsonl(path: Path, record: dict) -> None:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()

    def _phase(phase: str, **fields) -> None:
        _append_jsonl(progress_path, {
            "phase": phase,
            "wall_utc": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"),
            "monotonic_ns": time.monotonic_ns(),
            **fields,
        })

    seed = train_cfg["seed"]
    mx.random.seed(seed)
    rng = random.Random(seed)

    # ---- 加载模型（计时） ----
    _phase("model_load_start")
    load_t0 = time.perf_counter()
    model, tokenizer = mlx_lm.load(model_cfg["local_path"])
    model_load_seconds = time.perf_counter() - load_t0
    _phase("model_load_end")

    # ---- 冻结 + LoRA（mlx_lm.lora 的标准流程） ----
    parameter_count_base = sum(v.size for _, v in tree_flatten(model.parameters()))
    # 量化检测（在 LoRA 包装前，从真实层读取，不猜）
    quant_info: list[tuple[int, int]] = []

    def _detect(_path, module):
        if isinstance(module, nn.QuantizedLinear):
            quant_info.append((module.bits, module.group_size))

    model.apply_to_modules(_detect)
    quantization_state = "quantized" if quant_info else "unquantized"
    quant_bits = quant_info[0][0] if quant_info else None
    quant_group = quant_info[0][1] if quant_info else None
    if len(set(quant_info)) > 1:
        print(f"[警告] 检测到混合量化配置: {set(quant_info)}", flush=True)
    model_quant_config = {}
    try:
        model_quant_config = (json.loads(
            (Path(model_cfg["local_path"]) / "config.json").read_text(encoding="utf-8"))
        ).get("quantization") or {}
    except (OSError, json.JSONDecodeError):
        pass
    _phase("adapter_setup_start")
    model.freeze()
    if train_cfg["method"] == "full":
        # full fine-tuning：解冻全部参数（LoRA 包装跳过）
        model.unfreeze()
        trainable_parameters = sum(v.size for _, v in tree_flatten(model.trainable_parameters()))
        total_parameters = trainable_parameters
    else:
        lora = train_cfg["lora"]
        rank = lora["rank"]
        alpha = lora["alpha"]
        scale = alpha / rank
        linear_to_lora_layers(
            model,
            len(model.layers),
            {"rank": rank, "scale": scale, "dropout": lora["dropout"],
             "keys": lora["target_modules"]},
        )
        trainable_parameters = sum(v.size for _, v in tree_flatten(model.trainable_parameters()))
        total_parameters = sum(v.size for _, v in tree_flatten(model.parameters()))
    _phase("adapter_setup_end")

    # ---- 数据：本地 jsonl 的 text 字段，截断到 max_sequence_length ----
    seq_len = data_cfg["max_sequence_length"]

    def _load_samples(paths: list[str]) -> list[list[int]]:
        out: list[list[int]] = []
        for path in paths:
            for line in Path(path).read_text(encoding="utf-8").splitlines():
                if line.strip():
                    ids = tokenizer.encode(json.loads(line)["text"])
                    out.append(ids[:seq_len])
        return out

    samples = _load_samples(data_cfg["local_paths"])
    if not samples:
        raise SystemExit("数据集为空")
    val_samples = _load_samples(data_cfg.get("validation_local_paths") or [])
    pad_id = tokenizer.pad_token_id
    pad_id = pad_id if pad_id is not None else 0

    def _eval_validation_loss() -> float | None:
        """验证集上 loss-bearing 交叉熵的样本加权均值（forward-only，确定性顺序）。"""
        if not val_samples:
            return None
        total_loss, total_toks = 0.0, 0
        for i in range(0, len(val_samples), batch_size):
            batch_ids, lengths = _pad_batch(
                val_samples[i:i + batch_size], pad_id)
            loss, toks = _forward_validation_loss(
                model, mx.array(batch_ids), mx.array(lengths))
            mx.eval(loss, toks)
            total_loss += float(loss) * int(toks)
            total_toks += int(toks)
        return total_loss / total_toks if total_toks else None

    # ---- 训练循环 ----
    optimizer = Adam(train_cfg["learning_rate"])
    grad_fn = nn.value_and_grad(model, default_loss)
    max_steps = train_cfg["max_steps"]
    batch_size = train_cfg["micro_batch_size"]
    eval_interval = train_cfg.get("evaluation_interval_steps")
    validation_trajectory: list[dict] = []
    if val_samples:
        _phase("initial_validation_start")
        pre = _eval_validation_loss()
        validation_trajectory.append({"step": 0, "loss": pre})
        print(f"[val] step 0 loss={pre:.4f}", flush=True)
        _phase("initial_validation_end")

    order = list(range(len(samples)))
    if data_cfg.get("shuffle", False):
        rng.shuffle(order)
    cursor = 0
    step_records: list[dict] = []
    losses: list[float] = []
    tokens_total = 0
    samples_total = 0
    try:
        mx.metal.reset_peak_memory()
    except Exception:
        pass
    resolved_runtime = {
        "protocol_version": "0.2.0",
        "optimizer_declared": (train_cfg.get("optimizer") or {}).get("name"),
        "optimizer_effective": "mlx.optimizers.Adam",
        "shuffle_declared": bool(data_cfg.get("shuffle", False)),
        "initial_shuffle_effective": bool(data_cfg.get("shuffle", False)),
        "scheduler_declared": (train_cfg.get("scheduler") or {}).get("name"),
        "scheduler_effective": "constant/no explicit scheduler",
        "gradient_accumulation_effective": 1,
        "validation_effective": "forward-only default_loss",
        "step_timing_write_mode": "append-and-flush per completed optimizer step",
    }
    (artifacts_dir / "resolved_runtime_config.json").write_text(
        json.dumps(resolved_runtime, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    _phase("training_loop_start")
    loop_t0 = time.perf_counter()
    for step in range(1, max_steps + 1):
        chunk = []
        for _ in range(batch_size):
            if cursor >= len(order):
                rng.shuffle(order)
                cursor = 0
            chunk.append(samples[order[cursor]])
            cursor += 1
        # 右侧 pad + lengths 逐行 mask；与 validation 同一 helper（D5）
        batch_ids, lengths = _pad_batch(chunk, pad_id)
        batch = mx.array(batch_ids)
        lens = mx.array(lengths)

        _phase("train_step_start", step=step)
        monotonic_ns_start = time.monotonic_ns()
        t0 = time.perf_counter()
        (loss, toks), grad = grad_fn(model, batch, lens)
        optimizer.update(model, grad)
        mx.eval(model.parameters(), optimizer.state)
        step_seconds = time.perf_counter() - t0
        monotonic_ns_end = time.monotonic_ns()

        loss_value = float(loss)
        toks_value = int(toks)
        losses.append(loss_value)
        tokens_total += toks_value
        samples_total += batch_size
        step_record = {
            "step": step,
            "loss": loss_value,
            "loss_bearing_tokens": toks_value,
            "step_time_seconds": step_seconds,
            "wall_utc": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"),
            "monotonic_ns_start": monotonic_ns_start,
            "monotonic_ns_end": monotonic_ns_end,
        }
        step_records.append(step_record)
        _append_jsonl(timing_path, step_record)
        _phase("train_step_end", step=step)
        print(f"step {step}/{max_steps} loss={loss_value:.4f} "
              f"tokens={toks_value} step_time={step_seconds:.3f}s", flush=True)
        if val_samples and eval_interval and (step % eval_interval == 0
                                              or step == max_steps):
            _phase("scheduled_validation_start", step=step)
            v = _eval_validation_loss()
            validation_trajectory.append({"step": step, "loss": v})
            print(f"[val] step {step} loss={v:.4f}", flush=True)
            _phase("scheduled_validation_end", step=step)
    training_loop_seconds = time.perf_counter() - loop_t0
    _phase("training_loop_end")

    try:
        peak_gpu_bytes = int(mx.metal.get_peak_memory())
    except Exception:
        peak_gpu_bytes = None

    excluded = min(int(train_cfg.get("excluded_warmup_steps", 0)), len(step_records))
    measured = step_records[excluded:]
    if not measured:
        raise SystemExit("excluded_warmup_steps 覆盖了全部步数，无测量区间")
    measured_step_times = [r["step_time_seconds"] for r in measured]
    measured_tokens = sum(r["loss_bearing_tokens"] for r in measured)
    measured_interval_seconds = sum(measured_step_times)
    resolved_rev, rev_source = _resolve_local_revision(Path(model_cfg["local_path"]))

    metrics = {
        "model_load_seconds": model_load_seconds,
        "training_loop_seconds": training_loop_seconds,
        "successful_steps": len(step_records),
        "attempted_micro_steps": len(step_records) * batch_size,
        "measured_steps": len(measured),
        "excluded_warmup_steps": excluded,
        "average_step_time_seconds": statistics.fmean(measured_step_times),
        "median_step_time_seconds": statistics.median(measured_step_times),
        "tokens_processed": measured_tokens,
        "token_count_definition":
            "loss-bearing target tokens（default_loss 掩码后的非 padding 目标 token）",
        "tokens_per_second": measured_tokens / measured_interval_seconds,
        "samples_processed": len(measured) * batch_size,
        "samples_per_second": len(measured) * batch_size / measured_interval_seconds,
        "throughput_interval_definition":
            f"训练循环内排除前 {excluded} 个 warmup 步后的测得区间；"
            "每步计时含前向+反向+优化器更新+mx.eval",
        "measured_interval_seconds": measured_interval_seconds,
        "total_tokens_all_steps": tokens_total,
        "training_loss_final": losses[-1] if losses else None,
        "validation_loss_final": (validation_trajectory[-1]["loss"]
                                  if validation_trajectory else None),
        "validation_loss_trajectory": validation_trajectory,
        "validation_n_samples": len(val_samples),
        "optimizer_declared": (train_cfg.get("optimizer") or {}).get("name"),
        "optimizer_effective": "mlx.optimizers.Adam",
        "shuffle_declared": bool(data_cfg.get("shuffle", False)),
        "initial_shuffle_effective": bool(data_cfg.get("shuffle", False)),
        "scheduler_declared": (train_cfg.get("scheduler") or {}).get("name"),
        "scheduler_effective": "constant/no explicit scheduler",
        "gradient_accumulation_effective": 1,
        "method_effective": train_cfg["method"],
        "lora_scale": scale if train_cfg["method"] != "full" else None,
        "lora_scale_formula": "alpha / rank",
        "trainable_parameters": trainable_parameters,
        "total_parameters": total_parameters,
        "trainable_parameter_ratio": trainable_parameters / total_parameters,
        "model_architecture": getattr(model, "model_type", None),
        "parameter_count": parameter_count_base,
        "parameter_count_method":
            "sum(array.size) over mlx_lm.load 结果的 parameters()（LoRA 附加前）",
        "quantization_state": quantization_state,
        "quantization_bits": quant_bits,
        "quantization_group_size": quant_group,
        "quantization_scheme": model_quant_config.get("scheme"),
        "model_dtype": str(next(v for _, v in tree_flatten(model.parameters())).dtype),
        "logical_parameter_count": _logical_parameter_count(model),
        "logical_parameter_count_method":
            "named_modules walk: QuantizedLinear/Embedding → scales.size×group_size"
            "+bias；dense leaf modules → sum(array.size)（weight/config inspection）",
        "resolved_revision": resolved_rev,
        "revision_source": rev_source,
        "peak_metal_gpu_memory_bytes": peak_gpu_bytes,
        "peak_gpu_memory_note":
            "mx.metal.get_peak_memory()，GPU 侧峰值；进程级峰值内存仍为 unresolved",
    }

    (artifacts_dir / "training_metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"[train] done: {len(step_records)} steps, "
          f"final_loss={metrics['training_loss_final']:.4f}, "
          f"tokens={tokens_total}, "
          f"trainable={trainable_parameters / 1e6:.3f}M/"
          f"{total_parameters / 1e6:.3f}M")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("用法: train_lora.py <experiment-config.yaml>", file=sys.stderr)
        return 2
    return run(Path(argv[0]))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
