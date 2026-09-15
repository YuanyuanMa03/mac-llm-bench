"""统计聚合与 scaling 拟合（预注册 §9 分析计划）。

规则：
- formal 重复（3 seeds）报告全部点值 + mean ± SD + 95% CI（t 分布，n=3）；
- log-log 最小二乘拟合必须报告 slope / intercept / R² / n；n<3 不拟合；
- 不使用两点拟合宣称 scaling law。
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import stats as sps

try:
    from scipy import stats as sps
except ImportError:  # scipy 未安装时的最小回退（t 临界值表，df=2）
    sps = None

T_CRIT_DF2_975 = 4.302652729911275  # scipy 缺失时的固定 t 值（n=3）


def mean_sd_ci(values: list[float]) -> dict | None:
    vals = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    n = len(vals)
    if n == 0:
        return None
    mean = float(np.mean(vals))
    sd = float(np.std(vals, ddof=1)) if n > 1 else None
    ci = None
    if n > 1:
        t = float(sps.t.ppf(0.975, n - 1)) if sps is not None else T_CRIT_DF2_975
        ci = t * sd / math.sqrt(n)
    return {"n": n, "values": vals, "mean": mean, "sd": sd, "ci95": ci}


def loglog_fit(x: list[float], y: list[float]) -> dict | None:
    pts = [(a, b) for a, b in zip(x, y)
           if a is not None and b is not None and a > 0 and b > 0
           and not (isinstance(a, float) and math.isnan(a))
           and not (isinstance(b, float) and math.isnan(b))]
    if len(pts) < 3:
        return None
    lx = np.log10([p[0] for p in pts])
    ly = np.log10([p[1] for p in pts])
    slope, intercept, r, p, se = sps.linregress(lx, ly) if sps else (None,) * 5
    return {
        "n": len(pts), "slope": float(slope), "intercept": float(intercept),
        "r_squared": float(r ** 2), "p_value": float(p), "stderr_slope": float(se),
        "model_form": "log10(y) = slope*log10(x) + intercept",
    }


def paired_ratio(df: pd.DataFrame, group_a: str, group_b: str,
                 seed_col: str = "training.seed",
                 value_col: str = "tm.peak_metal_gpu_memory_bytes") -> list[dict]:
    """按 seed 配对取比值 b/a；仅使用双方都存在的 seed。

    每组每个 seed 只保留一行（value 非空的最早行）——同 seed 可能同时有
    success 与 interrupted 的重复行（如 4B-bf16 依 D1）。
    """
    def _one_row(group: str) -> pd.DataFrame:
        sub = df[df["experiment.comparison_group_id"] == group]
        sub = sub[sub[value_col].notna()]
        sub = sub.sort_values("experiment.id").drop_duplicates(subset=[seed_col])
        return sub.set_index(seed_col)

    a, b = _one_row(group_a), _one_row(group_b)
    out = []
    for seed in sorted(set(a.index) & set(b.index)):
        va, vb = a.loc[seed, value_col], b.loc[seed, value_col]
        if pd.notna(va) and pd.notna(vb) and va:
            out.append({"seed": int(seed), "a": float(va), "b": float(vb),
                        "ratio_b_over_a": float(vb) / float(va)})
    return out
