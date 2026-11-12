"""High-dimensional WOA, MFO, SSA mathematics and compatibility regression tests."""
import numpy as np
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.dimensional import (
    DimensionalRequest, _mfo_flames, _mfo_generation, _ssa_generation,
    _woa_generation, objective_nd, run_dimensional,
)
from app.main import app


@pytest.mark.parametrize('algorithm', ['woa', 'mfo', 'ssa'])
@pytest.mark.parametrize('dimensions', [2, 10, 30])
def test_deterministic_real_dimensions_and_exact_nfe(algorithm, dimensions):
    cfg = DimensionalRequest(algorithms=['pso',algorithm], dimensions=dimensions,
                             objective='sphere', population_size=12, iterations=13,
                             trials=2, seed_start=42)
    a, b = run_dimensional(cfg), run_dimensional(cfg)
    assert a.total_evaluations == 12 * 14 * 2 * 2
    x, y = a.groups[1], b.groups[1]
    assert x.algorithm == y.algorithm == algorithm
    for trial, repeat in zip(x.trials, y.trials):
        assert trial.trajectory == repeat.trajectory
        assert len(trial.best_position) == dimensions
        assert trial.function_evaluations == 12 * 14
        assert [p.evaluations for p in trial.trajectory] == list(range(12, 12*15, 12))
        assert all(first.best_error >= second.best_error for first, second in
                   zip(trial.trajectory, trial.trajectory[1:]))
        assert np.isclose(objective_nd('sphere', np.array(trial.best_position))[0],
                          trial.best_error, atol=1e-11, rtol=1e-9)
        assert all(-5.12 <= coordinate <= 5.12 for coordinate in trial.best_position)


def test_woa_forced_spiral_exact_equation_without_random_peer():
    old = np.array([[.2, -.9, 1., .8], [.8, -1., .3, -.2]])
    best = np.array([.0, .1, .2, .3])
    rng = np.random.default_rng(17)
    computed = _woa_generation(old, best, rng, 2.0, 1.2, 1.0, -2, 2)
    check = np.random.default_rng(17)
    expected = []
    for i in range(2):
        assert check.random() < 1
        ell = check.uniform(-1, 1)
        expected.append(best + np.abs(best-old[i]) * np.exp(1.2*ell)*np.cos(2*np.pi*ell))
    np.testing.assert_allclose(computed, np.clip(expected, -2, 2))


def test_woa_forced_encircling_vector_coefficients():
    old = np.array([[.2,-.2], [.3,-.4], [.5,-.6]])
    best = np.array([.2,.2])
    seed = 15
    candidate = _woa_generation(old,best,np.random.default_rng(seed),.4,1.,0.,-2,2)
    check = np.random.default_rng(seed)
    expected = []
    for x in old:
        check.random()
        A = 2*.4*check.random(2)-.4
        C = 2*check.random(2)
        expected.append(best-A*np.abs(C*best-x))
    np.testing.assert_allclose(candidate,np.array(expected))


def test_mfo_spiral_targets_d_by_d_and_flame_decrease():
    n, d = 12, 10
    old = np.linspace(-1, 1, n*d).reshape(n,d)
    fitness = np.arange(n,dtype=float)
    rng1=np.random.default_rng(17)
    updated,count = _mfo_generation(old,fitness,old.copy(),7,10,rng1,1.2,-2,2)
    assert count == max(1,int(np.floor(n-7*(n-1)/10+.5)))
    rng2=np.random.default_rng(17)
    expected=np.empty_like(old)
    r = -1-7/10
    for rank,index in enumerate(np.argsort(fitness,kind='stable')):
        flame=old[min(rank,count-1)]
        t=rng2.uniform(r,1,size=d)
        expected[index]=np.clip(flame+np.abs(flame-old[index])*
                                np.exp(1.2*t)*np.cos(2*np.pi*t),-2,2)
    np.testing.assert_allclose(updated,expected)
    assert updated.shape==(n,d)
    _,last_flames=_mfo_generation(old,fitness,old.copy(),10,10,np.random.default_rng(2),1.,-2,2)
    assert last_flames==1


def test_mfo_duplicate_archive_stays_full_without_evaluating_new_points():
    x=np.zeros((12,30))
    archive,fit=_mfo_flames(x,np.zeros(12),x,np.zeros(12),12)
    assert archive.shape==(12,30)
    assert np.array_equal(fit,np.zeros(12))
    assert np.array_equal(archive,np.zeros((12,30)))


def test_ssa_sequential_chain_and_leader_equation():
    old=np.linspace(-1.,1.,5*10).reshape(5,10)
    food=np.linspace(.3,.6,10)
    coeff=.35
    observed=_ssa_generation(old,food,np.random.default_rng(42),coeff,-2,2)
    rng=np.random.default_rng(42)
    c2,c3=rng.random(10),rng.random(10)
    expected=np.empty_like(old)
    expected[0]=np.clip(food+np.where(c3>=.5,1.,-1.)*coeff*(4*c2-2),-2,2)
    for i in range(1,5):
        expected[i]=np.clip(.5*(old[i]+expected[i-1]),-2,2)
    np.testing.assert_allclose(observed,expected)


@pytest.mark.parametrize('algorithm', ['woa','mfo','ssa'])
@pytest.mark.parametrize('objective', ['rastrigin','ackley','rosenbrock','griewank'])
def test_extended_algorithms_objectives_finite(algorithm,objective):
    cfg=DimensionalRequest(algorithms=['pso',algorithm],dimensions=10,
        objective=objective,population_size=10,iterations=8,trials=2)
    trial=run_dimensional(cfg).groups[1].trials[0]
    assert np.isfinite(trial.best_error)
    assert trial.best_error>=0
    assert len(trial.best_position)==10


@pytest.mark.parametrize('invalid', [
    {'woa_spiral_probability':1.1},{'woa_spiral_b':0},
    {'mfo_spiral_b':3.1},{'ssa_c1_initial':0},
    {'algorithms':['pso','gwo','de','woa','ssa']},
    {'algorithms':['woa','woa']},
])
def test_reject_invalid_ext_params(invalid):
    with pytest.raises(ValidationError):
        DimensionalRequest(**invalid)


def test_archive_roundtrip_of_six_algorithm_subset_and_prior_fields(tmp_path,monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    client=TestClient(app)
    data={'algorithms':['woa','mfo','ssa','de'],'dimensions':5,'population_size':12,
          'iterations':8,'trials':2,'woa_spiral_probability':.6,'mfo_spiral_b':1.3}
    resp=client.post('/api/dimensional',json=data)
    assert resp.status_code==200,resp.text
    saved=resp.json()
    assert saved['total_evaluations']==12*9*2*4
    assert [g['algorithm'] for g in saved['groups']]==data['algorithms']
    assert saved['parameters']['woa_spiral_probability']==.6
    assert client.get('/api/dimensional/'+saved['experiment_id']).json()['groups']==saved['groups']
    # A previous v2.2.0 payload without the added fields still remains valid.
    legacy=DimensionalRequest.model_validate({'algorithms':['pso','de']})
    assert legacy.woa_initial_a==2.0
