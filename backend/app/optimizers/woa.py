"""Inspectable 2D Whale Optimization Algorithm (WOA).

Based on Mirjalili & Lewis (2016), DOI 10.1016/j.advengsoft.2016.01.008.
The original encircling, random-peer search and bubble-net spiral equations
are implemented without additional local search or unreported evaluations.

For each whale, draw independent 2D r1,r2 and define vector A=2*a*r1-a,
C=2*r2. Draw p. When p<(1-spiral_probability) the whale uses the encircling
family; when max(abs(A))>=1 the target is a DIFFERENT random whale from the
old population, otherwise the target is the frozen historical best. When p
is at least (1-spiral_probability), use a single l in [-1,1] for the 2D spiral.

The max-absolute-component exploration test explicitly resolves the standard
vector-|A| ambiguity for the educational 2D visualization; with the default
spiral probability 0.5 it follows the original WOA branch probabilities.
Every target and candidate coefficient is recorded for verification. The
"target" is a frozen pre-update position, not the new animated position.
A decreases linearly from a0 on the first update to zero on the last update.
NFE = N*(T+1); all updates are synchronous; positions are clipped to bounds.
"""
from __future__ import annotations

from time import perf_counter
from uuid import uuid4

import numpy as np

from ..models import AgentState, RunRequest, RunResponse, SimulationFrame
from ..objectives import OBJECTIVES

VARIANT = (
    "WOA 2D synchronous standard encircling / random-peer search / bubble-net spiral; "
    "vector A,C per whale, exploration when max(abs(A)) >= 1; best-so-far frozen "
    "per generation; one spiral l per whale; clipping; archival best; "
    "a(l)=a0*(1-(l-1)/(T-1)), T=1 implies a=0"
)


def _a(iteration: int, iterations: int, initial_a: float) -> float:
    if iterations <= 1:
        return 0.0
    return float(initial_a * (1.0 - (iteration - 1.0) / (iterations - 1.0)))


def simulate(request: RunRequest) -> RunResponse:
    objective = OBJECTIVES[request.objective]
    low, high = objective.bounds
    n = request.population_size
    rng = np.random.default_rng(request.seed)
    started = perf_counter()

    positions = rng.uniform(low, high, size=(n, 2))
    fitness = np.array([objective.evaluate(*point) for point in positions], dtype=float)
    evaluations = n
    winner = int(np.argmin(fitness))
    best_value = float(fitness[winner])
    best_position = positions[winner].copy()
    frames: list[SimulationFrame] = []

    def record(iteration: int, a: float, moves: list[dict] | None) -> None:
        minimum = float(fitness.min())
        span = max(float(fitness.max()) - minimum, 1e-12)
        center = positions.mean(axis=0)
        agents = []
        counts = {'search': 0, 'encircle': 0, 'spiral': 0}
        for i in range(n):
            move = moves[i] if moves is not None else {}
            kind = move.get('kind')
            if kind:
                counts[kind] += 1
            def pair(key: str):
                value = move.get(key)
                return (float(value[0]), float(value[1])) if value is not None else None
            agents.append(AgentState(
                id=i, x=float(positions[i, 0]), y=float(positions[i, 1]),
                fitness=float(fitness[i]),
                brightness=float(np.clip(1 - (fitness[i] - minimum) / span, 0, 1)),
                target_id=move.get('peer'),
                woa_move_kind=kind,
                woa_previous=pair('old'), woa_target=pair('target'),
                woa_target_id=move.get('peer'), woa_A=pair('A'), woa_C=pair('C'),
                woa_p=float(move['p']) if 'p' in move else None,
                woa_l=float(move['l']) if 'l' in move else None,
            ))
        frames.append(SimulationFrame(
            iteration=iteration, agents=agents, current_best=minimum,
            best_so_far=best_value,
            best_position=(float(best_position[0]), float(best_position[1])),
            mean_fitness=float(fitness.mean()),
            diversity=float(np.linalg.norm(positions - center, axis=1).mean()),
            function_evaluations=evaluations, woa_a=a,
            woa_search_count=counts['search'],
            woa_encircle_count=counts['encircle'],
            woa_spiral_count=counts['spiral'],
        ))

    record(0, request.woa_initial_a, None)
    for iteration in range(1, request.iterations + 1):
        a = _a(iteration, request.iterations, request.woa_initial_a)
        old_population = positions.copy()
        frozen_best = best_position.copy()
        new_population = np.empty_like(old_population)
        moves: list[dict] = []
        for i in range(n):
            old = old_population[i].copy()
            p = float(rng.random())
            if p < 1.0 - request.woa_spiral_probability:
                A = 2 * a * rng.random(2) - a
                C = 2 * rng.random(2)
                if float(np.max(np.abs(A))) >= 1:
                    # Sample another whale without a rejection loop.
                    peer = int(rng.integers(0, n - 1))
                    if peer >= i:
                        peer += 1
                    target = old_population[peer].copy()
                    kind = 'search'
                else:
                    target = frozen_best.copy()
                    peer = None
                    kind = 'encircle'
                candidate = target - A * np.abs(C * target - old)
                moves.append({'kind': kind, 'old': old, 'target': target,
                              'peer': peer, 'A': A, 'C': C, 'p': p})
            else:
                ell = float(rng.uniform(-1, 1))
                target = frozen_best.copy()
                distance = np.abs(target - old)
                candidate = target + distance * np.exp(request.woa_spiral_b * ell) * np.cos(2*np.pi*ell)
                moves.append({'kind': 'spiral', 'old': old, 'target': target,
                              'peer': None, 'p': p, 'l': ell})
            new_population[i] = np.clip(candidate, low, high)

        positions = new_population
        fitness = np.array([objective.evaluate(*point) for point in positions], dtype=float)
        evaluations += n
        winner = int(np.argmin(fitness))
        if float(fitness[winner]) < best_value:
            best_value = float(fitness[winner])
            best_position = positions[winner].copy()
        record(iteration, a, moves)

    return RunResponse(
        run_id=str(uuid4()), algorithm='woa', objective=request.objective,
        seed=request.seed, bounds=objective.bounds, optimum=objective.optimum,
        frames=frames, duration_ms=round((perf_counter() - started) * 1000, 2),
        variant=VARIANT, parameters=request.model_dump(),
    )
