"""Inspectable two-dimensional Salp Swarm Algorithm (SSA).

The original SSA leader/follower equations from Mirjalili et al. (2017)
are implemented with the following explicit educational conventions:

- x[0] is the leader; all other array slots are ordered followers.
- F is the archived best solution *before* the generation update, frozen
  for the entire leader/follower step.
- Each leader coordinate samples independent c2,c3 ~ U(0,1) and moves to
  F_j +/- c1 * ((upper-lower)*c2_j + lower), then clips to bounds.
- c1(t) = c1_initial * exp(-(4*t/T)^2), with canonical c1_initial=2.
- Followers are updated in chain order, using their OLD own position and
  the NEW position of the preceding salp: x'[i] = .5*(x[i]+x'[i-1]).
  This sequential convention (rather than fully synchronous neighbors)
  is identified in the API variant, documentation, and telemetry.
- Every generation evaluates each resulting position exactly once;
  function_evaluations = N * (T + 1). The archived best is retained.

Source: Mirjalili, Gandomi, Mirjalili, Saremi, Faris, Mirjalili (2017),
"Salp Swarm Algorithm: A bio-inspired optimizer for engineering design
problems", Advances in Engineering Software 114, 163-191.
DOI 10.1016/j.advengsoft.2017.07.002.
"""
from __future__ import annotations

from time import perf_counter
from uuid import uuid4

import numpy as np

from ..models import AgentState, RunRequest, RunResponse, SimulationFrame
from ..objectives import OBJECTIVES

VARIANT = (
    'SSA 2D canonical leader and sequential follower chain; archived best '
    'frozen as food before each generation; independent c2,c3 per leader '
    'coordinate; c1(t)=c1_initial*exp(-(4t/T)^2); clipped bounds; '
    'follower new=0.5*(old_self+new_predecessor); NFE=N*(T+1)'
)


def control_coefficient(iteration: int, iterations: int, initial: float = 2.0) -> float:
    if not 1 <= iteration <= iterations:
        raise ValueError('Iteration must be between 1 and the iteration limit')
    return float(initial * np.exp(-((4.0 * iteration / iterations) ** 2)))


def simulate(request: RunRequest) -> RunResponse:
    objective = OBJECTIVES[request.objective]
    low, high = objective.bounds
    n = request.population_size
    rng = np.random.default_rng(request.seed)
    started = perf_counter()
    positions = rng.uniform(low, high, size=(n, 2))
    fitness = np.array([objective.evaluate(*point) for point in positions], dtype=float)
    evaluations = n
    initial_winner = int(np.argmin(fitness))
    best_value = float(fitness[initial_winner])
    best_position = positions[initial_winner].copy()
    frames: list[SimulationFrame] = []

    def record(iteration: int, c1: float, moves: list[dict] | None, food: np.ndarray) -> None:
        minimum = float(fitness.min())
        span = max(float(fitness.max()) - minimum, 1e-12)
        center = positions.mean(axis=0)
        agents: list[AgentState] = []
        for i in range(n):
            move = moves[i] if moves is not None else {}
            def as_pair(key: str) -> tuple[float, float] | None:
                value = move.get(key)
                return (float(value[0]), float(value[1])) if value is not None else None
            agents.append(AgentState(
                id=i, x=float(positions[i, 0]), y=float(positions[i, 1]),
                fitness=float(fitness[i]),
                brightness=float(np.clip(1-(fitness[i]-minimum)/span,0,1)),
                target_id=i-1 if i>0 else None,
                ssa_role='leader' if i==0 else 'follower',
                ssa_previous=as_pair('old'),
                ssa_target=as_pair('target'),
                ssa_c2=as_pair('c2'),
                ssa_c3=as_pair('c3'),
            ))
        chain_length = float(np.linalg.norm(np.diff(positions, axis=0), axis=1).sum())
        frames.append(SimulationFrame(
            iteration=iteration, agents=agents,
            current_best=minimum, best_so_far=best_value,
            best_position=(float(best_position[0]),float(best_position[1])),
            mean_fitness=float(fitness.mean()),
            diversity=float(np.linalg.norm(positions-center,axis=1).mean()),
            function_evaluations=evaluations, ssa_c1=c1,
            ssa_food_position=(float(food[0]),float(food[1])),
            ssa_chain_length=chain_length,
            ssa_leader_distance=float(np.linalg.norm(positions[0]-food)),
        ))

    record(0, request.ssa_c1_initial, None, best_position.copy())
    for iteration in range(1, request.iterations+1):
        coefficient = control_coefficient(iteration, request.iterations, request.ssa_c1_initial)
        old_positions = positions.copy()
        food = best_position.copy()
        new_positions = np.empty_like(old_positions)
        # Leader: independent component-wise draws and the original signed range term.
        c2 = rng.random(2)
        c3 = rng.random(2)
        sign = np.where(c3>=0.5,1.0,-1.0)
        leader = food + sign*coefficient*((high-low)*c2+low)
        new_positions[0] = np.clip(leader,low,high)
        moves: list[dict] = [{'old':old_positions[0], 'target':food,
                              'c2':c2,'c3':c3}]
        # Followers use NEW predecessor, OLD own position (chain order).
        for i in range(1,n):
            predecessor = new_positions[i-1].copy()
            new_positions[i] = np.clip(0.5*(old_positions[i]+predecessor),low,high)
            moves.append({'old':old_positions[i], 'target':predecessor})

        positions = new_positions
        fitness = np.array([objective.evaluate(*point) for point in positions],dtype=float)
        evaluations += n
        winner = int(np.argmin(fitness))
        if float(fitness[winner]) < best_value:
            best_value = float(fitness[winner])
            best_position = positions[winner].copy()
        record(iteration, coefficient, moves, food)

    return RunResponse(
        run_id=str(uuid4()), algorithm='ssa', objective=request.objective,
        seed=request.seed, bounds=objective.bounds, optimum=objective.optimum,
        frames=frames, duration_ms=round((perf_counter()-started)*1000,2),
        variant=VARIANT, parameters=request.model_dump(),
    )
