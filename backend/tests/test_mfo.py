"""MFO regression tests for the numerical update, telemetry and API."""
import math

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import RunRequest
from app.objectives import OBJECTIVES
from app.optimizers.mfo import _flame_count, _merge_flames, simulate


def make(**kwargs):
    return RunRequest(**{'algorithm':'mfo', 'objective':'sphere', 'population_size':24,
                         'iterations':15, 'seed':42, **kwargs})


def test_same_seed_identical_frames():
    first, second = simulate(make()), simulate(make())
    assert first.run_id != second.run_id
    assert first.frames == second.frames
    assert first.parameters == second.parameters


def test_nfe_and_flame_schedule():
    result = simulate(make(iterations=90))
    assert len(result.frames) == 91
    assert [f.function_evaluations for f in result.frames] == [24*(i+1) for i in range(91)]
    assert [f.flame_count for f in result.frames] == [24] + [_flame_count(24, i, 90) for i in range(1,91)]
    assert result.frames[-1].flame_count == 1
    assert all(a.flame_rank == 0 for a in result.frames[-1].agents)


def test_fitness_and_bounds_for_all_objectives():
    for obj_name in ('sphere','ackley','rastrigin','rosenbrock'):
        result = simulate(make(objective=obj_name,iterations=7))
        bests = [f.best_so_far for f in result.frames]
        assert all(a >= b - 1e-12 for a,b in zip(bests,bests[1:]))
        for f in result.frames:
            assert len(f.agents) == 24
            assert f.best_so_far <= f.current_best + 1e-8
            assert all(math.isfinite(x) for x in [f.best_so_far, f.diversity])
            for agent in f.agents:
                assert result.bounds[0] <= agent.x <= result.bounds[1]
                assert result.bounds[0] <= agent.y <= result.bounds[1]
                assert result.bounds[0] <= agent.flame_x <= result.bounds[1]
                assert result.bounds[0] <= agent.flame_y <= result.bounds[1]
                assert agent.fitness == pytest.approx(OBJECTIVES[obj_name].evaluate(agent.x,agent.y))
                assert 0 <= agent.flame_rank < f.flame_count


def test_first_spiral_step_is_recomputable_from_reported_flame_and_t():
    result = simulate(make(iterations=5, mfo_spiral_b=1.25))
    prev, next_frame = result.frames[:2]
    lo, hi = result.bounds
    for before, after in zip(prev.agents, next_frame.agents):
        t = np.array([after.spiral_t_x, after.spiral_t_y])
        flame = np.array([after.flame_x, after.flame_y])
        p = np.array([before.x,before.y])
        calculated = np.clip(flame+np.abs(flame-p)*np.exp(1.25*t)*np.cos(2*np.pi*t),lo,hi)
        assert np.allclose(calculated,[after.x, after.y], atol=1e-12)


def test_archive_merging_skips_duplicate_positions():
    old = np.array([[0.,0.],[1.,1.],[2.,2.]])
    incoming = np.array([[0.,0.],[.25,.25],[4.,4.]])
    pos, fitness = _merge_flames(old,np.array([0.,2.,8.]), incoming,
                                np.array([0.,.125,32.]), 3)
    assert len(pos) == len({tuple(x) for x in pos}) == 3
    assert fitness.tolist() == [0.,.125,2.]


def test_api_catalog_and_parameters():
    client = TestClient(app)
    assert next(a for a in client.get('/api/catalog').json()['algorithms'] if a['id']=='mfo')['status']=='ready'
    body = client.post('/api/simulations',json=make(iterations=3).model_dump())
    assert body.status_code == 200, body.text
    resp = body.json()
    assert resp['algorithm']=='mfo'
    assert resp['frames'][-1]['function_evaluations']==96
    assert resp['parameters']['mfo_spiral_b']==1.0
    assert resp['frames'][-1]['flame_count']==1


def test_invalid_spiral_rejected():
    client=TestClient(app)
    for bad in (0.,-1.,3.01,1e20):
        req=make().model_dump()
        req['mfo_spiral_b']=bad
        assert client.post('/api/simulations',json=req).status_code==422


def test_flames_monotonically_reduce():
    assert all(_flame_count(5,t,11)>=_flame_count(5,t+1,11) for t in range(11))
    assert _flame_count(5,0,11)==5 and _flame_count(5,11,11)==1
