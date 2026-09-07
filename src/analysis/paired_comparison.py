"""配对探针对比：从两个 raw result 生成机器可读 comparison summary。

规则（prompt11）：只比较真实观测值；null → "unavailable"，不计算差值；
不修改 raw results；措辞为 preliminary observation。
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# 受控因子：除声明的变量（权重精度→模型仓库/路径/量化/方法）外必须一致
CONTROLLED_FACTORS = [
    ("dataset.name", lambda r: r["dataset"]["name"]),
    ("dataset.max_sequence_length", lambda r: r["dataset"]["max_sequence_length"]),
    ("training.micro_batch_size", lambda r: r["training"]["micro_batch_size"]),
    ("training.sequence_length", lambda r: r["training"]["sequence_length"]),
    ("training.lora_rank", lambda r: r["training"]["lora_rank"]),
    ("training.lora_alpha", lambda r: r["training"]["lora_alpha"]),
    ("training.seed", lambda r: r["training"]["seed"]),
    ("training.requested_steps", lambda r: r["training"]["requested_steps"]),
    ("training.learning_rate", lambda r: r["training"]["learning_rate"]),
    ("training.optimizer", lambda r: r["training"]["optimizer"]),
    ("training.target_modules", lambda r: r["training"]["target_modules"]),
]
DECLARED_VARIABLES = ["model.id", "model.repository", "model.resolved_revision",
                      "training.method", "training.quantization_bits"]


def latest_run(group_id: str) -> tuple[Path, dict]:
    runs = []
    for d in sorted((ROOT / "results" / "raw").iterdir()):
        result = json.loads((d / "result.json").read_text(encoding="utf-8"))
        if result["experiment"]["comparison_group_id"] == group_id:
            runs.append((d, result))
    if not runs:
        raise SystemExit(f"未找到分组：{group_id}")
    return runs[-1]


def _get(path: str, result: dict):
    node: object = result
    for part in path.split("."):
        node = node.get(part) if isinstance(node, dict) else None
    return node


def build(group_a: str, group_b: str) -> dict:
    da, ra = latest_run(group_a)
    db, rb = latest_run(group_b)

    factor_check = {}
    for name, fn in CONTROLLED_FACTORS:
        va, vb = fn(ra), fn(rb)
        factor_check[name] = {"a": va, "b": vb, "equal": va == vb}
    extra_ok = all(v["equal"] for v in factor_check.values())

    def obs(r: dict, mm: dict | None) -> dict:
        rt = r["runtime"]
        mm = mm or {}
        return {
            "terminal_state": r["status"]["terminal_state"],
            "exit_code": r["status"]["exit_code"],
            "completed_steps": rt["successful_steps"],
            "trainable": r["status"]["terminal_state"] == "success",
            "wall_clock_seconds": rt["wall_clock_seconds"],
            "median_step_time_seconds": rt["median_step_time_seconds"],
            "average_step_time_seconds": rt["average_step_time_seconds"],
            "tokens_per_second": rt["tokens_per_second"],
            "peak_metal_gpu_memory_bytes": mm.get("peak_metal_gpu_memory_bytes"),
            "initial_swap_bytes": rt["initial_swap_bytes"]["value"],
            "peak_process_memory_bytes": rt["peak_process_memory_bytes"]["value"],
            "model_load_seconds": rt["model_load_seconds"],
        }

    def load_mm(d: Path) -> dict | None:
        try:
            return json.loads((d / "training_metrics.json").read_text(encoding="utf-8"))
        except OSError:
            return None

    oa, ob = obs(ra, load_mm(da)), obs(rb, load_mm(db))

    diffs = {}
    for key in oa:
        if key in ("terminal_state", "exit_code", "trainable", "completed_steps"):
            continue
        va, vb = oa[key], ob[key]
        if va is None or vb is None:
            diffs[key] = "unavailable"
        elif isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            base = va if va else 1
            diffs[key] = {"a_minus_b": va - vb, "ratio_b_over_a": vb / va
                          if va not in (0, None) else "unavailable"}

    return {
        "kind": "paired-probe-comparison",
        "epistemic_status": "preliminary observation（单对 20-step probe，非统计显著结论）",
        "runs": {"a": {"id": ra["experiment"]["id"], "dir": da.name},
                 "b": {"id": rb["experiment"]["id"], "dir": db.name}},
        "controlled_factors": factor_check,
        "controlled_comparison_valid": extra_ok,
        "declared_variables": {p: {"a": _get(p, ra), "b": _get(p, rb)}
                               for p in DECLARED_VARIABLES},
        "observations": {"a": oa, "b": ob},
        "differences": diffs,
        "notes": [
            "peak_process_memory_bytes / thermal / energy / page faults 仍为 unresolved → unavailable",
            "口径：4bit 的 parameter_count 为打包存储元素口径，不参与比较",
            "本文件由 scripts/compare_probes.py 从 raw results 派生，可随时重新生成",
        ],
    }


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3):
        print("用法: compare_probes.py <group_a> <group_b> [输出路径]", file=__import__("sys").stderr)
        return 2
    summary = build(argv[0], argv[1])
    out = Path(argv[2]) if len(argv) == 3 else (
        ROOT / "results" / "processed" / "comparison_paired_probe.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"[compare] controlled_valid={summary['controlled_comparison_valid']} → {out}")
    return 0
