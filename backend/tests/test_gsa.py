"""Mathematical regression and telemetry checks for Gravitational Search Algorithm."""
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import RunRequest
from app.optimizers.gravitational import (
    VARIANT, force_acceleration, gravity, kbest_count, normalized_masses, simulate,
)

CLIENT = TestClient(app)


def config(**kwargs):
    return RunRequest(algorithm='gsa', objective='sphere', population_size=24,
                      iterations=90, seed=42, **kwargs)


def test_mass_normalization_minimization_and_ties():
    np.testing.assert_allclose(normalized_masses(np.array([0., 1., 2.])), [2/3, 1/3, 0])
    np.testing.assert_allclose(normalized_masses(np.ones(3)), [1/3]*3)
    np.testing.assert_allclose(normalized_masses(np.array([10., 10., 10.])), [1/3]*3)
    with pytest.raises(ValueError):
        normalized_masses(np.array([1., np.nan]))


def test_gravity_and_elite_schedule_endpoints():
    assert gravity(0, 90, 100, 20) == pytest.approx(100)
    assert gravity(90, 90, 100, 20) == pytest.approx(100*np.exp(-20))
    assert kbest_count(0, 90, 24) == 24
    assert kbest_count(90, 90, 24) == 1
    assert all(kbest_count(t+1, 90, 24) <= kbest_count(t, 90, 24) for t in range(90))


class HalfRng:
    def random(self, count):
        return np.full(count, 0.5)


def test_newtonian_acceleration_and_dominant_target():
    pos=np.array([[0.,0.],[2.,0.],[0.,3.]])
    mass=np.array([.4,.6,0.])
    force, acceleration, targets, target_positions=force_acceleration(pos,mass,2,10,1,HalfRng())
    # Force on #0 due to #1: 0.5 * G * M0 * M1 / (2+1) * (2,0).
    np.testing.assert_allclose(force[0], [0.8,0])
    np.testing.assert_allclose(acceleration[0], [2,0])
    np.testing.assert_allclose(force[1], [-0.8,0])
    np.testing.assert_allclose(acceleration[1], [-0.8/.6,0])
    np.testing.assert_allclose(acceleration[2], [0,0])
    assert targets[:2] == [1,0]
    assert target_positions[0] == (2.,0.)


def test_determinism_ignoring_uuid_and_runtime():
    first,second=simulate(config()),simulate(config())
    assert first.run_id != second.run_id
    assert first.frames == second.frames
    assert first.variant == VARIANT


def test_true_evaluation_count_bounds_and_archive():
    run=simulate(config())
    assert len(run.frames) == 91
    assert len(run.frames[-1].agents) == 24
    assert [frame.function_evaluations for frame in run.frames] == [24*(i+1) for i in range(91)]
    assert all(-5.12<=a.x<=5.12 and -5.12<=a.y<=5.12 for f in run.frames for a in f.agents)
    assert all(run.frames[i].best_so_far <= run.frames[i-1].best_so_far + 1e-12 for i in range(1,91))
    assert all(f.gsa_max_mass==pytest.approx(max(a.gsa_mass for a in f.agents)) for f in run.frames)
    assert all(sum(a.gsa_mass for a in f.agents)==pytest.approx(1) for f in run.frames)


def test_force_velocity_position_telemetry_reconstructs_every_move():
    run=simulate(config())
    low,high=run.bounds
    for old,new in zip(run.frames[:-1],run.frames[1:]):
        for current,agent in zip(old.agents,new.agents):
            assert agent.gsa_previous == pytest.approx((current.x,current.y))
            assert agent.gsa_previous_velocity == pytest.approx((current.vx,current.vy))
            assert agent.gsa_force_mass == pytest.approx(current.gsa_mass)
            force=np.array(agent.gsa_force)
            acc=force/max(agent.gsa_force_mass,1e-12)
            np.testing.assert_allclose(acc,agent.gsa_acceleration,atol=1e-9,rtol=1e-7)
            proposed_v = np.array(agent.gsa_velocity_draw)*np.array(agent.gsa_previous_velocity)+acc
            proposed_position=np.array(agent.gsa_previous)+proposed_v
            actual=np.clip(proposed_position,low,high)
            np.testing.assert_allclose(actual,[agent.x,agent.y],atol=1e-9,rtol=1e-7)
            expected_velocity=np.where(actual!=proposed_position,0,proposed_v)
            np.testing.assert_allclose(expected_velocity,[agent.vx,agent.vy],atol=1e-9,rtol=1e-7)


def test_actual_position_fitness_and_finite_telemetry():
    run=simulate(config())
    for frame in run.frames:
        assert frame.gsa_gravity >= 0
        assert frame.gsa_mean_acceleration >= 0
        assert np.isfinite(frame.gsa_mean_acceleration)
        for agent in frame.agents:
            assert agent.fitness == pytest.approx(agent.x**2+agent.y**2)
            assert 0<=agent.gsa_mass<=1
            if agent.gsa_attractor is not None:
                assert agent.target_id is not None


def test_other_benchmark_functions():
    for objective in ['sphere','rastrigin','ackley','rosenbrock']:
        run=simulate(RunRequest(
            algorithm='gsa',objective=objective,population_size=10,iterations=9,seed=42))
        assert run.frames[-1].function_evaluations == 100
        assert np.isfinite(run.frames[-1].best_so_far)


def test_api_contract_and_ready_catalog():
    assert CLIENT.get('/api/health').json()['version']=='3.0.0'
    algos=CLIENT.get('/api/catalog').json()['algorithms']
    assert len([a for a in algos if a['status']=='ready']) == 15
    assert next(a for a in algos if a['id']=='gsa')['status']=='ready'
    response=CLIENT.post('/api/simulations',json={'algorithm':'gsa','objective':'sphere','iterations':5,'seed':42})
    assert response.status_code==200,response.text
    data=response.json()
    assert len(data['frames'])==6
    assert data['parameters']['gsa_initial_gravity']==100
    assert 'GSA' in data['variant']


def test_api_rejects_invalid_gsa_settings():
    for key,val in [('gsa_initial_gravity',0),('gsa_initial_gravity',1000),
                    ('gsa_decay',-1),('gsa_decay',41),('gsa_epsilon',0),('gsa_epsilon',1e-10),('gsa_epsilon',1.1)]:
        res=CLIENT.post('/api/simulations',json={'algorithm':'gsa',key:val})
        assert res.status_code==422,(key,val,res.text)
