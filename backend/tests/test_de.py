"""Regression and mathematical audit tests for synchronous DE/rand/1/bin."""
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import RunRequest
from app.objectives import OBJECTIVES
from app.optimizers.differential import binomial_crossover, mutate, simulate


def make(**kwargs):
    return RunRequest(algorithm='de', objective='sphere', population_size=12,
                      iterations=8, seed=42, **kwargs)


def test_mutation_exact_and_bound_repair():
    raw, bounded = mutate(np.array([2., -2.]), np.array([4., 0.]),
                          np.array([-2., 3.]), .5, (-3., 3.))
    np.testing.assert_allclose(raw, [5., -3.5])
    np.testing.assert_allclose(bounded, [3., -3.])


def test_binomial_forces_dimension_with_zero_cr():
    trial, mask = binomial_crossover(np.array([1., 2.]), np.array([7., 8.]),
                                     0., np.array([.3, .4]), 1)
    assert mask.tolist() == [False, True]
    np.testing.assert_array_equal(trial, [1., 8.])


def test_binomial_full_cr_and_validation():
    trial, mask = binomial_crossover(np.array([1., 2.]), np.array([7., 8.]),
                                     1., np.array([.3, .4]), 0)
    assert mask.tolist() == [True, True]
    np.testing.assert_array_equal(trial, [7., 8.])
    with pytest.raises(ValueError):
        binomial_crossover(np.zeros(2), np.zeros(2), .5, np.zeros(2), 4)


def test_frozen_population_and_telemetry_reproduce_all_mutations_and_trials():
    request = make()
    result = simulate(request)
    for before, after in zip(result.frames[:-1], result.frames[1:]):
        assert after.function_evaluations - before.function_evaluations == 12
        assert after.de_accepted_count + after.de_rejected_count == 12
        assert after.de_forced_crossover_count <= 12
        for agent in after.agents:
            old = before.agents[agent.id]
            assert agent.de_parent == pytest.approx((old.x, old.y))
            donors = agent.de_donors
            assert donors is not None
            assert len(set([*donors, agent.id])) == 4
            donor_points = np.array([(before.agents[i].x, before.agents[i].y) for i in donors])
            np.testing.assert_allclose(agent.de_donor_positions, donor_points)
            raw, mutant = mutate(*donor_points, request.de_mutation_factor, result.bounds)
            np.testing.assert_allclose(agent.de_mutant_raw, raw)
            np.testing.assert_allclose(agent.de_mutant, mutant)
            trial, mask = binomial_crossover(np.array(agent.de_parent), mutant,
                request.de_crossover_rate, np.array(agent.de_crossover_draws), agent.de_j_rand)
            np.testing.assert_allclose(agent.de_trial, trial)
            assert tuple(mask) == agent.de_crossover_mask
            assert mask.any()
            f = OBJECTIVES[result.objective].evaluate(*trial)
            assert agent.de_trial_fitness == pytest.approx(f)
            accepted = f <= old.fitness
            assert agent.de_accepted == accepted
            np.testing.assert_allclose([agent.x, agent.y], trial if accepted else [old.x, old.y])
            assert agent.fitness == pytest.approx(f if accepted else old.fitness)


def test_seed_replay_identical_data_not_uuid_or_runtime():
    first = simulate(make())
    second = simulate(make())
    assert [f.model_dump() for f in first.frames] == [f.model_dump() for f in second.frames]
    assert first.parameters == second.parameters


def test_best_archive_nonincreasing_and_feasible():
    for objective in ('sphere', 'rastrigin', 'ackley', 'rosenbrock'):
        result = simulate(RunRequest(algorithm='de', objective=objective, population_size=8, iterations=7))
        best = [frame.best_so_far for frame in result.frames]
        assert all(a >= b for a, b in zip(best[:-1], best[1:]))
        lo, hi = result.bounds
        assert all(lo <= value <= hi for frame in result.frames for agent in frame.agents for value in (agent.x, agent.y))
        assert result.frames[-1].function_evaluations == 8 * 8


def test_api_parameters_and_422_validation():
    client = TestClient(app)
    response = client.post('/api/simulations', json={
        'algorithm':'de', 'objective':'sphere', 'population_size':6,
        'iterations':3, 'seed':7, 'de_mutation_factor':0.6, 'de_crossover_rate':0.3,
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['algorithm'] == 'de'
    assert data['parameters']['de_mutation_factor'] == 0.6
    assert data['frames'][-1]['function_evaluations'] == 24
    assert data['frames'][1]['agents'][0]['de_trial'] is not None
    assert client.post('/api/simulations', json={'algorithm':'de', 'de_crossover_rate':1.5}).status_code == 422
    assert client.post('/api/simulations', json={'algorithm':'de', 'de_mutation_factor':-0.1}).status_code == 422


def test_crossover_extremes_through_full_optimizer():
    for cr in (0, 1):
        result = simulate(make(de_crossover_rate=cr))
        mask_values = [agent.de_crossover_mask for frame in result.frames[1:] for agent in frame.agents]
        assert all(sum(mask) == (1 if cr == 0 else 2) for mask in mask_values)


def test_catalog_all_fifteen_ready():
    client = TestClient(app)
    assert len([x for x in client.get('/api/catalog').json()['algorithms'] if x['status']=='ready']) == 15
