from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from app.comparison import ComparisonRequest, compare
from app.main import app


def test_same_seeds_same_budget_and_correct_statistics():
    request = ComparisonRequest(objective='sphere', population_size=6,
                                iterations=5, trials=3, seed_start=17, success_tolerance=0.1)
    result = compare(request)
    assert result.seeds == [17, 18, 19]
    assert result.evaluations_per_run == 36
    assert [g.algorithm for g in result.groups] == ['fa', 'pso']
    for group in result.groups:
        assert len(group.trials) == 3
        assert [t.function_evaluations for t in group.trials] == [36] * 3
        assert [c.evaluations for c in group.curve] == [6, 12, 18, 24, 30, 36]
        assert group.std_best >= 0
        assert group.min_best <= group.mean_best <= group.max_best
        assert 0 <= group.success_rate <= 1
        for a, b in zip(group.curve, group.curve[1:]):
            assert b.mean_best <= a.mean_best + 1e-12
        median_trial = sorted(group.trials, key=lambda t: (t.best_value, t.seed))[1]
        assert group.representative_run.seed == median_trial.seed


def test_reproducibility_and_mean_curve():
    request = ComparisonRequest(population_size=5, iterations=3, trials=2)
    a, b = compare(request), compare(request)
    for ga, gb in zip(a.groups, b.groups):
        assert [t.best_value for t in ga.trials] == [t.best_value for t in gb.trials]
        assert [point.mean_best for point in ga.curve] == [point.mean_best for point in gb.curve]


def test_api_persists_and_reopens(tmp_path, monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR', str(tmp_path))
    client = TestClient(app)
    payload = {'objective':'sphere', 'population_size': 5, 'iterations': 3,
               'trials': 2, 'seed_start': 100}
    response = client.post('/api/comparisons', json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    comparison_id = data['comparison_id']
    assert data['evaluations_per_run'] == 20
    assert data['parameters']['seed_start'] == 100
    history = client.get('/api/comparisons').json()['comparisons']
    assert len(history) == 1
    assert history[0]['comparison_id'] == comparison_id
    opened = client.get('/api/comparisons/' + comparison_id)
    assert opened.status_code == 200
    assert opened.json()['groups'] == data['groups']
    assert client.get('/api/comparisons/not-found').status_code == 404


@pytest.mark.parametrize('payload', [
    {'trials': 1}, {'trials': 9}, {'iterations': 500},
    {'population_size': 90}, {'success_tolerance': 0},
    {'seed_start': 2147483647}, {'fa_alpha': 2},
    {'pso_velocity_limit': 0}, {'objective': 'invalid'},
    {'unrecognized_parameter': 1},
])
def test_comparison_rejects_invalid_input(payload, tmp_path, monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR', str(tmp_path))
    assert TestClient(app).post('/api/comparisons', json=payload).status_code == 422


def test_success_threshold_is_scored_against_archived_best():
    req = ComparisonRequest(objective='sphere', population_size=5, iterations=4,
                            trials=2, seed_start=7, success_tolerance=100)
    result = compare(req)
    for group in result.groups:
        assert group.success_rate == 1.0
        assert all(t.first_success_evaluations == 5 for t in group.trials)
        assert group.std_best >= 0


def test_three_way_comparison_has_exact_nfe_alignment():
    request = ComparisonRequest(algorithms=['fa', 'pso', 'abc'],
                                objective='sphere', population_size=8,
                                iterations=9, trials=3, seed_start=42, abc_limit=2)
    result = compare(request)
    assert [g.algorithm for g in result.groups] == ['fa', 'pso', 'abc']
    checkpoints = [8 * (i + 1) for i in range(10)]
    assert result.evaluations_per_run == 80
    for group in result.groups:
        assert [p.evaluations for p in group.curve] == checkpoints
        assert [t.function_evaluations for t in group.trials] == [80] * 3
        assert [frame.function_evaluations for frame in group.representative_run.frames] == checkpoints
        assert len(group.representative_run.frames) == 10
        assert all(a >= b - 1e-12 for a, b in zip(
            [f.best_so_far for f in group.representative_run.frames],
            [f.best_so_far for f in group.representative_run.frames][1:],
        ))
    assert 'ABC' in result.methodology


def test_abc_budget_sampling_reproducible_and_telemetry_consistent():
    req = ComparisonRequest(algorithms=['fa', 'abc'], population_size=6,
                            iterations=12, trials=2, abc_limit=1, seed_start=24)
    a, b = compare(req), compare(req)
    ga, gb = a.groups[-1], b.groups[-1]
    assert [t.best_value for t in ga.trials] == [t.best_value for t in gb.trials]
    assert ga.curve == gb.curve
    run = ga.representative_run
    assert run.algorithm == 'abc'
    assert [f.function_evaluations for f in run.frames] == [6 * i for i in range(1, 14)]
    assert all(len(f.agents) == 6 for f in run.frames)
    assert all(abs(f.agents[j].fitness - (f.agents[j].x**2 + f.agents[j].y**2)) < 1e-9
               for f in run.frames for j in range(6))
    assert 'budget_nfe' in run.parameters


def test_three_way_api_persistence_and_legacy_archives(tmp_path, monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR', str(tmp_path))
    client = TestClient(app)
    for chosen in [['fa', 'pso'], ['fa', 'pso', 'abc']]:
        payload = {'algorithms': chosen, 'population_size': 5,
                   'iterations': 5, 'trials': 2, 'abc_limit': 1}
        response = client.post('/api/comparisons', json=payload)
        assert response.status_code == 200, response.text
        data = response.json()
        loaded = client.get('/api/comparisons/' + data['comparison_id'])
        assert loaded.status_code == 200
        assert loaded.json()['groups'] == data['groups']
    hist = client.get('/api/comparisons').json()['comparisons']
    assert len(hist) == 2
    assert set(hist[0]['mean_best']) in ({'fa', 'pso'}, {'fa', 'pso', 'abc'})


@pytest.mark.parametrize('algorithms', [['abc'], ['fa', 'fa'], ['pso','pso','abc'],
                                        ['fa', 'incorrect'], ['fa', 'pso', 'abc', 'other']])
def test_invalid_algorithm_selection_rejected(algorithms):
    assert TestClient(app).post('/api/comparisons', json={'algorithms': algorithms}).status_code == 422
