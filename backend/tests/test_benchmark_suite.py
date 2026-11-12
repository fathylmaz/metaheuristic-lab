"""v1.9 scientific benchmark matrix and new objective invariants."""
from math import isclose
from fastapi.testclient import TestClient
from app.main import app
from app.objectives import OBJECTIVES
from app.benchmark_suite import BenchmarkSuiteRequest, benchmark_suite, average_ranks
from app.comparison import ComparisonRequest


def small_request():
    return BenchmarkSuiteRequest(
        objectives=['sphere', 'griewank', 'himmelblau'],
        comparison=ComparisonRequest(algorithms=['pso', 'gwo', 'de'],
                                     population_size=5, iterations=4, trials=2,
                                     seed_start=42, success_tolerance=.001),
    )


def test_new_objectives_known_optima_and_nonnegative():
    for name, optimum in {'griewank':(0,0), 'himmelblau':(3,2),
                          'beale':(3,.5), 'booth':(1,3)}.items():
        obj=OBJECTIVES[name]
        assert obj.optimum == optimum
        assert isclose(obj.evaluate(*optimum), 0, abs_tol=1e-10)
        assert obj.evaluate(*optimum) <= obj.evaluate(1.3,-2.4)


def test_average_ranks_ties_and_permutation():
    assert average_ranks([5,1,1,9]) == [3,1.5,1.5,4]
    assert average_ranks([0,0,0]) == [2,2,2]


def test_suite_equal_budget_cross_objective_ranks():
    data=benchmark_suite(small_request())
    assert len(data.rows)==3
    assert data.total_evaluations==3*3*2*25
    assert data.evaluations_per_run==25
    assert len(data.summary)==3
    for row in data.rows:
        assert isclose(row.optimum_value, 0.0, abs_tol=1e-12)
        assert len(row.cells)==3
        assert isclose(sum(x.rank for x in row.cells), 6)
        for cell in row.cells:
            assert len(cell.trials)==2
            assert all(t.function_evaluations==25 for t in cell.trials)
            assert all(t.absolute_error>=0 for t in cell.trials)
            assert all(0 <= cell.success_rate <= 1 for _ in [0])
    assert [x.mean_rank for x in data.summary] == sorted(x.mean_rank for x in data.summary)


def test_suite_reproducibility_with_fixed_seeds():
    first=benchmark_suite(small_request())
    second=benchmark_suite(small_request())
    for a,b in zip(first.rows,second.rows):
        for x,y in zip(a.cells,b.cells):
            assert [t.best_value for t in x.trials]==[t.best_value for t in y.trials]
            assert x.rank==y.rank
    assert [(s.algorithm, s.mean_rank) for s in first.summary] == [(s.algorithm, s.mean_rank) for s in second.summary]


def test_suite_validation_and_limit():
    client=TestClient(app)
    for payload in [
        {'objectives':['sphere','sphere']},
        {'objectives':['sphere']},
        {'objectives':['sphere','bogus']},
        {'comparison':{'algorithms':['fa','pso','abc','mfo','gwo']}},
        {'comparison':{'population_size':40,'iterations':150,'trials':8,'algorithms':['fa','pso','abc','gwo']},
         'objectives':['sphere','rastrigin','ackley','rosenbrock','griewank']},
    ]:
        assert client.post('/api/benchmarks',json=payload).status_code==422


def test_suite_api_archive_compatibility(tmp_path,monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    client=TestClient(app)
    req=small_request()
    r=client.post('/api/benchmarks',json=req.model_dump())
    assert r.status_code==200, r.text
    result=r.json()
    assert len(result['rows'])==3
    assert len(client.get('/api/benchmarks').json()['benchmarks'])==1
    restored=client.get('/api/benchmarks/'+result['benchmark_id'])
    assert restored.status_code==200
    assert restored.json()['summary']==result['summary']
    assert client.get('/api/benchmarks/unknown').status_code==404
    assert client.get('/api/comparisons').json()['comparisons']==[]


def test_new_functions_accessible_to_simulator_and_compare():
    client=TestClient(app)
    for objective in ('griewank','himmelblau','beale','booth'):
        response=client.post('/api/simulations',json={'algorithm':'pso','objective':objective,
            'population_size':5,'iterations':3,'seed':42})
        assert response.status_code==200,response.text
        data=response.json()
        assert data['objective']==objective
        assert data['frames'][-1]['function_evaluations']==20
    cmp=client.post('/api/comparisons',json={'objective':'beale','algorithms':['fa','pso'],
        'population_size':5,'iterations':3,'trials':2})
    assert cmp.status_code==200,cmp.text
