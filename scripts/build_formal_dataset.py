#!/usr/bin/env python3
"""构建并冻结正式 benchmark 数据集 data/formal_sft_v1/（预注册 §4）。

流程：
1. 从 HuggingFaceHub 下载 HuggingFaceH4/ultrachat_200k 的 train_sft split parquet；
2. 用 seed=42 确定性抽取 train 2048 + validation 32 条多轮对话；
3. 用本地 Qwen3-4B tokenizer 的 chat template（Qwen3 家族共享）格式化为纯文本；
4. 写 train.jsonl / validation.jsonl / SHA256SUMS / MANIFEST.json（含 upstream
   revision、抽样规则、模板、tokenizer、长度统计、逐文件 SHA-256）。

冻结语义：本脚本一次性生成，之后 formal benchmark 全部模型共享同一份文件；
重建必须走全新目录（formal_sft_v2 等），不允许覆盖。
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "formal_sft_v1"
UPSTREAM = "HuggingFaceH4/ultrachat_200k"
N_TRAIN, N_VAL, SEED = 2048, 32, 42
TEMPLATE_TOKENIZER = ROOT / "models" / "Qwen3-4B"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if OUT.exists():
        print(f"[freeze] 拒绝覆盖已冻结数据集：{OUT}", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True)

    import pyarrow.parquet as pq
    from huggingface_hub import HfApi, hf_hub_download
    from transformers import AutoTokenizer

    api = HfApi()
    info = api.dataset_info(UPSTREAM)
    revision = info.sha
    print(f"[freeze] upstream revision: {revision}")

    files = [s.rfilename for s in info.siblings
             if s.rfilename.startswith("data/train_sft-") and s.rfilename.endswith(".parquet")]
    files.sort()
    local = [hf_hub_download(UPSTREAM, f, repo_type="dataset", revision=revision)
             for f in files]
    print(f"[freeze] {len(files)} parquet shards downloaded")

    tables = [pq.read_table(f, columns=["messages"]) for f in local]
    print(f"[freeze] total train_sft conversations: {sum(t.num_rows for t in tables)}")

    # 确定性抽样：先按全局行号洗牌（seed 42），再取前 N
    rng = random.Random(SEED)
    total = sum(t.num_rows for t in tables)
    order = list(range(total))
    rng.shuffle(order)
    wanted = set(order[:N_TRAIN + N_VAL])

    picked: list[dict] = []
    base = 0
    for t in tables:
        msgs_col = t.column("messages").to_pylist()
        for i, msgs in enumerate(msgs_col):
            gi = base + i
            if gi in wanted:
                picked.append({"global_row": gi, "messages": msgs})
        base += t.num_rows
    assert len(picked) == N_TRAIN + N_VAL, f"抽样数不符：{len(picked)}"
    picked.sort(key=lambda x: x["global_row"])

    tok = AutoTokenizer.from_pretrained(str(TEMPLATE_TOKENIZER))
    records = []
    for item in picked:
        text = tok.apply_chat_template(
            item["messages"], chat_template=None, tokenize=False,
            add_generation_prompt=False, enable_thinking=False)
        records.append({"global_row": item["global_row"], "text": text})

    # 长度统计（用同一 tokenizer，供 MANIFEST 记录；训练时按 seq 截断）
    print("[freeze] tokenizing for length stats ...")
    lengths = [len(tok.encode(r["text"])) for r in records]
    train_lengths = lengths[:N_TRAIN]

    train_recs = records[:N_TRAIN]
    val_recs = records[N_TRAIN:]
    for name, recs in (("train.jsonl", train_recs), ("validation.jsonl", val_recs)):
        (OUT / name).write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs),
            encoding="utf-8")

    (OUT / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(OUT / f)}  {f}\n" for f in ("train.jsonl", "validation.jsonl")),
        encoding="utf-8")

    manifest = {
        "kind": "formal-dataset-freeze",
        "version": "formal_sft_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration": "research/preregistration.md",
        "upstream": {
            "dataset": UPSTREAM,
            "revision": revision,
            "split": "train_sft",
            "total_conversations": total,
            "license": "uc-nc (see upstream card); research use",
        },
        "sampling": {
            "seed": SEED,
            "method": "global row order shuffled with random.Random(42); "
                      "first 2048 -> train, next 32 -> validation; "
                      "sorted back by global_row",
            "n_train": N_TRAIN, "n_validation": N_VAL,
        },
        "preprocessing": {
            "chat_template": "tokenizer.apply_chat_template(messages, "
                             "add_generation_prompt=False, enable_thinking=False)",
            "template_tokenizer": "models/Qwen3-4B (Qwen3 family shared)",
            "field_mapping": "messages -> text; loss over all tokens (no prompt masking)",
            "truncation": "at training time to training.sequence_length",
            "packing": False,
        },
        "tokenizer": {"id": "Qwen/Qwen3-4B",
                      "local_path": "models/Qwen3-4B"},
        "length_stats": {
            "unit": "Qwen3 tokens (full formatted text, pre-truncation)",
            "train_min": min(train_lengths), "train_max": max(train_lengths),
            "train_mean": round(sum(train_lengths) / len(train_lengths), 1),
            "train_p50": sorted(train_lengths)[len(train_lengths) // 2],
        },
        "files": {f: {"sha256": sha256_file(OUT / f),
                      "size_bytes": (OUT / f).stat().st_size}
                  for f in ("train.jsonl", "validation.jsonl", "SHA256SUMS")},
        "usage_restriction": "synthetic/long-context workloads separate; "
                             "this frozen subset is the ONLY formal SFT data",
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                       encoding="utf-8")
    print(f"[freeze] {OUT}: train={N_TRAIN} val={N_VAL} "
          f"len[min,max]=[{min(train_lengths)},{max(train_lengths)}] "
          f"revision={revision[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
