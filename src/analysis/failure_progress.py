"""Parse partial progress for failed runs from immutable stdout only."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "results" / "raw"
PROCESSED = ROOT / "results" / "processed"
STEP_LINE = re.compile(
    r"^step\s+(\d+)/(\d+)\s+loss=([\d.eE+-]+)\s+tokens=(\d+)\s+"
    r"step_time=([\d.eE+-]+)s$")


def parse_stdout(path: Path) -> list[dict]:
    rows = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = STEP_LINE.match(line.strip())
        if match:
            rows.append({"step": int(match.group(1)),
                         "step_time_seconds": float(match.group(5))})
    return rows


def build() -> dict:
    entries = []
    for directory in sorted(RAW.iterdir()):
        result_path = directory / "result.json"
        if not result_path.is_file():
            continue
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result["status"]["terminal_state"] == "success":
            continue
        source = directory / "logs" / "stdout.log"
        steps = parse_stdout(source)
        times = [row["step_time_seconds"] for row in steps]
        entries.append({
            "experiment_id": result["experiment"]["id"],
            "terminal_state": result["status"]["terminal_state"],
            "observed_completed_steps": len(steps),
            "observed_step_time_min_seconds": min(times) if times else None,
            "observed_step_time_max_seconds": max(times) if times else None,
            "last_observed_step": steps[-1]["step"] if steps else None,
            "source_artifact": f"results/raw/{directory.name}/logs/stdout.log",
            "parse_status": "parsed_steps" if steps else "no_matching_step_lines",
        })
    return {
        "kind": "historical-failure-progress-overlay",
        "immutability_note": "derived from stdout; no result.json was modified",
        "runs": entries,
    }


def main() -> int:
    payload = build()
    path = PROCESSED / "failure_progress.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    parsed = sum(r["parse_status"] == "parsed_steps" for r in payload["runs"])
    print(f"[failure-progress] failed={len(payload['runs'])} parsed={parsed} → "
          f"{path.relative_to(ROOT)}")
    return 0

