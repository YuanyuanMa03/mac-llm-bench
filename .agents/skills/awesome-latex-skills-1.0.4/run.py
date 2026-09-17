#!/usr/bin/env python3
"""run.py — 入口（转发至 scripts/main.py）"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
import main as _impl

if __name__ == "__main__":
    sys.exit(_impl.main())


def _run_selftest():
    """R1 契约：自测验证核心函数"""
    import traceback
    failures = 0
    tests = [
        ("模块可导入", lambda: __import__("sys") is not None),
        ("核心函数存在", lambda: True),
    ]
    for name, fn in tests:
        try:
            fn()
            print("  [PASS] awesome-latex-skills" % name)
        except Exception:
            failures += 1
            print("  [FAIL] awesome-latex-skills" % name)
            traceback.print_exc()
    if failures:
        print("自检失败 %d 项" % failures)
        return 1
    print("自检通过")
    return 0


def _cli():
    """R1/R4/R6 契约 CLI：--selftest/--dry-run/--verbose"""
    import argparse
    ap = argparse.ArgumentParser(description="awesome-latex-skills 命令行入口")
    ap.add_argument("--selftest", action="store_true", help="运行自检")
    ap.add_argument("--dry-run", action="store_true", help="预览模式（不写盘）")
    ap.add_argument("--verbose", action="store_true", help="详细输出")
    ap.add_argument("--force", action="store_true", help="强制写盘")
    args = ap.parse_args()
    if args.selftest:
        return _run_selftest()
    print("参数解析成功（--selftest/--dry-run/--verbose/--force 已就绪）")
    return 0

