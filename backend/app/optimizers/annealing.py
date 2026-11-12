"""Traceable 2D Metropolis simulated annealing (SA) for minimization.

Kirkpatrick, Gelatt, Vecchi (1983), Science 220(4598):671-680.
The proposal is a symmetric Gaussian random walk with clipping at the objective
bounds; a clipped proposal can be asymmetric at the boundary, so this module
is explicitly an educational Metropolis-style optimizer, not an equilibrium
MCMC sampler. One proposal is EVALUATED per step regardless of acceptance.
Geometric cooling T(t)=T0 * cooling_rate**(t-1). Best-so-far is archived
separately from the CURRENT (possibly uphill) state.
"""
from __future__ import annotations

from math import exp
from time import perf_counter
from uuid import uuid4

import numpy as np

from ..models import AgentState, RunRequest, RunResponse, SimulationFrame
from ..objectives import OBJECTIVES

VARIANT = (
    '2D Metropolis-style Simulated Annealing; symmetric Gaussian neighbor proposals '
    'clipped to function bounds; geometric temperature schedule T(t)=T0*r^(t-1); '
    'downhill always accepted, uphill with exp(-delta/T); one proposal evaluation '
    'per iteration; archival best separate from current solution.'
)


def temperature_at(iteration: int, initial: float, cooling_rate: float) -> float:
    """Temperature used for proposal t (t>=1); initial frame t=0 shows T0."""
    if iteration < 0 or initial <= 0 or not 0 < cooling_rate <= 1:
        raise ValueError('Invalid annealing temperature schedule')
    return float(initial * cooling_rate ** max(0, iteration - 1))


def metropolis_probability(delta: float, temperature: float) -> float:
    """P(accept) for minimization; tie and better candidates accepted."""
    if not np.isfinite(delta) or not np.isfinite(temperature) or temperature <= 0:
        raise ValueError('Delta and temperature must be finite; temperature > 0')
    return 1.0 if delta <= 0 else float(exp(-delta / temperature))


def simulate(request: RunRequest) -> RunResponse:
    objective = OBJECTIVES[request.objective]
    low, high = objective.bounds
    rng = np.random.default_rng(request.seed)
    started = perf_counter()
    current = rng.uniform(low, high, size=2)
    current_fitness = float(objective.evaluate(*current))
    best = current.copy()
    best_fitness = current_fitness
    evaluations = 1
    accepted_total = 0
    uphill_accepted_total = 0
    rejected_total = 0
    frames: list[SimulationFrame] = []

    def pair(position: np.ndarray) -> tuple[float, float]:
        return float(position[0]), float(position[1])

    def record(iteration: int, temperature: float, *, previous: np.ndarray | None = None,
               candidate: np.ndarray | None = None, candidate_fitness: float | None = None,
               delta: float | None = None, probability: float | None = None,
               draw: float | None = None, accepted: bool | None = None,
               step: np.ndarray | None = None) -> None:
        agent = AgentState(
            id=0, x=float(current[0]), y=float(current[1]),
            fitness=current_fitness, brightness=1.0,
            sa_previous=pair(previous) if previous is not None else None,
            sa_candidate=pair(candidate) if candidate is not None else None,
            sa_candidate_fitness=candidate_fitness, sa_delta=delta,
            sa_accept_probability=probability, sa_accept_draw=draw,
            sa_accepted=accepted,
            sa_step=pair(step) if step is not None else None,
        )
        frames.append(SimulationFrame(
            iteration=iteration, agents=[agent], current_best=current_fitness,
            best_so_far=best_fitness, best_position=pair(best),
            mean_fitness=current_fitness, diversity=0.0,
            function_evaluations=evaluations, sa_temperature=temperature,
            sa_accepted_total=accepted_total, sa_uphill_accepted_total=uphill_accepted_total,
            sa_rejected_total=rejected_total,
            sa_last_accepted=accepted,
        ))

    record(0, request.sa_initial_temperature)
    for t in range(1, request.iterations + 1):
        temperature = temperature_at(t, request.sa_initial_temperature, request.sa_cooling_rate)
        previous = current.copy()
        # Proposal scale is a fraction of the objective domain span.
        step = rng.normal(0.0, request.sa_step_scale * (high - low), size=2)
        candidate = np.clip(previous + step, low, high)
        candidate_fitness = float(objective.evaluate(*candidate))
        evaluations += 1
        delta = candidate_fitness - current_fitness
        probability = metropolis_probability(delta, temperature)
        draw = float(rng.random())
        accepted = draw < probability
        if accepted:
            current = candidate.copy()
            current_fitness = candidate_fitness
            accepted_total += 1
            if delta > 0:
                uphill_accepted_total += 1
            if current_fitness < best_fitness:
                best = current.copy()
                best_fitness = current_fitness
        else:
            rejected_total += 1
        record(t, temperature, previous=previous, candidate=candidate,
               candidate_fitness=candidate_fitness, delta=delta,
               probability=probability, draw=draw, accepted=accepted, step=step)

    return RunResponse(
        run_id=str(uuid4()), algorithm='sa', objective=request.objective,
        seed=request.seed, bounds=objective.bounds, optimum=objective.optimum,
        frames=frames, duration_ms=round((perf_counter()-started)*1000, 2),
        variant=VARIANT, parameters=request.model_dump(),
    )
