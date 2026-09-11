#!/usr/bin/env python3
"""顺序执行 formal benchmark 批次（预注册矩阵），幂等可断点续跑。

- 严格串行（机器时间政策：绝不并发训练）；
- 跳过规则：results/raw/ 中已存在同 comparison_group_id 且 config_sha256 相同的
  terminal success → 跳过；失败结果不自动重试（协议：失败是有效观测）；
- 每个实验经 Experiment Supervisor 启动，caffeinate 包裹由调用方决定；
- 批次结束打印汇总（新增成功/跳过/失败清单）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def config_digest(config_path: Path) -> str:
    import yaml
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return hashlib.sha256(
        json.dumps(config, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def existing_success(group: str, digest: str) -> str | None:
    raw = ROOT / "results" / "raw"
    if not raw.exists():
        return None
    for d in sorted(raw.iterdir()):
        rj = d / "result.json"
        if not rj.is_file():
            continue
        try:
            r = json.loads(rj.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if (r["experiment"].get("comparison_group_id") == group
                and r["experiment"].get("config_sha256") == digest
                and r["status"]["terminal_state"] == "success"):
            return r["experiment"]["id"]
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("configs", nargs="+", help="formal config yaml 路径列表")
    parser.add_argument("--timeout", type=float, default=7200.0)
    args = parser.parse_args()

    ran, skipped, failed = [], [], []
    for cfg in args.configs:
        config_path = ROOT / cfg if not Path(cfg).is_absolute() else Path(cfg)
        import yaml
        group = yaml.safe_load(
            config_path.read_text(encoding="utf-8"))["experiment"]["comparison_group_id"]
        digest = config_digest(config_path)
        done = existing_success(group, digest)
        if done:
            print(f"[skip] {config_path.name} → 已有成功 run {done[:44]}…", flush=True)
            skipped.append(config_path.name)
            continue
        print(f"[run ] {config_path.name} (group={group})", flush=True)
        t0 = time.monotonic()
        proc = subprocess.run(
            ["uv", "run", "python", "scripts/run_experiment.py",
             "--config", str(config_path), "--timeout", str(args.timeout),
             "--", "uv", "run", "python", "scripts/train_lora.py",
             str(config_path)],
            cwd=ROOT, capture_output=True, text=True)
        wall = time.monotonic() - t0
        out = (proc.stdout or "").strip().splitlines()
        result_dir = out[-1] if out and out[-1].startswith("results/raw") else "?"
        if proc.returncode == 0:
            ran.append(config_path.name)
            print(f"[ok  ] {config_path.name} → {result_dir} ({wall:.0f}s)", flush=True)
        else:
            failed.append((config_path.name, proc.returncode,
                           (proc.stderr or "")[-300:]))
            print(f"[FAIL] {config_path.name} rc={proc.returncode} ({wall:.0f}s)",
                  flush=True)

    print(json.dumps({"ran": ran, "skipped": skipped,
                      "failed": [f[0] for f in failed]}, indent=1))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
