"""Scientific comparison invariants for the three NFE-adapted algorithms."""
from math import isclose

import pytest
from fastapi.testclient import TestClient

from app.comparison import ComparisonRequest, compare
from app.models import RunRequest
from app.main import app
from app.objectives import OBJECTIVES
from app.optimizers.budgeted_extra import (
    simulate_cs_budgeted, simulate_iwo_budgeted, simulate_sa_budgeted,
)

RUNNERS = {'cs':simulate_cs_budgeted,'iwo':simulate_iwo_budgeted,'sa':simulate_sa_budgeted}


@pytest.mark.parametrize('algorithm', RUNNERS)
@pytest.mark.parametrize('objective', ['sphere','rastrigin','ackley','rosenbrock'])
def test_true_nfe_monotonic_archive_and_fitness(algorithm, objective):
    n, steps = 8, 9
    request = RunRequest(algorithm=algorithm,objective=objective,
                         population_size=n,iterations=steps,seed=42)
    result=RUNNERS[algorithm](request,n*(steps+1))
    assert len(result.frames)==steps+1
    assert [f.function_evaluations for f in result.frames]==list(range(n,n*(steps+1)+1,n))
    assert all(len(f.agents)>0 for f in result.frames)
    assert all(a.fitness>=0 for f in result.frames for a in f.agents)
    assert all(f.best_so_far>=0 for f in result.frames)
    assert all(a.x >= result.bounds[0] and a.x<=result.bounds[1] and
               a.y>=result.bounds[0] and a.y<=result.bounds[1]
               for f in result.frames for a in f.agents)
    assert all(f.best_so_far<=result.frames[i-1].best_so_far
               for i,f in enumerate(result.frames) if i)
    objective_fn=OBJECTIVES[objective].evaluate
    assert all(isclose(a.fitness,objective_fn(a.x,a.y),abs_tol=1e-9)
               for f in result.frames for a in f.agents)
    assert isclose(result.frames[-1].best_so_far,objective_fn(*result.frames[-1].best_position),abs_tol=1e-9)


@pytest.mark.parametrize('algorithm', RUNNERS)
def test_identical_seed_reproducibility_full_trajectory(algorithm):
    request=RunRequest(algorithm=algorithm,objective='sphere',population_size=8,iterations=11,seed=17)
    a=RUNNERS[algorithm](request,96)
    b=RUNNERS[algorithm](request,96)
    assert [f.model_dump() for f in a.frames]==[f.model_dump() for f in b.frames]
    assert a.frames[-1].function_evaluations==96


def test_sa_consumes_one_evaluation_per_proposal_and_tracks_uphill():
    request=RunRequest(algorithm='sa',objective='sphere',population_size=8,iterations=8,seed=42)
    result=simulate_sa_budgeted(request,72)
    last=result.frames[-1]
    assert last.sa_accepted_total+last.sa_rejected_total==71
    assert last.sa_uphill_accepted_total<=last.sa_accepted_total
    assert len(last.agents)==1
    assert last.sa_temperature is not None and 0<last.sa_temperature<request.sa_initial_temperature


def test_iwo_population_cap_and_identity_and_budget_sigma():
    req=RunRequest(algorithm='iwo',population_size=8,iterations=12,seed=42,
                   iwo_max_population=12)
    r=simulate_iwo_budgeted(req,104)
    assert [f.function_evaluations for f in r.frames]==list(range(8,105,8))
    assert all(len(f.agents)<=12 for f in r.frames)
    assert all(len({a.id for a in f.agents})==len(f.agents) for f in r.frames)
    assert r.frames[0].iwo_sigma==req.iwo_sigma_initial
    assert isclose(r.frames[-1].iwo_sigma,req.iwo_sigma_final)


def test_cs_archive_consistent_despite_nest_abandonment():
    req=RunRequest(algorithm='cs', population_size=8, iterations=12, seed=42,cs_discovery_rate=.75)
    r=simulate_cs_budgeted(req,104)
    assert all(f.best_so_far<=f.current_best for f in r.frames)
    assert all(f.function_evaluations==8*(i+1) for i,f in enumerate(r.frames))


def test_public_api_and_benchmark_select_new_algorithms(tmp_path,monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    client=TestClient(app)
    payload={'algorithms':['cs','iwo','sa'],'objective':'sphere',
             'population_size':8,'iterations':6,'trials':2,'seed_start':42}
    response=client.post('/api/comparisons',json=payload)
    assert response.status_code==200,response.text
    result=response.json()
    assert len(result['groups'])==3
    assert all(g['representative_run']['frames'][-1]['function_evaluations']==56 for g in result['groups'])
    assert len(result['pairwise'])==3
    assert client.get('/api/comparisons/'+result['comparison_id']).status_code==200
    data=client.post('/api/benchmarks',json={
        'objectives':['sphere','rastrigin'],'comparison':payload}).json()
    assert len(data['rows'])==2 and data['total_evaluations']==2*3*2*56


@pytest.mark.parametrize('payload',[
    {'algorithms':['pso','iwo'],'iwo_max_seeds':0},
    {'algorithms':['pso','iwo'],'iwo_max_population':5,'population_size':8},
    {'algorithms':['pso','iwo'],'iwo_min_seeds':7,'iwo_max_seeds':3},
    {'algorithms':['pso','iwo'],'iwo_sigma_initial':.01,'iwo_sigma_final':1},
    {'algorithms':['pso','cs'],'cs_levy_exponent':2.5},
    {'algorithms':['pso','sa'],'sa_cooling_rate':0},
])
def test_invalid_budgeted_configuration_rejected(payload):
    assert TestClient(app).post('/api/comparisons',json=payload).status_code==422
