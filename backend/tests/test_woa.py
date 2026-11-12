"""WOA equations, reproducibility, honest NFE and telemetry/API contract."""
import math

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import RunRequest
from app.objectives import OBJECTIVES
from app.optimizers.woa import _a, simulate


def make(**kwargs):
    values = dict(algorithm='woa', objective='sphere', population_size=24,
                  iterations=12, seed=42)
    values.update(kwargs)
    return RunRequest(**values)


def test_same_seed_same_entire_history():
    first, second = simulate(make()), simulate(make())
    assert first.run_id != second.run_id
    assert first.frames == second.frames
    assert first.parameters == second.parameters


def test_frames_evaluations_counts_and_archive():
    run = simulate(make(iterations=90))
    assert len(run.frames) == 91
    assert [f.function_evaluations for f in run.frames] == [24 * (i+1) for i in range(91)]
    assert all(a.best_so_far >= b.best_so_far for a,b in zip(run.frames, run.frames[1:]))
    assert run.frames[0].woa_search_count == run.frames[0].woa_encircle_count == run.frames[0].woa_spiral_count == 0
    assert all(f.woa_search_count+f.woa_encircle_count+f.woa_spiral_count == 24 for f in run.frames[1:])
    assert run.frames[1].woa_a == pytest.approx(2.0)
    assert run.frames[-1].woa_a == pytest.approx(0.0)
    assert run.frames[-1].woa_search_count == 0


def test_formulas_match_stored_coefficient_and_previous_state():
    run = simulate(make(iterations=12))
    kinds = set()
    for previous, frame in zip(run.frames, run.frames[1:]):
        for whale in frame.agents:
            kinds.add(whale.woa_move_kind)
            old = np.array([previous.agents[whale.id].x, previous.agents[whale.id].y])
            assert whale.woa_previous == pytest.approx(old)
            target = np.asarray(whale.woa_target)
            assert target.shape == (2,)
            if whale.woa_move_kind == 'spiral':
                assert whale.woa_l is not None
                assert whale.woa_target == previous.best_position
                assert whale.woa_A is None and whale.woa_C is None
                expect = target + np.abs(target-old)*np.exp(run.parameters['woa_spiral_b']*whale.woa_l)*np.cos(2*np.pi*whale.woa_l)
            else:
                assert whale.woa_A is not None and whale.woa_C is not None
                A,C = np.array(whale.woa_A), np.array(whale.woa_C)
                expect = target - A * np.abs(C*target-old)
                if whale.woa_move_kind == 'search':
                    assert whale.woa_target_id != whale.id
                    peer = previous.agents[whale.woa_target_id]
                    assert whale.woa_target == (peer.x,peer.y)
                    assert max(abs(A)) >= 1
                else:
                    assert whale.woa_target == previous.best_position
                    assert max(abs(A)) < 1
            assert [whale.x, whale.y] == pytest.approx(np.clip(expect,*run.bounds))
    assert kinds == {'search','encircle','spiral'}


def test_four_functions_fitness_and_bounds():
    for objective in ('sphere','rastrigin','ackley','rosenbrock'):
        run = simulate(make(objective=objective, iterations=6))
        for frame in run.frames:
            assert math.isfinite(frame.diversity)
            assert math.isfinite(frame.best_so_far)
            for a in frame.agents:
                assert run.bounds[0] <= a.x <= run.bounds[1]
                assert run.bounds[0] <= a.y <= run.bounds[1]
                assert a.fitness == pytest.approx(OBJECTIVES[objective].evaluate(a.x,a.y))


def test_probability_extremes_and_schedule():
    assert [_a(i,5,2) for i in range(1,6)] == [2,1.5,1,.5,0]
    assert _a(1,1,2) == 0
    spiral = simulate(make(woa_spiral_probability=1))
    assert all(f.woa_spiral_count==24 for f in spiral.frames[1:])
    encircle_family = simulate(make(woa_spiral_probability=0))
    assert all(f.woa_spiral_count==0 for f in encircle_family.frames[1:])
    assert any(f.woa_search_count>0 for f in encircle_family.frames[1:])


def test_parameter_changes_change_search_trajectory():
    first=simulate(make(woa_spiral_b=1))
    second=simulate(make(woa_spiral_b=2.5))
    assert first.frames[1].agents != second.frames[1].agents


def test_single_iteration_no_search_no_nan():
    run=simulate(make(iterations=1,population_size=5))
    assert len(run.frames)==2
    assert run.frames[-1].function_evaluations==10
    assert run.frames[-1].woa_search_count==0


def test_api_catalog_and_metadata():
    client=TestClient(app)
    assert client.get('/api/health').json()['version']=='3.0.0'
    entry=next(x for x in client.get('/api/catalog').json()['algorithms'] if x['id']=='woa')
    assert entry['status']=='ready'
    response=client.post('/api/simulations',json=make(iterations=3).model_dump())
    assert response.status_code==200,response.text
    value=response.json()
    assert value['algorithm']=='woa'
    assert value['parameters']['woa_spiral_b']==1.0
    assert value['frames'][-1]['function_evaluations']==96
    assert value['frames'][1]['agents'][0]['woa_previous'] is not None


def test_bad_params_fail_validation():
    client=TestClient(app)
    for key,bad in (('woa_spiral_b',0),('woa_spiral_b',3.5),
                    ('woa_initial_a',0),('woa_initial_a',3.5),
                    ('woa_spiral_probability',-0.1),('woa_spiral_probability',1.1)):
        data=make().model_dump()
        data[key]=bad
        assert client.post('/api/simulations',json=data).status_code==422
