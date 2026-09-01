#!/usr/bin/env python3
"""薄 CLI：核心逻辑在 src/benchmark/supervisor.py。

用法：
  uv run python scripts/run_experiment.py --config configs/experiments/X.yaml \
      [--timeout 秒] -- <exact command argv...>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from benchmark.supervisor import (  # noqa: E402
    ConfigValidationError,
    load_and_validate_config,
    run_experiment,
)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="经由 Experiment Supervisor 启动一个实验子进程并产出 raw result")
    parser.add_argument("--config", required=True, help="experiment YAML 路径")
    parser.add_argument("--timeout", type=float, default=None,
                        help="子进程超时秒数（缺省不限）")
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="'--' 之后的精确命令 argv")
    args = parser.parse_args(argv)

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("缺少命令：在 '--' 之后给出精确的命令 argv")

    try:
        load_and_validate_config(args.config)
    except ConfigValidationError as exc:
        print(f"[run_experiment] 配置验证失败：{exc}", file=sys.stderr)
        return 2

    try:
        result_dir = run_experiment(args.config, command,
                                    timeout_seconds=args.timeout)
    except RuntimeError as exc:
        print(f"[run_experiment] 拒绝运行：{exc}", file=sys.stderr)
        return 3
    print(result_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
