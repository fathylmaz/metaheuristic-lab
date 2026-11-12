"""PSO state, reproducibility, and mathematical invariants."""
from math import isclose

import pytest
from app.models import RunRequest
from app.optimizers.pso import simulate


def test_reproducible_trajectory_and_evaluation_budget():
    request = RunRequest(algorithm='pso', objective='sphere', seed=42,
                         population_size=24, iterations=90)
    first = simulate(request)
    second = simulate(request)
    assert first.frames == second.frames
    assert len(first.frames) == 91
    assert first.frames[-1].function_evaluations == 24 * 91
    assert first.parameters['inertia_weight'] == 0.72
    assert first.parameters['algorithm'] == 'pso'


def test_initial_positions_match_fa_for_same_seed():
    from app.optimizers.firefly import simulate as simulate_fa
    settings = {'seed': 7, 'population_size': 12, 'iterations': 2, 'objective': 'sphere'}
    fa = simulate_fa(RunRequest(algorithm='fa', **settings))
    pso = simulate(RunRequest(algorithm='pso', **settings))
    assert [(a.x, a.y) for a in fa.frames[0].agents] == [(a.x, a.y) for a in pso.frames[0].agents]


def test_personal_best_archive_bounds_and_fitness_are_consistent():
    run = simulate(RunRequest(algorithm='pso', population_size=15, iterations=35,
                              objective='rastrigin', seed=99))
    low, high = run.bounds
    assert all(b.best_so_far <= a.best_so_far for a, b in zip(run.frames, run.frames[1:]))
    from app.objectives import OBJECTIVES
    f = OBJECTIVES[run.objective]
    for frame in run.frames:
        for agent in frame.agents:
            assert low <= agent.x <= high and low <= agent.y <= high
            assert low <= agent.pbest_x <= high and low <= agent.pbest_y <= high
            assert abs(agent.vx) <= 0.2 * (high-low) + 1e-12
            assert abs(agent.vy) <= 0.2 * (high-low) + 1e-12
            assert isclose(agent.fitness, f.evaluate(agent.x, agent.y), abs_tol=1e-10)
            assert isclose(agent.pbest_fitness, f.evaluate(agent.pbest_x, agent.pbest_y), abs_tol=1e-10)
            assert agent.pbest_fitness <= agent.fitness + 1e-12
        assert frame.best_so_far <= frame.current_best + 1e-12


def test_disabled_acceleration_keeps_stationary_particles():
    config = RunRequest(algorithm='pso', cognitive_coefficient=0,
                         social_coefficient=0, population_size=8, iterations=5)
    run = simulate(config)
    assert run.frames[0].agents == run.frames[-1].agents
    assert run.frames[0].best_so_far == run.frames[-1].best_so_far


@pytest.mark.parametrize('objective', ['sphere', 'rastrigin', 'ackley', 'rosenbrock'])
def test_all_objectives(objective):
    run = simulate(RunRequest(algorithm='pso', objective=objective,
                              population_size=8, iterations=4))
    assert len(run.frames) == 5


def test_parameters_change_trajectory():
    common = dict(algorithm='pso', seed=42, population_size=12, iterations=4)
    a = simulate(RunRequest(**common, social_coefficient=1.49))
    b = simulate(RunRequest(**common, social_coefficient=2.8))
    assert a.frames[0] == b.frames[0]
    assert a.frames[1] != b.frames[1]
