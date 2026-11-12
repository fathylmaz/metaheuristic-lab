"""v2.4 true D-dimensional FA / BA / GSA, no synthetic evaluation counts."""
import numpy as np
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.dimensional import (
    DimensionalRequest, _fa_generation, _ba_generation, _gsa_generation,
    _gsa_masses, objective_nd, run_dimensional,
)
from app.main import app


@pytest.mark.parametrize('algorithm', ['fa', 'ba', 'gsa'])
@pytest.mark.parametrize('dimensions', [2, 10, 30])
def test_deterministic_real_nd_with_exact_evaluations(algorithm, dimensions):
    cfg = DimensionalRequest(algorithms=[algorithm, 'pso'], dimensions=dimensions,
                             objective='sphere', population_size=12, iterations=12, trials=2)
    a, b = run_dimensional(cfg), run_dimensional(cfg)
    assert a.total_evaluations == 12*13*2*2
    first, second = a.groups[0], b.groups[0]
    for trial, repeat in zip(first.trials, second.trials):
        assert trial.trajectory == repeat.trajectory
        assert len(trial.best_position) == dimensions
        assert len(trial.trajectory) == 13
        assert trial.function_evaluations == 156
        assert [p.evaluations for p in trial.trajectory] == [12*k for k in range(1,14)]
        assert all(u.best_error >= v.best_error for u, v in zip(trial.trajectory, trial.trajectory[1:]))
        assert all(len(p.best_position) == dimensions for p in trial.trajectory)
        assert np.isclose(objective_nd('sphere', np.array(trial.best_position))[0],
                          trial.best_error, rtol=1e-9, atol=1e-10)
        assert all(-5.12 <= v <= 5.12 for v in trial.best_position)


@pytest.mark.parametrize('algorithm', ['fa','ba','gsa'])
@pytest.mark.parametrize('objective', ['rastrigin','ackley','rosenbrock','griewank'])
def test_new_algorithms_objectives_finite(algorithm, objective):
    cfg = DimensionalRequest(algorithms=[algorithm,'de'], dimensions=10, objective=objective,
                             population_size=10, iterations=8, trials=2)
    trial = run_dimensional(cfg).groups[0].trials[0]
    assert np.isfinite(trial.best_error) and trial.best_error >= 0
    assert len(trial.best_position) == 10


def test_fa_all_equal_brightness_explores_once_per_firefly():
    points = np.array([[.5,-.5, .1], [-.7,.2, -.3], [.2,.1, .2]])
    rng = np.random.default_rng(7)
    out = _fa_generation(points,np.zeros(3),rng,.2,1.,.1,-2.,2.)
    expected = np.clip(points + .2*4*(np.random.default_rng(7).random((3,3))-.5),-2,2)
    np.testing.assert_allclose(out,expected)


def test_fa_sequential_attraction_and_random_offset_equation():
    points = np.array([[1.,1.],[.0,.0],[.5,.5]])
    fitness = np.array([2.,0.,.5])
    seed = 13
    observed = _fa_generation(points,fitness,np.random.default_rng(seed),.1,1.,.2,-3,3)
    check = np.random.default_rng(seed)
    expected = []
    for i in range(3):
        working = points[i].copy()
        attracted = False
        for j in range(3):
            if fitness[j] >= fitness[i]: continue
            delta=points[j]-working
            beta=np.exp(-.2*np.dot(delta,delta))
            working=np.clip(working+beta*delta+.1*6*(check.random(2)-.5),-3,3)
            attracted=True
        if not attracted:
            working=np.clip(working+.1*6*(check.random(2)-.5),-3,3)
        expected.append(working)
    np.testing.assert_allclose(observed,expected)


def test_bat_rejects_all_when_acceptance_probability_cannot_win():
    cfg = DimensionalRequest(algorithms=['ba','gwo'],objective='sphere',
        ba_min_frequency=0,ba_max_frequency=2,ba_initial_loudness=.01)
    old=np.array([[1.,-.3], [.6,.5]])
    fit=objective_nd('sphere',old)
    vel=np.zeros_like(old)
    loud=np.full(2,.01)
    pulse=np.zeros(2)
    newpos,newvel,newfit,newloud,newpulse,candidates,accepted = _ba_generation(
        old,vel,fit,np.array([0.,0.]),loud,pulse,np.random.default_rng(2),cfg,1,-5.12,5.12)
    assert np.array_equal(newpos,old)
    assert np.array_equal(newfit,fit)
    assert np.array_equal(newloud,loud)
    assert np.array_equal(newpulse,pulse)
    assert accepted.sum()==0
    assert candidates.shape == old.shape
    assert np.any(newvel!=0)


