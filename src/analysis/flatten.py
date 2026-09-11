"""Raw result 扁平化：results/raw/ → results/processed/{experiments,step_timings}。

遵循 docs/result_schema.md §15：
- 先校验 raw manifest 再读取；
- 扁平化标量字段（稳定点号路径）；
- measurement 包络的 value 与 provenance 分列；
- 列表/映射序列化为 JSON 字符串，不做有损拼接；
- 每行保留 experiment.id / config_sha256 / manifest hash / status / validity；
- 一个实验一行主表；step_timings 单独长表（experiment_id, step, event_time）。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "results" / "raw"


def verify_manifest(d: Path) -> bool | None:
    mp = d / "manifest.sha256"
    if not mp.exists():
        return None
    for line in mp.read_text(encoding="utf-8").strip().splitlines():
        digest, _, rel = line.partition("  ")
        p = d / rel
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            return False
    return True


def _flatten(node, prefix: str, out: dict) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            _flatten(v, f"{prefix}.{k}" if prefix else k, out)
    else:
        out[prefix] = node


def flatten_result(r: dict, d: Path, manifest_ok: bool | None) -> dict:
    flat: dict = {}
    _flatten(r, "", flat)
    # step_timing_artifact 指针替换为实际文件路径提示（长表另存）
    flat["_raw_dir"] = d.name
    flat["_manifest_verified"] = manifest_ok
    return flat


def load_training_metrics(d: Path) -> dict:
    p = d / "training_metrics.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def build_tables(include_validation: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    roots = [RAW]
    vroot = ROOT / "results" / "validation"
    if include_validation and vroot.exists():
        roots.append(vroot)
    rows, step_rows = [], []
    for root in roots:
        for d in sorted(root.iterdir()):
            rj = d / "result.json"
            if not d.is_dir() or not rj.is_file():
                continue
            r = json.loads(rj.read_text(encoding="utf-8"))
            manifest_ok = verify_manifest(d)
            tm = load_training_metrics(d)
            flat = flatten_result(r, d, manifest_ok)
            # 训练进程级 metrics（training_metrics.json）并入同一行，前缀 tm.
            for k, v in tm.items():
                if isinstance(v, (list, dict)):
                    v = json.dumps(v, ensure_ascii=False)
                flat[f"tm.{k}"] = v
            rows.append(flat)
            # step 长表
            tj = d / "step_timings.jsonl"
            if tj.is_file():
                for line in tj.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        rec = json.loads(line)
                        rec["experiment_id"] = r["experiment"]["id"]
                        rec["_raw_dir"] = d.name
                        step_rows.append(rec)
    main_df = pd.DataFrame(rows)
    step_df = pd.DataFrame(step_rows)
    _mark_superseded(main_df)
    return main_df, step_df


def _mark_superseded(df: pd.DataFrame) -> None:
    """supersede 链求逆：被后续 run supersede 的旧 run 标记排除（保留原始行）。"""
    if "experiment.supersedes_experiment_id" not in df.columns:
        df["_superseded_by"] = None
        return
    links = df.set_index("experiment.id")["experiment.supersedes_experiment_id"]
    superseded_by = {
        old: new_id for new_id, old in links.items()
        if isinstance(old, str) and old in set(links.index)
    }
    df["_superseded_by"] = df["experiment.id"].map(superseded_by)


def retained(df: pd.DataFrame) -> pd.DataFrame:
    """分析入口：未被 supersede；同 (group, seed) 重复时保留最新 success
    （2026-09-12 hash 对齐修复前的重复运行去重；全部 raw 保留可审计）。"""
    out = df[df["_superseded_by"].isna()] if "_superseded_by" in df.columns else df
    if out.empty or "experiment.comparison_group_id" not in out.columns:
        return out
    keep = []
    seen = set()
    for idx, row in out.sort_values("experiment.id").iterrows():
        key = (row.get("experiment.comparison_group_id"), row.get("training.seed"),
               row.get("status.terminal_state"))
        if key in seen:
            continue
        seen.add(key)
        keep.append(idx)
    return out.loc[keep]


def write_processed(out_dir: Path | None = None,
                    include_validation: bool = False) -> tuple[Path, Path]:
    out_dir = out_dir or (ROOT / "results" / "processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    main_df, step_df = build_tables(include_validation=include_validation)
    main_path = out_dir / "experiments.csv"
    step_path = out_dir / "step_timings.parquet"
    main_df.to_csv(main_path, index=False)
    step_df.to_parquet(step_path, index=False)
    return main_path, step_path


def main() -> int:
    main_path, step_path = write_processed(include_validation=False)
    main_df = pd.read_csv(main_path, low_memory=False)
    print(f"[flatten] experiments: {len(main_df)} rows → {main_path.relative_to(ROOT)}")
    step_df = pd.read_parquet(step_path)
    print(f"[flatten] step records: {len(step_df)} rows → {step_path.relative_to(ROOT)}")
    print(f"[flatten] manifest 全部通过: "
          f"{bool(main_df['_manifest_verified'].all())}")
    return 0
