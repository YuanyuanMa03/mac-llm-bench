"""scripts/prompt_log.py 的单元/集成测试。

在 tmp_path 中构建临时 git 仓库，把模块全局 ROOT/PROMPT_MD/README_SPECS
重定向过去后直调 main([...])。main 会捕获 PromptLogError 返回 2，因此
失败路径断言退出码 2 + stderr 消息片段；直调的纯函数用 pytest.raises。
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "prompt_log.py"

_spec = importlib.util.spec_from_file_location("prompt_log", SCRIPT)
pl = importlib.util.module_from_spec(_spec)
sys.modules["prompt_log"] = pl  # dataclass 在 3.13 需要 sys.modules 里有本模块
_spec.loader.exec_module(pl)

SAMPLE = """# Prompt 记录

| Prompt | 日期 | 状态 | Git | 产出文件 |
| --- | --- | --- | --- | --- |
| [prompt01](#prompt01) | 2026-08-30 | 已完成 | `abc1234` | [docs/a.md](docs/a.md) |
| [prompt02](#prompt02) | 2026-08-30 | 未完成 | `abc1234`（补提交） | [tests/b.py](tests/b.py)（仅测试，实现缺失） |
| [prompt03](#prompt03) | 2026-08-31 | 已完成 | `abc1234`（补提交） | [c.md](c.md)<br>[d.md](d.md)<br>models/（说明文字） |

状态含义：

- 富文本说明行，sync 时必须字节不动。

---

# prompt01:

第一段原文。

---

# prompt02:

第二段原文。

---

# prompt03:

第三段原文，含空行与【特殊字符】。
"""

README_EN = "# T\n\n## Documentation\n\n- x\n"
README_ZH = "# T\n\n## 文档\n\n- x\n"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.name", "tester")
    _git(tmp_path, "config", "user.email", "tester@example.com")
    (tmp_path / "PROMPT.md").write_text(SAMPLE, encoding="utf-8")
    (tmp_path / "README.md").write_text(README_EN, encoding="utf-8")
    (tmp_path / "README.zh-CN.md").write_text(README_ZH, encoding="utf-8")
    monkeypatch.setattr(pl, "ROOT", tmp_path)
    monkeypatch.setattr(pl, "PROMPT_MD", tmp_path / "PROMPT.md")
    monkeypatch.setitem(pl.README_SPECS["en"], "path", tmp_path / "README.md")
    monkeypatch.setitem(pl.README_SPECS["zh"], "path", tmp_path / "README.zh-CN.md")
    assert pl.main(["sync", "--init"]) == 0
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "init")
    return tmp_path


def _fails(args: list[str], frag: str, capsys: pytest.CaptureFixture[str]) -> None:
    """main 捕获异常返回 2：断言退出码 + stderr 消息片段。"""
    assert pl.main(args) == 2, f"预期失败但成功了：{args}"
    assert frag in capsys.readouterr().err


def _prompt_file(repo: Path, text: str) -> Path:
    outside = repo.parent / f"{repo.name}-outside"
    outside.mkdir(exist_ok=True)
    f = outside / "p.txt"
    f.write_text(text, encoding="utf-8")
    return f


def _read(repo: Path, name: str) -> str:
    return (repo / name).read_text(encoding="utf-8")


def _row(repo: Path, n: int) -> str:
    for line in _read(repo, "PROMPT.md").splitlines():
        if line.startswith(f"| [prompt{n:02d}]"):
            return line
    raise AssertionError(f"row prompt{n:02d} not found")


def test_begin_appends_section_verbatim_and_inserts_row(repo: Path) -> None:
    body = "正式 prompt04 原文。\n第二行：含 `反引号` 与【括号】。\n"
    assert pl.main(["begin", "--file", str(_prompt_file(repo, body)),
                    "--date", "2026-09-01"]) == 0
    text = _read(repo, "PROMPT.md")
    assert f"# prompt04:\n\n{body.rstrip()}\n" in text  # 逐字（仅去尾部空白）
    assert _row(repo, 4) == ("| [prompt04](#prompt04) | 2026-09-01 | 进行中 "
                             "| （进行中） | 待补 |")
    assert _git(repo, "log", "-1", "--format=%s").stdout.strip() == "prompt04: 记录任务开始"


def test_begin_refuses_dirty_tree(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (repo / "junk.txt").write_text("x", encoding="utf-8")
    _fails(["begin", "--file", str(_prompt_file(repo, "x"))], "未提交变更", capsys)
    assert "prompt04" not in _read(repo, "PROMPT.md")
    assert _git(repo, "log", "--format=%s").stdout.strip() == "init"  # 无新提交


def test_begin_flags_table_section_mismatch(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    lines = _read(repo, "PROMPT.md").splitlines(keepends=True)
    lines = [l for l in lines if not l.startswith("| [prompt03]")]
    (repo / "PROMPT.md").write_text("".join(lines), encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "break")
    _fails(["begin", "--file", str(_prompt_file(repo, "x"))], "编号不一致", capsys)


def test_begin_rejects_empty_or_missing_file(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _fails(["begin", "--file", str(repo / "nope.txt")], "不存在", capsys)
    _fails(["begin", "--file", str(_prompt_file(repo, "  \n"))], "原文为空", capsys)


def _begin4(repo: Path, date: str = "2026-09-01") -> None:
    assert pl.main(["begin", "--file", str(_prompt_file(repo, "prompt04 原文。")),
                    "--date", date]) == 0


def test_finish_happy_path_two_commits_and_git_cell(repo: Path) -> None:
    _begin4(repo)
    task = repo / "docs" / "models_disk_usage.md"
    task.parent.mkdir()
    task.write_text("统计结果", encoding="utf-8")
    rc = pl.main(["finish", "4", "--status", "已完成",
                  "--outputs", "docs/models_disk_usage.md",
                  "--evidence", "du -sk models/* | sort"])
    assert rc == 0
    row = _row(repo, 4)
    assert "| 2026-09-01 | 已完成 |" in row  # 日期保持 begin 日期
    assert "[docs/models_disk_usage.md](docs/models_disk_usage.md)" in row
    shas = _git(repo, "log", "--format=%h").stdout.split("\n")
    sha_a = shas[1]  # HEAD=登记提交(B)，其父=任务产出提交(A)
    assert f"| `{sha_a}` |" in row
    show_a = _git(repo, "show", "--stat", "--format=", sha_a).stdout
    assert "docs/models_disk_usage.md" in show_a
    assert "PROMPT.md" in show_a  # 决策：任务产出与记录同在 commit A
    logs = _git(repo, "log", "-3", "--format=%B").stdout
    assert "evidence: du -sk" in logs
    assert "登记完成，产出提交" in logs


def test_finish_rejects_nonexistent_output(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _begin4(repo)
    _fails(["finish", "4", "--status", "已完成",
            "--outputs", "ghost.md", "--evidence", "x"], "不存在", capsys)
    assert "进行中" in _row(repo, 4)  # 拒绝后状态未变


def test_finish_rejects_already_finalized_and_unknown_number(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _fails(["finish", "9", "--status", "已完成", "--evidence", "x"], "不在台账中", capsys)
    _begin4(repo)
    assert pl.main(["finish", "4", "--status", "未完成", "--evidence", "复现失败：import error"]) == 0
    _fails(["finish", "4", "--status", "已完成", "--evidence", "x"], "已终结", capsys)


def test_finish_without_outputs_warns_but_proceeds(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _begin4(repo)
    assert pl.main(["finish", "4", "--status", "未完成", "--evidence", "调研无产出"]) == 0
    assert "无代码/文档产出" in capsys.readouterr().err
    assert "（无文件产出）" in _row(repo, 4)


def test_sync_is_idempotent_and_restores_hand_edits(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert pl.main(["sync"]) == 0
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""  # 幂等
    capsys.readouterr()
    readme = repo / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace("✅ done", "手工改动", 1),
        encoding="utf-8")
    _fails(["sync", "--check"], "漂移", capsys)
    assert pl.main(["sync"]) == 0
    assert "✅ done" in readme.read_text(encoding="utf-8")


def test_sync_without_markers_fails_then_init_adds(
        repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (repo / "README.zh-CN.md").write_text(README_ZH, encoding="utf-8")
    _fails(["sync"], "缺少镜像标记", capsys)
    assert pl.main(["sync", "--init"]) == 0
    assert "## Prompt 台账" in _read(repo, "README.zh-CN.md")


def test_parse_rejects_malformed_row() -> None:
    bad = ("| [prompt02](#prompt02) | 2026-08-30 | 未完成 | `abc1234` "
           "| 有 | 竖格 | 单元格 |")
    with pytest.raises(pl.PromptLogError, match="列数异常"):
        pl.parse_rows(SAMPLE.replace(
            "| [prompt02](#prompt02) | 2026-08-30 | 未完成 | `abc1234`（补提交） "
            "| [tests/b.py](tests/b.py)（仅测试，实现缺失） |", bad))


def test_rich_text_neighbor_rows_byte_preserved(repo: Path) -> None:
    before = [l for l in _read(repo, "PROMPT.md").splitlines()
              if l.startswith("| [prompt")]
    _begin4(repo)
    after = [l for l in _read(repo, "PROMPT.md").splitlines()
             if l.startswith("| [prompt")]
    assert after[:3] == before  # 既有 3 行字节不动
