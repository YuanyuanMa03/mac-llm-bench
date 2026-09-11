#!/usr/bin/env python3
"""生成确定性长文本合成数据集（ctx 边界探针系列用）。

构造方式与已有 data/exp0_long_ctx2048.jsonl / ctx8192.jsonl 一致：
从既有 2048 文件提取句池，seeded 洗牌拼接至目标字符数，每文件 8 样本。
生成后用 Qwen3 tokenizer 实测每样本 token 数（含 special tokens），
保证 max_sequence_length 截断前样本本征长度 < context ceiling（与 2048/8192
文件做法一致，即本征长度≈0.85×ctx）。

用途限制：synthetic long-context workload 仅用于 systems context-scaling
分析（内存/步时/边界），不得用于 downstream model quality 结论。
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POOL_FILE = ROOT / "data" / "exp0_long_ctx2048.jsonl"
N_SAMPLES = 8
SEED = 42

TARGETS = {  # context -> 目标字符数/样本（源自 2048 文件的 实测 chars/tokens≈3.42）
    4096: 11_900,
}


def sentence_pool() -> list[str]:
    text = json.loads(POOL_FILE.read_text(encoding="utf-8").splitlines()[0])["text"]
    parts = [p.strip() for p in
             text.replace("。", "。|").replace(". ", ". |").split("|") if p.strip()]
    seen, pool = set(), []
    for s in parts:
        if s not in seen:
            seen.add(s)
            pool.append(s)
    return pool


def make_sample(pool: list[str], rng: random.Random, target_chars: int) -> str:
    parts: list[str] = []
    size = 0
    while size < target_chars:
        s = rng.choice(pool)
        parts.append(s)
        size += len(s) + 1
    return " ".join(parts)


def main() -> int:
    ctx = int(sys.argv[1]) if len(sys.argv) == 1 or sys.argv[1].isdigit() else 4096
    if ctx not in TARGETS:
        print(f"未定义目标长度：{ctx}；支持：{sorted(TARGETS)}", file=sys.stderr)
        return 2
    target = TARGETS[ctx]
    pool = sentence_pool()
    rng = random.Random(SEED)
    samples = [make_sample(pool, rng, target) for _ in range(N_SAMPLES)]

    out = ROOT / "data" / f"exp0_long_ctx{ctx}.jsonl"
    out.write_text("".join(json.dumps({"text": s}, ensure_ascii=False) + "\n"
                           for s in samples), encoding="utf-8")

    # 用真实 tokenizer 验证本征长度 < ctx
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(str(ROOT / "models" / "Qwen3-4B-4bit"))
    lengths = [len(tok.encode(s)) for s in samples]
    print(f"[gen] {out.relative_to(ROOT)}: {len(samples)} samples, "
          f"chars/sample={sorted(len(s) for s in samples)}")
    print(f"[gen] tokenized lengths: {lengths} (max={max(lengths)} < ctx{ctx}: "
          f"{max(lengths) < ctx})")
    if max(lengths) >= ctx:
        print("[gen] 错误：样本本征长度超出 context ceiling", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
