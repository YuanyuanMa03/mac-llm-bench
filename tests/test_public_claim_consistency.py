"""Lightweight invariants for the frozen public claim chain."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from analysis.coverage import build_coverage  # noqa: E402
from analysis.flatten import build_tables  # noqa: E402


def _ledger() -> dict[str, dict[str, str]]:
    with (ROOT / "research" / "claim_ledger.csv").open(newline="", encoding="utf-8") as f:
        return {row["claim_id"]: row for row in csv.DictReader(f)}


def test_frozen_public_counts_and_manifest_warnings() -> None:
    experiments, steps = build_tables(include_validation=False)
    coverage = build_coverage(experiments)
    assert len(experiments) == 118
    assert int((experiments["status.terminal_state"] != "success").sum()) == 27
    assert coverage["dispositions"]["aggregation_included"] == 46
    assert int((experiments["_manifest_verified"] != True).sum()) == 6  # noqa: E712
    assert len(steps) == 7180


def test_completed_8b_seed_set_and_valid_batch8_evidence() -> None:
    experiments, _ = build_tables(include_validation=False)
    completed_8b = experiments[
        (experiments["experiment.comparison_group_id"] == "formal-axis1-8b-4bit-qlora")
        & (experiments["status.terminal_state"] == "success")
    ]
    assert set(completed_8b["training.seed"].astype(int)) == {42, 123, 2026}

    coverage = build_coverage(experiments)
    invalid_d5 = {
        experiment_id
        for experiment_id, row in coverage["per_run"].items()
        if row["disposition"] == "excluded:implementation-invalid-d5"
    }
    ledger = _ledger()
    for claim_id in ("C9", "C19"):
        positive_ids = set(ledger[claim_id]["raw_source_ids"].split(";"))
        assert len(positive_ids) == 3
        assert all("20260915T" in experiment_id for experiment_id in positive_ids)
        assert positive_ids.isdisjoint(invalid_d5)


def test_14b_parser_and_monitor_coverage() -> None:
    progress = json.loads((ROOT / "results" / "processed" / "failure_progress.json").read_text())
    parsed_14b = [
        row for row in progress["runs"]
        if "14b-4bit" in row["experiment_id"] and row["parse_status"] == "parsed_steps"
    ]
    assert len(parsed_14b) == 1
    assert parsed_14b[0]["observed_completed_steps"] == 70
    assert parsed_14b[0]["last_observed_step"] == 70

    state = json.loads((ROOT / "results" / "processed" / "system_state.json").read_text())
    assert state["monitor_coverage"]["runs_parsed_ge10_samples"] == 95


def test_public_claim_sources_exist() -> None:
    for row in _ledger().values():
        for source in row["processed_source"].split(";"):
            path = source.split("#", 1)[0]
            assert (ROOT / path).exists(), (row["claim_id"], path)
        raw_ids = [item for item in row["raw_source_ids"].split(";") if item]
        assert raw_ids, row["claim_id"]
        for experiment_id in raw_ids:
            assert (ROOT / "results" / "raw" / experiment_id).is_dir(), (
                row["claim_id"], experiment_id
            )
