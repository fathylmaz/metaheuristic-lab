"""IWO scientific and API regression tests."""
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import RunRequest
from app.optimizers.iwo import dispersal_sigma, seed_counts, simulate


def req(**kw):
    cfg = dict(algorithm='iwo', objective='sphere', population_size=8,
               iterations=8, seed=42, iwo_max_population=17, iwo_max_seeds=4)
    cfg.update(kw)
    return RunRequest(**cfg)


def test_dispersion_schedule_exact_endpoints_and_decreases():
    values = [dispersal_sigma(t, 8, 1.5, .02, 3) for t in range(9)]
    assert values[0] == pytest.approx(1.5)
    assert values[-1] == pytest.approx(.02)
    assert all(x >= y for x, y in zip(values, values[1:]))


def test_seed_counts_monotonic_and_limits():
    assert seed_counts(np.array([0., 1., 2., 4.]), 0, 4).tolist() == [4, 3, 2, 0]
    assert seed_counts(np.array([3., 3.]), 1, 3).tolist() == [3, 3]


def test_deterministic_all_frames_and_metadata():
    first, second = simulate(req()), simulate(req())
    assert [f.model_dump() for f in first.frames] == [f.model_dump() for f in second.frames]
    assert first.run_id != second.run_id
    assert first.parameters['iwo_max_population'] == 17


def test_variable_population_and_real_nfe():
    run = simulate(req())
    assert len(run.frames) == 9
    assert run.frames[0].iwo_population_after == 8
    for previous, current in zip(run.frames, run.frames[1:]):
        assert current.iwo_population_before == previous.iwo_population_after
        assert current.function_evaluations - previous.function_evaluations == current.iwo_seeds_generated
        assert current.iwo_population_after <= 17
        assert current.iwo_seeds_survived <= current.iwo_seeds_generated
        assert current.iwo_competitive_exclusions == (
            current.iwo_population_before + current.iwo_seeds_generated - current.iwo_population_after)
        assert len(current.agents) == current.iwo_population_after
        assert len({a.id for a in current.agents}) == len(current.agents)


def test_actual_positions_are_reconstructable_from_parent_and_step():
    run = simulate(req())
    lo, hi = run.bounds
    all_births = 0
    for frame in run.frames[1:]:
        for plant in frame.agents:
            if plant.iwo_origin != 'offspring':
                continue
            all_births += 1
            observed = np.array([plant.x, plant.y])
            predicted = np.clip(np.array(plant.iwo_parent_position) +
                                np.array(plant.iwo_raw_step), lo, hi)
            assert observed == pytest.approx(predicted)
            assert plant.iwo_birth_generation == frame.iteration
    assert all_births > 0


def test_best_archive_monotonic_and_fitness_math():
    run = simulate(req())
    assert [f.best_so_far for f in run.frames] == sorted(
        (f.best_so_far for f in run.frames), reverse=True)
    for f in run.frames:
        for plant in f.agents:
            assert plant.fitness == pytest.approx(plant.x**2 + plant.y**2)
            assert 0 <= plant.brightness <= 1
        assert f.best_so_far <= f.current_best + 1e-12


def test_zero_seeds_keeps_population_and_no_spurious_nfe():
    run = simulate(req(iwo_min_seeds=0, iwo_max_seeds=0))
    assert all(f.function_evaluations == 8 for f in run.frames)
    assert all(f.iwo_population_after == 8 for f in run.frames)
    assert all(f.iwo_seeds_generated == 0 for f in run.frames[1:])


def test_all_four_objectives_produce_finite_responses():
    for objective in ('sphere', 'rastrigin', 'ackley', 'rosenbrock'):
        response = simulate(
            RunRequest(algorithm='iwo', objective=objective, population_size=8,
                       iterations=3, iwo_max_population=17, seed=42))
        assert np.isfinite(response.frames[-1].best_so_far)
        low, high = response.bounds
        assert all(low <= a.x <= high and low <= a.y <= high
                   for f in response.frames for a in f.agents)


def test_invalid_combinations_are_rejected():
    client = TestClient(app)
    for update in [
        dict(population_size=24, iwo_max_population=10),
        dict(iwo_min_seeds=6, iwo_max_seeds=2),
        dict(iwo_sigma_initial=.1, iwo_sigma_final=.5),
    ]:
        assert client.post('/api/simulations', json={'algorithm':'iwo', **update}).status_code == 422


def test_api_catalog_and_simulation_schema():
    client = TestClient(app)
    assert client.get('/api/health').json()['version'] == '3.0.0'
    catalog = client.get('/api/catalog').json()
    assert len([a for a in catalog['algorithms'] if a['status'] == 'ready']) == 15
    result = client.post('/api/simulations', json={
        'algorithm':'iwo','objective':'sphere','iterations':4,
        'population_size':8,'iwo_max_population':17
    })
    assert result.status_code == 200, result.text
    data = result.json()
    assert data['algorithm'] == 'iwo'
    assert len(data['frames']) == 5
    assert data['frames'][-1]['iwo_sigma'] > 0
