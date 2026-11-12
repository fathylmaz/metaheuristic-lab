"""Two-dimensional Gravitational Search Algorithm (GSA) laboratory.

The standard minimization mass scheme (Rashedi et al., 2009) is used.
The accelerating force is a random weighted sum over Kbest agents, with
G(t)=G0*exp(-alpha*t/T) and Kbest declining linearly from N to 1.

Educational implementation conventions: fitness and masses are frozen during
one generation; random factors are sampled separately for each source and
coordinate; position is clipped at the box boundary and blocked velocity
components are reset to zero. Every resulting population position is evaluated
once. The best-so-far archive is independent of the current population.
"""
from __future__ import annotations

from time import perf_counter
from uuid import uuid4

import numpy as np

from ..models import AgentState, RunRequest, RunResponse, SimulationFrame
from ..objectives import OBJECTIVES

VARIANT = (
    'GSA 2D standard minimization normalized masses and random Kbest forces; '
    'G(t)=G0*exp(-alpha*t/T); Kbest=ceil(N-(N-1)t/T), min 1; '
    'frozen prior-generation masses and positions; coordinate-wise random '
    'force factors; v_new=rand*v_old+a, x_new=clip(x_old+v_new); '
    'blocked velocity is set to zero; archived best; NFE=N*(T+1)'
)


def normalized_masses(fitness: np.ndarray) -> np.ndarray:
    """Fitness-based masses for minimization; ties are assigned equal mass."""
    values = np.asarray(fitness, dtype=float)
    if values.ndim != 1 or len(values) == 0 or not np.isfinite(values).all():
        raise ValueError('Fitness must be a nonempty finite vector')
    best, worst = float(values.min()), float(values.max())
    if np.isclose(best, worst, rtol=0.0, atol=1e-15):
        return np.full(len(values), 1.0 / len(values), dtype=float)
    raw = np.maximum((worst - values) / (worst - best), 0.0)
    total = float(raw.sum())
    if total <= 0:
        return np.full(len(values), 1.0 / len(values), dtype=float)
    return raw / total


def gravity(iteration: int, iterations: int, g0: float, decay: float) -> float:
    if not 0 <= iteration <= iterations or iterations < 1:
        raise ValueError('Invalid gravity schedule iteration')
    return float(g0 * np.exp(-decay * iteration / iterations))


def kbest_count(iteration: int, iterations: int, population: int) -> int:
    if not 0 <= iteration <= iterations or iterations < 1 or population < 2:
        raise ValueError('Invalid elite schedule')
    return max(1, min(population, int(np.ceil(population - (population - 1) * iteration / iterations))))


def force_acceleration(
    positions: np.ndarray, masses: np.ndarray, kbest: int,
    g: float, epsilon: float, rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, list[int | None], list[tuple[float, float] | None]]:
    """Return force, acceleration, strongest randomly weighted attraction, location.

    Velocity is not involved. The test suite recomputes a_i = F_i / M_i.
    """
    n = len(masses)
    elite = np.argsort(-masses, kind='stable')[:kbest]
    force = np.zeros_like(positions)
    targets: list[int | None] = []
    target_positions: list[tuple[float, float] | None] = []
    for i in range(n):
        strongest = -1.0
        dominant: int | None = None
        for j in elite:
            j = int(j)
            if j == i:
                continue
            displacement = positions[j] - positions[i]
            distance = float(np.linalg.norm(displacement))
            random_vector = rng.random(2)
            contribution = random_vector * g * masses[i] * masses[j] / (distance + epsilon) * displacement
            force[i] += contribution
            strength = float(np.linalg.norm(contribution))
            if strength > strongest and strength > 0:
                strongest = strength
                dominant = j
        targets.append(dominant)
        target_positions.append(None if dominant is None else (float(positions[dominant, 0]), float(positions[dominant, 1])))
    acceleration = force / np.maximum(masses[:, None], 1e-12)
    return force, acceleration, targets, target_positions


