"""Synchronous, two-dimensional DE/rand/1/bin minimization laboratory.

Storn & Price (1997), DOI 10.1023/A:1008202821328. Three *distinct*
mutation donors are also distinct from the target. Each generation reads an
unchanged source population (generational, not immediate replacement).

The mutant is V = X[r1] + F*(X[r2]-X[r3]); V is clipped to objective bounds.
Binomial crossover uses an independent uniform draw per coordinate and a
mandatory j_rand coordinate. The trial replaces the target when fitness is
less-than-or-equal. Rejected trials still consume a function evaluation.

Explicit frame records preserve donor ids and positions, raw/clipped mutant,
crossover draws and mask, target and evaluated trial for mathematical audits.
"""
from __future__ import annotations

from time import perf_counter
from uuid import uuid4

import numpy as np

from ..models import AgentState, RunRequest, RunResponse, SimulationFrame
from ..objectives import OBJECTIVES

VARIANT = (
    'DE/rand/1/bin 2D synchronous minimization; frozen generation donors; '
    'r1/r2/r3 pairwise distinct and different from target; '
    'V=clip(Xr1+F*(Xr2-Xr3)); Uj=Vj if randj<CR or j=jrand, else Xij; '
    'greedy selection fitness(U)<=fitness(X); archived best; NFE=N*(T+1)'
)


def mutate(base: np.ndarray, difference_a: np.ndarray,
           difference_b: np.ndarray, f: float, bounds: tuple[float, float]) -> tuple[np.ndarray, np.ndarray]:
    """Return (raw mutant, bounded mutant), without evaluating the objective."""
    raw = np.asarray(base, dtype=float) + f * (
        np.asarray(difference_a, dtype=float) - np.asarray(difference_b, dtype=float)
    )
    return raw, np.clip(raw, *bounds)


def binomial_crossover(target: np.ndarray, mutant: np.ndarray, cr: float,
                       draws: np.ndarray, j_rand: int) -> tuple[np.ndarray, np.ndarray]:
    """The forced coordinate ensures a nonempty mutant mask, even at CR=0."""
    if not 0 <= cr <= 1 or len(target) != len(mutant) or len(draws) != len(target):
        raise ValueError('Invalid crossover inputs')
    if not 0 <= j_rand < len(target):
        raise ValueError('Invalid mandatory crossover dimension')
    mask = np.asarray(draws) < cr
    mask[j_rand] = True
    return np.where(mask, mutant, target), mask


def simulate(request: RunRequest) -> RunResponse:
    if request.population_size < 4:
        raise ValueError('DE/rand/1 requires at least four population members')
    objective = OBJECTIVES[request.objective]
    bounds = objective.bounds
    n, total = request.population_size, request.iterations
    rng = np.random.default_rng(request.seed)
    started = perf_counter()
    positions = rng.uniform(*bounds, size=(n, 2))
    fitness = np.array([objective.evaluate(*xy) for xy in positions], dtype=float)
    evaluations = n
    best_id = int(np.argmin(fitness))
    archived_value = float(fitness[best_id])
    archived_position = positions[best_id].copy()
    frames: list[SimulationFrame] = []

    def record(iteration: int, moves: list[dict] | None = None) -> None:
        center = positions.mean(axis=0)
        low = float(fitness.min())
        span = max(float(fitness.max()-low), 1e-12)
        agents: list[AgentState] = []
        for i in range(n):
            move = moves[i] if moves is not None else {}
            def pair(key: str) -> tuple[float, float] | None:
                value = move.get(key)
                return None if value is None else (float(value[0]), float(value[1]))
            agents.append(AgentState(
                id=i, x=float(positions[i, 0]), y=float(positions[i, 1]),
                fitness=float(fitness[i]),
                brightness=float(np.clip(1-(fitness[i]-low)/span, 0, 1)),
                de_parent=pair('parent'), de_donors=move.get('donor_ids'),
                de_donor_positions=move.get('donor_positions'),
                de_mutant_raw=pair('mutant_raw'), de_mutant=pair('mutant'),
                de_trial=pair('trial'), de_trial_fitness=move.get('trial_fitness'),
                de_crossover_draws=pair('draws'),
                de_crossover_mask=move.get('mask'), de_j_rand=move.get('j_rand'),
                de_accepted=move.get('accepted'),
            ))
        accepted = sum(int(move['accepted']) for move in moves) if moves else 0
        frames.append(SimulationFrame(
            iteration=iteration, agents=agents,
            current_best=float(fitness.min()), best_so_far=archived_value,
            best_position=(float(archived_position[0]), float(archived_position[1])),
            mean_fitness=float(fitness.mean()),
            diversity=float(np.linalg.norm(positions-center, axis=1).mean()),
            function_evaluations=evaluations, de_accepted_count=accepted,
            de_rejected_count=n-accepted if moves else 0,
            de_forced_crossover_count=sum(int(move['forced_only']) for move in moves) if moves else 0,
        ))

    record(0)
    for iteration in range(1, total+1):
        old_population = positions.copy()
        old_fitness = fitness.copy()
        next_population = old_population.copy()
        next_fitness = old_fitness.copy()
        moves: list[dict] = []
        for i in range(n):
            pool = np.delete(np.arange(n), i)
            r1, r2, r3 = [int(index) for index in rng.choice(pool, size=3, replace=False)]
            raw, mutant = mutate(
                old_population[r1], old_population[r2], old_population[r3],
                request.de_mutation_factor, bounds,
            )
            draws = rng.random(2)
            j_rand = int(rng.integers(0, 2))
            trial, mask = binomial_crossover(
                old_population[i], mutant, request.de_crossover_rate, draws, j_rand,
            )
            trial_fitness = float(objective.evaluate(*trial))
            evaluations += 1
            accepted = trial_fitness <= float(old_fitness[i])
            if accepted:
                next_population[i] = trial
                next_fitness[i] = trial_fitness
            moves.append(dict(
                parent=old_population[i], donor_ids=(r1,r2,r3),
                donor_positions=[(float(old_population[r,0]),float(old_population[r,1])) for r in (r1,r2,r3)],
                mutant_raw=raw, mutant=mutant, trial=trial, draws=draws,
                j_rand=j_rand, mask=[bool(v) for v in mask],
                forced_only=not np.any(draws < request.de_crossover_rate),
                trial_fitness=trial_fitness, accepted=bool(accepted),
            ))
        positions, fitness = next_population, next_fitness
        best_id = int(np.argmin(fitness))
        if float(fitness[best_id]) < archived_value:
            archived_value = float(fitness[best_id])
            archived_position = positions[best_id].copy()
        record(iteration, moves)

    return RunResponse(
        run_id=str(uuid4()), algorithm='de', objective=request.objective,
        seed=request.seed, bounds=bounds, optimum=objective.optimum,
        frames=frames, duration_ms=round((perf_counter()-started)*1000, 2),
        variant=VARIANT, parameters=request.model_dump(),
    )
