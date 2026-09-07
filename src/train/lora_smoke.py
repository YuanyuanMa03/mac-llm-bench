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
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
import mlx_lm
import yaml
from mlx.optimizers import Adam
from mlx_lm.tuner import linear_to_lora_layers
from mlx_lm.tuner.trainer import default_loss
from mlx.utils import tree_flatten


def _resolve_local_revision(model_dir: Path) -> tuple[str | None, str | None]:
    """从本地 hf 缓存 tree 元数据读取已落盘 revision（文件名即完整 sha）。"""
    trees = sorted((model_dir / ".cache" / "huggingface" / "trees").glob("*.json"))
    if len(trees) == 1:
        return trees[0].stem, "hf local cache trees/<sha>.json"
    if not trees:
        return None, None
    return None, f"多个 tree 元数据（{len(trees)}），无法唯一定位"


def run(config_path: Path) -> int:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    model_cfg = config["model"]
    train_cfg = config["training"]
    data_cfg = config["dataset"]

    artifacts_dir = Path(os.environ.get("BENCH_EXPERIMENT_ARTIFACTS_DIR", "."))
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    seed = train_cfg["seed"]
    mx.random.seed(seed)
    rng = random.Random(seed)

    # ---- 加载模型（计时） ----
    load_t0 = time.perf_counter()
    model, tokenizer = mlx_lm.load(model_cfg["local_path"])
    model_load_seconds = time.perf_counter() - load_t0

    # ---- 冻结 + LoRA（mlx_lm.lora 的标准流程） ----
    parameter_count_base = sum(v.size for _, v in tree_flatten(model.parameters()))
    model.freeze()
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

    # ---- 数据：本地 jsonl 的 text 字段，截断到 max_sequence_length ----
    seq_len = data_cfg["max_sequence_length"]
    samples = []
    for path in data_cfg["local_paths"]:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                ids = tokenizer.encode(json.loads(line)["text"])
                samples.append(ids[:seq_len])
    if not samples:
        raise SystemExit("数据集为空")

    # ---- 训练循环 ----
    optimizer = Adam(train_cfg["learning_rate"])
    grad_fn = nn.value_and_grad(model, default_loss)
    max_steps = train_cfg["max_steps"]
    batch_size = train_cfg["micro_batch_size"]

    order = list(range(len(samples)))
    cursor = 0
    step_records: list[dict] = []
    losses: list[float] = []
    tokens_total = 0
    samples_total = 0
    try:
        mx.metal.reset_peak_memory()
    except Exception:
        pass
    loop_t0 = time.perf_counter()
    for step in range(1, max_steps + 1):
        batch_ids, lengths = [], []
        for _ in range(batch_size):
            if cursor >= len(order):
                rng.shuffle(order)
                cursor = 0
            batch_ids.append(samples[order[cursor]])
            lengths.append([0, len(samples[order[cursor]])])
            cursor += 1
        batch = mx.array(batch_ids)
        lens = mx.array(lengths)

        t0 = time.perf_counter()
        (loss, toks), grad = grad_fn(model, batch, lens)
        optimizer.update(model, grad)
        mx.eval(model.parameters(), optimizer.state)
        step_seconds = time.perf_counter() - t0

        loss_value = float(loss)
        toks_value = int(toks)
        losses.append(loss_value)
        tokens_total += toks_value
        samples_total += batch_size
        step_records.append({
            "step": step,
            "loss": loss_value,
            "loss_bearing_tokens": toks_value,
            "step_time_seconds": step_seconds,
            "wall_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        print(f"step {step}/{max_steps} loss={loss_value:.4f} "
              f"tokens={toks_value} step_time={step_seconds:.3f}s", flush=True)
    training_loop_seconds = time.perf_counter() - loop_t0

    try:
        peak_gpu_bytes = int(mx.metal.get_peak_memory())
    except Exception:
        peak_gpu_bytes = None

    step_times = [r["step_time_seconds"] for r in step_records]
    resolved_rev, rev_source = _resolve_local_revision(Path(model_cfg["local_path"]))

    metrics = {
        "model_load_seconds": model_load_seconds,
        "training_loop_seconds": training_loop_seconds,
        "successful_steps": len(step_records),
        "attempted_micro_steps": len(step_records) * batch_size,
        "measured_steps": len(step_records),
        "excluded_warmup_steps": 0,
        "average_step_time_seconds": statistics.fmean(step_times),
        "median_step_time_seconds": statistics.median(step_times),
        "tokens_processed": tokens_total,
        "token_count_definition":
            "loss-bearing target tokens（default_loss 掩码后的非 padding 目标 token）",
        "tokens_per_second": tokens_total / training_loop_seconds,
        "samples_processed": samples_total,
        "samples_per_second": samples_total / training_loop_seconds,
        "throughput_interval_definition":
            "仅训练循环（不含模型加载）；每步计时含前向+反向+优化器更新+mx.eval",
        "training_loss_final": losses[-1] if losses else None,
        "lora_scale": scale,
        "lora_scale_formula": "alpha / rank",
        "trainable_parameters": trainable_parameters,
        "total_parameters": total_parameters,
        "trainable_parameter_ratio": trainable_parameters / total_parameters,
        "model_architecture": getattr(model, "model_type", None),
        "parameter_count": parameter_count_base,
        "parameter_count_method":
            "sum(array.size) over mlx_lm.load 结果的 parameters()（LoRA 附加前）",
        "model_dtype": str(next(v for _, v in tree_flatten(model.parameters())).dtype),
        "quantization_state": "unquantized",
        "resolved_revision": resolved_rev,
        "revision_source": rev_source,
        "peak_metal_gpu_memory_bytes": peak_gpu_bytes,
        "peak_gpu_memory_note":
            "mx.metal.get_peak_memory()，GPU 侧峰值；进程级峰值内存仍为 unresolved",
    }

    (artifacts_dir / "step_timings.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in step_records),
        encoding="utf-8")
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
