"""result.json 构建（严格对应 docs/result_schema.md）。

measurement<T> 信封：value 与其证据不分离；collection_status != "measured"
时 value 必须为 null。缺失/不可得 = null，绝不 0、绝不估算。
"""

from __future__ import annotations

from pathlib import Path

SCHEMA_VERSION = "0.1.0"
PROTOCOL_VERSION = "0.2.0"


def measurement(
    *,
    value,
    unit: str,
    source: str | None,
    status: str,
    notes: str | None = None,
    sample_time_utc: str | None = None,
    raw_artifact_path: str | None = None,
) -> dict:
    assert status in ("measured", "unavailable", "failed", "not_applicable", "unresolved")
    if status != "measured":
        value = None
    return {
        "value": value,
        "unit": unit,
        "source": source,
        "sample_time_utc": sample_time_utc,
        "raw_artifact_path": raw_artifact_path,
        "collection_status": status,
        "notes": notes,
    }


def unresolved(unit: str, source: str | None, reason: str) -> dict:
    return measurement(value=None, unit=unit, source=source, status="unresolved",
                       notes=reason)


def artifact_ref(path: str, *, size_bytes: int | None, sha256: str | None = None,
                 media_type: str | None = None, complete: bool = True,
                 path_kind: str = "relative") -> dict:
    return {
        "path": path,
        "path_kind": path_kind,
        "sha256": sha256,
        "size_bytes": size_bytes,
        "media_type": media_type,
        "complete": complete,
    }


def null_artifact_ref(path: str) -> dict:
    """artifact 从未创建：sha256/size 为 null，complete=False。"""
    return artifact_ref(path, size_bytes=None, sha256=None, complete=False)


def build_training_section(config: dict) -> dict:
    t = config["training"]
    lora = t.get("lora") or {}
    quant = t.get("quantization") or {}
    is_lora = t["method"] in ("lora", "qlora")
    return {
        "method": t["method"],
        "quantization_bits": quant.get("bits"),
        "quantization_scheme": quant.get("scheme"),
        "quantization_group_size": quant.get("group_size"),
        "lora_rank": lora.get("rank") if is_lora else None,
        "lora_alpha": lora.get("alpha") if is_lora else None,
        "lora_dropout": lora.get("dropout") if is_lora else None,
        "target_modules": lora.get("target_modules") if is_lora else [],
        "trainable_layers": None,  # 需初始化模型后实测，v0 未接训练
        "trainable_parameters": None,
        "total_parameters": None,
        "trainable_parameter_ratio": None,
        "micro_batch_size": t["micro_batch_size"],
        "gradient_accumulation_steps": t["gradient_accumulation_steps"],
        "world_size": 1,
        "effective_batch_size": t["micro_batch_size"] * t["gradient_accumulation_steps"],
        "effective_batch_size_formula": (
            "micro_batch_size * gradient_accumulation_steps * world_size"
        ),
        "sequence_length": t["sequence_length"],
        "learning_rate": t["learning_rate"],
        "optimizer": (t.get("optimizer") or {}).get("name"),
        "optimizer_parameters": t.get("optimizer") or {},
        "scheduler": (t.get("scheduler") or {}).get("name"),
        "scheduler_parameters": t.get("scheduler") or {},
        "warmup_steps": (t.get("warmup") or {}).get("steps"),
        "warmup_ratio": (t.get("warmup") or {}).get("ratio"),
        "requested_steps": t.get("max_steps"),
        "requested_epochs": t.get("epochs"),
        "stop_criteria": t.get("stop_criteria") or {},
        "seed": t["seed"],
        "library_seeds": {"python_random": None, "numpy": None, "mlx": None},
        "gradient_checkpointing": t.get("gradient_checkpointing", False),
        "parameter_dtype": (t.get("precision") or {}).get("parameter_dtype"),
        "compute_dtype": (t.get("precision") or {}).get("compute_dtype"),
        "optimizer_state_dtype": (t.get("precision") or {}).get("optimizer_state_dtype"),
        "packing": (config["dataset"].get("preprocessing") or {}).get("packing", False),
        "evaluation_interval_steps": t.get("evaluation_interval_steps"),
        "checkpoint_interval_steps": t.get("checkpoint_interval_steps"),
        "logging_interval_steps": t.get("logging_interval_steps"),
        "resume_checkpoint": None,
    }


def build_model_dataset_sections(config: dict) -> tuple[dict, dict]:
    m = config["model"]
    model = {
        "id": m.get("id"),
        "provider": m.get("provider"),
        "repository": m.get("repository"),
        "requested_revision": m.get("revision"),
        "resolved_revision": None,  # v0 未接模型加载，未验证即 null
        "revision_source": None,
        "local_path": m.get("local_path"),
        "architecture": None,
        "parameter_count": None,
        "parameter_count_method": None,
        "quantization_state": None,
        "quantization_bits": None,
        "quantization_scheme": None,
        "model_files_size_bytes": None,
        "model_files_manifest": None,
        "tokenizer_id": m.get("tokenizer_id"),
        "tokenizer_resolved_revision": None,
    }
    d = config["dataset"]
    dataset = {
        "name": d.get("name"),
        "source": d.get("source"),
        "requested_revision": d.get("revision"),
        "resolved_revision": None,
        "train_split": d.get("train_split"),
        "validation_split": d.get("validation_split"),
        "test_split": d.get("test_split"),
        "train_examples": None,
        "validation_examples": None,
        "test_examples": None,
        "preprocessing": d.get("preprocessing") or {},
        "preprocessing_code_revision": None,
        "tokenizer_id": (d.get("tokenizer") or {}).get("id"),
        "tokenizer_revision": (d.get("tokenizer") or {}).get("revision"),
        "max_sequence_length": d["max_sequence_length"],
        "shuffle": d.get("shuffle"),
        "split_seed": d.get("split_seed"),
        "subset_rule": None,
        "data_manifest": None,
    }
    return model, dataset


def build_metrics_section() -> dict:
    return {
        "training_loss_final": None,
        "validation_loss_final": None,
        "test_metrics": {},
        "metric_definitions": {},
        "raw_metrics_artifact": None,
    }


def experiment_conditions() -> dict:
    """隔离观察：v0 仅记录可可靠获取的电源状态；其余 null。"""
    return {
        "concurrent_ml_jobs_detected": None,
        "major_background_applications": None,
        "cooldown_seconds": None,
        "cache_state": None,
        "run_order_index": None,
        "low_power_mode": None,
        "external_display_count": None,
        "notes": "v0 supervisor 未实现周期采集与进程清单检查",
    }


def config_sha256(config: dict) -> str:
    import hashlib
    import json

    canonical = json.dumps(config, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def posix_rel(path: Path, base: Path) -> str:
    return path.resolve().relative_to(base.resolve()).as_posix()
