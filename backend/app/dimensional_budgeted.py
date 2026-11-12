"""Exact-NFE true-D optimizers for ABC, CS, SMA, IWO and SA.

These are explicitly *budget-normalized variants*: each trial stops on exactly
N*(T+1) real objective calls and records checkpoints at N, 2N, ..., N*(T+1).
A checkpoint can interrupt an algorithmic phase; it is NOT an iteration of SA,
ABC, CS or IWO. Only accepted/current locations are represented as solutions,
while rejected/abandoned evaluations still contribute to NFE. No 2D surrogate.
"""
from __future__ import annotations

from math import floor
from time import perf_counter
import numpy as np

from .dimensional import (
    DimensionalRequest, DimensionalTrial, DimensionalPoint, objective_nd, _BOUNDS,
)
from .optimizers.cuckoo import _levy
from .optimizers.iwo import seed_counts


def _sma_generation(old: np.ndarray, fitness: np.ndarray, best_pos: np.ndarray,
                    global_best: float, rng: np.random.Generator, step: int,
                    iterations: int, restart_rate: float, low: float, high: float
                    ) -> np.ndarray:
    """Vector SMA food approach, contraction, random restart; frozen generation.

    Weight ranking uses current objective scores; p uses the archived best.
    Coordinate-wise vb/vc draws share one branch decision per agent. At T,
    vc=0 exactly (the characteristic collapse-to-origin property).
    """
    n, d = old.shape
    ranks = np.argsort(fitness, kind='stable')
    current_best = float(fitness[ranks[0]])
    current_worst = float(fitness[ranks[-1]])
    weights = np.ones(n)
    if current_worst > current_best:
        for rank, i in enumerate(ranks):
            ratio = (current_best - float(fitness[i])) / (current_best - current_worst)
            variation = float(rng.random()) * np.log1p(max(0., ratio))
            weights[i] = 1. + variation if rank < n/2 else 1. - variation
    a = np.arctanh(max(1e-12, 1 - step/iterations))
    b = 1 - step/iterations
    result = np.empty_like(old)
    for i in range(n):
        if float(rng.random()) < restart_rate:
            result[i] = rng.uniform(low, high, d)
        elif float(rng.random()) < np.tanh(abs(float(fitness[i]) - global_best)):
            peers = np.delete(np.arange(n), i)
            ia, ib = rng.choice(peers, size=2, replace=False)
            vb = rng.uniform(-a, a, d)
            result[i] = np.clip(best_pos + vb*(weights[i]*old[ia] - old[ib]), low, high)
        else:
            vc = rng.uniform(-b, b, d)
            result[i] = np.clip(vc*old[i], low, high)
    return result


