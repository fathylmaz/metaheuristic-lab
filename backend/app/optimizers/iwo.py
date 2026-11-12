"""Inspectable 2-D Invasive Weed Optimization (IWO) minimizer.

Mehrabian & Lucas (2006), Ecological Informatics 1(4), 355–366.
https://doi.org/10.1016/j.ecoinf.2006.07.003

This is the reproduction / Gaussian seed dispersal / global competitive exclusion
variant. Parents can survive; offspring have stable unique IDs and a recorded parent
and actual pre-clipping Gaussian displacement. All evaluated offspring count toward
NFE, including those rejected by competition. No hidden objective evaluations.
"""
from __future__ import annotations

from time import perf_counter
from uuid import uuid4

import numpy as np

from ..models import AgentState, RunRequest, RunResponse, SimulationFrame
from ..objectives import OBJECTIVES

VARIANT = (
    'IWO 2D original-style fitness-proportional seed count for minimization; '
    'normally dispersed offspring; nonlinear sigma schedule; parent+offspring '
    'global competitive exclusion; archived elite and exact NFE including '
    'discarded seeds; stable globally unique weed IDs.'
)


def dispersal_sigma(iteration: int, iterations: int, sigma_initial: float,
                    sigma_final: float, modulation: float) -> float:
    """Sigma decreases from initial at generation 0 to final at generation T."""
    if iterations < 1 or not 0 <= iteration <= iterations:
        raise ValueError('Iteration must be inside [0,T]')
    if sigma_initial < sigma_final or sigma_final <= 0 or modulation <= 0:
        raise ValueError('Invalid dispersal schedule')
    return float(sigma_final + (sigma_initial - sigma_final) *
                 ((iterations - iteration) / iterations) ** modulation)


def seed_counts(fitness: np.ndarray, min_seeds: int, max_seeds: int) -> np.ndarray:
    """Linear fitness rank interpolation, rounding toward lower integer.

    If all fitness values tie, assign max_seeds to maintain exploration rather
    than divide by zero. More-fit individuals always produce at least as many
    seeds as less-fit individuals.
    """
    if fitness.ndim != 1 or not len(fitness) or not np.isfinite(fitness).all():
        raise ValueError('Fitness must be a finite non-empty one-dimensional array')
    if not 0 <= min_seeds <= max_seeds:
        raise ValueError('Seed limits must be sorted and nonnegative')
    smallest, largest = float(fitness.min()), float(fitness.max())
    if largest == smallest:
        return np.full(len(fitness), max_seeds, dtype=int)
    quality = np.clip((largest - fitness) / (largest - smallest), 0, 1)
    return np.floor(min_seeds + quality * (max_seeds - min_seeds) + 1e-12).astype(int)


