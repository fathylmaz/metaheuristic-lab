"""Grey Wolf Optimizer equation, telemetry, boundary, validation and API tests."""
import math

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import RunRequest
from app.objectives import OBJECTIVES
from app.optimizers.gwo import _a, simulate


def make(**kwargs):
    values = {'algorithm': 'gwo', 'objective': 'sphere', 'population_size': 24,
              'iterations': 12, 'seed': 42}
    values.update(kwargs)
    return RunRequest(**values)


def test_reproducibility():
    first, second = simulate(make()), simulate(make())
    assert first.run_id != second.run_id
    assert first.frames == second.frames
    assert first.parameters == second.parameters


def test_budget_and_leader_ranks():
    run = simulate(make(iterations=90))
    assert len(run.frames) == 91
    assert [f.function_evaluations for f in run.frames] == [24 * (i + 1) for i in range(91)]
    for f in run.frames:
        roles = [a.wolf_role for a in f.agents]
        assert roles.count('alpha') == roles.count('beta') == roles.count('delta') == 1
        assert roles.count('omega') == 21
        assert len(f.gwo_leader_positions) == len(f.gwo_leader_ids) == 3
        assert len(set(f.gwo_leader_ids)) == 3
    assert run.frames[-1].gwo_a == pytest.approx(0.0)
    assert run.frames[1].gwo_a == pytest.approx(2.0)


def test_last_three_leaders_are_source_frame_positions():
    run = simulate(make(iterations=5))
    for previous, after in zip(run.frames, run.frames[1:]):
        for leader_id, leader_point in zip(after.gwo_leader_ids, after.gwo_leader_positions):
            source = previous.agents[leader_id]
            assert leader_point == (source.x, source.y)
        assert [a.id for a in sorted(previous.agents, key=lambda x:(x.fitness,x.id))[:3]] == after.gwo_leader_ids


def test_update_is_exact_mean_of_three_reported_candidates_then_clipped():
    run = simulate(make(iterations=6))
    low, high = run.bounds
    for frame in run.frames[1:]:
        for wolf in frame.agents:
            candidates = np.array([wolf.gwo_x1, wolf.gwo_x2, wolf.gwo_x3])
            position = np.clip(candidates.mean(axis=0), low, high)
            assert np.allclose(position, [wolf.x, wolf.y], atol=1e-12)


def test_fitness_bests_and_bounds_for_four_objectives():
    for name in ('sphere', 'ackley', 'rastrigin', 'rosenbrock'):
        run = simulate(make(objective=name, iterations=9))
        bests = [f.best_so_far for f in run.frames]
        assert all(a >= b for a, b in zip(bests, bests[1:]))
        for frame in run.frames:
            assert math.isfinite(frame.diversity)
            assert frame.best_so_far <= frame.current_best + 1e-10
            for agent in frame.agents:
                assert run.bounds[0] <= agent.x <= run.bounds[1]
                assert run.bounds[0] <= agent.y <= run.bounds[1]
                assert agent.fitness == pytest.approx(OBJECTIVES[name].evaluate(agent.x,agent.y))


def test_coefficient_schedule():
    assert [_a(i, 5, 2) for i in range(1,6)] == [2,1.5,1,.5,0]
    assert _a(1, 1, 2) == 0
    assert _a(1, 8, 1.2) == pytest.approx(1.2)


def test_api_catalog_and_payload():
    client = TestClient(app)
    catalog = client.get('/api/catalog').json()
    assert next(a for a in catalog['algorithms'] if a['id']=='gwo')['status'] == 'ready'
    result = client.post('/api/simulations', json=make(iterations=4).model_dump())
    assert result.status_code == 200, result.text
    body = result.json()
    assert body['algorithm'] == 'gwo'
    assert body['parameters']['gwo_initial_a'] == 2.0
    assert body['frames'][-1]['function_evaluations'] == 120
    assert len(body['frames'][-1]['gwo_leader_positions']) == 3
    assert body['frames'][-1]['agents'][0]['gwo_x1'] is not None


def test_invalid_initial_a_rejected():
    client = TestClient(app)
    for invalid in (0, -1, 3.1, 1e20):
        req = make().model_dump()
        req['gwo_initial_a'] = invalid
        assert client.post('/api/simulations', json=req).status_code == 422


def test_wolf_roles_reflect_current_fitness_not_historical_leader():
    run = simulate(make(iterations=8))
    for f in run.frames:
        sorted_wolves = sorted(f.agents, key=lambda w: (w.fitness, w.id))
        assert [w.wolf_role for w in sorted_wolves[:3]] == ['alpha', 'beta', 'delta']
