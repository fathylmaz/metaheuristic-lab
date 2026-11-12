"""Auditable 2-D Slime Mould Algorithm (SMA), minimization.

Li, Chen, Wang, Heidari & Mirjalili (2020), *Slime mould algorithm: A
new method for stochastic optimization*, Future Generation Computer
Systems, 111, 300--323, DOI 10.1016/j.future.2020.03.055.

Educational implementation choices (also described in docs/SMA_METHODOLOGY.md):
- Weights W use the CURRENT pre-update fitness ranks, with per-individual
  U[0,1] draw and positive/negative feedback for top/bottom halves.
- DF and X_b refer to the all-time best archive *before* each update.
- Each of vb and vc is an independent 2-D vector draw per individual;
  vb ~ U[-a,a]^2 and vc ~ U[-b,b]^2, b=1-t/T,
  a=atanh(1-t/T). At t=T both shrink to zero.
- Branches: random reinitialization with probability z; otherwise a fresh
  random draw chooses best-directed motion (r<p) or contraction (r>=p).
- Positions are synchronously updated from the frozen old population and
  clamped to the objective domain; all NEW fitnesses are evaluated exactly
  once. Elitism is in the archive only, not extra fitness evaluations.
- Every stored movement contains the exact inputs to reconstruct its
  position (including random restart coordinates), and NFE=N*(T+1).
"""
from __future__ import annotations

from time import perf_counter
from uuid import uuid4

import numpy as np

from ..models import AgentState, RunRequest, RunResponse, SimulationFrame
from ..objectives import OBJECTIVES

VARIANT = (
    'SMA 2D synchronous original-style adaptive weights; archived pre-step '
    'best; per-coordinate vb~U[-atanh(1-t/T),atanh(1-t/T)], '
    'vc~U[-(1-t/T),1-t/T], restart with z, p=tanh(|fitness-DF|); '
    'top-half positive feedback; clamp bounds; NFE=N*(T+1).'
)


def control_coefficients(iteration: int, iterations: int) -> tuple[float, float]:
    """Return finite shrinking a and b, t in [1,T]."""
    if iterations < 1 or not 1 <= iteration <= iterations:
        raise ValueError('iteration must be between 1 and iterations')
    b = 1.0 - iteration / iterations
    return float(np.arctanh(b)), float(b)


