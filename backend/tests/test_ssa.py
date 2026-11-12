"""SSA mathematical reconstruction, reproducibility, NFE and API contracts."""
import math

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import RunRequest
from app.objectives import OBJECTIVES
from app.optimizers.ssa import control_coefficient, simulate


def make(**overrides):
    fields = dict(algorithm='ssa', objective='sphere', population_size=24,
                  iterations=12, seed=42)
    fields.update(overrides)
    return RunRequest(**fields)


def test_deterministic_frames_parameters_and_unique_run_ids():
    first, second = simulate(make()), simulate(make())
    assert first.run_id != second.run_id
    assert first.frames == second.frames
    assert first.parameters == second.parameters


def test_frame_budget_and_nonincreasing_archival_best():
    result = simulate(make(iterations=90))
    assert len(result.frames) == 91
    assert [frame.function_evaluations for frame in result.frames] == [24*(i+1) for i in range(91)]
    assert all(x.best_so_far >= y.best_so_far for x,y in zip(result.frames,result.frames[1:]))
    assert all(len(frame.agents) == 24 for frame in result.frames)
    assert result.frames[-1].ssa_c1 < result.frames[1].ssa_c1


def test_leader_equation_reconstructs_using_frozen_food_and_random_draws():
    result=simulate(make(iterations=8))
    low,high=result.bounds
    for old_frame, new_frame in zip(result.frames, result.frames[1:]):
        leader=new_frame.agents[0]
        assert leader.ssa_role == 'leader'
        assert leader.ssa_previous == pytest.approx((old_frame.agents[0].x,old_frame.agents[0].y))
        assert leader.ssa_target == old_frame.best_position
        assert new_frame.ssa_food_position == old_frame.best_position
        assert leader.ssa_c2 is not None and leader.ssa_c3 is not None
        assert new_frame.ssa_c1 == pytest.approx(control_coefficient(new_frame.iteration,8,2))
        draw=np.array(leader.ssa_c2)
        sign=np.where(np.array(leader.ssa_c3)>=.5,1,-1)
        candidate=np.array(old_frame.best_position)+sign*new_frame.ssa_c1*((high-low)*draw+low)
        assert np.array([leader.x,leader.y]) == pytest.approx(np.clip(candidate,low,high))


def test_followers_use_old_self_and_new_predecessor_in_chain_order():
    result=simulate(make(iterations=6))
    for previous, current in zip(result.frames,result.frames[1:]):
        for i in range(1,24):
            member=current.agents[i]
            assert member.ssa_role == 'follower'
            assert member.target_id == i-1
            assert member.ssa_previous == pytest.approx((previous.agents[i].x,previous.agents[i].y))
            predecessor=current.agents[i-1]
            assert member.ssa_target == pytest.approx((predecessor.x,predecessor.y))
            expected=(np.array([previous.agents[i].x,previous.agents[i].y])+
                      np.array([predecessor.x,predecessor.y]))*.5
            assert [member.x,member.y] == pytest.approx(expected)
            assert member.ssa_c2 is None and member.ssa_c3 is None


def test_chain_length_and_leader_distance_accurate():
    run=simulate(make(iterations=4))
    for frame in run.frames:
        coords=np.array([[a.x,a.y] for a in frame.agents])
        assert frame.ssa_chain_length == pytest.approx(np.linalg.norm(np.diff(coords,axis=0),axis=1).sum())
        assert frame.ssa_leader_distance == pytest.approx(np.linalg.norm(coords[0]-np.array(frame.ssa_food_position)))


def test_all_objectives_respect_bounds_and_fitness():
    for name in ('sphere','rastrigin','ackley','rosenbrock'):
        run=simulate(make(objective=name,iterations=6))
        for frame in run.frames:
            assert math.isfinite(frame.best_so_far)
            for a in frame.agents:
                assert run.bounds[0]<=a.x<=run.bounds[1]
                assert run.bounds[0]<=a.y<=run.bounds[1]
                assert a.fitness == pytest.approx(OBJECTIVES[name].evaluate(a.x,a.y))


def test_parameter_variation_changes_trajectory():
    first=simulate(make(ssa_c1_initial=1))
    second=simulate(make(ssa_c1_initial=3))
    assert first.frames[2].agents != second.frames[2].agents


def test_small_population_and_one_generation():
    run=simulate(make(population_size=5,iterations=1))
    assert len(run.frames)==2
    assert run.frames[1].function_evaluations==10
    assert run.frames[1].ssa_c1 == pytest.approx(2*np.exp(-16))


def test_api_catalog_version_and_input_validation():
    client=TestClient(app)
    assert client.get('/api/health').json()['version']=='3.0.0'
    algo=next(x for x in client.get('/api/catalog').json()['algorithms'] if x['id']=='ssa')
    assert algo['status']=='ready'
    response=client.post('/api/simulations',json=make(iterations=3).model_dump())
    assert response.status_code==200,response.text
    obj=response.json()
    assert obj['algorithm']=='ssa'
    assert obj['frames'][-1]['function_evaluations']==24*4
    assert obj['frames'][1]['agents'][0]['ssa_c2'] is not None
    assert obj['parameters']['ssa_c1_initial']==2.0
    for value in (-1,0,.24,3.01):
        payload=make().model_dump()
        payload['ssa_c1_initial']=value
        assert client.post('/api/simulations',json=payload).status_code==422
