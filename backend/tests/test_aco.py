import math

import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.optimizers.aco import ACORequest, _normalized_cycle, simulate_aco

client = TestClient(app)


def test_aco_contract_and_pheromone_symmetry():
    cfg = ACORequest(city_count=9, ant_count=7, iterations=8, seed=42, city_seed=8)
    result = simulate_aco(cfg)
    assert len(result.frames) == 8
    assert result.algorithm == 'aco'
    for idx, frame in enumerate(result.frames, 1):
        assert frame.tours_evaluated == idx * 7
        assert len(frame.ant_tours) == 7
        assert len(frame.best_route) == 9
        assert sorted(frame.best_route) == list(range(9))
        assert frame.iteration_best >= frame.best_length - 1e-12
        assert 1 <= frame.unique_tours <= 7
        pheromone = np.asarray(frame.pheromone)
        assert np.allclose(pheromone, pheromone.T)
        assert np.allclose(np.diag(pheromone), 0)
        assert np.all(pheromone[np.triu_indices(9, 1)] >= 0)
        for tour in frame.ant_tours:
            assert sorted(tour.route) == list(range(9))
            ids = np.asarray(tour.route)
            coords = np.asarray([[c.x, c.y] for c in result.cities])
            actual = np.linalg.norm(coords[ids] - coords[np.roll(ids, -1)], axis=1).sum()
            assert math.isclose(actual, tour.length, rel_tol=1e-12)


def test_aco_reproducible_seed_and_city_seed():
    cfg = ACORequest(city_count=14, ant_count=8, iterations=8, seed=24, city_seed=14, layout='clusters')
    first = simulate_aco(cfg)
    second = simulate_aco(cfg)
    assert first.cities == second.cities
    assert first.frames == second.frames
    assert first.run_id != second.run_id
    changed = simulate_aco(cfg.model_copy(update={'seed': 25}))
    assert changed.cities == first.cities
    assert changed.frames[0].ant_tours != first.frames[0].ant_tours
    new_cities = simulate_aco(cfg.model_copy(update={'city_seed': 15}))
    assert new_cities.cities != first.cities


def test_aco_nonincreasing_global_best_and_parameter_effect():
    cfg = ACORequest(city_count=12, ant_count=10, iterations=12)
    baseline = simulate_aco(cfg)
    changed = simulate_aco(cfg.model_copy(update={'beta': 0}))
    values = [f.best_length for f in baseline.frames]
    assert all(b <= a + 1e-12 for a, b in zip(values, values[1:]))
    assert baseline.frames[0].ant_tours != changed.frames[0].ant_tours


def test_aco_cycle_normalization():
    assert _normalized_cycle([2, 1, 0, 3]) == _normalized_cycle([3, 0, 1, 2])
    assert _normalized_cycle([2, 1, 0, 3]) == _normalized_cycle([0, 1, 2, 3])


def test_aco_api_and_invalid_parameters():
    r = client.post('/api/aco/simulations', json={
        'city_count': 7, 'ant_count': 5, 'iterations': 4, 'seed': 42, 'layout': 'circle'
    })
    assert r.status_code == 200, r.text
    result = r.json()
    assert result['problem'] == 'symmetric_euclidean_tsp'
    assert result['frames'][-1]['tours_evaluated'] == 20
    assert result['frames'][-1]['iteration'] == 4
    assert len(result['cities']) == 7
    assert client.post('/api/aco/simulations', json={'city_count': 3}).status_code == 422
    assert client.post('/api/aco/simulations', json={'evaporation': 1}).status_code == 422
    assert client.post('/api/aco/simulations', content='{"alpha": NaN}', headers={'Content-Type': 'application/json'}).status_code == 422
    assert client.post('/api/aco/simulations', json={'layout': 'invalid'}).status_code == 422
    assert client.post('/api/simulations', json={'algorithm': 'aco'}).status_code == 422


def test_aco_circle_layout_places_evenly_spaced():
    output = simulate_aco(ACORequest(city_count=10, iterations=1, ant_count=4, layout='circle'))
    distances = [math.hypot(c.x - .5, c.y - .5) for c in output.cities]
    assert all(abs(v - .39) < 1e-12 for v in distances)
