#!/usr/bin/env python3
"""薄 CLI：LoRA 训练核心在 src/train/lora_smoke.py。

用法：uv run python scripts/train_lora.py configs/experiments/exp0_qwen3_0.6b_lora.yaml
正常应经 scripts/run_experiment.py（Supervisor）启动本脚本。
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from train.lora_smoke import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
