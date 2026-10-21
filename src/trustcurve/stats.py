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
    groups = [[float(x) for x in v] for v in clusters.values() if len(v)]  # float: numpy ints break statistics.mean
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


def wilson_upper_one_sided(x: int, n: int) -> float:
    return wilson(x, n, Z90)[1]


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


def icc_bootstrap(clusters: dict[str, list[int]], B: int = 5000, seed: int = 1) -> tuple[float, float, float]:
    """Cluster-preserving bootstrap of the ANOVA ICC: (median, 2.5%, 97.5%). Resamples whole tasks."""
    rng = random.Random(seed); keys = list(clusters); vals = []
    for _ in range(B):
        sample = {f"{i}": clusters[rng.choice(keys)] for i in range(len(keys))}
        v = icc_binary(sample)
        if v == v:  # drop NaN (degenerate resamples)
            vals.append(v)
    vals.sort()
    if not vals:
        return (float("nan"),) * 3
    return (vals[len(vals) // 2], vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1])


def zero_event_upper(n: float, conf: float = 0.95) -> float:
    """One-sided upper bound on a rate after 0 events in n (independent) trials."""
    return 1 - (1 - conf) ** (1 / n)


def weighted_cluster_size(sizes: list[int]) -> float:
    """m_w = sum(m^2)/sum(m): the cluster size that enters the design effect with unequal clusters."""
    return sum(m * m for m in sizes) / sum(sizes)
