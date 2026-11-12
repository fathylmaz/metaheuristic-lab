"""SMA auditability, original-style update branches, and API contracts."""
import numpy as np
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models import RunRequest
from app.objectives import OBJECTIVES
from app.optimizers.sma import adaptive_weights, control_coefficients, simulate


def request(**overrides):
    base = dict(algorithm='sma', objective='sphere', population_size=24,
                iterations=8, seed=42, sma_restart_probability=0.03)
    base.update(overrides)
    return RunRequest(**base)


def test_reproducibility_full_frames_and_parameters():
    a, b = simulate(request()), simulate(request())
    assert a.run_id != b.run_id
    assert a.frames == b.frames
    assert a.parameters == b.parameters
    assert a.variant == b.variant


def test_evaluation_budget_and_archived_best_monotone():
    r = simulate(request(iterations=90))
    assert len(r.frames) == 91
    assert [f.function_evaluations for f in r.frames] == [24*(i+1) for i in range(91)]
    assert all(f.best_so_far >= g.best_so_far for f,g in zip(r.frames,r.frames[1:]))
    assert all(len(f.agents) == 24 for f in r.frames)
    assert all(f.sma_restart_count+f.sma_approach_count+f.sma_contract_count==24 for f in r.frames[1:])
    assert r.frames[0].sma_restart_count == 0


def test_all_equations_reconstruct_clipped_positions():
    r = simulate(request(sma_restart_probability=.2))
    low,high=r.bounds
    modes=set()
    for old,new in zip(r.frames,r.frames[1:]):
        for i,agent in enumerate(new.agents):
            modes.add(agent.sma_move_kind)
            assert agent.sma_previous == pytest.approx((old.agents[i].x,old.agents[i].y))
            assert agent.sma_best_reference == pytest.approx(old.best_position)
            assert agent.sma_source_a_position == pytest.approx((old.agents[agent.sma_source_a].x,old.agents[agent.sma_source_a].y))
            assert agent.sma_source_b_position == pytest.approx((old.agents[agent.sma_source_b].x,old.agents[agent.sma_source_b].y))
            assert agent.sma_source_a != agent.sma_source_b
            assert agent.sma_weight is not None
            assert agent.sma_probability == pytest.approx(np.tanh(abs(old.agents[i].fitness-old.best_so_far)))
            assert agent.sma_restart_draw is not None
            assert agent.sma_branch_draw is not None
            if agent.sma_move_kind=='restart':
                assert agent.sma_restart_draw < r.parameters['sma_restart_probability']
                expected=np.array(agent.sma_raw_position)
            elif agent.sma_move_kind=='approach':
                assert agent.sma_restart_draw >= r.parameters['sma_restart_probability']
                assert agent.sma_branch_draw < agent.sma_probability
                expected=(np.array(agent.sma_best_reference)+np.array(agent.sma_vb)*
                          (agent.sma_weight*np.array(agent.sma_source_a_position)-np.array(agent.sma_source_b_position)))
            else:
                assert agent.sma_move_kind=='contract'
                assert agent.sma_restart_draw >= r.parameters['sma_restart_probability']
                assert agent.sma_branch_draw >= agent.sma_probability
                expected=np.array(agent.sma_vc)*np.array(agent.sma_previous)
            assert agent.sma_raw_position == pytest.approx(expected)
            assert [agent.x,agent.y] == pytest.approx(np.clip(expected,low,high))
    assert modes == {'restart','approach','contract'}


def test_ranks_weights_and_equal_fitness_guard():
    fitness=np.array([1.,2.,3.,4.,5.,6.])
    weights=adaptive_weights(fitness,np.ones(6))
    assert np.all(weights[:3]>=1)
    assert np.all(weights[3:]<=1)
    assert weights[0]>weights[1]>weights[2]
    assert weights[3]<weights[4] or weights[3] == pytest.approx(weights[4])  # lower-ranked nearer the bottom
    assert np.allclose(adaptive_weights(np.ones(6),np.ones(6)),np.ones(6))


def test_schedule_finite_shrinking():
    early=control_coefficients(1,90)
    late=control_coefficients(90,90)
    assert early[0]>0 and early[1]>0
    assert late==(0.,0.)
    assert early[0]>control_coefficients(10,90)[0]
    with pytest.raises(ValueError): control_coefficients(0,90)


def test_restart_probability_one_and_zero():
    all_restart=simulate(request(sma_restart_probability=1))
    assert all(f.sma_restart_count==24 for f in all_restart.frames[1:])
    assert all(f.sma_approach_count==f.sma_contract_count==0 for f in all_restart.frames[1:])
    no_restart=simulate(request(sma_restart_probability=0))
    assert all(f.sma_restart_count==0 for f in no_restart.frames[1:])


def test_objective_bounds_and_fitness():
    for name in OBJECTIVES:
        result=simulate(request(objective=name))
        lo,hi=result.bounds
        for frame in result.frames:
            for a in frame.agents:
                assert lo <= a.x <= hi and lo <= a.y <= hi
                assert a.fitness == pytest.approx(OBJECTIVES[name].evaluate(a.x,a.y))
                assert 0<=a.brightness<=1
            assert np.isfinite(frame.mean_fitness)
            assert np.isfinite(frame.sma_mean_weight)


def test_invalid_probability_rejected():
    with pytest.raises(ValidationError): request(sma_restart_probability=-.1)
    with pytest.raises(ValidationError): request(sma_restart_probability=1.1)


def test_api_catalog_and_simulation():
    api=TestClient(app)
    assert api.get('/api/health').json()['version']=='3.0.0'
    catalog=api.get('/api/catalog').json()
    assert next(x for x in catalog['algorithms'] if x['id']=='sma')['status']=='ready'
    response=api.post('/api/simulations',json=request().model_dump())
    assert response.status_code==200
    result=response.json()
    assert result['algorithm']=='sma' and len(result['frames'])==9
    assert result['frames'][-1]['sma_mean_weight'] is not None
    assert result['parameters']['sma_restart_probability']==.03


def test_json_serialization_never_infinite():
    result=simulate(request(iterations=90,sma_restart_probability=0))
    assert result.model_dump_json(exclude_none=False)
    assert all(np.isfinite(f.sma_a) for f in result.frames)
