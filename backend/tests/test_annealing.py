"""Regression and algebraic validation of the SA simulation contract."""
import math

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import RunRequest
from app.optimizers.annealing import metropolis_probability, simulate, temperature_at


def req(**kw):
    defaults = dict(algorithm='sa', objective='sphere', iterations=90,
                    sa_initial_temperature=10, sa_cooling_rate=.95,
                    sa_step_scale=.10, seed=42)
    defaults.update(kw)
    return RunRequest(**defaults)


def test_temperature_schedule_exact():
    assert temperature_at(0, 10, .95) == 10
    assert temperature_at(1, 10, .95) == 10
    assert temperature_at(2, 10, .95) == pytest.approx(9.5)
    assert temperature_at(90, 10, .95) == pytest.approx(10 * .95 ** 89)


def test_metropolis_acceptance_and_overflow_safe():
    assert metropolis_probability(-1, 1) == 1
    assert metropolis_probability(0, 1) == 1
    assert metropolis_probability(2, 4) == pytest.approx(math.exp(-.5))
    assert metropolis_probability(1e6, 1e-4) == 0


def test_metropolis_invalid_params_rejected():
    for delta, temperature in [(1, 0), (float('nan'), 1), (1, float('inf'))]:
        with pytest.raises(ValueError):
            metropolis_probability(delta, temperature)
    with pytest.raises(ValueError):
        temperature_at(-1, 10, .95)


def test_frames_deterministic_and_explicit_config():
    first, second = simulate(req()), simulate(req())
    assert [f.model_dump() for f in first.frames] == [f.model_dump() for f in second.frames]
    assert first.run_id != second.run_id
    assert first.parameters['sa_initial_temperature'] == 10


def test_one_evaluation_per_proposal_and_no_population():
    result = simulate(req(iterations=40))
    assert len(result.frames) == 41
    for i, frame in enumerate(result.frames):
        assert frame.function_evaluations == i + 1
        assert frame.iteration == i
        assert len(frame.agents) == 1
        assert frame.diversity == 0


def test_saved_probability_and_acceptance_are_recomputable():
    result = simulate(req())
    accepted_worse = 0
    rejected = 0
    for old, current in zip(result.frames, result.frames[1:]):
        a = current.agents[0]
        assert a.sa_previous == pytest.approx((old.agents[0].x, old.agents[0].y))
        assert a.sa_delta == pytest.approx(a.sa_candidate_fitness - old.current_best)
        assert a.sa_accept_probability == pytest.approx(metropolis_probability(a.sa_delta, current.sa_temperature))
        assert a.sa_accepted == (a.sa_accept_draw < a.sa_accept_probability)
        assert a.sa_accepted is not None
        if a.sa_accepted:
            assert (a.x, a.y) == pytest.approx(a.sa_candidate)
        else:
            rejected += 1
            assert (a.x, a.y) == pytest.approx(a.sa_previous)
        accepted_worse += int(a.sa_accepted and a.sa_delta > 0)
    assert result.frames[-1].sa_uphill_accepted_total == accepted_worse
    assert result.frames[-1].sa_rejected_total == rejected
    assert result.frames[-1].sa_accepted_total + rejected == 90
    assert accepted_worse > 0 and rejected > 0


def test_candidate_matches_saved_gaussian_step_and_clipping():
    result = simulate(req())
    low, high = result.bounds
    for f in result.frames[1:]:
        a=f.agents[0]
        expected = np.clip(np.array(a.sa_previous) + np.array(a.sa_step), low, high)
        assert a.sa_candidate == pytest.approx(expected)
        assert a.sa_candidate_fitness == pytest.approx(sum(v*v for v in expected))
        assert low <= a.x <= high and low <= a.y <= high


def test_archive_never_increases_and_current_can_increase():
    result = simulate(req())
    records = [f.best_so_far for f in result.frames]
    assert records == sorted(records, reverse=True)
    assert all(f.best_so_far <= f.current_best + 1e-14 for f in result.frames)
    assert result.frames[-1].sa_uphill_accepted_total > 0
    assert any(b.current_best > a.current_best for a,b in zip(result.frames,result.frames[1:]))


def test_all_objectives_finite_and_bounded():
    for objective in ['sphere', 'rastrigin', 'ackley', 'rosenbrock']:
        result = simulate(req(objective=objective, iterations=7))
        assert math.isfinite(result.frames[-1].best_so_far)
        lo,hi=result.bounds
        assert all(lo <= a.x <= hi and lo <= a.y <= hi for f in result.frames for a in f.agents)


def test_sa_api_contract_and_catalog_ready():
    client = TestClient(app)
    ready=[a['id'] for a in client.get('/api/catalog').json()['algorithms'] if a['status']=='ready']
    assert len(ready) == 15 and ready[-1]=='de'
    assert client.get('/api/health').json()['version']=='3.0.0'
    res=client.post('/api/simulations',json={'algorithm':'sa','objective':'sphere','iterations':5,'seed':42})
    assert res.status_code==200,res.text
    assert res.json()['frames'][-1]['function_evaluations']==6
    assert res.json()['parameters']['sa_cooling_rate']==0.95


def test_invalid_sa_parameters_are_rejected():
    client=TestClient(app)
    for field,value in [('sa_initial_temperature',0),('sa_cooling_rate',0),
                        ('sa_cooling_rate',1.01),('sa_step_scale',0),
                        ('sa_step_scale',2)]:
        res=client.post('/api/simulations',json={'algorithm':'sa',field:value})
        assert res.status_code==422,(field,res.text)
