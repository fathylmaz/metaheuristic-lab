"""BA deterministic data, mathematical branches, evaluation honesty and API validation."""
import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import RunRequest
from app.objectives import OBJECTIVES
from app.optimizers.bat import _pulse_schedule, simulate


def make(**overrides):
    config = dict(algorithm='ba', objective='sphere', population_size=24,
                  iterations=12, seed=42)
    config.update(overrides)
    return RunRequest(**config)


def test_reproducible_every_agent_frame_and_parameters():
    first, second = simulate(make()), simulate(make())
    assert first.run_id != second.run_id
    assert first.frames == second.frames
    assert first.parameters == second.parameters


def test_exact_budget_archival_best_and_population():
    result = simulate(make(iterations=90))
    assert len(result.frames) == 91
    assert [f.function_evaluations for f in result.frames] == [24*(i+1) for i in range(91)]
    assert all(a.best_so_far >= b.best_so_far for a,b in zip(result.frames, result.frames[1:]))
    assert all(len(f.agents) == 24 for f in result.frames)
    assert result.frames[0].ba_local_proposals == 0
    assert all(f.ba_global_proposals + f.ba_local_proposals == 24 for f in result.frames[1:])
    assert all(0 <= f.ba_accepted_count <= 24 for f in result.frames)


def test_frequency_velocity_local_candidate_and_acceptance_reconstructable():
    result = simulate(make(iterations=8))
    kinds = set()
    for previous, current in zip(result.frames, result.frames[1:]):
        for bat in current.agents:
            prior = previous.agents[bat.id]
            kinds.add(bat.ba_move_kind)
            old = np.array([prior.x, prior.y])
            assert bat.ba_previous == pytest.approx(old)
            assert 0 <= bat.ba_frequency <= 2
            expected_velocity = np.array([prior.vx, prior.vy]) + (old - np.array(previous.best_position))*bat.ba_frequency
            assert [bat.vx, bat.vy] == pytest.approx(expected_velocity)
            candidate = np.array(bat.ba_candidate)
            assert bat.ba_reference_best == previous.best_position
            if bat.ba_move_kind == 'local':
                assert bat.ba_local_epsilon is not None
                expected = np.array(previous.best_position) + np.array(bat.ba_local_epsilon)*bat.ba_mean_loudness
                assert bat.ba_pulse_draw > prior.ba_pulse_rate
            else:
                assert bat.ba_local_epsilon is None
                expected = old + expected_velocity
                assert bat.ba_pulse_draw <= prior.ba_pulse_rate
            assert candidate == pytest.approx(np.clip(expected,*result.bounds))
            assert bat.ba_candidate_fitness == pytest.approx(OBJECTIVES['sphere'].evaluate(*candidate))
            expected_accepted = bat.ba_candidate_fitness < prior.fitness and bat.ba_accept_draw < prior.ba_loudness
            assert bat.ba_accepted == expected_accepted
            if bat.ba_accepted:
                assert [bat.x, bat.y] == pytest.approx(candidate)
                assert bat.ba_loudness == pytest.approx(prior.ba_loudness * result.parameters['ba_loudness_decay'])
                assert bat.ba_pulse_rate == pytest.approx(_pulse_schedule(result.parameters['ba_initial_pulse_rate'], result.parameters['ba_pulse_growth'],current.iteration))
            else:
                assert [bat.x, bat.y] == pytest.approx(old)
                assert bat.ba_loudness == pytest.approx(prior.ba_loudness)
                assert bat.ba_pulse_rate == pytest.approx(prior.ba_pulse_rate)
    assert kinds == {'global', 'local'}


def test_candidates_rejected_still_count_as_nfe():
    result = simulate(make(ba_initial_loudness=0.01, iterations=5))
    assert result.frames[-1].function_evaluations == 24*6
    assert any(a.ba_accepted is False for f in result.frames[1:] for a in f.agents)


def test_all_objectives_bounded_and_finite():
    for objective in ('sphere','rastrigin','ackley','rosenbrock'):
        result = simulate(make(objective=objective, iterations=5))
        for frame in result.frames:
            assert math.isfinite(frame.best_so_far)
            assert math.isfinite(frame.ba_mean_loudness)
            for a in frame.agents:
                assert result.bounds[0] <= a.x <= result.bounds[1]
                assert result.bounds[0] <= a.y <= result.bounds[1]
                assert a.fitness == pytest.approx(OBJECTIVES[objective].evaluate(a.x,a.y))


def test_control_parameter_change_affects_trajectory():
    a = simulate(make(ba_frequency_max=1))
    b = simulate(make(ba_frequency_max=3))
    assert a.frames[2].agents != b.frames[2].agents


def test_pulse_schedule_and_one_step_small_population():
    assert _pulse_schedule(0.5, 0.9, 0) == 0
    assert _pulse_schedule(0.5, 0.9, 100) == pytest.approx(.5)
    result = simulate(make(iterations=1,population_size=5))
    assert result.frames[-1].function_evaluations == 10
    assert result.frames[1].ba_global_proposals+result.frames[1].ba_local_proposals == 5


def test_api_catalog_response_and_version():
    client = TestClient(app)
    assert client.get('/api/health').json()['version'] == '3.0.0'
    entry = next(x for x in client.get('/api/catalog').json()['algorithms'] if x['id']=='ba')
    assert entry['status'] == 'ready'
    response = client.post('/api/simulations', json=make(iterations=3).model_dump())
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['algorithm'] == 'ba'
    assert data['frames'][-1]['function_evaluations'] == 24*4
    assert data['frames'][1]['agents'][0]['ba_frequency'] is not None
    assert data['parameters']['ba_frequency_max'] == 2


def test_invalid_parameters_return_422():
    client = TestClient(app)
    for field, value in [('ba_frequency_min',-1), ('ba_frequency_max',5.1),
                         ('ba_initial_loudness',0), ('ba_loudness_decay',0),
                         ('ba_initial_pulse_rate',1.1), ('ba_pulse_growth',0)]:
        request=make().model_dump()
        request[field]=value
        assert client.post('/api/simulations',json=request).status_code == 422
    assert client.post('/api/simulations',json=make(ba_frequency_min=3,ba_frequency_max=2).model_dump()).status_code == 422
