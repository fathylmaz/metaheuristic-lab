"""v1.8.0 controlled multi-algorithm benchmark invariants."""
import pytest
from fastapi.testclient import TestClient
from app.comparison import (ComparisonRequest, ComparisonResponse, compare,
                            exact_paired_sign_flip, pairwise_statistics)
from app.main import app

ALGORITHMS = ['fa','pso','abc','mfo','gwo','woa','ba','ssa','sma','gsa','de']


@pytest.mark.parametrize('algorithm', ALGORITHMS)
def test_all_comparable_algorithms_have_exact_nfe(algorithm):
    result = compare(ComparisonRequest(algorithms=['fa', algorithm] if algorithm!='fa' else ['fa','pso'],
                                       population_size=6, iterations=5, trials=2,
                                       seed_start=103))
    expected = [6, 12, 18, 24, 30, 36]
    for group in result.groups:
        assert [f.function_evaluations for f in group.representative_run.frames] == expected
        assert [t.function_evaluations for t in group.trials] == [36, 36]
        assert [p.evaluations for p in group.curve] == expected
        assert all(frame.best_so_far >= 0 for frame in group.representative_run.frames)
    assert len(result.pairwise) == 1


def test_six_way_comparison_determinism_and_statistics():
    req = ComparisonRequest(algorithms=['abc','mfo','gwo','woa','gsa','de'],
                            objective='rastrigin', population_size=6, iterations=8,
                            trials=3, seed_start=101)
    a, b = compare(req), compare(req)
    assert len(a.groups) == 6 and len(a.pairwise) == 15
    for ga, gb in zip(a.groups,b.groups):
        assert [t.best_value for t in ga.trials] == [t.best_value for t in gb.trials]
        assert [p.mean_best for p in ga.curve] == [p.mean_best for p in gb.curve]
    assert [p.model_dump() for p in a.pairwise] == [p.model_dump() for p in b.pairwise]
    for p in a.pairwise:
        assert p.a_wins + p.b_wins + p.ties == 3
        assert 0 <= p.p_value <= p.p_holm <= 1


def test_signflip_extreme_and_zero_cases():
    assert exact_paired_sign_flip([0,0,0]) == 1
    assert exact_paired_sign_flip([1,1,1]) == 0.25
    assert exact_paired_sign_flip([-1,-1,-1,-1]) == 0.125
    assert exact_paired_sign_flip([1,-1]) == 1


def test_comparison_input_caps_and_bat_frequency():
    client = TestClient(app)
    for payload in [
      {'algorithms':['fa','pso','abc','mfo','gwo','woa','ba']},
      {'algorithms':['fa','iwo'],'iwo_max_seeds':0},
      {'algorithms':['fa','iwo'],'iwo_max_population':5,'population_size':10},
      {'algorithms':['fa','iwo'],'iwo_sigma_initial':.01,'iwo_sigma_final':.5},
      {'algorithms':['fa','gsa'],'gsa_decay':-1},
      {'algorithms':['fa','ba'],'ba_frequency_min':3,'ba_frequency_max':1},
      {'algorithms':['fa','de'],'de_mutation_factor':3},
    ]:
        response = client.post('/api/comparisons', json=payload)
        assert response.status_code == 422, response.text


def test_new_pairwise_api_archive_and_old_json(tmp_path, monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR', str(tmp_path))
    client = TestClient(app)
    payload = {'algorithms':['pso','gwo','de'], 'objective':'sphere',
               'population_size':5,'iterations':4,'trials':3}
    response = client.post('/api/comparisons',json=payload)
    assert response.status_code==200, response.text
    data=response.json()
    assert len(data['pairwise'])==3
    loaded=client.get('/api/comparisons/'+data['comparison_id']).json()
    assert loaded['pairwise']==data['pairwise']
    del data['pairwise']
    old=ComparisonResponse.model_validate(data)
    assert old.pairwise==[]
