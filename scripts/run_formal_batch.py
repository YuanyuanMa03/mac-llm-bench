#!/usr/bin/env python3
"""顺序执行 formal benchmark 批次（预注册矩阵），幂等可断点续跑。

- 严格串行（机器时间政策：绝不并发训练）；
- 自然排序：按 (逻辑参数量, 方法, ctx, batch, rank, seed) 排序，避免字符串
  排序把 14b 排到 4b 前；
- swap 闸门：每个 run 开始前轮询 vm.swapusage，used > 阈值则等待
  （统一内存机器上 swap 基线漂移会污染跨 run 可比性；
  2026-09-12 深夜事件实证：swap>9GB 时 14B 24min 零步完成）；
- supersede：--supersede 模式下，同 group+config hash 已有 success 时不再
  跳过，而是将 supersedes_experiment_id 指向旧 run 重新执行（旧结果保留）；
- 跳过规则（缺省）：已有同 group+hash 的 success 且未被 supersede → 跳过；
  失败结果不自动重试（协议：失败是有效观测）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_config(config_path: Path) -> dict:
    return yaml.safe_load(config_path.read_text(encoding="utf-8"))


def config_digest(config: dict) -> str:
    """与 src/benchmark/schema.config_sha256 完全一致（紧凑分隔符）。"""
    return hashlib.sha256(
        json.dumps(config, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def sort_key(config: dict) -> tuple:
    tr = config["training"]
    params = config.get("_params_hint") or 0
    return (params, tr["method"], tr["sequence_length"],
            tr["micro_batch_size"], (tr.get("lora") or {}).get("rank") or 0,
            tr["seed"])


import re

PARAM_ORDER = {"0.6": 1, "1.7": 2, "4": 3, "8": 4, "14": 5}


def model_order(config: dict) -> int:
    """从 model id 解析参数规模（Qwen3 命名 N.B / NN B，匹配 'B' 后边界，
    不受 '-4bit' 后缀干扰）。"""
    name = str(config["model"]["id"])
    m = re.search(r"(\d+(?:\.\d+)?)B(?![a-z])", name)
    if not m:
        return 9
    return PARAM_ORDER.get(m.group(1), 9)


def swap_used_bytes() -> int | None:
    import re
    import subprocess as sp
    out = sp.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True)
    if out.returncode != 0:
        return None
    m = re.search(r"used\s*=\s*([\d.]+)M", out.stdout)
    return int(round(float(m.group(1)) * 1024 * 1024)) if m else None


def existing_runs(group: str, digest: str) -> list[dict]:
    raw = ROOT / "results" / "raw"
    hits = []
    if not raw.exists():
        return hits
    for d in sorted(raw.iterdir()):
        rj = d / "result.json"
        if not rj.is_file():
            continue
        try:
            r = json.loads(rj.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if (r["experiment"].get("comparison_group_id") == group
                and r["experiment"].get("config_sha256") == digest):
            hits.append({"id": r["experiment"]["id"],
                         "state": r["status"]["terminal_state"]})
    return hits


def wait_for_swap(max_bytes: int, patience_s: float) -> dict:
    t0 = time.monotonic()
    while True:
        used = swap_used_bytes()
        if used is None or used <= max_bytes:
            return {"gate": "pass", "swap_used_bytes": used,
                    "waited_s": round(time.monotonic() - t0, 1)}
        if time.monotonic() - t0 > patience_s:
            return {"gate": "timeout", "swap_used_bytes": used,
                    "waited_s": round(time.monotonic() - t0, 1)}
        time.sleep(30)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("configs", nargs="+")
    parser.add_argument("--timeout", type=float, default=7200.0)
    parser.add_argument("--max-swap-before", type=float, default=8.5,
                        help="swap used 阈值 GiB；超过则等待（0 关闭闸门）")
    parser.add_argument("--swap-patience", type=float, default=3600.0,
                        help="闸门最长等待秒数，超时后带 gate=timeout 记录并继续")
    parser.add_argument("--supersede", action="store_true",
                        help="已有 success 的配置重跑并链接 supersedes_experiment_id")
    args = parser.parse_args()

    items = []
    for cfg in args.configs:
        p = Path(cfg)
        config = load_config(p)
        config["_params_hint"] = model_order(config)
        items.append((p, config))
    items.sort(key=lambda x: sort_key(x[1]))

    ran, skipped, failed = [], [], []
    for path, config in items:
        group = config["experiment"]["comparison_group_id"]
        digest = config_digest(config)
        prior = existing_runs(group, digest)
        has_success = any(h["state"] == "success" for h in prior)
        supersede_ids = [h["id"] for h in prior if h["state"] == "success"]

        if has_success and not args.supersede:
            print(f"[skip] {path.name} → 已有成功 run", flush=True)
            skipped.append(path.name)
            continue

        run_config_path = path
        if args.supersede and supersede_ids:
            # 派生配置：仅追加 supersedes_experiment_id 链（科学变量不变）
            derived = dict(config)
            derived.pop("_params_hint", None)
            derived["experiment"] = {**derived["experiment"],
                                     "supersedes_experiment_id": supersede_ids[0]}
            run_config_path = Path("/tmp") / f"formal-derived-{path.name}"
            run_config_path.write_text(
                yaml.safe_dump(derived, sort_keys=False, allow_unicode=True),
                encoding="utf-8")
            print(f"[supersede] {path.name} ← {supersede_ids[0][:40]}…", flush=True)

        gate = {"gate": "disabled"} if args.max_swap_before <= 0 else \
            wait_for_swap(int(args.max_swap_before * 2**30), args.swap_patience)
        print(f"[run ] {path.name} (group={group}, {gate})", flush=True)
        t0 = time.monotonic()
        proc = subprocess.run(
            ["uv", "run", "python", "scripts/run_experiment.py",
             "--config", str(run_config_path), "--timeout", str(args.timeout),
             "--", "uv", "run", "python", "scripts/train_lora.py",
             str(run_config_path)],
            cwd=ROOT, capture_output=True, text=True)
        wall = time.monotonic() - t0
        if proc.returncode == 0:
            ran.append(path.name)
            print(f"[ok  ] {path.name} ({wall:.0f}s)", flush=True)
        else:
            failed.append((path.name, proc.returncode, (proc.stderr or "")[-200:]))
            print(f"[FAIL] {path.name} rc={proc.returncode} ({wall:.0f}s)",
                  flush=True)

    print(json.dumps({"ran": ran, "skipped": skipped,
                      "failed": [f[0] for f in failed]}, indent=1))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