def adaptive_weights(fitness: np.ndarray, random_draws: np.ndarray) -> np.ndarray:
    """Rank-based positive/negative feedback, stable for tied fitness."""
    if fitness.ndim != 1 or fitness.size == 0 or random_draws.shape != fitness.shape:
        raise ValueError('fitness and draws must be 1D equal non-empty arrays')
    if not np.all(np.isfinite(fitness)) or not np.all(np.isfinite(random_draws)):
        raise ValueError('inputs must be finite')
    order = np.argsort(fitness, kind='stable')
    best, worst = float(fitness[order[0]]), float(fitness[order[-1]])
    scale = max(worst - best, 1e-12)
    ratio = np.clip((worst - fitness) / scale, 0, 1)
    shift = random_draws * np.log1p(ratio)
    weights = np.ones_like(fitness, dtype=float)
    weights[order[:(len(order) + 1) // 2]] += shift[order[:(len(order) + 1) // 2]]
    weights[order[(len(order) + 1) // 2:]] -= shift[order[(len(order) + 1) // 2:]]
    return weights


def simulate(request: RunRequest) -> RunResponse:
    objective = OBJECTIVES[request.objective]
    low, high = objective.bounds
    n, iterations = request.population_size, request.iterations
    z = request.sma_restart_probability
    rng = np.random.default_rng(request.seed)
    started = perf_counter()
    positions = rng.uniform(low, high, size=(n, 2))
    fitness = np.array([objective.evaluate(*pt) for pt in positions], dtype=float)
    evaluations = n
    best_index = int(np.argmin(fitness))
    best_value = float(fitness[best_index])
    best_position = positions[best_index].copy()
    frames: list[SimulationFrame] = []

    def pair(point: np.ndarray) -> tuple[float, float]:
        return float(point[0]), float(point[1])

    def record(iteration: int, a: float, b: float, moves: list[dict] | None) -> None:
        minimum = float(fitness.min())
        spread = max(float(fitness.max()) - minimum, 1e-12)
        center = positions.mean(axis=0)
        agents: list[AgentState] = []
        counts = {'restart': 0, 'approach': 0, 'contract': 0}
        for i in range(n):
            move = moves[i] if moves is not None else {}
            mode = move.get('kind')
            if mode is not None:
                counts[mode] += 1
            agents.append(AgentState(
                id=i, x=float(positions[i, 0]), y=float(positions[i, 1]),
                fitness=float(fitness[i]),
                brightness=float(np.clip(1 - (fitness[i] - minimum) / spread, 0, 1)),
                sma_move_kind=mode,
                sma_weight=move.get('weight'), sma_probability=move.get('p'),
                sma_previous=pair(move['previous']) if 'previous' in move else None,
                sma_best_reference=pair(move['best']) if 'best' in move else None,
                sma_source_a=move.get('source_a'), sma_source_b=move.get('source_b'),
                sma_source_a_position=pair(move['position_a']) if 'position_a' in move else None,
                sma_source_b_position=pair(move['position_b']) if 'position_b' in move else None,
                sma_vb=pair(move['vb']) if 'vb' in move else None,
                sma_vc=pair(move['vc']) if 'vc' in move else None,
                sma_branch_draw=move.get('branch_draw'),
                sma_restart_draw=move.get('restart_draw'),
                sma_raw_position=pair(move['raw']) if 'raw' in move else None,
            ))
        frames.append(SimulationFrame(
            iteration=iteration, agents=agents, current_best=minimum,
            best_so_far=best_value, best_position=pair(best_position),
            mean_fitness=float(fitness.mean()),
            diversity=float(np.linalg.norm(positions - center, axis=1).mean()),
            function_evaluations=evaluations,
            sma_a=a, sma_b=b, sma_restart_probability=z,
            sma_restart_count=counts['restart'],
            sma_approach_count=counts['approach'],
            sma_contract_count=counts['contract'],
            sma_mean_weight=float(np.mean([m['weight'] for m in moves])) if moves is not None else 1.0,
        ))

    record(0, 0.0, 1.0, None)
    for iteration in range(1, iterations + 1):
        a, b = control_coefficients(iteration, iterations)
        old_positions = positions.copy()
        old_fitness = fitness.copy()
        archived = best_position.copy()
        weight_draws = rng.random(n)
        weights = adaptive_weights(old_fitness, weight_draws)
        probabilities = np.tanh(np.abs(old_fitness - best_value))
        updated = np.empty_like(old_positions)
        moves: list[dict] = []
        for i in range(n):
            restart_draw = float(rng.random())
            branch_draw = float(rng.random())
            vb = rng.uniform(-a, a, size=2)
            vc = rng.uniform(-b, b, size=2)
            # Sampling two distinct candidate indices avoids a zero difference
            # caused merely by choosing the same random individual twice.
            source_a, source_b = (int(j) for j in rng.choice(n, size=2, replace=False))
            pos_a, pos_b = old_positions[source_a], old_positions[source_b]
            kind: str
            if restart_draw < z:
                raw = rng.uniform(low, high, size=2)
                kind = 'restart'
            elif branch_draw < probabilities[i]:
                raw = archived + vb * (weights[i] * pos_a - pos_b)
                kind = 'approach'
            else:
                raw = vc * old_positions[i]
                kind = 'contract'
            updated[i] = np.clip(raw, low, high)
            moves.append(dict(kind=kind, previous=old_positions[i].copy(),
                              best=archived.copy(), weight=float(weights[i]),
                              p=float(probabilities[i]), vb=vb, vc=vc,
                              source_a=source_a, source_b=source_b,
                              position_a=pos_a.copy(), position_b=pos_b.copy(),
                              branch_draw=branch_draw, restart_draw=restart_draw,
                              raw=raw.copy()))
        positions = updated
        fitness = np.array([objective.evaluate(*pt) for pt in positions], dtype=float)
        evaluations += n
        winner = int(np.argmin(fitness))
        if float(fitness[winner]) < best_value:
            best_value = float(fitness[winner])
            best_position = positions[winner].copy()
        record(iteration, a, b, moves)

    return RunResponse(
        run_id=str(uuid4()), algorithm='sma', objective=request.objective,
        seed=request.seed, bounds=objective.bounds, optimum=objective.optimum,
        frames=frames, duration_ms=round((perf_counter() - started) * 1000, 2),
        variant=VARIANT, parameters=request.model_dump(),
    )
