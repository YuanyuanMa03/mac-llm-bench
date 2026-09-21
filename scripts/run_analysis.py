#!/usr/bin/env python3
"""一键重算全部 processed 数据 / 图 / 表（raw results 只读）。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    from analysis import failure_taxonomy, figures, flatten, summary, tables
    from analysis import context_boundary, coverage, hypothesis_audit
    # D12 事后探索性分析（论文重写版新增；只读 raw，产物同管线规范）
    from analysis import step_dynamics, system_state, memory_decomposition

    flatten.main()
    coverage.main()
    failure_taxonomy.main()
    context_boundary.main([])
    summary.main()
    figures.main()
    tables.main()
    step_dynamics.main()
    system_state.main()
    memory_decomposition.main()
    hypothesis_audit.main()
    print("[analysis] 全部 processed/figures/tables 已从 raw results 重新生成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
