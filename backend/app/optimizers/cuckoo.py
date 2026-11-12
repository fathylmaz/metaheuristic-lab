"""Cuckoo Search (CS) on bounded continuous 2D benchmark objectives.

Explicit variant following Yang & Deb's 2009 brood-parasitism rules:
* n Levy-flight candidate eggs, each tested against one random host nest
* greedy replacement only if the candidate is better
* round(pa*n) of the WORST nests (excluding the current best) are abandoned
  and independently reinitialized uniformly within bounds
* global best ever evaluated is archived and never lost

Mantegna sampler parameterizes stable heavy-tailed flight increments. The
flight step is scaled by the displacement from global best plus a small
isotropic term so a nest at the global best can still explore. The abandonment
stage is a fixed-count variant of the probability/fraction p_a rule.

Total NFE = n + iterations*(n + min(n-1, round(pa*n))). Count every candidate,
including rejected eggs and abandoned/rebuilt nests.
"""
from __future__ import annotations

from math import gamma, pi, sin
from time import perf_counter
from uuid import uuid4

import numpy as np

from ..models import AgentState, RunRequest, RunResponse, SimulationFrame
from ..objectives import OBJECTIVES

VARIANT = (
    'CS: Mantegna Levy flights beta in [1.1,1.9]; one random host per egg, '
    'greedy survival; worst round(pa*n) nests (excluding best) reinitialized '
    'uniformly; elitist best archive, clipped boundaries'
)


def _levy(rng: np.random.Generator, beta: float, shape: tuple[int, ...]) -> np.ndarray:
    """Sample symmetric beta-stable Levy steps with Mantegna's method."""
    sigma = (
        gamma(1.0 + beta) * sin(pi * beta / 2.0)
        / (gamma((1.0 + beta) / 2.0) * beta * 2.0 ** ((beta - 1.0) / 2.0))
    ) ** (1.0 / beta)
    u = rng.normal(0.0, sigma, size=shape)
    v = rng.normal(0.0, 1.0, size=shape)
    return u / np.maximum(np.abs(v), 1e-12) ** (1.0 / beta)


def simulate(request: RunRequest) -> RunResponse:
    obj = OBJECTIVES[request.objective]
    low, high = obj.bounds
    width = high - low
    n = request.population_size
    rng = np.random.default_rng(request.seed)
    positions = rng.uniform(low, high, size=(n, 2))
    fitness = np.asarray([obj.evaluate(*point) for point in positions], dtype=float)
    evals = n
    idx = int(np.argmin(fitness))
    archive_value = float(fitness[idx])
    archive_position = positions[idx].copy()
    abandoned_per_generation = min(n - 1, int(np.floor(request.cs_discovery_rate * n + 0.5)))
    frames: list[SimulationFrame] = []
    start = perf_counter()

    def record(iteration: int, actions: list[str], flight_lengths: list[float],
               accepted: int, abandoned: int) -> None:
        current_best = float(np.min(fitness))
        scale = max(float(np.max(fitness) - current_best), 1e-12)
        center = np.mean(positions, axis=0)
        frames.append(SimulationFrame(
            iteration=iteration,
            agents=[AgentState(
                id=i, x=float(positions[i, 0]), y=float(positions[i, 1]),
                fitness=float(fitness[i]), brightness=float(1-(fitness[i]-current_best)/scale),
                move_kind=actions[i], proposed_flight_length=float(flight_lengths[i]),
            ) for i in range(n)],
            current_best=current_best, best_so_far=archive_value,
            best_position=(float(archive_position[0]), float(archive_position[1])),
            mean_fitness=float(fitness.mean()),
            diversity=float(np.linalg.norm(positions - center, axis=1).mean()),
            function_evaluations=evals,
            abandoned_this_iteration=abandoned,
            accepted_levy_this_iteration=accepted,
        ))

    record(0, ['retained'] * n, [0.0] * n, 0, 0)
    for iteration in range(1, request.iterations + 1):
        actions = ['retained'] * n
        lengths = [0.0] * n
        accepted = 0
        # Each egg is laid in a randomly chosen host nest. One true evaluation.
        for _ in range(n):
            source = int(rng.integers(n))
            host = int(rng.integers(n))
            step = _levy(rng, request.cs_levy_exponent, (2,))
            # Long-tailed direction: near the best also allow a small random jump.
            direction = positions[source] - archive_position + 0.02 * width * rng.standard_normal(2)
            displacement = request.cs_step_scale * step * direction
            candidate = np.clip(positions[source] + displacement, low, high)
            value = float(obj.evaluate(*candidate))
            evals += 1
            lengths[host] = float(np.linalg.norm(displacement))
            if value < float(fitness[host]):
                positions[host] = candidate
                fitness[host] = value
                actions[host] = 'levy'
                accepted += 1
                if value < archive_value:
                    archive_value = value
                    archive_position = candidate.copy()
        # Deterministic fixed-fraction abandonment of WORST current host nests.
        # Preserve at least one best current nest; archive also retained.
        if abandoned_per_generation:
            worst = np.argsort(fitness)[::-1]
            elite = int(np.argmin(fitness))
            targets = [int(j) for j in worst if int(j) != elite][:abandoned_per_generation]
            for j in targets:
                candidate = rng.uniform(low, high, 2)
                value = float(obj.evaluate(*candidate))
                evals += 1
                positions[j] = candidate
                fitness[j] = value
                actions[j] = 'abandoned'
                lengths[j] = 0.0
                if value < archive_value:
                    archive_value = value
                    archive_position = candidate.copy()
        record(iteration, actions, lengths, accepted, abandoned_per_generation)

    return RunResponse(
        run_id=str(uuid4()), algorithm='cs', objective=request.objective,
        seed=request.seed, bounds=obj.bounds, optimum=obj.optimum,
        frames=frames, duration_ms=round((perf_counter() - start) * 1000, 2),
        variant=VARIANT, parameters=request.model_dump(),
    )
