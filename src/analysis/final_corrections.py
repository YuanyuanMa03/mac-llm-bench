"""Historical semantic overlays required by the final evidence audit."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .coverage import build_coverage
from .flatten import retained

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "results" / "raw"
PROC = ROOT / "results" / "processed"
TABLES = ROOT / "paper" / "submission" / "tables"


def _load() -> tuple[pd.DataFrame, pd.DataFrame]:
    return (pd.read_csv(PROC / "experiments.csv", low_memory=False),
            pd.read_parquet(PROC / "step_timings.parquet"))


def data_order_audit(df: pd.DataFrame) -> dict:
    formal = df[df["experiment.comparison_group_id"].astype(str)
                .str.startswith("formal-")]
    rows = []
    for group, sub in formal.groupby("experiment.comparison_group_id"):
        requested = pd.to_numeric(sub["training.requested_steps"],
                                  errors="coerce").max()
        batch = pd.to_numeric(sub["training.micro_batch_size"],
                              errors="coerce").max()
        attempted = int(requested * batch) if pd.notna(requested * batch) else None
        rows.append({
            "comparison_group_id": group,
            "requested_steps": int(requested) if pd.notna(requested) else None,
            "micro_batch_size": int(batch) if pd.notna(batch) else None,
            "maximum_examples_consumed_per_run": attempted,
            "train_examples": 2048,
            "epoch_wrap_possible": bool(attempted is not None and attempted >= 2048),
            "historical_initial_order": "fixed source-file order",
        })
    return {
        "protocol": "historical protocol 0.1.0",
        "finding": ("shuffle was applied only after epoch wrap; no formal run "
                    "could traverse all 2,048 training examples"),
        "seed_effective_role": "MLX/LoRA initialization, not initial sample order",
        "groups": sorted(rows, key=lambda row: row["comparison_group_id"]),
    }


def context_lengths(df: pd.DataFrame, steps: pd.DataFrame) -> dict:
    formal = df[df["experiment.comparison_group_id"].astype(str)
                .str.startswith("formal-")]
    kept = retained(formal)
    kept = kept[kept["status.terminal_state"] == "success"]
    rows = []
    for cap, group in ((512, "formal-axis1-4b-4bit-qlora"),
                       (1024, "formal-axis2-ctx1024"),
                       (2048, "formal-axis2-ctx2048")):
        ids = set(kept.loc[kept["experiment.comparison_group_id"] == group,
                           "experiment.id"].astype(str))
        values = pd.to_numeric(
            steps.loc[steps["experiment_id"].astype(str).isin(ids),
                      "loss_bearing_tokens"], errors="coerce").dropna() + 1
        array = values.to_numpy(dtype=float)
        rows.append({
            "maximum_sequence_length_cap": cap,
            "comparison_group_id": group,
            "experiment_ids": sorted(ids),
            "n_steps": int(len(array)),
            "min_input_tokens": int(array.min()),
            "max_input_tokens": int(array.max()),
            "mean_input_tokens": float(array.mean()),
            "median_input_tokens": float(np.median(array)),
            "p10_input_tokens": float(np.percentile(array, 10)),
            "p90_input_tokens": float(np.percentile(array, 90)),
            "fraction_hitting_cap": float(np.mean(array == cap)),
        })
    return {
        "definition": "input tokens per step = loss_bearing_tokens + 1",
        "interpretation": "configured sequence length is a maximum cap, not fixed work",
        "cells": rows,
    }


def effective_runtime_overlay(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        command = str(row.get("experiment.exact_command_display") or "")
        trainer = "lora_smoke" in command
        rows.append({
            "experiment_id": row["experiment.id"],
            "optimizer_declared": row.get("training.optimizer"),
            "optimizer_effective": "mlx.optimizers.Adam" if trainer else "unknown",
            "shuffle_declared": row.get("dataset.shuffle"),
            "initial_shuffle_effective": False if trainer else None,
            "scheduler_declared": row.get("training.scheduler"),
            "scheduler_effective": "constant/no explicit scheduler" if trainer else "unknown",
            "gradient_accumulation_effective": 1 if trainer else None,
            "source_evidence": ("src/train/lora_smoke.py at historical run commit; "
                                "processed overlay, raw unchanged"),
        })
    return pd.DataFrame(rows)


def _git_status_text(raw_dir: str) -> str:
    path = RAW / raw_dir / "environment" / "raw_environment.txt"
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"## git status --porcelain=v1\n(.*?)(?=\n\n## )",
                      text, flags=re.DOTALL)
    return match.group(1).strip() if match else ""


def _provenance_category(row: pd.Series) -> tuple[str, str]:
    dirty = row.get("software.git_dirty")
    status = _git_status_text(str(row["_raw_dir"]))
    if dirty is False or str(dirty).lower() == "false":
        return "clean", status
    paths = []
    for line in status.splitlines():
        if line.strip():
            paths.append(line[3:].strip().split(" -> ")[-1])
    if not paths:
        return "unknown", status
    execution_prefixes = ("src/", "scripts/", "configs/", "pyproject.toml")
    if any(path.startswith(execution_prefixes) for path in paths):
        if all(path in {"uv.lock", "pyproject.toml"} for path in paths):
            return "dirty_dependency_files", status
        return "dirty_source_code", status
    if any(path == "uv.lock" for path in paths):
        return "dirty_dependency_files", status
    if all(path.startswith(("paper/", "research/", "reviews/", "PROMPT.md",
                            "README", ".agents/")) for path in paths):
        return "dirty_nonexecution_artifact_only", status
    return "unknown", status


def git_provenance_audit(df: pd.DataFrame) -> pd.DataFrame:
    coverage = build_coverage(df)
    rows = []
    for _, row in df.iterrows():
        exp_id = str(row["experiment.id"])
        disposition = coverage["per_run"][exp_id]["disposition"]
        if disposition != "aggregation_included":
            continue
        category, status = _provenance_category(row)
        rows.append({
            "experiment_id": exp_id,
            "comparison_group_id": row.get("experiment.comparison_group_id"),
            "git_commit": row.get("software.git_commit_sha"),
            "git_dirty": row.get("software.git_dirty"),
            "category": category,
            "git_status_paths": " | ".join(
                line[3:].strip() for line in status.splitlines() if line.strip()),
            "git_patch_preserved": bool(row.get("software.git_patch.sha256")),
        })
    return pd.DataFrame(rows)


def final_validity_audit(df: pd.DataFrame) -> pd.DataFrame:
    coverage = build_coverage(df)
    rows = []
    for _, row in df.iterrows():
        exp_id = str(row["experiment.id"])
        disposition = coverage["per_run"][exp_id]["disposition"]
        included = disposition == "aggregation_included"
        manifest = row.get("_manifest_verified")
        rows.append({
            "experiment_id": exp_id,
            "raw_protocol_valid": row.get("experiment.validity.protocol_valid"),
            "raw_performance_valid": row.get("experiment.validity.performance_valid"),
            "final_disposition": disposition,
            "included_in_aggregation": included,
            "evidence_grade": "aggregation" if included else "retained_context",
            "manifest_verified": manifest,
            "deviation_ids": "D6" if manifest is not True else "",
            "reason": ("raw validity flags are supervisor-v0 placeholders; "
                       "coverage disposition is authoritative"),
            "auditor_version": "final-validity-1.0.0",
        })
    return pd.DataFrame(rows)


def hypothesis_rule_comparison() -> dict:
    audit = json.loads((PROC / "hypothesis_audit.json").read_text())
    revised = audit["hypotheses"]
    rows = []
    for hid in ("H2", "H6"):
        post = revised[hid]
        if hid == "H2":
            frozen_rule = "14B 4-bit QLoRA completes all three formal seeds"
            frozen_verdict = "not_supported"
        else:
            frozen_rule = ("step-time amplification divided by token-count "
                           "amplification is at least 10")
            frozen_verdict = "not_supported"
        rows.append({
            "hypothesis": hid,
            "frozen_rule": frozen_rule,
            "frozen_verdict": frozen_verdict,
            "posthoc_rule": post["rule"],
            "posthoc_verdict": post["conclusion_status"],
            "reason_for_revision": post.get("rule_revision", "D9 post-result revision"),
            "revision_date": "2026-09-16",
        })
    return {
        "rule_comparison": rows,
        "practical_comparison": {
            "frozen_practical": "Trainable AND P1 AND P2",
            "revised_operational_practical": "Trainable AND P2",
            "status": "post-hoc sensitivity interpretation (D11)",
        },
    }


def _write_context_table(payload: dict) -> None:
    lines = [
        r"\begin{table}[t]\centering",
        r"\caption{Observed input lengths under each maximum sequence-length cap. Input tokens equal loss-bearing target tokens plus one. Values pool the three retained seeds.}",
        r"\label{tab:actual-context}",
        r"\footnotesize\setlength{\tabcolsep}{3pt}",
        r"\begin{tabular}{rrrrrr}", r"\toprule",
        r"Cap & $n$ & Min & Mean & Median & At cap\\", r"\midrule",
    ]
    for row in payload["cells"]:
        lines.append(
            f"{row['maximum_sequence_length_cap']} & {row['n_steps']} & "
            f"{row['min_input_tokens']} & {row['mean_input_tokens']:.1f} & "
            f"{row['median_input_tokens']:.0f} & "
            f"{100 * row['fraction_hitting_cap']:.0f}\\%\\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    TABLES.mkdir(parents=True, exist_ok=True)
    (TABLES / "table_context_actual_lengths.tex").write_text(
        "\n".join(lines), encoding="utf-8")


def main() -> int:
    df, steps = _load()
    outputs = {
        "data_order_audit.json": data_order_audit(df),
        "context_actual_lengths.json": context_lengths(df, steps),
    }
    for name, payload in outputs.items():
        (PROC / name).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
    _write_context_table(outputs["context_actual_lengths.json"])
    overlay = effective_runtime_overlay(df)
    overlay.to_csv(PROC / "effective_runtime_config.csv", index=False)
    (PROC / "effective_runtime_config.json").write_text(
        json.dumps(overlay.to_dict(orient="records"), indent=2,
                   ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    git_provenance_audit(df).to_csv(PROC / "git_provenance_audit.csv", index=False)
    final_validity_audit(df).to_csv(PROC / "final_validity_audit.csv", index=False)
    (PROC / "hypothesis_rule_comparison.json").write_text(
        json.dumps(hypothesis_rule_comparison(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print("[final-corrections] data order, context lengths, runtime, validity, "
          "git provenance, and hypothesis overlays generated")
    return 0