def test_bat_accepts_better_global_reference_with_high_loudness():
    cfg = DimensionalRequest(algorithms=['ba','gwo'],objective='sphere',
        ba_min_frequency=0,ba_max_frequency=1,
        ba_initial_loudness=1,ba_initial_pulse_rate=.5,ba_loudness_decay=.9)
    old=np.array([[4.,4.],[-2.,-2.]])
    fit=objective_nd('sphere',old)
    vel=np.zeros_like(old)
    loud=np.ones(2)
    pulse=np.zeros(2)
    out = _ba_generation(old,vel,fit,np.zeros(2),loud,pulse,np.random.default_rng(3),cfg,2,-5.12,5.12)
    newpos,newvel,newfit,newloud,newpulse,candidates,accepted = out
    assert np.all(accepted)
    assert np.all(newfit < fit)
    np.testing.assert_allclose(newfit, objective_nd('sphere',newpos))
    np.testing.assert_allclose(newloud, np.full(2,.9))
    np.testing.assert_allclose(newpulse, np.full(2,.5*(1-np.exp(-.9*2))))
    assert candidates.shape==(2,2)


def test_gsa_normalized_masses_and_equal_fitness():
    np.testing.assert_allclose(_gsa_masses(np.array([0.,1.,2.])),np.array([2./3.,1./3.,0.]))
    np.testing.assert_allclose(_gsa_masses(np.ones(5)),np.ones(5)/5)


def test_gsa_recomputed_force_and_velocity_with_fixed_random_draws():
    cfg=DimensionalRequest(algorithms=['gsa','pso'],dimensions=5,gsa_initial_gravity=20,
        gsa_decay=1,gsa_epsilon=.05,iterations=10)
    n,d=4,5
    old=np.linspace(-1,1,n*d).reshape(n,d)
    v=np.ones_like(old)*.02
    f=np.array([.1,.4,.7,1.2])
    seed=13
    observed = _gsa_generation(old,v,f,np.random.default_rng(seed),cfg,3,-3,3)
    pos,vel,masses,accel,G,kbest=observed
    assert kbest==int(np.ceil(n-(n-1)*3/10))
    assert G==pytest.approx(20*np.exp(-.3))
    np.testing.assert_allclose(masses,_gsa_masses(f))
    rng=np.random.default_rng(seed)
    force=np.zeros_like(old)
    elite=np.argsort(-masses,kind='stable')[:kbest]
    for i in range(n):
        for j in elite:
            if j==i:continue
            dx=old[j]-old[i]
            force[i]+=rng.random(d)*G*masses[i]*masses[j]/(np.linalg.norm(dx)+.05)*dx
    expected_acceleration=force/np.maximum(masses[:,None],1e-12)
    expected_velocity=rng.random((n,d))*v+expected_acceleration
    expected_pos=np.clip(old+expected_velocity,-3,3)
    expected_velocity[expected_pos != old+expected_velocity]=0
    np.testing.assert_allclose(accel,expected_acceleration)
    np.testing.assert_allclose(pos,expected_pos)
    np.testing.assert_allclose(vel,expected_velocity)


@pytest.mark.parametrize('bad',[{'ba_min_frequency':2,'ba_max_frequency':2},
                                 {'fa_alpha':1.1},{'ba_loudness_decay':1.1},
                                 {'ba_pulse_growth':0},{'gsa_epsilon':0},
                                 {'gsa_initial_gravity':0},{'gsa_decay':50}])
def test_invalid_new_params_rejected(bad):
    with pytest.raises(ValidationError):DimensionalRequest(**bad)


def test_api_archive_and_old_parameter_defaults(tmp_path,monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    client=TestClient(app)
    payload={'algorithms':['fa','ba','gsa'],'objective':'sphere',
             'dimensions':10,'population_size':12,'iterations':8,'trials':2,
             'fa_alpha':.11,'ba_initial_loudness':.8,'gsa_initial_gravity':30}
    response=client.post('/api/dimensional',json=payload)
    assert response.status_code==200,response.text
    result=response.json()
    assert result['total_evaluations']==12*9*3*2
    assert result['parameters']['fa_alpha']==.11
    assert result['parameters']['gsa_initial_gravity']==30
    assert len(result['groups'])==3
    assert client.get('/api/dimensional/'+result['experiment_id']).json()['groups']==result['groups']
    legacy=DimensionalRequest.model_validate({'algorithms':['pso','gwo']})
    assert legacy.fa_alpha==.18
    assert legacy.gsa_epsilon==.01
    assert client.post('/api/dimensional',json={**payload,'ba_min_frequency':3,'ba_max_frequency':2}).status_code==422
