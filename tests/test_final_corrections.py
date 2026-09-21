"""End-to-end invariants for evidence-preserving final corrections."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "results" / "processed"


def test_context_actual_lengths_are_raw_traceable() -> None:
    payload = json.loads((PROC / "context_actual_lengths.json").read_text())
    cells = {row["maximum_sequence_length_cap"]: row for row in payload["cells"]}
    assert set(cells) == {512, 1024, 2048}
    assert cells[512]["n_steps"] == 300
    assert cells[1024]["n_steps"] == cells[2048]["n_steps"] == 60
    assert cells[512]["mean_input_tokens"] == pytest.approx(500.1)
    assert cells[1024]["mean_input_tokens"] == pytest.approx(916.05)
    assert cells[2048]["mean_input_tokens"] == pytest.approx(1215.1)
    assert cells[2048]["fraction_hitting_cap"] == pytest.approx(0.05)


def test_scaling_fit_is_identical_for_all_consumers() -> None:
    key = json.loads((PROC / "key_numbers.json").read_text())["fits"]
    memory = json.loads((PROC / "memory_scaling_fits.json").read_text())
    timing = json.loads((PROC / "step_time_scaling_fits.json").read_text())
    assert key["bf16_lora"]["memory"] == memory["BF16 LoRA"]
    assert key["4bit_qlora"]["memory"] == memory["4bit QLoRA"]
    assert key["bf16_lora"]["step_time"] == timing["BF16 LoRA"]
    assert key["4bit_qlora"]["step_time"] == timing["4bit QLoRA"]


def test_batch8_figure_source_contains_three_trajectories_and_true_max() -> None:
    summary = json.loads((PROC / "figure8c_batch8_source.json").read_text())
    source = pd.read_csv(PROC / "figure8c_batch8_source.csv")
    assert summary["n_trajectories"] == 3
    assert source["experiment_id"].nunique() == 3
    assert source["swap_gib"].max() == pytest.approx(
        summary["plotted_swap_gib_max"])
    assert summary["plotted_swap_gib_max"] == pytest.approx(
        summary["swap_peak_gib_max"])


def test_final_validity_and_git_provenance_cover_aggregation() -> None:
    validity = pd.read_csv(PROC / "final_validity_audit.csv")
    provenance = pd.read_csv(PROC / "git_provenance_audit.csv")
    assert len(validity) == 118
    assert int(validity["included_in_aggregation"].sum()) == 46
    assert len(provenance) == 46
    assert set(provenance["category"]) <= {
        "clean", "dirty_nonexecution_artifact_only", "dirty_dependency_files",
        "dirty_source_code", "unknown"}
    assert provenance["category"].value_counts().to_dict() == {
        "dirty_dependency_files": 33,
        "clean": 9,
        "dirty_nonexecution_artifact_only": 3,
        "dirty_source_code": 1,
    }


def test_hypothesis_rules_are_side_by_side() -> None:
    payload = json.loads((PROC / "hypothesis_rule_comparison.json").read_text())
    assert {row["hypothesis"] for row in payload["rule_comparison"]} == {"H2", "H6"}
    for row in payload["rule_comparison"]:
        assert row["frozen_rule"] and row["posthoc_rule"]
        assert row["frozen_verdict"] and row["posthoc_verdict"]
    practical = payload["practical_comparison"]
    assert practical["frozen_practical"] == "Trainable AND P1 AND P2"
    assert practical["revised_operational_practical"] == "Trainable AND P2"

