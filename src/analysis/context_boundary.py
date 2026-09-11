"""Context 边界探针系列汇总：从 raw results 聚合 ctx-scaling probe 证据。

规则：
- 只读取 results/raw/，不改写任何 raw 内容；
- 只报告真实观测值；null → null，不补估算；
- SIGKILL/失败保持原分类，绝不自动改写为 OOM；
- pre-run swap 等系统状态差异记录为 confounder；
- 措辞为 preliminary probe observation，不做统计显著声明。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "results" / "raw"

# probe 系列的 comparison group 前缀（prompt14 ctx 边界系列）
GROUP_PREFIX = "probe-4b-4bit-ctx"


def _swap_after_bytes(d: Path) -> int | None:
    env_txt = d / "environment" / "raw_environment.txt"
    if not env_txt.is_file():
        return None
    matches = re.findall(r"used\s*=\s*([\d.]+)M",
                         env_txt.read_text(encoding="utf-8"))
    return int(round(float(matches[1]) * 1024 * 1024)) if len(matches) >= 2 else None


def _load_metrics(d: Path) -> dict:
    try:
        return json.loads((d / "training_metrics.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def collect_series() -> list[dict]:
    """返回按 sequence_length 升序的 ctx 探针观测列表。"""
    entries: dict[int, dict] = {}
    for d in sorted(RAW.iterdir()):
        rj = d / "result.json"
        if not rj.is_file():
            continue
        r = json.loads(rj.read_text(encoding="utf-8"))
        group = r["experiment"].get("comparison_group_id") or ""
        if not group.startswith(GROUP_PREFIX):
            continue
        rt, st, tr = r["runtime"], r["status"], r["training"]
        ctx = tr["sequence_length"]
        tm = _load_metrics(d)
        obs = {
            "experiment_id": r["experiment"]["id"],
            "comparison_group_id": group,
            "sequence_length": ctx,
            "dataset_name": r["dataset"]["name"],
            "terminal_state": st["terminal_state"],
            "signal": st["signal"],
            "exit_code": st["exit_code"],
            "completed_steps": rt["successful_steps"],
            "requested_steps": tr["requested_steps"],
            "wall_clock_seconds": rt["wall_clock_seconds"],
            "average_step_time_seconds": rt["average_step_time_seconds"],
            "median_step_time_seconds": rt["median_step_time_seconds"],
            "tokens_per_second": rt["tokens_per_second"],
            "peak_metal_gpu_memory_bytes": tm.get("peak_metal_gpu_memory_bytes"),
            "initial_swap_bytes": (rt["initial_swap_bytes"] or {}).get("value"),
            "swap_after_bytes": _swap_after_bytes(d),
            "model_id": r["model"]["id"],
            "model_resolved_revision": r["model"].get("resolved_revision"),
            "git_commit_sha": r["software"].get("git_commit_sha"),
            "raw_result_path": f"results/raw/{d.name}",
        }
        prev = entries.get(ctx)
        # 同一 ctx 多次运行：保留目录名排序最后（=最新）的一次，并记录重复
        if prev is None:
            entries[ctx] = obs
        else:
            prev.setdefault("superseded_run_ids", []).append(prev["experiment_id"])
            entries[ctx] = obs
    return [entries[ctx] for ctx in sorted(entries)]


def build(series: list[dict] | None = None) -> dict:
    series = collect_series() if series is None else series

    # 边界区间：最后一个 success 与其后第一个非 success 之间（仅当可比时才推断）
    boundary = {"trainable_upper_bound_ctx": None,
                "first_failure_ctx": None,
                "inference_valid": False,
                "statement": None}
    last_success = None
    for obs in series:
        if obs["terminal_state"] == "success":
            last_success = obs
        elif last_success is not None and boundary["first_failure_ctx"] is None:
            boundary["first_failure_ctx"] = obs["sequence_length"]
            boundary["trainable_upper_bound_ctx"] = last_success["sequence_length"]
            boundary["inference_valid"] = True

    confounders = []
    for obs in series:
        before, after = obs["initial_swap_bytes"], obs["swap_after_bytes"]
        if before is not None and after is not None and after > before:
            confounders.append({
                "experiment_id": obs["experiment_id"],
                "kind": "system_swap_delta",
                "swap_before_bytes": before,
                "swap_after_bytes": after,
                "note": "系统级 swap 为全体进程共享；Δ为观测值，不能归因到单一进程",
            })
        if obs["model_resolved_revision"] is None:
            confounders.append({
                "experiment_id": obs["experiment_id"],
                "kind": "model_resolved_revision_unresolved",
                "note": "训练进程未写出 metrics → resolved_revision 为 null；"
                        "模型身份由 config.yaml 锚定",
            })

    return {
        "kind": "context-boundary-probe-summary",
        "epistemic_status": "preliminary probe observation（单次 20-step probe 系列，"
                            "非 formal benchmark，非统计显著结论）",
        "series": series,
        "boundary_interval": boundary,
        "confounders": confounders,
        "notes": [
            "success 的步时含 MLX 统一内存换页效应；peak_metal_gpu_memory_bytes 为 "
            "MLX 分配器口径（可超过物理 RAM，超过即依赖系统换页），非进程 RSS",
            "SIGKILL 不自动归类为 OOM：只有显式 OOM 证据才允许 terminal_state=oom",
            "本文件由 src/analysis/context_boundary.py 从 raw results 派生，可重新生成",
        ],
    }


def main(argv: list[str]) -> int:
    out = Path(argv[0]) if argv else (
        ROOT / "results" / "processed" / "context_boundary_probe_summary.json")
    summary = build()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    b = summary["boundary_interval"]
    print(f"[ctx-boundary] n={len(summary['series'])} "
          f"boundary={'ctx<=%s trainable, first failure ctx=%s' % (
              b['trainable_upper_bound_ctx'], b['first_failure_ctx'])
              if b['inference_valid'] else '尚无可推断区间'} → {out}")
    return 0
