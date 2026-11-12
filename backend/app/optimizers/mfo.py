"""Two-dimensional Moth-Flame Optimization (MFO) with inspectable dynamics.

Mirjalili (2015)-style rank-based flame assignment and component-wise
logarithmic spiral: x_new = F + abs(F-x) * exp(b*t) * cos(2*pi*t),
with t sampled independently per dimension from [r, 1] and
r = -1 - iteration / iterations. The flame count declines from N to 1.

The elite flame archive stores the best N unique evaluated positions from
previous memory and current moths, avoiding repeated copies of a single
elite when merging populations. This explicit diversity-preserving archive
rule is a documented variant rather than a claim of exact reproduction of
all reference implementations.

One objective evaluation per moth per generation. NFE = N*(T+1).
"""
from __future__ import annotations

from time import perf_counter
from uuid import uuid4

import numpy as np

from ..models import AgentState, RunRequest, RunResponse, SimulationFrame
from ..objectives import OBJECTIVES

VARIANT = (
    'MFO: ranked moths with sorted elite flame memory; per-dimension spiral '
    'S=F+|F-M| exp(b*t) cos(2*pi*t), t in [r,1], r=-1-l/T; '
    'flames=round(N-l*(N-1)/T), last flame shared; unique best-N archive '
    'over previous memory and current moths; clipped bounds'
)


def _flame_count(n: int, iteration: int, total: int) -> int:
    # Half-up rather than Python's bankers rounding for a stable schedule.
    return max(1, min(n, int(np.floor(n - iteration * (n - 1) / total + 0.5))))


def _merge_flames(old_positions: np.ndarray, old_fitness: np.ndarray,
                  positions: np.ndarray, fitness: np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray]:
    all_positions = np.vstack((old_positions, positions))
    all_fitness = np.concatenate((old_fitness, fitness))
    unique_indices = []
    seen = set()
    for i in np.argsort(all_fitness, kind='stable'):
        # Same exact evaluated location has the same deterministic fitness.
        key = tuple(float(x) for x in all_positions[i])
        if key not in seen:
            seen.add(key)
            unique_indices.append(int(i))
        if len(unique_indices) == n:
            break
    indices = np.asarray(unique_indices, dtype=int)
    return all_positions[indices].copy(), all_fitness[indices].copy()


def simulate(request: RunRequest) -> RunResponse:
    obj = OBJECTIVES[request.objective]
    low, high = obj.bounds
    n = request.population_size
    rng = np.random.default_rng(request.seed)
    positions = rng.uniform(low, high, size=(n, 2))
    fitness = np.asarray([obj.evaluate(*p) for p in positions], dtype=float)
    evaluations = n
    initial_order = np.argsort(fitness, kind='stable')
    flames = positions[initial_order].copy()
    flame_fitness = fitness[initial_order].copy()
    frames: list[SimulationFrame] = []
    start = perf_counter()

    def record(iteration: int, targets: np.ndarray, ranks: list[int],
               spiral_t: np.ndarray, count: int) -> None:
        current_min = float(np.min(fitness))
        scale = max(float(np.max(fitness) - current_min), 1e-12)
        center = positions.mean(axis=0)
        frames.append(SimulationFrame(
            iteration=iteration,
            agents=[AgentState(
                id=i, x=float(positions[i, 0]), y=float(positions[i, 1]),
                fitness=float(fitness[i]),
                brightness=float(1 - (fitness[i] - current_min) / scale),
                flame_x=float(targets[i, 0]), flame_y=float(targets[i, 1]),
                flame_rank=ranks[i],
                spiral_t_x=float(spiral_t[i, 0]), spiral_t_y=float(spiral_t[i, 1]),
            ) for i in range(n)],
            current_best=current_min,
            best_so_far=float(flame_fitness[0]),
            best_position=(float(flames[0, 0]), float(flames[0, 1])),
            mean_fitness=float(fitness.mean()),
            diversity=float(np.linalg.norm(positions - center, axis=1).mean()),
            function_evaluations=evaluations,
            flame_count=count,
        ))

    initial_targets = np.zeros_like(positions)
    initial_ranks = [0] * n
    for rank, i in enumerate(initial_order):
        initial_targets[i] = flames[rank]
        initial_ranks[int(i)] = int(rank)
    record(0, initial_targets, initial_ranks, np.zeros_like(positions), n)

    for iteration in range(1, request.iterations + 1):
        count = _flame_count(n, iteration, request.iterations)
        ranks = [0] * n
        targets = np.zeros_like(positions)
        t_values = np.zeros_like(positions)
        updated = np.zeros_like(positions)
        # Ranking at the start of the generation binds each moth to a flame.
        moth_order = np.argsort(fitness, kind='stable')
        r = -1.0 - iteration / request.iterations
        for rank, i in enumerate(moth_order):
            j = min(rank, count - 1)
            target = flames[j]
            t = rng.uniform(r, 1.0, size=2)
            distance = np.abs(target - positions[i])
            # exp(b*t) cannot overflow for b<=3 and -2<=t<=1.
            moved = target + distance * np.exp(request.mfo_spiral_b * t) * np.cos(2 * np.pi * t)
            updated[i] = np.clip(moved, low, high)
            targets[i] = target
            t_values[i] = t
            ranks[int(i)] = j
        positions = updated
        fitness = np.asarray([obj.evaluate(*p) for p in positions], dtype=float)
        evaluations += n
        flames, flame_fitness = _merge_flames(flames, flame_fitness, positions, fitness, n)
        record(iteration, targets, ranks, t_values, count)

    return RunResponse(
        run_id=str(uuid4()), algorithm='mfo', objective=request.objective,
        seed=request.seed, bounds=obj.bounds, optimum=obj.optimum,
        frames=frames, duration_ms=round((perf_counter() - start) * 1000, 2),
        variant=VARIANT, parameters=request.model_dump(),
    )
