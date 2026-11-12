"""Seeded 2D Firefly Algorithm; snapshot-brightness sequential attraction variant.

At generation t, comparisons use all fitness values and reference positions
from the start of that generation. Each firefly moves sequentially toward each
better firefly, using the **current working position** for distance and the
snapshot position for the brighter target. One random vector is applied per
attraction; agents without brighter peers perform one random exploration step.
We evaluate the objective once per agent at the end of each generation.
This deliberate, documented variant preserves the canonical attraction term,
while keeping evaluation counts comparable to other algorithms.
"""
from __future__ import annotations

from math import exp
from time import perf_counter
from uuid import uuid4

import numpy as np

from ..models import AgentState, RunRequest, RunResponse, SimulationFrame
from ..objectives import OBJECTIVES

VARIANT = 'Senkron parlaklık, ardışık çekim, sınır kırpma; random U(-0.5, 0.5), adım ölçeği α × alan genişliği'


def simulate(request: RunRequest) -> RunResponse:
    obj = OBJECTIVES[request.objective]
    low, high = obj.bounds
    rng = np.random.default_rng(request.seed)
    n = request.population_size
    positions = rng.uniform(low, high, size=(n, 2))
    fitness = np.array([obj.evaluate(*p) for p in positions], dtype=float)
    best_idx = int(np.argmin(fitness))
    best_value = float(fitness[best_idx])
    best_position = (float(positions[best_idx, 0]), float(positions[best_idx, 1]))
    frames: list[SimulationFrame] = []
    start = perf_counter()

    def record(iteration: int, targets: list[int | None]):
        current_min = float(np.min(fitness))
        current_max = float(np.max(fitness))
        span = max(1e-12, current_max - current_min)
        center = np.mean(positions, axis=0)
        diversity = float(np.mean(np.linalg.norm(positions - center, axis=1)))
        agents = [
            AgentState(
                id=i, x=float(positions[i, 0]), y=float(positions[i, 1]),
                fitness=float(fitness[i]),
                brightness=float(1.0 - (fitness[i] - current_min) / span),
                target_id=targets[i],
            )
            for i in range(n)
        ]
        frames.append(SimulationFrame(
            iteration=iteration, agents=agents,
            current_best=current_min, best_so_far=best_value,
            best_position=best_position,
            mean_fitness=float(np.mean(fitness)), diversity=diversity,
            function_evaluations=n * (iteration + 1),
        ))

    record(0, [None] * n)
    step_scale = request.alpha * (high - low)
    for t in range(1, request.iterations + 1):
        original_positions = positions.copy()
        original_fitness = fitness.copy()
        next_positions = positions.copy()
        targets: list[int | None] = [None] * n
        for i in range(n):
            working = original_positions[i].copy()
            strongest_attraction = -1.0
            attracted = False
            for j in range(n):
                if original_fitness[j] >= original_fitness[i]:
                    continue
                dx = float(original_positions[j, 0] - working[0])
                dy = float(original_positions[j, 1] - working[1])
                beta = request.beta0 * exp(-request.gamma * (dx * dx + dy * dy))
                if beta > strongest_attraction:
                    strongest_attraction = beta
                    targets[i] = j
                working += beta * (original_positions[j] - working)
                working += step_scale * (rng.random(2) - 0.5)
                working = np.clip(working, low, high)
                attracted = True
            if not attracted:
                working += step_scale * (rng.random(2) - 0.5)
            next_positions[i] = np.clip(working, low, high)
        positions = next_positions
        fitness = np.array([obj.evaluate(*p) for p in positions], dtype=float)
        candidate = int(np.argmin(fitness))
        if fitness[candidate] < best_value:
            best_value = float(fitness[candidate])
            best_position = (float(positions[candidate, 0]), float(positions[candidate, 1]))
        record(t, targets)

    return RunResponse(
        run_id=str(uuid4()), algorithm='fa', objective=request.objective,
        seed=request.seed, bounds=obj.bounds, optimum=obj.optimum,
        frames=frames, duration_ms=round((perf_counter() - start) * 1000, 2),
        variant=VARIANT, parameters=request.model_dump(),
    )
