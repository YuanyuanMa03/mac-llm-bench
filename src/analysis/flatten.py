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
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "results" / "raw"

# 派生输出的路径脱敏（raw 不动）：本地仓库前缀与用户家目录替换为占位符，
# 使 processed CSV 可公开分发。仅作用于字符串字段，不触及任何数值。
_REPO_PREFIX = re.compile(re.escape(str(ROOT)))
_HOME_PREFIX = re.compile(r"<home>/\\\"']+")


def _sanitize(value):
    if isinstance(value, str):
        value = _REPO_PREFIX.sub("<repo>", value)
        value = _HOME_PREFIX.sub("<home>", value)
    elif isinstance(value, (list, tuple)):
        value = [_sanitize(v) for v in value]
    return value


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
        out[prefix] = _sanitize(node)


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


TIER_A_SWAPIN_MB_PER_STEP = 50.0  # deviations.md D4（预先冻结）


def _swapin_per_step(row) -> float:
    """vm_stat swap-in 增量 × 页大小 / 完成步数（MB/步）。

    兼容两种行形态：flatten 内部（JSON 字符串字段）与展平后的
    experiments.csv（嵌套字段展开为点分列名）。2026-09-16 修复：此前
    只读 JSON 字符串列，在展平 CSV 上 KeyError 静默返回 inf，导致
    全部 run 被判 Tier-B（round-1 review R1-W2 的根因）。
    """
    import json as _json
    b_col = "runtime.system_vm_counters_before"
    a_col = "runtime.system_vm_counters_after"
    try:
        if b_col in row.index and isinstance(row.get(b_col), str):
            b = _json.loads(row[b_col])
            a = _json.loads(row[a_col])
            b_swap = b["counters_pages"]["swapins"]
            a_swap = a["counters_pages"]["swapins"]
            page = b["page_size_bytes"]
        else:
            page = float(row[
                "runtime.system_vm_counters_before.value.page_size_bytes"])
            b_swap = float(row[
                "runtime.system_vm_counters_before.value.counters_pages.swapins"])
            a_swap = float(row[
                "runtime.system_vm_counters_after.value.counters_pages.swapins"])
        steps = float(row["runtime.successful_steps"] or 0)
        if not steps:
            return float("inf")
        return (a_swap - b_swap) * page / 2**20 / steps
    except (TypeError, KeyError, ValueError, _json.JSONDecodeError):
        return float("inf")


def _tier(row) -> str:
    return "A" if _swapin_per_step(row) < TIER_A_SWAPIN_MB_PER_STEP else "B"


def retained(df: pd.DataFrame) -> pd.DataFrame:
    """分析入口（deviations.md D2/D4 机械规则）：
    - 未被 supersede；
    - 同 (group, seed, state) 重复时：优先 Tier-A（paging 弱），并列取最早；
    - 全部原始行保留在 CSV 并带 _tier / _swapin_per_step 列。"""
    out = df[df["_superseded_by"].isna()] if "_superseded_by" in df.columns else df
    if out.empty or "experiment.comparison_group_id" not in out.columns:
        return out
    out = out.copy()
    out["_swapin_per_step"] = out.apply(_swapin_per_step, axis=1)
    out["_tier"] = out.apply(_tier, axis=1)
    keep = []
    seen = set()
    for idx, row in out.sort_values(["_tier", "experiment.id"]).iterrows():
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
