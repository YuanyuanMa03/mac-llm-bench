"""coverage 模块测试：raw ↔ processed 对账不变量与 disposition 规则。

合成 result.json（结构遵循 result_schema 0.1.0）验证派生逻辑；
合成数据仅用于测试软件行为，不作为研究 benchmark 数据。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis import coverage  # noqa: E402


def _mk_run(raw_root: Path, exp_id: str, *, group: str, state: str,
            seed: int, err: str | None = None,
            supersedes: str | None = None) -> str:
    d = raw_root / exp_id
    d.mkdir(parents=True)
    result = {
        "experiment": {
            "id": exp_id, "comparison_group_id": group,
            "supersedes_experiment_id": supersedes,
        },
        "software": {"git_commit_sha": "a" * 40, "git_dirty": False},
        "training": {"seed": seed, "micro_batch_size": 1,
                     "requested_steps": 20, "successful_steps": 20},
        "runtime": {
            "successful_steps": 20 if state == "success" else None,
            "wall_clock_seconds": 10.0,
            "median_step_time_seconds": 0.5,
            "system_vm_counters_before": json.dumps(
                {"counters_pages": {"swapins": 0}, "page_size_bytes": 16384}),
            "system_vm_counters_after": json.dumps(
                {"counters_pages": {"swapins": 1}, "page_size_bytes": 16384}),
        },
        "status": {
            "terminal_state": state,
            "exit_code": 0 if state == "success" else 1,
            "error_message": err,
        },
    }
    (d / "result.json").write_text(json.dumps(result), encoding="utf-8")
    return exp_id


def _to_df(raw_root: Path) -> "list[dict]":
    import pandas as pd
    rows = []
    for d in sorted(raw_root.iterdir()):
        r = json.loads((d / "result.json").read_text(encoding="utf-8"))
        flat = {
            "experiment.id": r["experiment"]["id"],
            "experiment.comparison_group_id": r["experiment"]["comparison_group_id"],
            "experiment.supersedes_experiment_id":
                r["experiment"]["supersedes_experiment_id"],
            "training.seed": r["training"]["seed"],
            "status.terminal_state": r["status"]["terminal_state"],
            "status.error_message": r["status"]["error_message"],
            "runtime.system_vm_counters_before":
                r["runtime"]["system_vm_counters_before"],
            "runtime.system_vm_counters_after":
                r["runtime"]["system_vm_counters_after"],
            "runtime.successful_steps": r["runtime"]["successful_steps"],
        }
        rows.append(flat)
    return pd.DataFrame(rows)


@pytest.fixture()
def synthetic_root(tmp_path: Path) -> Path:
    raw = tmp_path / "raw"
    raw.mkdir()
    # 1. 普通 success（formal）→ included
    _mk_run(raw, "run_ok", group="formal-axis1-x", state="success", seed=42)
    # 2. D5 签名 runtime_error → implementation-invalid
    _mk_run(raw, "run_d5", group="formal-axis4-b2", state="runtime_error",
            seed=42, err="ValueError: Initialization encountered "
                         "non-uniform length")
    # 3. 普通 runtime_error（无 D5 签名）→ failed retained
    _mk_run(raw, "run_fail", group="formal-axis1-y", state="runtime_error",
            seed=42, err="ValueError: something else")
    # 4. probe success → included（probe 组也走 retained）
    _mk_run(raw, "run_probe", group="probe-x", state="success", seed=42)
    # 5/6. 同 (group, seed, success) 重复 → 一个 included 一个 duplicate
    _mk_run(raw, "run_dup_a", group="formal-axis1-z", state="success", seed=7)
    _mk_run(raw, "run_dup_b", group="formal-axis1-z", state="success", seed=7)
    # 7. 被 supersede 的旧 success
    _mk_run(raw, "run_old", group="formal-axis1-w", state="success", seed=42)
    _mk_run(raw, "run_new", group="formal-axis1-w", state="success", seed=42,
            supersedes="run_old")
    return raw


def test_dispositions_and_reconciliation(synthetic_root: Path):
    df = _to_df(synthetic_root)
    # 与 flatten.build_tables 一致的 supersession 逆标记
    links = dict(zip(df["experiment.id"],
                     df["experiment.supersedes_experiment_id"]))
    df["_superseded_by"] = [
        next((new for new, old in links.items() if old == eid), None)
        if any(old == eid for old in links.values()) else None
        for eid in df["experiment.id"]
    ]
    report = coverage.build_coverage(df, raw_root=synthetic_root,
                                     val_root=synthetic_root.parent / "noval")
    per = report["per_run"]

    assert per["run_ok"]["disposition"] == "aggregation_included"
    assert per["run_d5"]["disposition"] == "excluded:implementation-invalid-d5"
    assert per["run_fail"]["disposition"] == "failed_retained_for_taxonomy"
    assert per["run_probe"]["disposition"] == "non-formal:probe"
    assert per["run_old"]["disposition"] == "excluded:superseded"
    assert per["run_new"]["disposition"] == "aggregation_included"
    dup_disps = {per["run_dup_a"]["disposition"],
                 per["run_dup_b"]["disposition"]}
    assert dup_disps == {"aggregation_included", "excluded:duplicate"}

    assert report["raw_total"] == 8
    assert report["processed_total"] == 8
    assert report["reconciliation_ok"] is True
    assert sum(report["dispositions"].values()) == 8
    assert report["validation_total"] == 0


def test_reconciliation_detects_missing_processed_row(synthetic_root: Path):
    df = _to_df(synthetic_root)
    links = dict(zip(df["experiment.id"],
                     df["experiment.supersedes_experiment_id"]))
    df["_superseded_by"] = [
        next((new for new, old in links.items() if old == eid), None)
        if any(old == eid for old in links.values()) else None
        for eid in df["experiment.id"]
    ]
    df_dropped = df[df["experiment.id"] != "run_fail"]  # 模拟 36/101 丢失
    report = coverage.build_coverage(df_dropped, raw_root=synthetic_root,
                                     val_root=synthetic_root.parent / "noval")
    assert report["reconciliation_ok"] is False
    assert report["processed_total"] == 7
    assert report["raw_total"] == 8


def test_kind_classification():
    assert coverage._kind("formal-axis1-0.6b-bf16-lora") == "formal"
    assert coverage._kind("probe-4b-4bit-qlora20-seed42") == "probe"
    assert coverage._kind("calibration-1.7b-lora100-seed42") == "calibration"
    assert coverage._kind("exp0-smoke") == "exp0-smoke"
    assert coverage._kind("warmup-trainer-v0.2") == "warmup"
    assert coverage._kind("something-else") == "other"
