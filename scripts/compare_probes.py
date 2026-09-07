#!/usr/bin/env python3
"""薄 CLI：配对对比逻辑在 src/analysis/paired_comparison.py。"""
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis.paired_comparison import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
