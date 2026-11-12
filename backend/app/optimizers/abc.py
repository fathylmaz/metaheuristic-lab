"""Basic Artificial Bee Colony (ABC) algorithm, two-dimensional minimization.

There are N *food sources* (one employed bee and one onlooker evaluation
per source each cycle); scout bees replace exhausted sources. Each cycle:
  1. N employed candidates, greedy acceptance;
  2. N onlooker candidates, roulette selection proportional to nectar fitness;
  3. At most one exhausted source is replaced by a random scout candidate.

The displayed agents represent food sources, NOT every bee in the colony.
Every objective evaluation is counted, including failed proposals and scouts.
The best-so-far archive survives source abandonment. The random-number
stream is local and seeded for reproducibility.
"""
from __future__ import annotations

from time import perf_counter
from uuid import uuid4

import numpy as np

from ..models import AgentState, RunRequest, RunResponse, SimulationFrame
from ..objectives import OBJECTIVES

VARIANT = (
    'Basic ABC, 2D continuous minimization: one employed and one onlooker '
    'candidate per food source per cycle, proportional roulette selection, '
    'single-coordinate neighbor, greedy acceptance, at most one scout '
    'replacement per cycle. Food sources are visualized (not individual bees).'
)


def nectar(fitness: np.ndarray) -> np.ndarray:
    """Positive transform of minimization objective; safe for negative values."""
    return np.where(fitness >= 0, 1 / (1 + np.maximum(fitness, 0)),
                    1 + np.abs(np.minimum(fitness, 0)))


def simulate(request: RunRequest) -> RunResponse:
    obj = OBJECTIVES[request.objective]
    low, high = obj.bounds
    rng = np.random.default_rng(request.seed)
    n = request.population_size
    positions = rng.uniform(low, high, size=(n, 2))
    fitness = np.array([obj.evaluate(*p) for p in positions], dtype=float)
    trials = np.zeros(n, dtype=int)
    roles = ['employed'] * n
    last_sources: list[int | None] = [None] * n
    evaluations = n
    best_idx = int(np.argmin(fitness))
    archive_value = float(fitness[best_idx])
    archive_position = positions[best_idx].copy()
    frames: list[SimulationFrame] = []
    start = perf_counter()

    def remember() -> None:
        nonlocal archive_value, archive_position
        i = int(np.argmin(fitness))
        if float(fitness[i]) < archive_value:
            archive_value = float(fitness[i])
            archive_position = positions[i].copy()

    def record(iteration: int) -> None:
        center = positions.mean(axis=0)
        weights = nectar(fitness)
        probs = weights / weights.sum()
        agents = [
            AgentState(
                id=i, x=float(positions[i, 0]), y=float(positions[i, 1]),
                fitness=float(fitness[i]), brightness=float(probs[i] / probs.max()),
                target_id=last_sources[i], role=roles[i], trials=int(trials[i]),
                selection_probability=float(probs[i]),
            ) for i in range(n)
        ]
        frames.append(SimulationFrame(
            iteration=iteration, agents=agents, current_best=float(fitness.min()),
            best_so_far=archive_value,
            best_position=(float(archive_position[0]), float(archive_position[1])),
            mean_fitness=float(fitness.mean()),
            diversity=float(np.linalg.norm(positions - center, axis=1).mean()),
            function_evaluations=evaluations,
            scouts_this_iteration=sum(role == 'scout' for role in roles),
        ))

    def propose(i: int, role: str) -> None:
        nonlocal evaluations
        # Exclude the selected source from the neighbor index by construction.
        k = int(rng.integers(0, n - 1))
        if k >= i:
            k += 1
        j = int(rng.integers(0, 2))
        phi = float(rng.uniform(-1, 1))
        candidate = positions[i].copy()
        candidate[j] = np.clip(candidate[j] + phi * (candidate[j] - positions[k, j]), low, high)
        candidate_value = obj.evaluate(*candidate)
        evaluations += 1
        roles[i] = role
        last_sources[i] = k
        if candidate_value < fitness[i]:
            positions[i] = candidate
            fitness[i] = candidate_value
            trials[i] = 0
        else:
            trials[i] += 1

    record(0)
    for iteration in range(1, request.iterations + 1):
        roles = ['employed'] * n
        last_sources = [None] * n
        for i in range(n):
            propose(i, 'employed')
        probs = nectar(fitness)
        probs /= probs.sum()
        # Exactly N onlooker trials: each is an independent roulette draw.
        for _ in range(n):
            i = int(rng.choice(n, p=probs))
            propose(i, 'onlooker')
        # Basic ABC: one scout (maximum trial count) per cycle.
        abandoned = int(np.argmax(trials))
        if trials[abandoned] >= request.abc_limit:
            positions[abandoned] = rng.uniform(low, high, size=2)
            fitness[abandoned] = obj.evaluate(*positions[abandoned])
            evaluations += 1
            trials[abandoned] = 0
            roles[abandoned] = 'scout'
            last_sources[abandoned] = None
        remember()
        record(iteration)

    return RunResponse(
        run_id=str(uuid4()), algorithm='abc', objective=request.objective,
        seed=request.seed, bounds=obj.bounds, optimum=obj.optimum,
        frames=frames, duration_ms=round((perf_counter() - start) * 1000, 2),
        variant=VARIANT, parameters=request.model_dump(),
    )