def run_budgeted_nd(cfg: DimensionalRequest, algorithm: str, seed: int) -> DimensionalTrial:
    start = perf_counter()
    rng = np.random.default_rng(seed)
    n, d = cfg.population_size, cfg.dimensions
    low, high = _BOUNDS[cfg.objective]
    cap = n*(cfg.iterations+1)
    iterations = cfg.iterations
    evals = 0
    trajectory: list[DimensionalPoint] = []
    best = float('inf')
    best_pos: np.ndarray | None = None
    first_success: int | None = None

    def value(x: np.ndarray) -> float:
        nonlocal evals, best, best_pos, first_success
        f = float(objective_nd(cfg.objective, x)[0])
        evals += 1
        if f < best:
            best = f
            best_pos = x.copy()
        if first_success is None and best <= cfg.success_tolerance:
            first_success = evals
        return f

    def checkpoint():
        if evals % n == 0:
            assert best_pos is not None
            trajectory.append(DimensionalPoint(evaluations=evals,
                best_error=max(0.,best), best_position=best_pos.tolist()))

    if algorithm == 'sa':
        current = rng.uniform(low, high, d)
        current_f = value(current)
        while evals < cap:
            # Temperature horizon is Tref, not 2,184 artificial SA iterations.
            progress = (evals - 1)/max(1,cap - 1)
            temperature = cfg.sa_initial_temperature * cfg.sa_cooling_rate**(iterations*progress)
            candidate = np.clip(current + rng.normal(0,cfg.sa_step_scale*(high-low),d),low,high)
            f = value(candidate)
            delta = f - current_f
            probability = 1.0 if delta <= 0 else float(np.exp(-delta/max(temperature,1e-300)))
            if float(rng.random()) < probability:
                current, current_f = candidate, f
            checkpoint()
    else:
        pos = rng.uniform(low,high,(n,d))
        fitness = np.array([value(x) for x in pos],dtype=float)
        checkpoint()
        if algorithm == 'abc':
            trials = np.zeros(n,dtype=int)
        if algorithm == 'iwo':
            # Competitive selection: survivors stay bounded by max population.
            if cfg.iwo_max_population < n:
                raise ValueError('IWO maximum population must not be less than the initial count')
        generation = 0
        while evals < cap:
            generation += 1
            if algorithm == 'sma':
                assert best_pos is not None
                pos = _sma_generation(pos,fitness,best_pos,best,rng,
                     min(generation,iterations),iterations,cfg.sma_restart_probability,low,high)
                fitness = np.array([value(x) for x in pos],dtype=float)
                checkpoint()
            elif algorithm == 'abc':
                # Each employed bee generates one neighbour; then one onlooker
                # phase samples based on positive fitness. Scout consumes an
                # additional objective evaluation for every abandoned source.
                def propose(i: int):
                    nonlocal pos, fitness
                    other = int(rng.integers(n-1))
                    if other >= i:
                        other += 1
                    coordinate = int(rng.integers(d))
                    candidate = pos[i].copy()
                    candidate[coordinate] += float(rng.uniform(-1,1))*(pos[i,coordinate]-pos[other,coordinate])
                    candidate = np.clip(candidate,low,high)
                    f = value(candidate)
                    if f < fitness[i]:
                        pos[i],fitness[i],trials[i] = candidate,f,0
                    else:
                        trials[i] += 1
                    checkpoint()
                for i in range(n):
                    if evals == cap: break
                    propose(i)
                if evals == cap: break
                quality = 1/(1+np.maximum(fitness,0))
                probability = quality/float(quality.sum())
                for _ in range(n):
                    if evals == cap: break
                    propose(int(rng.choice(n,p=probability)))
                if evals == cap: break
                for i in range(n):
                    if evals == cap: break
                    if trials[i] >= cfg.abc_limit:
                        candidate = rng.uniform(low, high, d)
                        f = value(candidate)
                        pos[i],fitness[i],trials[i] = candidate,f,0
                        checkpoint()
            elif algorithm == 'cs':
                assert best_pos is not None
                abandoned = min(n-1,int(floor(cfg.cs_discovery_rate*n+.5)))
                for _ in range(n):
                    if evals == cap: break
                    source,host = int(rng.integers(n)),int(rng.integers(n))
                    step = _levy(rng,cfg.cs_levy_exponent,(d,))
                    direction = pos[source]-best_pos+.02*(high-low)*rng.standard_normal(d)
                    candidate = np.clip(pos[source]+cfg.cs_step_scale*step*direction,low,high)
                    f = value(candidate)
                    if f < fitness[host]:
                        pos[host],fitness[host] = candidate,f
                    checkpoint()
                if evals == cap: break
                elite = int(np.argmin(fitness))
                worst = [int(j) for j in np.argsort(fitness)[::-1] if j!=elite][:abandoned]
                for j in worst:
                    if evals == cap: break
                    candidate = rng.uniform(low,high,d)
                    f = value(candidate)
                    pos[j],fitness[j] = candidate,f
                    checkpoint()
            elif algorithm == 'iwo':
                parent_pos=pos.copy()
                counts = seed_counts(fitness,cfg.iwo_min_seeds,cfg.iwo_max_seeds)
                if not int(counts.sum()):
                    raise RuntimeError('IWO reproduction stalled: all seed counts are zero')
                for parent_index, count in enumerate(counts):
                    for _ in range(int(count)):
                        if evals == cap: break
                        # NFE-normalized rather than iteration-normalized sigma
                        progress = (evals-n)/max(1,cap-n)
                        sigma = cfg.iwo_sigma_final + (cfg.iwo_sigma_initial-cfg.iwo_sigma_final)*(1-progress)**cfg.iwo_modulation_index
                        candidate = np.clip(parent_pos[parent_index]+rng.normal(0,sigma,d),low,high)
                        f = value(candidate)
                        pos = np.vstack((pos,candidate))
                        fitness = np.concatenate((fitness,[f]))
                        if len(pos)>cfg.iwo_max_population:
                            keep = np.argsort(fitness,kind='stable')[:cfg.iwo_max_population]
                            pos,fitness = pos[keep].copy(),fitness[keep].copy()
                        checkpoint()
                    if evals == cap: break
            else:
                raise ValueError(f'Unknown budgeted algorithm: {algorithm}')

    assert evals == cap, (evals,cap)
    assert len(trajectory)==iterations+1, (len(trajectory),iterations)
    assert best_pos is not None
    return DimensionalTrial(seed=seed,best_error=max(0.,best),best_position=best_pos.tolist(),
                            function_evaluations=evals,first_success_nfe=first_success,
                            duration_ms=(perf_counter()-start)*1000,trajectory=trajectory)
