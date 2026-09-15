"""Coverage report：raw ↔ processed 对账（每个 finalized run 的机器可读处置）。

背景（2026-09-15，D5 之后引入）：曾出现 raw 101 个而 experiments.csv 仅
36 行、其余去向不明的不可对账状态。本模块保证两条不变量：

1. count(finalized raw) == count(processed rows)：每个 finalized run
   恰好出现一行于 experiments.csv；
2. 每行带 aggregation disposition（included / excluded:<reason>），
   无未知去向。

disposition 规则（机械、可审计，按优先级）：
- ``excluded:implementation-invalid-d5``：error_message 含
  "Initialization encountered non-uniform length"（D5 trainer bug 签名，
  research/deviations.md D5）——不作为失败/边界证据聚合；
- ``excluded:superseded``：被后续 run 的 supersedes_experiment_id 标记；
- ``excluded:duplicate``：同 (group, seed, state) 已有更优 run
  （Tier-A 优先、最早；D2 dedup，与 flatten.retained 一致）；
- ``failed_retained_for_taxonomy``：非 success 终态，保留于 failure
  taxonomy，不进性能聚合；
- ``aggregation_included``：retained 且 success，进入性能统计聚合。
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .flatten import retained

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "results" / "processed"

D5_ERROR_SIGNATURE = "Initialization encountered non-uniform length"

SCHEMA_VERSION = "1.0.0"


def _kind(group: str) -> str:
    g = str(group)
    if g == "exp0-smoke":
        return "exp0-smoke"
    for prefix in ("formal", "probe", "calibration", "warmup"):
        if g.startswith(prefix + "-"):
            return prefix
    return "other"


def _generator_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT,
            capture_output=True, text=True, check=True
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return None


KNOWN_DISPOSITIONS = {
    "aggregation_included",
    "failed_retained_for_taxonomy",
    "excluded:superseded",
    "excluded:duplicate",
    "excluded:implementation-invalid-d5",
} | {f"non-formal:{k}" for k in
     ("probe", "calibration", "exp0-smoke", "warmup", "other")}


def disposition_for(row: pd.Series, retained_ids: set,
                    all_ids: pd.Series) -> str:
    """单行处置判定（优先级见模块 docstring）。"""
    err = str(row.get("status.error_message") or "")
    if D5_ERROR_SIGNATURE in err:
        return "excluded:implementation-invalid-d5"
    if pd.notna(row.get("_superseded_by")):
        return "excluded:superseded"
    group = str(row.get("experiment.comparison_group_id") or "")
    if not group.startswith("formal-"):
        # probe/calibration/exp0/warmup：按预注册 §5 不进入主统计聚合，
        # 但保留于 processed table（对账不变量不依赖聚合资格）
        return f"non-formal:{_kind(group)}"
    if row.get("experiment.id") not in retained_ids:
        # 未被 supersede 且有同 (group, seed, state) 更优保留 run → D2 重复
        return "excluded:duplicate"
    if row.get("status.terminal_state") != "success":
        return "failed_retained_for_taxonomy"
    return "aggregation_included"


def build_coverage(df: pd.DataFrame | None = None, *,
                   raw_root: Path | None = None,
                   val_root: Path | None = None) -> dict:
    if df is None:
        df = pd.read_csv(PROCESSED / "experiments.csv", low_memory=False)

    raw_root = raw_root or (ROOT / "results" / "raw")
    raw_dirs = [d for d in sorted(raw_root.iterdir())
                if d.is_dir() and (d / "result.json").is_file()]
    raw_total = len(raw_dirs)

    val_root = val_root if val_root is not None else (ROOT / "results" / "validation")
    validation_total = (sum(1 for d in val_root.iterdir()
                            if d.is_dir() and (d / "result.json").is_file())
                        if val_root.exists() else 0)

    # 与 summary.py 相同的 retained 视图（性能聚合入口）
    retained_ids: set = set()
    if "experiment.comparison_group_id" in df.columns:
        formal = df[df["experiment.comparison_group_id"].astype(str)
                    .str.startswith("formal-")]
        if not formal.empty:
            retained_ids = set(retained(formal)["experiment.id"])

    per_run: dict[str, dict] = {}
    dispositions: dict[str, int] = {}
    kinds: dict[str, int] = {}
    for _, row in df.iterrows():
        exp_id = row.get("experiment.id")
        kind = _kind(row.get("experiment.comparison_group_id"))
        disp = disposition_for(row, retained_ids, df["experiment.id"])
        per_run[exp_id] = {
            "kind": kind,
            "group": row.get("experiment.comparison_group_id"),
            "state": row.get("status.terminal_state"),
            "disposition": disp,
        }
        dispositions[disp] = dispositions.get(disp, 0) + 1
        kinds[kind] = kinds.get(kind, 0) + 1

    processed_total = len(df)
    ids_csv = set(df["experiment.id"])
    ids_raw = {d.name for d in raw_dirs}
    unknown_dispositions = set(dispositions) - KNOWN_DISPOSITIONS
    reconciliation_ok = (
        processed_total == raw_total
        and ids_csv == ids_raw
        and sum(dispositions.values()) == processed_total
        and not unknown_dispositions
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generator_commit": _generator_commit(),
        "raw_total": raw_total,
        "validation_total": validation_total,
        "processed_total": processed_total,
        "formal_total": kinds.get("formal", 0),
        "probe_total": kinds.get("probe", 0),
        "by_kind": dict(sorted(kinds.items())),
        "dispositions": dict(sorted(dispositions.items())),
        "exclusion_reasons": {
            "excluded:superseded": "superseded by later run (supersedes_experiment_id)",
            "excluded:duplicate": "same (group, seed, state) has a retained run "
                                  "(D2 dedup: Tier-A first, then earliest)",
            "excluded:implementation-invalid-d5": "D5 trainer bug signature in "
                                                  "error_message; not usable as "
                                                  "failure/boundary evidence",
        },
        "reconciliation_ok": reconciliation_ok,
        "per_run": per_run,
    }


def main() -> int:
    report = build_coverage()
    out = PROCESSED / "coverage_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"[coverage] raw={report['raw_total']} processed={report['processed_total']} "
          f"reconciliation_ok={report['reconciliation_ok']} → {out.relative_to(ROOT)}")
    for disp, n in report["dispositions"].items():
        print(f"    {n:4d}  {disp}")
    return 0 if report["reconciliation_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
