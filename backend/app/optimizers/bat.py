"""Inspectable 2D Bat Algorithm (BA), standard Yang-style frequency tuning.

Based on Xin-She Yang (2010), DOI 10.1007/978-3-642-12538-6_6.
Each bat keeps a velocity, pulse frequency, loudness and pulse rate.
One candidate is *evaluated* per bat/iteration, even if subsequently rejected.

For iteration t, with frozen best x_best and the old position x_i:
    f_i ~ U(f_min, f_max)
    v_i <- v_i + (x_i - x_best) * f_i
    candidate <- clip(x_i + v_i)
If U(0,1) > r_i, replace candidate by clip(x_best + eps * mean(A)),
where eps has two U(-1,1) coordinates. Accept strictly better candidates
only when a separate U(0,1) < A_i. Upon acceptance:
    A_i <- alpha * A_i
    r_i <- r0 * (1-exp(-gamma*t))

The initialized *current* pulse rate is zero; `r0` is its asymptotic
upper rate, not a physical signal frequency. This transparent educational
variant is synchronous: all proposals use a frozen pre-update global best
and pre-update mean loudness. `v` is updated regardless of acceptance.
Boundary handling clips evaluated candidate positions; the archival best is
retained even when no bat accepts a solution.
NFE = population_size * (iterations + 1). Each candidate gets ONE evaluation.
"""
from __future__ import annotations

from time import perf_counter
from uuid import uuid4

import numpy as np

from ..models import AgentState, RunRequest, RunResponse, SimulationFrame
from ..objectives import OBJECTIVES

VARIANT = (
    'BA 2D Yang-style frequency update; synchronous frozen best/mean loudness; '
    'one candidate per bat per iteration; current pulse starts at zero, '
    'accepted candidates decrease loudness and update pulse; bound clipping; '
    'strict-improvement acceptance; elite archive; NFE=N*(T+1)'
)


def _pulse_schedule(rate_limit: float, gamma: float, iteration: int) -> float:
    return float(rate_limit * (1.0 - np.exp(-gamma * iteration)))


def simulate(request: RunRequest) -> RunResponse:
    objective = OBJECTIVES[request.objective]
    low, high = objective.bounds
    n = request.population_size
    rng = np.random.default_rng(request.seed)
    started = perf_counter()

    positions = rng.uniform(low, high, size=(n, 2))
    velocities = np.zeros((n, 2), dtype=float)
    fitness = np.array([objective.evaluate(*position) for position in positions], dtype=float)
    evaluations = n
    frequencies = np.zeros(n, dtype=float)
    loudness = np.full(n, request.ba_initial_loudness, dtype=float)
    pulse_rates = np.zeros(n, dtype=float)
    initial_best = int(np.argmin(fitness))
    best_position = positions[initial_best].copy()
    best_value = float(fitness[initial_best])
    frames: list[SimulationFrame] = []

    def record(iteration: int, moves: list[dict] | None) -> None:
        minimum = float(np.min(fitness))
        span = max(float(np.max(fitness) - minimum), 1e-12)
        center = positions.mean(axis=0)
        global_count = local_count = accept_count = 0
        agents: list[AgentState] = []
        for i in range(n):
            event = moves[i] if moves is not None else {}
            kind = event.get('kind')
            if kind == 'global':
                global_count += 1
            elif kind == 'local':
                local_count += 1
            if event.get('accepted', False):
                accept_count += 1

            def pair(key: str) -> tuple[float, float] | None:
                val = event.get(key)
                return (float(val[0]), float(val[1])) if val is not None else None

            agents.append(AgentState(
                id=i, x=float(positions[i, 0]), y=float(positions[i, 1]),
                fitness=float(fitness[i]),
                brightness=float(np.clip(1 - (fitness[i] - minimum) / span, 0, 1)),
                vx=float(velocities[i, 0]), vy=float(velocities[i, 1]),
                ba_frequency=float(frequencies[i]), ba_loudness=float(loudness[i]),
                ba_pulse_rate=float(pulse_rates[i]),
                ba_move_kind=kind, ba_accepted=event.get('accepted'),
                ba_previous=pair('old'), ba_candidate=pair('candidate'),
                ba_reference_best=pair('best'), ba_local_epsilon=pair('epsilon'),
                ba_mean_loudness=float(event['mean_loudness']) if 'mean_loudness' in event else None,
                ba_candidate_fitness=float(event['candidate_fitness']) if 'candidate_fitness' in event else None,
                ba_pulse_draw=float(event['pulse_draw']) if 'pulse_draw' in event else None,
                ba_accept_draw=float(event['accept_draw']) if 'accept_draw' in event else None,
            ))
        frames.append(SimulationFrame(
            iteration=iteration, agents=agents, current_best=minimum,
            best_so_far=best_value,
            best_position=(float(best_position[0]), float(best_position[1])),
            mean_fitness=float(fitness.mean()),
            diversity=float(np.linalg.norm(positions - center, axis=1).mean()),
            function_evaluations=evaluations,
            ba_global_proposals=global_count, ba_local_proposals=local_count,
            ba_accepted_count=accept_count,
            ba_mean_loudness=float(loudness.mean()),
            ba_mean_pulse_rate=float(pulse_rates.mean()),
        ))

    record(0, None)
    for iteration in range(1, request.iterations + 1):
        old_population = positions.copy()
        frozen_best = best_position.copy()
        mean_loudness = float(loudness.mean())
        proposals: list[dict] = []
        for i in range(n):
            old = old_population[i].copy()
            freq = float(rng.uniform(request.ba_frequency_min, request.ba_frequency_max))
            frequencies[i] = freq
            velocities[i] = velocities[i] + (old - frozen_best) * freq
            candidate = old + velocities[i]
            pulse_draw = float(rng.random())
            epsilon = None
            kind = 'global'
            if pulse_draw > pulse_rates[i]:
                epsilon = rng.uniform(-1, 1, size=2)
                candidate = frozen_best + epsilon * mean_loudness
                kind = 'local'
            candidate = np.clip(candidate, low, high)
            candidate_fit = float(objective.evaluate(*candidate))
            evaluations += 1
            accept_draw = float(rng.random())
            accepted = bool(candidate_fit < fitness[i] and accept_draw < loudness[i])
            if accepted:
                positions[i] = candidate
                fitness[i] = candidate_fit
                loudness[i] *= request.ba_loudness_decay
                pulse_rates[i] = _pulse_schedule(request.ba_initial_pulse_rate,
                                                  request.ba_pulse_growth, iteration)
            proposals.append({
                'kind': kind, 'accepted': accepted, 'old': old, 'candidate': candidate,
                'best': frozen_best, 'epsilon': epsilon, 'mean_loudness': mean_loudness,
                'candidate_fitness': candidate_fit,
                'pulse_draw': pulse_draw, 'accept_draw': accept_draw,
            })
        winner = int(np.argmin(fitness))
        if float(fitness[winner]) < best_value:
            best_value = float(fitness[winner])
            best_position = positions[winner].copy()
        record(iteration, proposals)

    return RunResponse(
        run_id=str(uuid4()), algorithm='ba', objective=request.objective,
        seed=request.seed, bounds=objective.bounds, optimum=objective.optimum,
        frames=frames, duration_ms=round((perf_counter() - started)*1000, 2),
        variant=VARIANT, parameters=request.model_dump(),
    )
