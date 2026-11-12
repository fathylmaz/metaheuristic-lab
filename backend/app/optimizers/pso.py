"""Synchronous global-best particle swarm optimization in 2D.

Velocity updates use the previous iteration's global best and each particle's
personal best. Both acceleration vectors contain independent U[0, 1) random
numbers for each coordinate and particle. Velocities are clamped to a user-
controlled fraction of the search width. Position clipping zeroes the velocity
component that would otherwise point through a boundary.
"""
from __future__ import annotations

from time import perf_counter
from uuid import uuid4

import numpy as np

from ..models import AgentState, RunRequest, RunResponse, SimulationFrame
from ..objectives import OBJECTIVES

VARIANT = (
    'Synchronous global-best PSO; independent per-coordinate uniform random '
    'coefficients, velocity clamp and zero-velocity boundary handling'
)


def simulate(request: RunRequest) -> RunResponse:
    obj = OBJECTIVES[request.objective]
    low, high = obj.bounds
    rng = np.random.default_rng(request.seed)
    n = request.population_size
    positions = rng.uniform(low, high, size=(n, 2))
    velocities = np.zeros((n, 2), dtype=float)
    fitness = np.asarray([obj.evaluate(*p) for p in positions], dtype=float)
    personal_positions = positions.copy()
    personal_fitness = fitness.copy()
    global_index = int(np.argmin(personal_fitness))
    global_value = float(personal_fitness[global_index])
    global_position = personal_positions[global_index].copy()
    vmax = request.velocity_limit * (high - low)
    frames: list[SimulationFrame] = []
    start = perf_counter()

    def record(iteration: int) -> None:
        current_min = float(fitness.min())
        span = max(1e-12, float(fitness.max()) - current_min)
        center = positions.mean(axis=0)
        diversity = float(np.linalg.norm(positions - center, axis=1).mean())
        agents = [
            AgentState(
                id=i, x=float(positions[i, 0]), y=float(positions[i, 1]),
                fitness=float(fitness[i]),
                brightness=float(1.0 - (fitness[i] - current_min) / span),
                target_id=None,
                vx=float(velocities[i, 0]), vy=float(velocities[i, 1]),
                pbest_x=float(personal_positions[i, 0]),
                pbest_y=float(personal_positions[i, 1]),
                pbest_fitness=float(personal_fitness[i]),
            )
            for i in range(n)
        ]
        frames.append(SimulationFrame(
            iteration=iteration, agents=agents, current_best=current_min,
            best_so_far=global_value,
            best_position=(float(global_position[0]), float(global_position[1])),
            mean_fitness=float(fitness.mean()), diversity=diversity,
            function_evaluations=n * (iteration + 1),
        ))

    record(0)
    for iteration in range(1, request.iterations + 1):
        r1 = rng.random((n, 2))
        r2 = rng.random((n, 2))
        velocities = (
            request.inertia_weight * velocities
            + request.cognitive_coefficient * r1 * (personal_positions - positions)
            + request.social_coefficient * r2 * (global_position - positions)
        )
        velocities = np.clip(velocities, -vmax, vmax)
        tentative = positions + velocities
        outside = (tentative < low) | (tentative > high)
        positions = np.clip(tentative, low, high)
        velocities[outside] = 0.0
        fitness = np.asarray([obj.evaluate(*p) for p in positions], dtype=float)

        improved = fitness < personal_fitness
        personal_positions[improved] = positions[improved]
        personal_fitness[improved] = fitness[improved]
        candidate = int(np.argmin(personal_fitness))
        if float(personal_fitness[candidate]) < global_value:
            global_value = float(personal_fitness[candidate])
            global_position = personal_positions[candidate].copy()
        record(iteration)

    return RunResponse(
        run_id=str(uuid4()), algorithm='pso', objective=request.objective,
        seed=request.seed, bounds=obj.bounds, optimum=obj.optimum,
        frames=frames, duration_ms=round((perf_counter() - start) * 1000, 2),
        variant=VARIANT, parameters=request.model_dump(),
    )
