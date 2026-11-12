"""Numerical correctness, reproducibility and boundary checks for CS."""
import math

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import RunRequest
from app.objectives import OBJECTIVES
from app.optimizers.cuckoo import simulate, _levy
import numpy as np


def request(**overrides):
    return RunRequest(**{'algorithm': 'cs', 'objective': 'sphere', 'seed': 42,
                         'population_size': 24, 'iterations': 12,
                         **overrides})


def test_reproducibility_every_frame():
    a, b = simulate(request()), simulate(request())
    assert a.run_id != b.run_id
    assert a.frames == b.frames
    assert a.parameters == b.parameters


def test_nfe_count_includes_every_rejected_candidate_and_abandoned_nest():
    r = simulate(request())
    assert len(r.frames) == 13
    for t, f in enumerate(r.frames):
        assert f.iteration == t
        assert f.function_evaluations == 24 + t * 30  # 24 egg tests + 6 abandoned
        assert f.abandoned_this_iteration == (0 if t == 0 else 6)
        assert 0 <= f.accepted_levy_this_iteration <= 24


def test_non_decreasing_fitness_quality_and_valid_positions():
    r = simulate(request(objective='rastrigin', iterations=20))
    bests = [frame.best_so_far for frame in r.frames]
    assert all(y <= x for x, y in zip(bests, bests[1:]))
    assert all(math.isfinite(x) for x in bests)
    for frame in r.frames:
        assert len(frame.agents) == 24
        assert frame.current_best >= frame.best_so_far - 1e-9
        for a in frame.agents:
            assert r.bounds[0] <= a.x <= r.bounds[1]
            assert r.bounds[0] <= a.y <= r.bounds[1]
            assert a.fitness == pytest.approx(OBJECTIVES[r.objective].evaluate(a.x, a.y))
        assert frame.diversity >= 0


def test_no_abandonment_budget_is_exact():
    r = simulate(request(cs_discovery_rate=0))
    assert all(f.abandoned_this_iteration == 0 for f in r.frames)
    assert r.frames[-1].function_evaluations == 24 * (12 + 1)


def test_full_discovery_preserves_elite():
    r = simulate(request(cs_discovery_rate=1, population_size=5, iterations=3))
    assert r.frames[-1].function_evaluations == 5 + 3 * (5 + 4)
    assert all(f.abandoned_this_iteration == 4 for f in r.frames[1:])


def test_levy_distribution_is_seeded_and_heavy_tailed():
    a = _levy(np.random.default_rng(17), 1.5, (1000, 2))
    b = _levy(np.random.default_rng(17), 1.5, (1000, 2))
    assert np.array_equal(a, b)
    assert np.isfinite(a).all()
    assert (abs(a) > 3).any()


def test_api_and_catalog():
    client = TestClient(app)
    catalog = client.get('/api/catalog').json()
    assert next(a for a in catalog['algorithms'] if a['id'] == 'cs')['status'] == 'ready'
    response = client.post('/api/simulations', json=request(iterations=3).model_dump())
    assert response.status_code == 200
    obj = response.json()
    assert obj['algorithm'] == 'cs'
    assert obj['frames'][-1]['function_evaluations'] == 24 + 3 * 30
    assert obj['parameters']['cs_discovery_rate'] == 0.25


def test_api_validates_cuckoo_parameters():
    client = TestClient(app)
    for item in ({'cs_step_scale': 0}, {'cs_levy_exponent': 2.1},
                 {'cs_discovery_rate': -0.1}, {'cs_discovery_rate': 1.01}):
        data = request().model_dump()
        data.update(item)
        response = client.post('/api/simulations', json=data)
        assert response.status_code == 422
