"""Experiment ID 生成（协议 §9）。

格式：<UTC>__<model-slug>__<method>-q<bits-or-none>__ctx<N>__b<M>-ga<G>__r<R-or-na>__s<S>__<uuid7>
- slug：小写 ASCII [a-z0-9-]，折叠连续连字符，模型 slug 上限 32 字符
- 不适用字段用字面量 na；未知必填配置是 preflight 错误，不是 "unknown" slug
- uuid7 提供程序化唯一性；ID 生成后永不重算或改名
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import uuid


def slugify(value: str, *, max_length: int = 32) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9-]", "-", lowered)
    collapsed = re.sub(r"-{2,}", "-", lowered).strip("-")
    if not collapsed:
        raise ValueError(f"slug 为空：{value!r}")
    return collapsed[:max_length].rstrip("-") or "na"


def uuid7() -> str:
    """RFC 9562 UUIDv7：48-bit Unix 毫秒时间戳 + 随机。canonical 小写。"""
    ms = int(_dt.datetime.now(_dt.timezone.utc).timestamp() * 1000)
    buf = bytearray(os.urandom(16))
    buf[0:6] = ms.to_bytes(6, "big")
    buf[6] = (buf[6] & 0x0F) | 0x70   # version 7（time_hi_and_version 高 4 位）
    buf[8] = (buf[8] & 0x3F) | 0x80   # variant 10xx（clock_seq_hi_and_reserved）
    parsed = uuid.UUID(bytes=bytes(buf))
    assert parsed.version == 7
    return str(parsed)


def _factor_int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"experiment ID 因子 {name} 必须为非负整数，得到 {value!r}")
    return value


def generate_experiment_id(config: dict) -> str:
    model_slug = slugify(str(config["model"]["id"]))
    training = config["training"]
    method = str(training["method"]).lower()
    if method not in ("full", "lora", "qlora"):
        raise ValueError(f"training.method 非法：{method!r}")
    bits = training.get("quantization", {}).get("bits")
    q_segment = f"q{bits}" if isinstance(bits, int) and bits > 0 else "qnone"
    if method == "full":
        rank_segment = "rna"
    else:
        rank_segment = f"r{_factor_int(training['lora']['rank'], 'lora.rank')}"
    ctx = _factor_int(training["sequence_length"], "sequence_length")
    micro = _factor_int(training["micro_batch_size"], "micro_batch_size")
    accum = _factor_int(training["gradient_accumulation_steps"],
                        "gradient_accumulation_steps")
    seed = _factor_int(training["seed"], "seed")
    utc = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return (
        f"{utc}__{model_slug}__{method}-{q_segment}__ctx{ctx}"
        f"__b{micro}-ga{accum}__{rank_segment}__s{seed}__{uuid7()}"
    )
