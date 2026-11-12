"""Exploratory, deterministic statistics computed only from saved trial records.

Bootstrap intervals describe uncertainty of the empirical sample mean; very
small trial counts give unstable intervals.  Exact sign tests use shared seed
labels as blocks, not identical random starting populations. No optimization
is ever re-run in this module.
"""
from __future__ import annotations
from hashlib import sha256
from itertools import combinations
from math import comb, log10
from random import Random
from statistics import mean, median


def bootstrap_mean_interval(values: list[float], key: str, samples: int = 4096) -> tuple[float, float]:
    """Deterministic 95% percentile bootstrap CI of a finite sample's mean."""
    if len(values) < 2:
        raise ValueError('Bootstrap requires at least two independent trials')
    if any(not (float('-inf') < v < float('inf')) for v in values):
        raise ValueError('Bootstrap values must be finite')
    rng = Random(int.from_bytes(sha256(key.encode('utf-8')).digest()[:8], 'big'))
    n = len(values)
    estimates = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(samples))
    return estimates[int(.025 * (samples-1))], estimates[int(.975 * (samples-1))]


def exact_sign_p(wins: int, losses: int) -> float:
    """Two-sided exact binomial sign test; ties excluded."""
    n = wins + losses
    if not n:
        return 1.0
    tail = sum(comb(n, k) for k in range(min(wins, losses)+1))
    return min(1.0, 2 * tail / (2 ** n))


def holm_adjust(p_values: list[float]) -> list[float]:
    """Monotone Holm step-down FWER adjustment."""
    results = [1.0] * len(p_values)
    running = 0.0
    for rank, index in enumerate(sorted(range(len(p_values)), key=lambda i:p_values[i])):
        running = max(running, min(1.0, (len(p_values)-rank) * p_values[index]))
        results[index] = running
    return results


def paired_seed_statistics(groups: list[tuple[str, dict[int, float]]]) -> list[dict[str, float|int|str]]:
    raw = []
    for (name_a, a), (name_b, b) in combinations(groups, 2):
        seeds = sorted(a.keys() & b.keys())
        if not seeds:
            continue
        pairs = [(a[s], b[s]) for s in seeds]
        wins = sum(1 for left,right in pairs if left < right)
        losses = sum(1 for left,right in pairs if left > right)
        # Use a floor for log(0) only; wins and exact ties use raw objective values.
        effect = median(log10(max(left,1e-100))-log10(max(right,1e-100)) for left,right in pairs)
        raw.append(dict(pair=f'{name_a} / {name_b}', n=len(seeds), a_wins=wins,
                        b_wins=losses, ties=len(seeds)-wins-losses,
                        median_log10_ratio=effect, p_raw=exact_sign_p(wins,losses)))
    adjusted = holm_adjust([float(item['p_raw']) for item in raw])
    for item, p in zip(raw,adjusted):
        item['p_holm'] = p
    return raw