def simulate(request: RunRequest) -> RunResponse:
    obj = OBJECTIVES[request.objective]
    low, high = obj.bounds
    n, total = request.population_size, request.iterations
    rng = np.random.default_rng(request.seed)
    started = perf_counter()
    positions = rng.uniform(low, high, size=(n, 2))
    velocities = np.zeros_like(positions)
    fitness = np.array([obj.evaluate(*xy) for xy in positions], dtype=float)
    masses = normalized_masses(fitness)
    evaluations = n
    winner = int(np.argmin(fitness))
    archived_fitness = float(fitness[winner])
    archived_position = positions[winner].copy()
    frames: list[SimulationFrame] = []

    def record(iteration: int, g: float, elite_count: int, moves: list[dict] | None) -> None:
        minimum = float(fitness.min())
        span = max(float(fitness.max()) - minimum, 1e-12)
        center = positions.mean(axis=0)
        agents: list[AgentState] = []
        for i in range(n):
            item = moves[i] if moves else {}
            def pair(key: str) -> tuple[float, float] | None:
                value = item.get(key)
                return (float(value[0]), float(value[1])) if value is not None else None
            agents.append(AgentState(
                id=i, x=float(positions[i, 0]), y=float(positions[i, 1]),
                fitness=float(fitness[i]),
                brightness=float(np.clip(1-(fitness[i]-minimum)/span, 0, 1)),
                target_id=item.get('target_id'),
                vx=float(velocities[i, 0]), vy=float(velocities[i, 1]),
                gsa_mass=float(masses[i]), gsa_force_mass=item.get('force_mass'),
                gsa_previous=pair('old'),
                gsa_previous_velocity=pair('old_velocity'),
                gsa_acceleration=pair('acceleration'),
                gsa_force=pair('force'), gsa_attractor=pair('attractor'),
                gsa_velocity_draw=pair('velocity_draw'),
            ))
        frames.append(SimulationFrame(
            iteration=iteration, agents=agents, current_best=minimum,
            best_so_far=archived_fitness,
            best_position=(float(archived_position[0]), float(archived_position[1])),
            mean_fitness=float(fitness.mean()),
            diversity=float(np.linalg.norm(positions-center,axis=1).mean()),
            function_evaluations=evaluations, gsa_gravity=g, gsa_kbest=elite_count,
            gsa_max_mass=float(masses.max()),
            gsa_mean_acceleration=float(np.mean([
                np.linalg.norm(m['acceleration']) for m in moves
            ])) if moves else 0.0,
        ))

    record(0, request.gsa_initial_gravity, n, None)
    for iteration in range(1, total+1):
        old_positions, old_velocities, old_masses = positions.copy(), velocities.copy(), masses.copy()
        g = gravity(iteration, total, request.gsa_initial_gravity, request.gsa_decay)
        elite_count = kbest_count(iteration, total, n)
        force, accel, target_ids, target_positions = force_acceleration(
            old_positions, old_masses, elite_count, g, request.gsa_epsilon, rng,
        )
        velocity_draws = rng.random((n, 2))
        proposed_velocity = velocity_draws * old_velocities + accel
        proposed_positions = old_positions + proposed_velocity
        positions = np.clip(proposed_positions, low, high)
        velocities = proposed_velocity.copy()
        velocities[positions != proposed_positions] = 0.0
        moves = [dict(
            old=old_positions[i], old_velocity=old_velocities[i],
            force=force[i], acceleration=accel[i], velocity_draw=velocity_draws[i],
            force_mass=float(old_masses[i]), target_id=target_ids[i],
            attractor=target_positions[i],
        ) for i in range(n)]
        fitness = np.array([obj.evaluate(*xy) for xy in positions], dtype=float)
        evaluations += n
        masses = normalized_masses(fitness)
        winner = int(np.argmin(fitness))
        if float(fitness[winner]) < archived_fitness:
            archived_fitness = float(fitness[winner])
            archived_position = positions[winner].copy()
        record(iteration, g, elite_count, moves)

    return RunResponse(
        run_id=str(uuid4()), algorithm='gsa', objective=request.objective,
        seed=request.seed, bounds=obj.bounds, optimum=obj.optimum,
        frames=frames, duration_ms=round((perf_counter()-started)*1000, 2),
        variant=VARIANT, parameters=request.model_dump(),
    )
