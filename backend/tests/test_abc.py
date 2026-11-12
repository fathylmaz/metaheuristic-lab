"""Basic ABC correctness, accounting, telemetry, and validation."""
from math import isclose

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models import RunRequest
from app.objectives import OBJECTIVES
from app.optimizers.abc import simulate


def test_seeded_reproducibility_and_nfe_without_scouts():
    params = RunRequest(algorithm='abc', objective='sphere', seed=42,
                        population_size=12, iterations=20, abc_limit=500)
    first, second = simulate(params), simulate(params)
    assert first.frames == second.frames
    assert first.frames[-1].function_evaluations == 12 + 2 * 12 * 20
    assert all(f.scouts_this_iteration == 0 for f in first.frames)
    assert first.parameters['abc_limit'] == 500


def test_bounds_archive_and_source_fitness_consistent():
    for obj in OBJECTIVES:
        result = simulate(RunRequest(algorithm='abc', objective=obj,
                                     population_size=10, iterations=12, abc_limit=10))
        low, high = result.bounds
        f = OBJECTIVES[obj]
        assert len(result.frames) == 13
        for frame in result.frames:
            assert frame.best_so_far <= frame.current_best + 1e-12
            assert sum(a.selection_probability for a in frame.agents) == pytest.approx(1)
            assert all(a.role in ('employed', 'onlooker', 'scout') for a in frame.agents)
            for a in frame.agents:
                assert low <= a.x <= high and low <= a.y <= high
                assert isclose(a.fitness, f.evaluate(a.x, a.y), abs_tol=1e-10)
                assert a.trials >= 0
        assert all(b.best_so_far <= a.best_so_far for a, b in zip(result.frames, result.frames[1:]))


def test_scout_mode_and_actual_evaluation_tracking():
    r = simulate(RunRequest(algorithm='abc', objective='sphere', population_size=8,
                            iterations=15, abc_limit=1, seed=4))
    assert any(f.scouts_this_iteration > 0 for f in r.frames)
    assert sum(f.scouts_this_iteration for f in r.frames) == (
        r.frames[-1].function_evaluations - 8 - 15 * 16)
    assert all(f.scouts_this_iteration <= 1 for f in r.frames)
    assert all(b.function_evaluations > a.function_evaluations for a, b in zip(r.frames, r.frames[1:]))


def test_limit_changes_scout_behavior():
    common = dict(algorithm='abc', seed=8, population_size=8, iterations=15)
    rarely = simulate(RunRequest(**common, abc_limit=500))
    often = simulate(RunRequest(**common, abc_limit=1))
    assert rarely.frames[0] == often.frames[0]
    assert often.frames[-1].function_evaluations > rarely.frames[-1].function_evaluations
    assert often.frames != rarely.frames


def test_abc_api_and_catalog():
    client = TestClient(app)
    catalog = client.get('/api/catalog').json()
    assert next(a for a in catalog['algorithms'] if a['id'] == 'abc')['status'] == 'ready'
    response = client.post('/api/simulations', json={
        'algorithm': 'abc', 'objective': 'sphere', 'population_size': 7,
        'iterations': 3, 'abc_limit': 2, 'seed': 42,
    })
    assert response.status_code == 200
    data = response.json()
    assert data['algorithm'] == 'abc'
    assert data['frames'][-1]['function_evaluations'] >= 7 + 3 * 14
    assert data['frames'][-1]['agents'][0]['role'] is not None
    assert client.get('/api/health').json()['version'] == '3.0.0'


@pytest.mark.parametrize('bad', [0, -1, 501])
def test_invalid_limit_rejected(bad):
    with pytest.raises(ValidationError):
        RunRequest(algorithm='abc', abc_limit=bad)
