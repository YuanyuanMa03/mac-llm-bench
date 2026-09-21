"""D12 事后探索性分析模块的纯函数测试（step_dynamics / system_state /
memory_decomposition）。合成数据仅测试软件行为，非 benchmark 数据。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis import memory_decomposition as md  # noqa: E402
from analysis import step_dynamics as sd  # noqa: E402
from analysis import system_state as ss  # noqa: E402


# ---------------------------------------------------------------- A1
def _step_df(eid: str, times: list[float]) -> pd.DataFrame:
    n = len(times)
    return pd.DataFrame({
        "step": range(1, n + 1),
        "loss": [1.0] * n,
        "loss_bearing_tokens": [100] * n,
        "step_time_seconds": times,
        "wall_utc": [f"2026-09-11T00:00:{i:02d}Z" for i in range(n)],
        "experiment_id": [eid] * n,
        "_raw_dir": [eid] * n,
    })


def _runs_frame(eid: str, warmup: float = 5.0) -> pd.DataFrame:
    return pd.DataFrame({
        "experiment.id": [eid],
        "experiment.comparison_group_id": ["formal-axis1-0.6b-4bit-qlora"],
        "training.seed": [42],
        "status.terminal_state": ["success"],
        "runtime.excluded_warmup_steps": [warmup],
        "_tier": ["A"],
    })


def test_per_run_stats_warmup_and_percentiles():
    eid = "runA"
    # 20 步：1..5 为 warmup（应排除），其余 15 步全为 2.0s（除最后一步 4.0）
    times = [9.0] * 5 + [2.0] * 14 + [4.0]
    stats = sd.per_run_stats(_step_df(eid, times), _runs_frame(eid))
    assert len(stats) == 1
    s = stats[0]
    assert s["n_steps"] == 15
    assert s["p50_s"] == pytest.approx(2.0)
    assert s["p99_s"] > 2.0  # 4.0 的尾被 p99 捕获
    assert s["drift_second_first"] == pytest.approx(1.0)  # 后半含 4.0
    assert s["cv"] > 0


def test_per_run_stats_skips_short_runs():
    eid = "runB"
    stats = sd.per_run_stats(_step_df(eid, [1.0] * 8), _runs_frame(eid))
    assert stats == []  # warmup 5 排除后仅 3 步 < 10


def test_per_group_aggregation():
    rows = [
        {"group": "g", "tier": "A", "p50_s": 1.0, "p90_s": 1.2, "p99_s": 1.4,
         "cv": 0.1, "p99_over_p50": 1.4, "drift_second_first": 1.0},
        {"group": "g", "tier": "A", "p50_s": 3.0, "p90_s": 3.2, "p99_s": 3.4,
         "cv": 0.3, "p99_over_p50": 1.1, "drift_second_first": 0.9},
    ]
    g = sd.per_group(rows)
    assert g["g"]["n_runs"] == 2
    assert g["g"]["p50_s"]["mean"] == pytest.approx(2.0)
    assert g["g"]["tiers"] == ["A"]


# ---------------------------------------------------------------- A2
def test_parse_stdout_steps(tmp_path):
    log = tmp_path / "logs" / "stdout.log"
    log.parent.mkdir()
    log.write_text(
        "loading model...\n"
        "step 1/100 loss=1.65 tokens=511 step_time=102.904s\n"
        "noise line\n"
        "step 2/100 loss=1.17 tokens=340 step_time=17.564s\n")
    steps = ss.parse_stdout_steps(tmp_path)
    assert [s["step"] for s in steps] == [1, 2]
    assert steps[0]["step_time_s"] == pytest.approx(102.904)
    assert steps[1]["tokens"] == 340


def test_load_monitor_and_summary(tmp_path):
    # 20 个样本，1s 节拍，swap 2.0→6.0 GiB 锯齿后回落
    lines = []
    for i in range(20):
        sw = 2.0 + 4.0 * (i / 19) if i < 15 else 3.0
        lines.append(json.dumps({
            "t_utc": f"2026-09-15T18:40:{i:02d}.000000Z",
            "swap_used_bytes": int(sw * 2**30)}))
    (tmp_path / "system_monitor.jsonl").write_text("\n".join(lines))
    mon = ss.load_monitor(tmp_path)
    assert mon is not None and mon["n"] == 20
    assert mon["cadence_median_s"] == pytest.approx(1.0, rel=0.02)
    s = ss.run_traj_summary(mon)
    assert s["swap_start_gib"] == pytest.approx(2.0, abs=0.01)
    assert s["swap_max_gib"] == pytest.approx(2.0 + 4.0 * 14 / 19, abs=0.02)
    assert s["swap_end_gib"] == pytest.approx(3.0, abs=0.01)
    assert s["swap_delta_gib"] == pytest.approx(1.0, abs=0.02)


def test_align_steps_interpolates_and_correlates(tmp_path):
    # monitor：0-30s，swap 0→3 GiB 线性；步时与 swap 完全单调 → rho=1
    lines = []
    for i in range(31):
        lines.append(json.dumps({
            "t_utc": f"2026-09-11T00:00:{i:02d}.000000Z",
            "swap_used_bytes": int((i / 10.0) * 2**30)}))
    (tmp_path / "system_monitor.jsonl").write_text("\n".join(lines))
    mon = ss.load_monitor(tmp_path)
    eid = "runC"
    times = [1.0 + 0.1 * i for i in range(15)]
    df = pd.DataFrame({
        "step": range(6, 21),
        "loss": [1.0] * 15,
        "loss_bearing_tokens": [10] * 15,
        "step_time_seconds": times,
        "wall_utc": [f"2026-09-11T00:00:{5 + i:02d}Z" for i in range(15)],
        "experiment_id": [eid] * 15,
        "_raw_dir": [eid] * 15,
    })
    runs = pd.DataFrame({
        "experiment.id": [eid],
        "experiment.comparison_group_id": ["formal-axis1-0.6b-4bit-qlora"],
        "training.seed": [42],
        "status.terminal_state": ["success"],
        "runtime.excluded_warmup_steps": [5],
        "_tier": ["B"],
    })
    out = ss.align_steps(df, runs, {eid: mon})
    assert len(out) == 1
    a = out[0]
    assert a["n_steps"] == 15
    assert a["spearman_rho"] == pytest.approx(1.0)
    assert a["concurrent_swap_mean_gib"] > 0


# ---------------------------------------------------------------- A3
def test_parse_manifest(tmp_path):
    models = tmp_path / "models"
    models.mkdir()
    (models / "MANIFEST.md").write_text(
        "# Model Manifest\n\n"
        "| Local directory | HF repository | Revision | safetensors on disk | Files |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| `models/Qwen3-0.6B` | `Qwen/Qwen3-0.6B` | `c1899de` | 1.503 GB | 10 |\n"
        "| `models/Qwen3-0.6B-4bit` | `mlx-community/Qwen3-0.6B-4bit` | `73e3e3` | 0.335 GB | 11 |\n")
    got = md.parse_manifest(models / "MANIFEST.md")
    assert got["Qwen3-0.6B"] == pytest.approx(1.503e9)
    assert got["Qwen3-0.6B-4bit"] == pytest.approx(0.335e9)


def test_decomposition_arithmetic():
    # 账目恒等式：accounted = weights + adapter + grads + 2×grads；残差可负
    weights_b = 0.335e9
    trainable = 2_293_760  # 0.6B r8 适配器参数
    adapter_b = trainable * 4
    grads_b = trainable * 4
    opt_b = 2 * grads_b
    accounted = (weights_b + adapter_b + grads_b + opt_b) / 2**30
    measured = 2.13
    unaccounted = measured - accounted
    assert accounted == pytest.approx((0.335e9 + 4 * 4 * trainable) / 2**30)
    assert unaccounted > 1.0  # 0.6B-4bit 残差量级 ~1.7-1.8 GiB
