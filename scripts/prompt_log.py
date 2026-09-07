#!/usr/bin/env python3
"""prompt_log —— 正式任务 prompt 的台账 harness。

PROMPT.md 是唯一事实源：元数据表（5 列）+ 逐字原文章节。本脚本负责全部
机械操作：登记（begin）、终结（finish）、README 镜像同步（sync）。

规则（与 AGENTS.md 对齐）：
- 原文逐字入账，绝不改字；缺失值如实标注，不猜。
- finish 的状态与产出必须来自真实运行证据（--evidence）。
- 提交无法包含自身 sha：finish 先提交任务产出（commit A），再把 A 的短
  sha 填进 Git 列并做登记提交（commit B）。

用法：
  uv run python scripts/prompt_log.py begin --file <原文文件> [--date YYYY-MM-DD]
  uv run python scripts/prompt_log.py finish N --status 已完成|未完成 \
      --outputs a.md,b.md --evidence "命令 + 关键输出" [--note ...]
  uv run python scripts/prompt_log.py sync [--check] [--init]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPT_MD = ROOT / "PROMPT.md"

MARK_BEGIN = "<!-- prompt-log:begin: 由 scripts/prompt_log.py 自动生成，请勿手工编辑 -->"
MARK_END = "<!-- prompt-log:end -->"

README_SPECS = {
    "en": {
        "path": ROOT / "README.md",
        "heading": "## Prompt log",
        "intro": "Auto-generated mirror of [PROMPT.md](PROMPT.md) — do not edit inside the markers.",
        "header": "| Prompt | Date | Status | Commit |",
        "status": {"已完成": "✅ done", "未完成": "⬜ not done", "进行中": "🔄 in progress"},
    },
    "zh": {
        "path": ROOT / "README.zh-CN.md",
        "heading": "## Prompt 台账",
        "intro": "[PROMPT.md](PROMPT.md) 的自动镜像——标记区内请勿手工编辑。",
        "header": "| Prompt | 日期 | 状态 | 提交 |",
        "status": {"已完成": "✅ 已完成", "未完成": "⬜ 未完成", "进行中": "🔄 进行中"},
    },
}
ANCHOR_BEFORE = {"en": "## Documentation", "zh": "## 文档"}

SECTION_RE = re.compile(r"^# prompt(\d+):")
PLACEHOLDER = "（见下一提交）"
STATUS_PENDING = "进行中"
STATUS_FINAL = ("已完成", "未完成")


class PromptLogError(Exception):
    """可预期的状态错误；消息面向用户，中文。"""


@dataclass
class Row:
    number: int
    date: str
    status: str
    git: str
    outputs: str
    line_idx: int
    raw_line: str


def run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True
    )
    if check and proc.returncode != 0:
        raise PromptLogError(f"git {' '.join(args)} 失败：{proc.stderr.strip()}")
    return proc


def git_identity_ok() -> bool:
    return run_git(["var", "GIT_AUTHOR_IDENT"], check=False).returncode == 0


def dirty_files() -> list[str]:
    out = run_git(["status", "--porcelain"]).stdout
    return [line[3:] for line in out.splitlines() if line.strip()]


def head_short() -> str:
    return run_git(["rev-parse", "--short", "HEAD"]).stdout.strip()


def require_clean_tree(context: str) -> None:
    dirty = dirty_files()
    if dirty:
        raise PromptLogError(
            f"{context}要求工作树干净，当前有未提交变更：\n  "
            + "\n  ".join(dirty)
            + "\n请先提交或处置这些变更后重试。"
        )


def parse_rows(text: str) -> list[Row]:
    rows: list[Row] = []
    for idx, line in enumerate(text.splitlines()):
        if not line.startswith("| [prompt"):
            continue
        parts = line.split("|")
        if len(parts) != 7:
            raise PromptLogError(
                f"PROMPT.md 第 {idx + 1} 行列数异常（应为 5 列 / split 后 7 段）：\n{line}\n"
                "单元格内不允许出现未转义的 |。请手工修复后重试。"
            )
        cell1 = parts[1].strip()
        m = re.fullmatch(r"\[prompt(\d+)\]\(#prompt\d+\)", cell1)
        if not m:
            raise PromptLogError(
                f"PROMPT.md 第 {idx + 1} 行首列锚点格式异常：{cell1}\n应为 [promptNN](#promptNN)。"
            )
        rows.append(
            Row(
                number=int(m.group(1)),
                date=parts[2].strip(),
                status=parts[3].strip(),
                git=parts[4].strip(),
                outputs=parts[5].strip(),
                line_idx=idx,
                raw_line=line,
            )
        )
    return rows


def section_numbers(text: str) -> set[int]:
    return {int(m.group(1)) for m in
            (SECTION_RE.match(l) for l in text.splitlines()) if m}


def check_consistency(rows: list[Row], text: str) -> None:
    t = {r.number for r in rows}
    s = section_numbers(text)
    if t != s:
        raise PromptLogError(
            f"表格行与章节标题编号不一致：表格={sorted(t)} 章节={sorted(s)}。"
            "请手工核对 PROMPT.md 后重试。"
        )


def render_row(number: int, date: str, status: str, git: str, outputs: str) -> str:
    return (
        f"| [prompt{number:02d}](#prompt{number:02d}) "
        f"| {date} | {status} | {git} | {outputs} |"
    )


def replace_row(text: str, row: Row, *, status: str | None = None,
                git: str | None = None, outputs: str | None = None) -> str:
    """只重渲染目标行（保留原行终止符风格），其余行字节不动。"""
    new_line = render_row(
        row.number,
        row.date,
        row.status if status is None else status,
        row.git if git is None else git,
        row.outputs if outputs is None else outputs,
    )
    lines = text.splitlines(keepends=True)
    old = lines[row.line_idx]
    terminator = "\r\n" if old.endswith("\r\n") else ("\n" if old.endswith("\n") else "")
    lines[row.line_idx] = new_line + terminator
    return "".join(lines)


def insert_row_after_last(text: str, new_line: str, rows: list[Row]) -> str:
    lines = text.splitlines(keepends=True)
    lines.insert(rows[-1].line_idx + 1, new_line + "\n")
    return "".join(lines)


def append_section(text: str, number: int, body: str) -> str:
    if not text.endswith("\n"):
        text += "\n"
    return f"{text}\n---\n\n# prompt{number:02d}:\n\n{body.rstrip()}\n"


def mirror_block(lang: str, rows: list[Row]) -> str:
    spec = README_SPECS[lang]
    lines = [MARK_BEGIN, spec["header"], "| --- | --- | --- | --- |"]
    for r in rows:
        status = spec["status"].get(r.status, r.status)
        lines.append(
            f"| [prompt{r.number:02d}](PROMPT.md#prompt{r.number:02d}) "
            f"| {r.date} | {status} | {r.git} |"
        )
    lines.append(MARK_END)
    return "\n".join(lines)


def sync_readmes(rows: list[Row], *, init: bool = False,
                 check: bool = False) -> list[str]:
    """把镜像块写入两个 README。返回被修改（或将漂移）的文件列表。"""
    changed: list[str] = []
    for lang, spec in README_SPECS.items():
        path: Path = spec["path"]
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        block = mirror_block(lang, rows)
        if MARK_BEGIN in text:
            head, rest = text.split(MARK_BEGIN, 1)
            _, tail = rest.split(MARK_END, 1)
            new_text = head + block + tail
        elif init:
            anchor = ANCHOR_BEFORE[lang]
            if f"\n{anchor}\n" not in "\n" + text:
                raise PromptLogError(
                    f"{path.name} 中未找到锚点标题 {anchor}，无法 --init 插入镜像节。"
                )
            section = (
                f"{spec['heading']}\n\n{spec['intro']}\n\n{block}\n\n"
            )
            new_text = text.replace(f"\n{anchor}\n", f"\n{section}{anchor}\n", 1)
        else:
            raise PromptLogError(
                f"{path.name} 缺少镜像标记，请先运行 sync --init（或手工放置标记）。"
            )
        if new_text != text:
            changed.append(path.name)
            if not check:
                path.write_text(new_text, encoding="utf-8")
    if check and changed:
        raise PromptLogError(
            "README 镜像与 PROMPT.md 存在漂移（--check 只核对不写入）：\n  "
            + "\n  ".join(changed)
        )
    return changed


def cmd_begin(args: argparse.Namespace) -> int:
    require_clean_tree("begin")
    if not git_identity_ok():
        raise PromptLogError(
            "git 无法解析提交身份（git var GIT_AUTHOR_IDENT 失败）。"
            "请先配置：git config --global user.name / user.email"
        )
    src = Path(args.file)
    if not src.is_file():
        raise PromptLogError(f"原文文件不存在：{src}")
    try:
        body = src.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise PromptLogError(f"原文文件不是有效 UTF-8：{exc}") from exc
    if not body.strip():
        raise PromptLogError("原文为空，拒绝登记。")

    text = PROMPT_MD.read_text(encoding="utf-8")
    rows = parse_rows(text)
    check_consistency(rows, text)
    sync_readmes(rows, check=True)  # 预检：标记缺失/镜像漂移都在改动 PROMPT.md 之前暴露

    number = max(r.number for r in rows) + 1
    date = args.date or _dt.date.today().isoformat()
    row_line = render_row(number, date, STATUS_PENDING, "（进行中）", "待补")
    text = insert_row_after_last(text, row_line, rows)
    text = append_section(text, number, body)
    PROMPT_MD.write_text(text, encoding="utf-8")

    rows_now = parse_rows(text)
    sync_readmes(rows_now)
    run_git(["add", "PROMPT.md", "README.md", "README.zh-CN.md"])
    run_git(["commit", "-m", f"prompt{number:02d}: 记录任务开始"])
    sha = head_short()
    print(f"[begin] prompt{number:02d} 已登记并提交（begin 提交 {sha}）")
    print(f"[begin] 日期 {date}；原文 {len(body)} 字符逐字入账")
    print(f"[begin] Git 列将在 finish 时填入任务产出提交的 sha")
    return 0


def cmd_finish(args: argparse.Namespace) -> int:
    if args.status not in STATUS_FINAL:
        raise PromptLogError(f"--status 只接受 {' / '.join(STATUS_FINAL)}，收到：{args.status}")
    if not git_identity_ok():
        raise PromptLogError("git 无法解析提交身份，请先配置 user.name / user.email。")
    if not args.evidence or not args.evidence.strip():
        raise PromptLogError("--evidence 不能为空：必须提供真实运行过的验证命令及其关键输出。")

    text = PROMPT_MD.read_text(encoding="utf-8")
    rows = parse_rows(text)
    check_consistency(rows, text)
    row = next((r for r in rows if r.number == args.number), None)
    if row is None:
        valid = ", ".join(str(r.number) for r in rows)
        raise PromptLogError(f"prompt{args.number:02d} 不在台账中。有效编号：{valid}")
    if row.status != STATUS_PENDING:
        raise PromptLogError(
            f"prompt{row.number:02d} 已终结于状态「{row.status}」，拒绝重复 finish。"
            "如确需更正，请手工编辑 PROMPT.md 并以普通 commit 说明理由。"
        )

    outputs_cell = "（无文件产出）"
    if args.outputs:
        paths = [p.strip() for p in args.outputs.split(",") if p.strip()]
        for p in paths:
            if not (ROOT / p).exists():
                raise PromptLogError(f"产出路径不存在：{p}（禁止登记不存在的文件）")
        outputs_cell = "<br>".join(f"[{p}]({p})" for p in paths)

    # commit A：终态行（Git 列占位）+ 该任务全部变更
    text = replace_row(text, row, status=args.status, git=PLACEHOLDER, outputs=outputs_cell)
    PROMPT_MD.write_text(text, encoding="utf-8")
    sync_readmes(parse_rows(text))
    task_dirty = [f for f in dirty_files()
                  if f not in ("PROMPT.md", "README.md", "README.zh-CN.md")]
    if not task_dirty:
        print("[警告] 本次任务除记录文件外无代码/文档产出（纯调研任务可继续）。", file=sys.stderr)
    run_git(["add", "-A"])
    msg_a = [f"prompt{args.number:02d}: {args.status} 任务产出", f"evidence: {args.evidence}"]
    if args.note:
        msg_a.append(f"note: {args.note}")
    if not task_dirty:
        msg_a.append("note: 本任务无代码产出")
    flat: list[str] = []
    for line in msg_a:
        flat.extend(["-m", line])
    run_git(["commit", *flat])
    sha_a = head_short()

    # commit B：把产出提交的 sha 写回 Git 列（提交无法包含自身 sha，故分两步）
    text = PROMPT_MD.read_text(encoding="utf-8")
    rows_now = parse_rows(text)
    row_now = next((r for r in rows_now if r.number == args.number), None)
    if row_now is None:
        raise PromptLogError(
            f"commit A 后未找到 prompt{args.number:02d} 行——PROMPT.md 可能在任务期间被外部修改，请人工核查。"
        )
    PROMPT_MD.write_text(
        replace_row(text, row_now, git=f"`{sha_a}`"), encoding="utf-8"
    )
    sync_readmes(parse_rows(PROMPT_MD.read_text(encoding="utf-8")))
    run_git(["add", "PROMPT.md", "README.md", "README.zh-CN.md"])
    run_git(["commit", "-m", f"prompt{args.number:02d}: 登记完成，产出提交 {sha_a}"])
    print(f"[finish] prompt{args.number:02d} {args.status}；产出提交 {sha_a}，登记提交 {head_short()}")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    text = PROMPT_MD.read_text(encoding="utf-8")
    rows = parse_rows(text)
    check_consistency(rows, text)
    changed = sync_readmes(rows, init=args.init, check=args.check)
    if args.check:
        print(f"[sync] 核对完成：{'无漂移' if not changed else '存在漂移'}")
    else:
        target = "已插入镜像节" if args.init else "已同步"
        print(f"[sync] {target}；本次修改：{changed if changed else '无'}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="prompt_log", description="PROMPT.md 台账 harness")
    sub = parser.add_subparsers(dest="command", required=True)

    p_begin = sub.add_parser("begin", help="登记一条正式 prompt（要求工作树干净）")
    p_begin.add_argument("--file", required=True, help="prompt 原文文件（UTF-8，逐字入账）")
    p_begin.add_argument("--date", default=None, help="覆盖登记日期 YYYY-MM-DD（默认今天）")

    p_finish = sub.add_parser("finish", help="终结一条 prompt（状态/产出须来自真实验证）")
    p_finish.add_argument("number", type=int, help="prompt 编号，如 4")
    p_finish.add_argument("--status", required=True, help="已完成 或 未完成")
    p_finish.add_argument("--outputs", default="", help="产出文件相对路径，逗号分隔（可空）")
    p_finish.add_argument("--evidence", required=True, help="验证命令及关键输出（进入 commit message）")
    p_finish.add_argument("--note", default="", help="备注（可选）")

    p_sync = sub.add_parser("sync", help="重建 README 镜像节")
    p_sync.add_argument("--check", action="store_true", help="只核对漂移不写入（漂移时退出码 2）")
    p_sync.add_argument("--init", action="store_true", help="镜像标记缺失时自动插入")

    args = parser.parse_args(argv)
    try:
        if args.command == "begin":
            return cmd_begin(args)
        if args.command == "finish":
            return cmd_finish(args)
        return cmd_sync(args)
    except PromptLogError as exc:
        print(f"[prompt_log] 错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
