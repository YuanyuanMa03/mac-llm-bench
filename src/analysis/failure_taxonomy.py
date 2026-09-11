"""Failure taxonomy：从 raw results 生成机器可读失败分类（预注册 §5/§9）。

分类原则（协议 §3.8 + 预注册）：
- 只使用真实退出证据（returncode / signal / stderr 模式 / 异常类型）；
- terminal_state 永不改写；本模块生成的是 evidence-based 二级标注；
- SIGKILL 不自动等同 OOM：标注为 sigkill_consistent，附可用上下文证据
  （swap 变化、完成步数、stderr 内容），并区分 observation 与 interpretation。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "results" / "raw"

# evidence-based 二级标签（不覆盖 terminal_state）
SIGKILL_PATTERNS = [
    ("sigkill_signal", lambda r: r["status"].get("signal") == "SIGKILL"),
    ("sigkill_exit_137", lambda r: r["status"].get("exit_code") == 137),
]

STDERR_PATTERNS = [
    ("import_error", re.compile(r"(ModuleNotFoundError|ImportError)")),
    ("cuda_mlx_error", re.compile(r"(Metal|metal) (error|panic)")),
    ("python_traceback", re.compile(r"Traceback \(most recent call last\)")),
]


def classify_failure(r: dict, d: Path) -> dict | None:
    status = r["status"]
    if status["terminal_state"] == "success":
        return None
    labels: list[str] = []
    if any(p(r) for _, p in SIGKILL_PATTERNS):
        labels.append("sigkill_consistent")
    stderr_path = d / "logs" / "stderr.log"
    stderr_tail = ""
    if stderr_path.is_file():
        stderr_tail = stderr_path.read_text(encoding="utf-8", errors="replace")[-4000:]
    for name, pattern in STDERR_PATTERNS:
        if pattern.search(stderr_tail or ""):
            labels.append(f"stderr:{name}")

    rt = r["runtime"]
    steps = rt.get("successful_steps")
    # 上下文证据（observation 层）
    context = {
        "completed_steps_observation": steps,
        "wall_clock_seconds_observation": rt.get("wall_clock_seconds"),
        "error_phase": status.get("error_phase"),
        "classification_evidence": status.get("classification_evidence"),
    }
    interpretation: list[str] = []
    if "sigkill_consistent" in labels:
        interpretation.append(
            "SIGKILL 由内核或外部信号发出；在本系列运行中该模式与严重内存压力同时出现"
            "（见 swap 观测），但本次运行本身没有足够证据判定 OOM 为根因")
    if steps is not None and steps == 0:
        interpretation.append("失败发生在任何训练步完成之前")

    return {
        "experiment_id": r["experiment"]["id"],
        "terminal_state": status["terminal_state"],
        "exit_code": status["exit_code"],
        "signal": status.get("signal"),
        "error_type": status.get("error_type"),
        "evidence_labels": labels or ["no_specific_pattern"],
        "context_observations": context,
        "interpretation_only": interpretation,
        "raw_result_path": f"results/raw/{d.name}",
    }


def build() -> dict:
    failures = []
    successes = 0
    for d in sorted(RAW.iterdir()):
        rj = d / "result.json"
        if not d.is_dir() or not rj.is_file():
            continue
        r = json.loads(rj.read_text(encoding="utf-8"))
        if r["status"]["terminal_state"] == "success":
            successes += 1
        else:
            failures.append(classify_failure(r, d))
    return {
        "kind": "failure-taxonomy",
        "n_success": successes,
        "n_failures": len(failures),
        "failures": failures,
        "notes": [
            "evidence_labels 为二级标注，不覆盖 raw result 的 terminal_state",
            "swap before/after 等系统上下文见 context_boundary_probe_summary.json 与各 raw result",
        ],
    }


def main() -> int:
    out = ROOT / "results" / "processed" / "failure_taxonomy.json"
    taxonomy = build()
    out.write_text(json.dumps(taxonomy, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"[taxonomy] {taxonomy['n_success']} success / "
          f"{taxonomy['n_failures']} failures → {out.relative_to(ROOT)}")
    return 0
