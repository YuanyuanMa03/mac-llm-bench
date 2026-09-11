#!/usr/bin/env python3
"""生成 formal benchmark 配置（research/preregistration.md §7 冻结矩阵）。

输出 configs/experiments/formal/*.yaml + generation_manifest.json。
重新生成会因文件已存在而拒绝（冻结语义）；确需重生成请先删除整个目录并在
commit message 中说明（正式运行开始前允许，运行开始后禁止）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "configs" / "experiments" / "formal"

MODELS = {
    "0.6b-bf16": {"local_path": "models/Qwen3-0.6B", "repo": "Qwen/Qwen3-0.6B",
                  "revision": "c1899de289a04d12100db370d81485cdf75e47ca",
                  "qbits": None, "params_b": 0.6},
    "1.7b-bf16": {"local_path": "models/Qwen3-1.7B", "repo": "Qwen/Qwen3-1.7B",
                  "revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
                  "qbits": None, "params_b": 1.7},
    "4b-bf16": {"local_path": "models/Qwen3-4B", "repo": "Qwen/Qwen3-4B",
                "revision": "1cfa9a7208912126459214e8b04321603b3df60c",
                "qbits": None, "params_b": 4.0},
    "8b-bf16": {"local_path": "models/Qwen3-8B", "repo": "Qwen/Qwen3-8B",
                "revision": None, "qbits": None, "params_b": 8.0},
    "0.6b-4bit": {"local_path": "models/Qwen3-0.6B-4bit",
                  "repo": "mlx-community/Qwen3-0.6B-4bit",
                  "revision": "73e3e38d9813", "qbits": 4, "params_b": 0.6},
    "1.7b-4bit": {"local_path": "models/Qwen3-1.7B-4bit",
                  "repo": "mlx-community/Qwen3-1.7B-4bit",
                  "revision": "3b1b1768f8f8", "qbits": 4, "params_b": 1.7},
    "4b-4bit": {"local_path": "models/Qwen3-4B-4bit",
                "repo": "mlx-community/Qwen3-4B-4bit",
                "revision": "4dcb3d101c2a062e5c1d4bb173588c54ea6c4d25",
                "qbits": 4, "params_b": 4.0},
    "8b-4bit": {"local_path": "models/Qwen3-8B-4bit",
                "repo": "mlx-community/Qwen3-8B-4bit",
                "revision": "545dc4251c05440727734bcd94334791f6ab0192",
                "qbits": 4, "params_b": 8.0},
    "14b-4bit": {"local_path": "models/Qwen3-14B-4bit",
                 "repo": "mlx-community/Qwen3-14B-4bit",
                 "revision": "a4d9b2df59d2c150bef02fcbe0d91046b7ca33a4",
                 "qbits": 4, "params_b": 14.0},
}
SEEDS = [42, 123, 2026]
TARGET_MODULES = ["self_attn.q_proj", "self_attn.k_proj",
                  "self_attn.v_proj", "self_attn.o_proj"]

# 数据集段（frozen formal_sft_v1）
def dataset_section(seq: int) -> dict:
    return {
        "data_files_sha256": None,
        "local_paths": ["data/formal_sft_v1/train.jsonl"],
        "validation_local_paths": ["data/formal_sft_v1/validation.jsonl"],
        "max_sequence_length": seq,
        "name": "formal_sft_v1",
        "preprocessing": {
            "add_special_tokens": True, "deduplication": None,
            "field_mapping": {"text": "text"}, "filtering": None,
            "label_mask_policy": "all-tokens-lm-loss",
            "normalization": None, "packing": False, "padding_side": "right",
            "prompt_template": "qwen3-chat-template (frozen in dataset artifacts)",
            "truncation": True,
        },
        "revision": "formal_sft_v1",
        "shuffle": True, "seed_note": None,
        "source": "HuggingFaceH4/ultrachat_200k@8049631c405ae6576f93f445c6b8166f76f5505a (frozen subset)",
        "split_seed": 42, "test_split": None, "train_split": "train",
        "validation_split": "validation",
        "tokenizer": {"id": "Qwen/Qwen3-4B", "revision": None, "use_fast": None},
    }


def build_config(*, group: str, model_key: str, method: str, seq: int,
                 rank: int, micro_batch: int, steps: int, seed: int,
                 excluded_warmup: int, eval_interval: int) -> dict:
    m = MODELS[model_key]
    is_qlora = method == "qlora"
    return {
        "dataset": dataset_section(seq),
        "experiment": {
            "comparison_group_id": group,
            "parent_experiment_id": None,
            "repeat_index": SEEDS.index(seed),
            "run_kind": "measured",
            "supersedes_experiment_id": None,
            "tags": ["formal-benchmark", "preregistered", model_key, method,
                     f"ctx{seq}", f"r{rank}", f"b{micro_batch}",
                     f"steps{steps}"],
        },
        "model": {
            "id": m["repo"], "local_path": m["local_path"],
            "provider": "huggingface", "repository": m["repo"],
            "revision": m["revision"],
            "tokenizer_id": m["repo"], "tokenizer_revision": None,
            "trust_remote_code": False,
        },
        "monitoring": {
            "capture_energy": False, "capture_power_source": True,
            "capture_process_time_l": False, "capture_swap_usage": True,
            "capture_thermal_state": False, "capture_vm_stat": True,
            "enabled": True, "fail_run_on_collector_error": False,
            "interval_seconds": 1.0, "required_raw_logs": True,
            "sample_swap": True,
        },
        "output": {
            "figures_root": "results/figures",
            "immutable_after_finalize": True,
            "processed_root": "results/processed",
            "raw_root": "results/raw",
            "write_sha256_manifest": True,
        },
        "protocol_version": "0.1.0",
        "schema_version": "0.1.0",
        "training": {
            "checkpoint_interval_steps": None,
            "epochs": None,
            "evaluation_interval_steps": eval_interval,
            "excluded_warmup_steps": excluded_warmup,
            "gradient_accumulation_steps": 1,
            "gradient_checkpointing": False,
            "learning_rate": 0.0001,
            "logging_interval_steps": 1,
            "lora": {"alpha": 2 * rank, "dropout": 0.0, "rank": rank,
                     "target_modules": TARGET_MODULES},
            "max_steps": steps,
            "method": method,
            "micro_batch_size": micro_batch,
            "optimizer": {"name": "adamw", "parameters": None},
            "precision": {"compute_dtype": None, "optimizer_state_dtype": None,
                          "parameter_dtype": None},
            "quantization": {"bits": m["qbits"] if is_qlora else None,
                             "group_size": 64 if is_qlora else None,
                             "scheme": None},
            "resume_checkpoint": None,
            "scheduler": {"name": "constant", "parameters": None},
            "seed": seed,
            "sequence_length": seq,
            "stop_criteria": {"early_stopping": False},
            "trainable_layers": None,
            "warmup": {"ratio": None, "steps": 0},
        },
    }


def main() -> int:
    if OUT.exists():
        print(f"[gen] 拒绝覆盖：{OUT} 已存在（冻结语义）", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True)
    generated = []

    def emit(name: str, cfg: dict) -> None:
        path = OUT / f"{name}.yaml"
        path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True),
                        encoding="utf-8")
        generated.append(name)

    # 轴 1 主矩阵：ctx512 / 100 steps / excluded 5 / eval 50 / 3 seeds
    for model_key, method in [
        ("0.6b-bf16", "lora"), ("1.7b-bf16", "lora"), ("4b-bf16", "lora"),
        ("0.6b-4bit", "qlora"), ("1.7b-4bit", "qlora"), ("4b-4bit", "qlora"),
        ("8b-4bit", "qlora"), ("14b-4bit", "qlora"),
        ("0.6b-bf16", "full"),
    ]:
        for seed in SEEDS:
            emit(f"axis1_{model_key}_{method}_ctx512_r8_b1_steps100_s{seed}",
                 build_config(
                     group=f"formal-axis1-{model_key}-{method}",
                     model_key=model_key, method=method, seq=512, rank=8,
                     micro_batch=1, steps=100, seed=seed,
                     excluded_warmup=5, eval_interval=50))

    # 轴 1b 配对深潜：4B lora vs qlora / 300 steps / excluded 10 / eval 50
    for model_key, method in [("4b-bf16", "lora"), ("4b-4bit", "qlora")]:
        for seed in SEEDS:
            emit(f"axis1b_{model_key}_{method}_ctx512_r8_b1_steps300_s{seed}",
                 build_config(
                     group=f"formal-axis1b-{model_key}-{method}",
                     model_key=model_key, method=method, seq=512, rank=8,
                     micro_batch=1, steps=300, seed=seed,
                     excluded_warmup=10, eval_interval=50))

    # 轴 2 context：4b-4bit ctx{1024,2048} / 20 steps / excluded 2 / eval 10
    for seq in (1024, 2048):
        for seed in SEEDS:
            emit(f"axis2_4b-4bit_qlora_ctx{seq}_r8_b1_steps20_s{seed}",
                 build_config(
                     group=f"formal-axis2-ctx{seq}", model_key="4b-4bit",
                     method="qlora", seq=seq, rank=8, micro_batch=1,
                     steps=20, seed=seed, excluded_warmup=2, eval_interval=10))

    # 轴 3 rank：4b-4bit r{4,32} / 20 steps / excluded 2
    for rank in (4, 32):
        for seed in SEEDS:
            emit(f"axis3_4b-4bit_qlora_ctx512_r{rank}_b1_steps20_s{seed}",
                 build_config(
                     group=f"formal-axis3-r{rank}", model_key="4b-4bit",
                     method="qlora", seq=512, rank=rank, micro_batch=1,
                     steps=20, seed=seed, excluded_warmup=2, eval_interval=10))

    # 轴 4 batch：4b-4bit b{2,4,8} / 20 steps / excluded 2
    for mb in (2, 4, 8):
        for seed in SEEDS:
            emit(f"axis4_4b-4bit_qlora_ctx512_r8_b{mb}_steps20_s{seed}",
                 build_config(
                     group=f"formal-axis4-b{mb}", model_key="4b-4bit",
                     method="qlora", seq=512, rank=8, micro_batch=mb,
                     steps=20, seed=seed, excluded_warmup=2, eval_interval=10))

    # 边界探针：8b-bf16 lora ctx512（预期失败证据）；14b-4bit ctx2048
    emit("probe_8b-bf16_lora_ctx512_r8_b1_steps20_s42",
         build_config(group="probe-8b-bf16-ctx512", model_key="8b-bf16",
                      method="lora", seq=512, rank=8, micro_batch=1,
                      steps=20, seed=42, excluded_warmup=2, eval_interval=10))
    emit("probe_14b-4bit_qlora_ctx2048_r8_b1_steps20_s42",
         build_config(group="probe-14b-4bit-ctx2048", model_key="14b-4bit",
                      method="qlora", seq=2048, rank=8, micro_batch=1,
                      steps=20, seed=42, excluded_warmup=2, eval_interval=10))

    (OUT / "generation_manifest.json").write_text(
        json.dumps({"n_configs": len(generated), "configs": generated,
                    "preregistration": "research/preregistration.md",
                    "note": "8b-bf16 revision 待下载锚定后由 runner 校验；"
                            "generator 输出 revision: null → 运行前必须补齐"},
                   indent=2) + "\n", encoding="utf-8")
    print(f"[gen] {len(generated)} configs → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
