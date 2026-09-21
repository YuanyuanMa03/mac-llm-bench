"""src/analysis 模块测试：paired_comparison 参数化 + context_boundary 聚合。

使用合成 result.json（结构遵循 result_schema 0.1.0）验证派生逻辑；
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

from analysis import context_boundary, paired_comparison  # noqa: E402


def _make_raw_result(root: Path, group: str, seq: int, state: str = "success",
                     steps: int | None = 20, peak_gpu: int | None = 1,
                     dataset: str = "ds", tag: str = "") -> Path:
    d = root / "results" / "raw" / f"20260101T000000000000Z__exp{tag}__ctx{seq}"
    d.mkdir(parents=True)
    result = {
        "experiment": {"id": d.name, "comparison_group_id": group},
        "software": {"git_commit_sha": "a" * 40, "git_dirty": False},
        "model": {"id": "m", "resolved_revision": "b" * 40},
        "dataset": {"name": dataset, "max_sequence_length": seq},
        "training": {"method": "qlora", "sequence_length": seq,
                     "micro_batch_size": 1, "gradient_accumulation_steps": 1,
                     "lora_rank": 8, "lora_alpha": 16, "seed": 42,
                     "requested_steps": 20, "learning_rate": 0.0001,
                     "optimizer": "adamw", "quantization_bits": 4,
                     "target_modules": ["q_proj"]},
        "runtime": {
            "successful_steps": steps, "wall_clock_seconds": 10.0,
            "average_step_time_seconds": 0.5, "median_step_time_seconds": 0.4,
            "tokens_per_second": 100.0, "model_load_seconds": 1.0,
            "initial_swap_bytes": {"value": 1000},
            "peak_process_memory_bytes": {"value": None},
        },
        "status": {"terminal_state": state, "exit_code": 0 if state == "success" else None,
                   "signal": "SIGKILL" if state == "runtime_error" else None},
    }
    (d / "result.json").write_text(json.dumps(result), encoding="utf-8")
    (d / "training_metrics.json").write_text(
        json.dumps({"peak_metal_gpu_memory_bytes": peak_gpu,
                    "training_loss_final": 1.5}), encoding="utf-8")
    (d / "environment").mkdir()
    (d / "environment" / "raw_environment.txt").write_text(
        "swapusage before used = 1.00M\nswapusage after used = 2.00M\n",
        encoding="utf-8")
    return d


def test_paired_comparison_ctx_scaling(tmp_path: Path) -> None:
    _make_raw_result(tmp_path, "g-ctx512", 512, dataset="ds512")
    _make_raw_result(tmp_path, "g-ctx2048", 2048, dataset="ds2048")
    monkey = pytest.MonkeyPatch()
    monkey.setattr(paired_comparison, "ROOT", tmp_path)
    summary = paired_comparison.build(
        "g-ctx512", "g-ctx2048",
        kind="context-scaling-pair",
        declared_variables=paired_comparison.CTX_DECLARED_VARIABLES,
        controlled_factors=[f for f in paired_comparison.CONTROLLED_FACTORS
                            if f[0] not in paired_comparison.CTX_DECLARED_VARIABLES])
    monkey.undo()
    assert summary["kind"] == "context-scaling-pair"
    assert summary["controlled_comparison_valid"] is True
    assert summary["declared_variables"]["training.sequence_length"] == {
        "a": 512, "b": 2048}
    assert summary["differences"]["median_step_time_seconds"]["a_minus_b"] == 0.0


def test_paired_comparison_flags_uncontrolled(tmp_path: Path) -> None:
    _make_raw_result(tmp_path, "ga", 512, tag="-a")
    _make_raw_result(tmp_path, "gb", 512, tag="-b")
    # 改动 b 的 seed → 受控性应变 False
    d = tmp_path / "results" / "raw" / "20260101T000000000000Z__exp-b__ctx512"
    r = json.loads((d / "result.json").read_text())
    r["training"]["seed"] = 7
    (d / "result.json").write_text(json.dumps(r))
    monkey = pytest.MonkeyPatch()
    monkey.setattr(paired_comparison, "ROOT", tmp_path)
    summary = paired_comparison.build("ga", "gb")
    monkey.undo()
    assert summary["controlled_comparison_valid"] is False


def test_context_boundary_series_and_confounder(tmp_path: Path) -> None:
    d512 = _make_raw_result(tmp_path, "probe-4b-4bit-ctx512-qlora20-seed42", 512)
    d2048 = _make_raw_result(tmp_path, "probe-4b-4bit-ctx2048-qlora20-seed42", 2048)
    d8192 = _make_raw_result(tmp_path, "probe-4b-4bit-ctx8192-qlora20-seed42", 8192,
                            state="runtime_error", steps=None, peak_gpu=None)
    monkey = pytest.MonkeyPatch()
    monkey.setattr(context_boundary, "RAW",
                   tmp_path / "results" / "raw")
    monkey.setattr(context_boundary, "SELECTED_EXPERIMENT_IDS",
                   {512: d512.name, 2048: d2048.name, 8192: d8192.name})
    summary = context_boundary.build()
    monkey.undo()
    series = summary["series"]
    assert [s["sequence_length"] for s in series] == [512, 2048, 8192]
    assert series[2]["terminal_state"] == "runtime_error"
    assert series[2]["signal"] == "SIGKILL"
    # 边界区间：最后 success=2048，首个失败=8192
    assert summary["boundary_interval"]["completed_cap"] == 2048
    assert summary["boundary_interval"]["first_failure_ctx"] == 8192
    assert summary["boundary_interval"]["inference_valid"] is True
    # swap 增长 confounder 被记录
    kinds = {c["kind"] for c in summary["confounders"]}
    assert "system_swap_delta" in kinds


def test_context_boundary_no_failure_keeps_boundary_open(tmp_path: Path) -> None:
    d512 = _make_raw_result(tmp_path, "probe-4b-4bit-ctx512-qlora20-seed42", 512)
    monkey = pytest.MonkeyPatch()
    monkey.setattr(context_boundary, "RAW",
                   tmp_path / "results" / "raw")
    monkey.setattr(context_boundary, "SELECTED_EXPERIMENT_IDS", {512: d512.name})
    summary = context_boundary.build()
    monkey.undo()
    assert summary["boundary_interval"]["inference_valid"] is False
    assert summary["boundary_interval"]["statement"] is None
