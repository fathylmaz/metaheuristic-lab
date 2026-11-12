"""Inspectable two-dimensional Grey Wolf Optimizer.

Canonical GWO hunting update (Mirjalili et al., 2014):
    A_k = 2*a*r1_k - a, C_k = 2*r2_k
    D_k = abs(C_k * leader_k - wolf)
    X_k = leader_k - A_k*D_k,  k in {alpha,beta,delta}
    new_wolf = clip((X_1 + X_2 + X_3)/3, bounds)

At each generation leaders are the three distinct best CURRENT wolves. They
are frozen while the next population is generated (synchronous updating).
The leaders used to generate a frame are exposed in frame.gwo_leader_positions,
while frame.wolf_role describes the NEW population ranks. The historical best
solution is separately archived so the displayed best never worsens.

The initial control a is 2 by default and linearly approaches 0. Altering its
initial value via the UI is an explicitly configurable GWO variant.
No local search or unreported objective calls are used. NFE = N*(T+1).
"""
from __future__ import annotations

from time import perf_counter
from uuid import uuid4

import numpy as np

from ..models import AgentState, RunRequest, RunResponse, SimulationFrame
from ..objectives import OBJECTIVES

VARIANT = (
    "GWO synchronous alpha-beta-delta encircling; a(l)=a0*(1-(l-1)/(T-1)) "
    "for update l=1..T (T=1 uses a=0); independent uniform coefficient "
    "vectors per wolf, leader and dimension; mean of three candidates, "
    "clipped positions; current-population distinct leaders, global-best archive"
)


def _a(iteration: int, iterations: int, initial_a: float) -> float:
    """Coefficient used for update iteration (1-based)."""
    if iterations <= 1:
        return 0.0
    return float(initial_a * (1.0 - (iteration - 1.0) / (iterations - 1.0)))


def _roles(fitness: np.ndarray) -> list[str]:
    order = np.argsort(fitness, kind="stable")
    roles = ["omega"] * len(fitness)
    for k, role in enumerate(("alpha", "beta", "delta")):
        roles[int(order[k])] = role
    return roles


def simulate(request: RunRequest) -> RunResponse:
    objective = OBJECTIVES[request.objective]
    low, high = objective.bounds
    n = request.population_size
    rng = np.random.default_rng(request.seed)
    started = perf_counter()

    positions = rng.uniform(low, high, size=(n, 2))
    fitness = np.asarray([objective.evaluate(*point) for point in positions], dtype=float)
    evaluations = n
    best_idx = int(np.argmin(fitness))
    best_fitness = float(fitness[best_idx])
    best_position = positions[best_idx].copy()
    frames: list[SimulationFrame] = []

    def record(iteration: int, leaders: np.ndarray, leader_ids: list[int],
               a: float, candidates: np.ndarray | None) -> None:
        current_min = float(fitness.min())
        scale = max(float(fitness.max() - current_min), 1e-12)
        center = positions.mean(axis=0)
        roles = _roles(fitness)
        agents = []
        for i in range(n):
            parts = candidates[i] if candidates is not None else None
            agents.append(AgentState(
                id=i, x=float(positions[i, 0]), y=float(positions[i, 1]),
                fitness=float(fitness[i]),
                brightness=float(np.clip(1 - (fitness[i] - current_min) / scale, 0, 1)),
                wolf_role=roles[i],
                gwo_x1=(float(parts[0, 0]), float(parts[0, 1])) if parts is not None else None,
                gwo_x2=(float(parts[1, 0]), float(parts[1, 1])) if parts is not None else None,
                gwo_x3=(float(parts[2, 0]), float(parts[2, 1])) if parts is not None else None,
            ))
        frames.append(SimulationFrame(
            iteration=iteration, agents=agents,
            current_best=current_min, best_so_far=best_fitness,
            best_position=(float(best_position[0]), float(best_position[1])),
            mean_fitness=float(fitness.mean()),
            diversity=float(np.linalg.norm(positions - center, axis=1).mean()),
            function_evaluations=evaluations,
            gwo_a=a,
            gwo_leader_ids=list(leader_ids),
            gwo_leader_positions=[(float(x), float(y)) for x, y in leaders],
        ))

    init_order = np.argsort(fitness, kind="stable")[:3]
    record(0, positions[init_order].copy(), [int(x) for x in init_order], request.gwo_initial_a, None)

    for iteration in range(1, request.iterations + 1):
        order = np.argsort(fitness, kind="stable")[:3]
        leaders = positions[order].copy()
        old_positions = positions.copy()
        a = _a(iteration, request.iterations, request.gwo_initial_a)
        # Each wolf: three independent leader-wise 2D coefficient pairs.
        r1 = rng.random(size=(n, 3, 2))
        r2 = rng.random(size=(n, 3, 2))
        A = 2.0 * a * r1 - a
        C = 2.0 * r2
        D = np.abs(C * leaders[None, :, :] - old_positions[:, None, :])
        candidates = leaders[None, :, :] - A * D
        positions = np.clip(candidates.mean(axis=1), low, high)
        fitness = np.asarray([objective.evaluate(*point) for point in positions], dtype=float)
        evaluations += n
        new_idx = int(np.argmin(fitness))
        if float(fitness[new_idx]) < best_fitness:
            best_fitness = float(fitness[new_idx])
            best_position = positions[new_idx].copy()
        record(iteration, leaders, [int(x) for x in order], a, candidates)

    return RunResponse(
        run_id=str(uuid4()), algorithm="gwo", objective=request.objective,
        seed=request.seed, bounds=objective.bounds, optimum=objective.optimum,
        frames=frames, duration_ms=round((perf_counter() - started) * 1000, 2),
        variant=VARIANT, parameters=request.model_dump(),
    )
