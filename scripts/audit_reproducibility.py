#!/usr/bin/env python3
"""Reproducibility audit（Phase 12）。

检查项（全部独立重算，不信任 processed 产物）：
1. results/raw 全部 manifest 校验；
2. formal 矩阵每个 (group, seed) 恰有一个 retained success（去重/supersede 报告）；
3. data/formal_sft_v1/SHA256SUMS 与文件一致；
4. models/MANIFEST.md 中 revision 与 formal raw result 的 resolved_revision 一致；
5. 关键数字抽查：key_numbers.json 的 scale_axis 值与从 raw 直接重算值一致。
输出 research/reproducibility_audit.json + 终端摘要。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from analysis.flatten import build_tables, retained  # noqa: E402
from analysis.stats import mean_sd_ci  # noqa: E402

CHECKS: list[dict] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append({"check": name, "ok": bool(ok), "detail": detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def main() -> int:
    main_df, _ = build_tables(include_validation=False)
    raw_df = main_df[main_df["_raw_dir"].notna()]

    # 1. manifests
    all_ok = bool(raw_df["_manifest_verified"].all())
    check("raw_manifests_verified", all_ok, f"n={len(raw_df)}")

    # 2. formal group completeness (retained successes only)
    formal = raw_df[raw_df["experiment.comparison_group_id"]
                    .astype(str).str.startswith("formal-")]
    kept = retained(formal)
    ok = kept[kept["status.terminal_state"] == "success"]
    counts = ok.groupby("experiment.comparison_group_id").size()
    bad = counts[counts != 3]
    check("formal_groups_have_3_seeds", bad.empty,
          f"n_groups={len(counts)}; bad={dict(bad) if not bad.empty else {}}")

    # 3. dataset hashes
    sums = (ROOT / "data" / "formal_sft_v1" / "SHA256SUMS").read_text().strip().splitlines()
    ds_ok = True
    for line in sums:
        digest, _, rel = line.partition("  ")
        p = ROOT / "data" / "formal_sft_v1" / rel
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            ds_ok = False
    check("formal_dataset_sha256", ds_ok, f"n_files={len(sums)}")

    # 4. model revisions: MANIFEST vs raw resolved_revision
    manifest_text = (ROOT / "models" / "MANIFEST.md").read_text()
    revs = {"Qwen/Qwen3-0.6B": "c1899de289a0", "Qwen/Qwen3-1.7B": "70d244cc86cc",
            "Qwen/Qwen3-4B": "1cfa9a720891", "mlx-community/Qwen3-0.6B-4bit": "73e3e38d9813",
            "mlx-community/Qwen3-1.7B-4bit": "3b1b1768f8f8",
            "mlx-community/Qwen3-4B-4bit": "4dcb3d101c2a",
            "mlx-community/Qwen3-8B-4bit": "545dc4251c05",
            "mlx-community/Qwen3-14B-4bit": "a4d9b2df59d2",
            "Qwen/Qwen3-8B": "b968826d9c46"}
    mismatch = []
    for _, r in kept.iterrows():
        mid, rev = r["model.id"], r["model.resolved_revision"]
        if isinstance(rev, str) and mid in revs:
            if not rev.startswith(revs[mid]):
                mismatch.append((mid, rev))
        elif mid in revs and revs[mid] not in manifest_text:
            mismatch.append((mid, "not in MANIFEST"))
    check("model_revisions_consistent", not mismatch, str(mismatch[:3]))

    # 5. key numbers spot check (recompute from raw independently)
    kn_path = ROOT / "results" / "processed" / "key_numbers.json"
    if kn_path.exists():
        kn = json.loads(kn_path.read_text())
        spot_ok = True
        detail = ""
        for g, entry in kn.get("scale_axis", {}).items():
            sub = ok[ok["experiment.comparison_group_id"] == g]
            if sub.empty:
                spot_ok, detail = False, f"{g} missing"
                break
            a = mean_sd_ci([float(v) for v in sub["tm.median_step_time_seconds"]])
            if a is None or abs(a["mean"] - entry["median_step_s"]["mean"]) > 1e-9:
                spot_ok, detail = False, f"{g} median mismatch"
                break
        check("key_numbers_traceable", spot_ok, detail)
    else:
        check("key_numbers_traceable", False, "key_numbers.json missing")

    out = ROOT / "research" / "reproducibility_audit.json"
    out.write_text(json.dumps({
        "kind": "reproducibility-audit",
        "n_checks": len(CHECKS),
        "all_passed": all(c["ok"] for c in CHECKS),
        "checks": CHECKS,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[audit] → {out.relative_to(ROOT)}")
    return 0 if all(c["ok"] for c in CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