def simulate_budgeted(request: RunRequest, target_evaluations: int) -> RunResponse:
    """Run ABC against an exact NFE cap and sample at common comparison checkpoints.

    Unlike ordinary ABC cycles, a budget-constrained run may end partway
    through the employed/onlooker phase. No uncounted proposals are evaluated.
    The returned frame number is a *budget checkpoint*, not an ABC cycle.
    The canonical standalone ``simulate`` function is unchanged.
    """
    n = request.population_size
    if target_evaluations < n or target_evaluations % n:
        raise ValueError('Budget must be a positive multiple of the source count')

    obj = OBJECTIVES[request.objective]
    low, high = obj.bounds
    rng = np.random.default_rng(request.seed)
    positions = rng.uniform(low, high, size=(n, 2))
    fitness = np.array([obj.evaluate(*p) for p in positions], dtype=float)
    counts = np.zeros(n, dtype=int)
    roles: list[str] = ['employed'] * n
    references: list[int | None] = [None] * n
    evaluations = n
    checkpoint = 0
    cycles_completed = 0
    scouts_since_checkpoint = 0
    best_index = int(np.argmin(fitness))
    archive_value = float(fitness[best_index])
    archive_position = positions[best_index].copy()
    frames: list[SimulationFrame] = []
    start = perf_counter()

    def remember() -> None:
        nonlocal archive_value, archive_position
        i = int(np.argmin(fitness))
        if float(fitness[i]) < archive_value:
            archive_value = float(fitness[i])
            archive_position = positions[i].copy()

    def snapshot() -> None:
        nonlocal checkpoint, scouts_since_checkpoint
        center = positions.mean(axis=0)
        weights = nectar(fitness)
        probabilities = weights / weights.sum()
        frames.append(SimulationFrame(
            iteration=checkpoint,
            agents=[AgentState(
                id=i, x=float(positions[i, 0]), y=float(positions[i, 1]),
                fitness=float(fitness[i]),
                brightness=float(probabilities[i] / probabilities.max()),
                target_id=references[i], role=roles[i], trials=int(counts[i]),
                selection_probability=float(probabilities[i]),
            ) for i in range(n)],
            current_best=float(fitness.min()), best_so_far=archive_value,
            best_position=(float(archive_position[0]), float(archive_position[1])),
            mean_fitness=float(fitness.mean()),
            diversity=float(np.linalg.norm(positions - center, axis=1).mean()),
            function_evaluations=evaluations,
            scouts_this_iteration=scouts_since_checkpoint,
        ))
        checkpoint += 1
        scouts_since_checkpoint = 0

    def check_snapshot() -> None:
        if evaluations % n == 0:
            snapshot()

    def evaluate_candidate(i: int, role: str) -> None:
        nonlocal evaluations
        k = int(rng.integers(0, n - 1))
        if k >= i:
            k += 1
        coordinate = int(rng.integers(0, 2))
        phi = float(rng.uniform(-1, 1))
        candidate = positions[i].copy()
        candidate[coordinate] = np.clip(
            candidate[coordinate] + phi * (candidate[coordinate] - positions[k, coordinate]), low, high,
        )
        value = obj.evaluate(*candidate)
        evaluations += 1
        roles[i] = role
        references[i] = k
        if value < fitness[i]:
            positions[i] = candidate
            fitness[i] = value
            counts[i] = 0
        else:
            counts[i] += 1
        remember()
        check_snapshot()

    snapshot()  # N initial evaluations, before optimization
    while evaluations < target_evaluations:
        roles = ['employed'] * n
        references = [None] * n
        for i in range(n):
            if evaluations >= target_evaluations:
                break
            evaluate_candidate(i, 'employed')
        if evaluations >= target_evaluations:
            break
        probabilities = nectar(fitness)
        probabilities /= probabilities.sum()
        for _ in range(n):
            if evaluations >= target_evaluations:
                break
            i = int(rng.choice(n, p=probabilities))
            evaluate_candidate(i, 'onlooker')
        if evaluations >= target_evaluations:
            break
        exhausted = int(np.argmax(counts))
        if counts[exhausted] >= request.abc_limit:
            positions[exhausted] = rng.uniform(low, high, size=2)
            fitness[exhausted] = obj.evaluate(*positions[exhausted])
            evaluations += 1
            counts[exhausted] = 0
            roles[exhausted] = 'scout'
            references[exhausted] = None
            scouts_since_checkpoint += 1
            remember()
            check_snapshot()
        cycles_completed += 1

    assert evaluations == target_evaluations
    assert len(frames) == target_evaluations // n
    return RunResponse(
        run_id=str(uuid4()), algorithm='abc', objective=request.objective,
        seed=request.seed, bounds=obj.bounds, optimum=obj.optimum,
        frames=frames, duration_ms=round((perf_counter() - start) * 1000, 2),
        variant=(VARIANT + ' Budgeted comparison: exact NFE cap, sampled every N evaluations; '
                 'frame iteration counts NFE checkpoints, not complete ABC cycles. '
                 f'{cycles_completed} complete ABC cycles; last phase may be partial.'),
        parameters={**request.model_dump(), 'budget_nfe': target_evaluations,
                    'abc_cycles_completed': cycles_completed},
    )
