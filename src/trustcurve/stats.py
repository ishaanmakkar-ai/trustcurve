"""Small, dependency-free statistics for clustered binary outcomes and credibility sizing."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from statistics import mean

Z90, Z95 = 1.6449, 1.96


def wilson(x: int, n: int, z: float = Z95) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = x / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def icc_binary(clusters: dict[str, list[int]]) -> float:
    """One-way ANOVA ICC estimator (handles unequal cluster sizes via n0)."""
    groups = [v for v in clusters.values() if v]
    k = len(groups); N = sum(len(g) for g in groups)
    if k < 2 or N <= k:
        return float("nan")
    grand = sum(sum(g) for g in groups) / N
    ssb = sum(len(g) * (mean(g) - grand) ** 2 for g in groups)
    ssw = sum(sum((y - mean(g)) ** 2 for y in g) for g in groups)
    msb, msw = ssb / (k - 1), ssw / (N - k)
    n0 = (N - sum(len(g) ** 2 for g in groups) / N) / (k - 1)
    den = msb + (n0 - 1) * msw
    return float("nan") if den == 0 else (msb - msw) / den


def task_bootstrap(clusters: dict[str, list[float]], stat, B: int = 5000, seed: int = 1) -> tuple[float, float]:
    rng = random.Random(seed); keys = list(clusters)
    vals = []
    for _ in range(B):
        sample = [clusters[rng.choice(keys)] for _ in keys]
        flat = [y for g in sample for y in g]
        vals.append(stat(flat))
    vals.sort()
    return (vals[int(0.025 * B)], vals[int(0.975 * B) - 1])


def runs_needed(q: float, cv2: float, k: float = 0.05, z: float = Z90) -> float:
    """Binomial limited-fluctuation standard for pure premium, in runs (independent)."""
    if q <= 0:
        return float("inf")
    return (z / k) ** 2 * ((1 - q) + cv2) / q


def eff_ceiling(n_tasks: int, rho: float) -> float:
    return float("inf") if rho <= 0 else n_tasks / rho


def group(rows, key, val):
    d = defaultdict(list)
    for r in rows:
        d[str(r[key])].append(val(r))
    return d
