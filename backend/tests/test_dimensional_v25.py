"""True-D / exact-NFE tests for newly budgeted ABC, CS, SMA, IWO and SA."""
import numpy as np
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from app.dimensional import DimensionalRequest, objective_nd, run_dimensional
from app.dimensional_budgeted import _sma_generation, run_budgeted_nd
from app.main import app

NEW = ['abc','cs','sma','iwo','sa']


@pytest.mark.parametrize('algorithm',NEW)
@pytest.mark.parametrize('dimensions',[2,5,10,30])
def test_exact_nfe_real_dimensions_archive_and_reproducibility(algorithm,dimensions):
    cfg=DimensionalRequest(algorithms=['de',algorithm],dimensions=dimensions,
        population_size=12,iterations=11,trials=2,objective='sphere',seed_start=37)
    left,right = run_budgeted_nd(cfg,algorithm,37),run_budgeted_nd(cfg,algorithm,37)
    assert left.trajectory==right.trajectory
    assert left.function_evaluations==12*12
    assert len(left.trajectory)==12
    assert [p.evaluations for p in left.trajectory]==list(range(12,145,12))
    assert all(len(p.best_position)==dimensions for p in left.trajectory)
    assert len(left.best_position)==dimensions
    assert all(-5.12<=v<=5.12 for v in left.best_position)
    assert np.isfinite(left.best_error)
    assert all(a.best_error>=b.best_error-1e-14 for a,b in zip(left.trajectory,left.trajectory[1:]))
    assert float(objective_nd('sphere',np.array(left.best_position))[0])==pytest.approx(left.best_error,rel=1e-9,abs=1e-13)


@pytest.mark.parametrize('algorithm',NEW)
@pytest.mark.parametrize('objective',['sphere','rastrigin','ackley','rosenbrock','griewank'])
def test_five_objectives_all_finite_nonnegative(algorithm,objective):
    cfg=DimensionalRequest(algorithms=['pso',algorithm],objective=objective,
                           dimensions=10,population_size=10,iterations=6,trials=2)
    trial=run_budgeted_nd(cfg,algorithm,42)
    assert len(trial.best_position)==10
    assert np.isfinite(trial.best_error)
    assert trial.best_error>=0
    assert trial.function_evaluations==70


@pytest.mark.parametrize('algorithm',NEW)
def test_real_evaluation_count_includes_unaccepted_and_restarted_candidates(monkeypatch,algorithm):
    import app.dimensional_budgeted as m
    count=[0]
    original=m.objective_nd
    def counted(name,x):
        count[0]+=1
        return original(name,x)
    monkeypatch.setattr(m,'objective_nd',counted)
    cfg=DimensionalRequest(algorithms=['gwo',algorithm],dimensions=5,
         objective='sphere',population_size=10,iterations=12,trials=2,
         abc_limit=1,cs_discovery_rate=.4)
    trial=run_budgeted_nd(cfg,algorithm,42)
    assert count[0]==trial.function_evaluations==130


def test_sma_last_contraction_makes_origin_when_p_is_zero():
    rng=np.random.default_rng(3)
    old=np.ones((8,10))*.5
    fit=np.ones(8)*2.5
    best=np.ones(10)*.5
    end=_sma_generation(old,fit,best,2.5,rng,step=12,iterations=12,
                        restart_rate=0.,low=-5.12,high=5.12)
    assert np.array_equal(end,np.zeros((8,10)))


def test_sa_one_state_initialization_and_sample_grid_are_not_fabricated_generations():
    cfg=DimensionalRequest(algorithms=['sa','pso'],population_size=10,iterations=10,
                           trials=2,dimensions=10,objective='rastrigin')
    trial=run_budgeted_nd(cfg,'sa',42)
    assert trial.function_evaluations==110
    assert trial.trajectory[0].evaluations==10
    assert trial.trajectory[-1].evaluations==110
    assert trial.best_error<=trial.trajectory[0].best_error


@pytest.mark.parametrize('invalid',[
    {'abc_limit':0},{'cs_discovery_rate':-0.01},{'cs_step_scale':0},
    {'cs_levy_exponent':1.99},{'sma_restart_probability':1.01},
    {'iwo_max_population':5},{'iwo_min_seeds':9},{'iwo_max_seeds':0},
    {'iwo_sigma_initial':0},{'iwo_sigma_final':0},{'iwo_modulation_index':0},
    {'sa_initial_temperature':0},{'sa_cooling_rate':0},{'sa_step_scale':0},
    {'algorithms':['pso','iwo'],'population_size':64,'iwo_max_population':60},
    {'algorithms':['pso','iwo'],'iwo_min_seeds':6,'iwo_max_seeds':5},
    {'algorithms':['pso','iwo'],'iwo_sigma_initial':.01,'iwo_sigma_final':.02},
])
def test_invalid_algorithm_parameter_rejected(invalid):
    with pytest.raises(ValidationError): DimensionalRequest(**invalid)


def test_api_save_reload_and_old_experiment_schema(monkeypatch,tmp_path):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    client=TestClient(app)
    r=client.post('/api/dimensional',json={'algorithms':['abc','cs','sma','iwo'],
      'dimensions':5,'population_size':10,'iterations':7,'trials':2,'objective':'sphere'})
    assert r.status_code==200,r.text
    result=r.json()
    assert result['evaluations_per_run']==80
    assert result['total_evaluations']==80*8
    for g in result['groups']:
        assert all(t['function_evaluations']==80 for t in g['trials'])
        assert all(len(t['best_position'])==5 for t in g['trials'])
    assert client.get('/api/dimensional/'+result['experiment_id']).json()['groups']==result['groups']
    assert any(x['experiment_id']==result['experiment_id'] for x in client.get('/api/dimensional').json()['experiments'])
    legacy=DimensionalRequest.model_validate({'algorithms':['pso','gwo'],'dimensions':10})
    assert legacy.abc_limit==30 and legacy.sa_initial_temperature==10
    assert legacy.iwo_max_population==60


def test_14_algorithm_full_selection_budget_limited_to_four():
    cfg=DimensionalRequest(algorithms=['abc','cs','iwo','sa'])
    assert len(cfg.algorithms)==4
    with pytest.raises(ValidationError): DimensionalRequest(algorithms=['pso','abc','cs','iwo','sa'])
