import math
import numpy as np
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.dimensional import DimensionalRequest, objective_nd, run_dimensional
from app.main import app


@pytest.mark.parametrize('name,where', [('sphere',0),('rastrigin',0),('ackley',0),('rosenbrock',1),('griewank',0)])
@pytest.mark.parametrize('dimension',[2,5,10,30])
def test_known_global_minimum(name,where,dimension):
    x=np.full((1,dimension),where,dtype=float)
    assert abs(float(objective_nd(name,x)[0]))<1e-10


@pytest.mark.parametrize('algorithm',['pso','gwo','de'])
def test_deterministic_exact_budget_and_incumbent(algorithm):
    cfg=DimensionalRequest(algorithms=['pso',algorithm] if algorithm!='pso' else ['pso','de'],
                           dimensions=10,objective='sphere',population_size=12,iterations=13,trials=2)
    a=run_dimensional(cfg)
    b=run_dimensional(cfg)
    assert a.total_evaluations==12*14*2*len(cfg.algorithms)
    for g,h in zip(a.groups,b.groups):
        assert g.mean_error==h.mean_error
        for t,u in zip(g.trials,h.trials):
            assert t.trajectory==u.trajectory
            assert t.function_evaluations==168
            assert len(t.best_position)==10
            assert len(t.trajectory)==14
            assert [p.evaluations for p in t.trajectory]==list(range(12,169,12))
            assert all(p.best_error >= q.best_error-1e-12 for p,q in zip(t.trajectory,t.trajectory[1:]))
            assert abs(float(objective_nd('sphere',np.array(t.best_position))[0])-t.best_error)<1e-9


def test_real_high_dimensional_not_just_two_coordinates():
    cfg=DimensionalRequest(algorithms=['pso','de'],objective='sphere',dimensions=30,
                           population_size=10,iterations=12,trials=2)
    result=run_dimensional(cfg)
    for group in result.groups:
        for trial in group.trials:
            vector=trial.best_position
            assert len(vector)==30
            assert sum(v*v for v in vector[2:])>0
            assert math.isclose(sum(v*v for v in vector),trial.best_error,rel_tol=1e-8,abs_tol=1e-11)


@pytest.mark.parametrize('params',[{'algorithms':['pso','pso']}, {'dimensions':3},
                                    {'population_size':3},{'algorithms':['pso']},
                                    {'trials':21},{'iterations':201},
                                    {'population_size':64,'iterations':200,'trials':8}])
def test_invalid_parameters_rejected(params):
    with pytest.raises(ValidationError):
        DimensionalRequest(**params)


def test_endpoint_archive_and_422(tmp_path,monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    client=TestClient(app)
    payload={'algorithms':['pso','de'],'dimensions':5,'objective':'ackley',
             'population_size':12,'iterations':10,'trials':2}
    response=client.post('/api/dimensional',json=payload)
    assert response.status_code==200,response.text
    record=response.json()
    assert record['evaluations_per_run']==132
    assert record['total_evaluations']==528
    key=record['experiment_id']
    assert any(r['experiment_id']==key for r in client.get('/api/dimensional').json()['experiments'])
    assert client.get('/api/dimensional/'+key).json()['groups']==record['groups']
    assert client.get('/api/dimensional/not-there').status_code==404
    assert client.post('/api/dimensional',json={'dimensions':11}).status_code==422
    assert client.post('/api/dimensional',json={**payload,'seed_start':-1}).status_code==422