def simulate(request: RunRequest) -> RunResponse:
    initial_n, iterations = request.population_size, request.iterations
    max_n = request.iwo_max_population
    if max_n < initial_n:
        raise ValueError('iwo_max_population must be >= population_size')
    if request.iwo_min_seeds > request.iwo_max_seeds:
        raise ValueError('iwo_min_seeds must not exceed iwo_max_seeds')
    if request.iwo_sigma_final > request.iwo_sigma_initial:
        raise ValueError('iwo_sigma_final must not exceed iwo_sigma_initial')

    objective = OBJECTIVES[request.objective]
    lo, hi = objective.bounds
    rng = np.random.default_rng(request.seed)
    started = perf_counter()
    population = rng.uniform(lo, hi, size=(initial_n, 2))
    fitness = np.array([objective.evaluate(*x) for x in population], dtype=float)
    ids: list[int] = list(range(initial_n))
    next_id = initial_n
    evaluations = initial_n
    best_idx = int(np.argmin(fitness))
    best_val = float(fitness[best_idx])
    best_pos = population[best_idx].copy()
    frames: list[SimulationFrame] = []

    def pair(a: np.ndarray) -> tuple[float, float]:
        return float(a[0]), float(a[1])

    def record(generation: int, sigma: float, parent_data: dict[int, dict],
               counts: dict[int, int], old_size: int, produced: int,
               selected_offspring: int, discarded: int) -> None:
        current_best = float(fitness.min())
        worst = float(fitness.max())
        denom = max(worst - current_best, 1e-12)
        centroid = population.mean(axis=0)
        agents: list[AgentState] = []
        for ix, weed_id in enumerate(ids):
            details = parent_data.get(weed_id)
            agents.append(AgentState(
                id=weed_id, x=float(population[ix, 0]), y=float(population[ix, 1]),
                fitness=float(fitness[ix]),
                brightness=float(np.clip(1 - (fitness[ix] - current_best) / denom, 0, 1)),
                iwo_origin='offspring' if details else 'survivor',
                iwo_parent_id=details['parent_id'] if details else None,
                iwo_parent_position=pair(details['parent_position']) if details else None,
                iwo_raw_step=pair(details['raw_step']) if details else None,
                iwo_seeds_produced=counts.get(weed_id, 0),
                iwo_birth_generation=details['birth_generation'] if details else None,
            ))
        frames.append(SimulationFrame(
            iteration=generation, agents=agents, current_best=current_best,
            best_so_far=best_val, best_position=pair(best_pos),
            mean_fitness=float(fitness.mean()),
            diversity=float(np.linalg.norm(population - centroid, axis=1).mean()),
            function_evaluations=evaluations,
            iwo_sigma=sigma,
            iwo_initial_population=initial_n,
            iwo_population_before=old_size,
            iwo_population_after=len(ids),
            iwo_seeds_generated=produced,
            iwo_seeds_survived=selected_offspring,
            iwo_competitive_exclusions=discarded,
        ))

    record(0, dispersal_sigma(0, iterations, request.iwo_sigma_initial,
           request.iwo_sigma_final, request.iwo_modulation_index), {}, {},
           initial_n, 0, 0, 0)

    for generation in range(1, iterations + 1):
        sigma = dispersal_sigma(generation, iterations, request.iwo_sigma_initial,
                               request.iwo_sigma_final, request.iwo_modulation_index)
        old_size = len(ids)
        counts_vector = seed_counts(fitness, request.iwo_min_seeds, request.iwo_max_seeds)
        counts_by_id = dict(zip(ids, (int(x) for x in counts_vector)))
        offspring_positions = []
        offspring_data: dict[int, dict] = {}
        offspring_ids: list[int] = []
        for i, parent_id in enumerate(ids):
            for _ in range(int(counts_vector[i])):
                raw_step = rng.normal(0, sigma, size=2)
                new_location = np.clip(population[i] + raw_step, lo, hi)
                offspring_positions.append(new_location)
                offspring_ids.append(next_id)
                offspring_data[next_id] = {
                    'parent_id': parent_id,
                    'parent_position': population[i].copy(),
                    'raw_step': raw_step.copy(),
                    'birth_generation': generation,
                }
                next_id += 1
        produced = len(offspring_ids)
        if produced:
            offspring_array = np.array(offspring_positions, dtype=float)
            offspring_fitness = np.array(
                [objective.evaluate(*x) for x in offspring_array], dtype=float)
            evaluations += produced
            candidate_positions = np.vstack((population, offspring_array))
            candidate_fitness = np.concatenate((fitness, offspring_fitness))
            candidate_ids = ids + offspring_ids
            # Stable priority for equal fitness: prior plants then ascending seed id.
            survivors = np.argsort(candidate_fitness, kind='stable')[:max_n]
            population = candidate_positions[survivors].copy()
            fitness = candidate_fitness[survivors].copy()
            ids = [candidate_ids[j] for j in survivors]
        # If no seeds, the old plants remain and the NFE does not change.
        child_metadata = {weed_id: offspring_data[weed_id] for weed_id in ids
                          if weed_id in offspring_data}
        kept_new = len(child_metadata)
        discarded = old_size + produced - len(ids)
        winner = int(np.argmin(fitness))
        if float(fitness[winner]) < best_val:
            best_val = float(fitness[winner])
            best_pos = population[winner].copy()
        record(generation, sigma, child_metadata, counts_by_id,
               old_size, produced, kept_new, discarded)

    return RunResponse(
        run_id=str(uuid4()), algorithm='iwo', objective=request.objective,
        seed=request.seed, bounds=objective.bounds, optimum=objective.optimum,
        frames=frames, duration_ms=round((perf_counter() - started) * 1000, 2),
        variant=VARIANT, parameters=request.model_dump(),
    )
