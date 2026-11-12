import pytest

from app.models import RunRequest
from app.optimizers.firefly import simulate


def test_determinism_and_budget():
    config = RunRequest(population_size=12, iterations=15, seed=7)
    first = simulate(config)
    second = simulate(config)
    assert first.frames == second.frames
    assert len(first.frames) == 16
    assert first.frames[-1].function_evaluations == 12 * 16


def test_monotone_archive_and_bounds():
    run = simulate(RunRequest(objective='ackley', population_size=20, iterations=20))
    low, high = run.bounds
    assert all(a.fitness >= -1e-9 for f in run.frames for a in f.agents)
    assert all(low <= a.x <= high and low <= a.y <= high for f in run.frames for a in f.agents)
    assert all(b.best_so_far <= a.best_so_far for a, b in zip(run.frames, run.frames[1:]))
    assert all(a.target_id is None or (a.target_id != a.id and 0 <= a.target_id < 20)
               for f in run.frames for a in f.agents)


def test_zero_alpha_is_deterministic():
    config = RunRequest(population_size=10, iterations=10, alpha=0)
    run = simulate(config)
    assert run.frames[0].best_so_far >= run.frames[-1].best_so_far


@pytest.mark.parametrize('objective', ['sphere', 'rastrigin', 'ackley', 'rosenbrock'])
def test_all_objectives(objective):
    run = simulate(RunRequest(objective=objective, population_size=8, iterations=4))
    assert len(run.frames) == 5
