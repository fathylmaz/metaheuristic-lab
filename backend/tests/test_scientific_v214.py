"""v2.14: saved scientific audit, independent objective reference points, local profiling."""
from __future__ import annotations

import json
import subprocess
import sys
from math import cos, exp, pi, sqrt
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.dimensional import DimensionalRequest, objective_nd, run_dimensional
from app.main import app
from app.scientific_validation import _quantile, audit_dimensional

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def sample():
    return run_dimensional(DimensionalRequest(algorithms=['pso', 'gwo'],
      dimensions=5, objective='sphere', population_size=8, iterations=5, trials=2))


@pytest.mark.parametrize('algorithms', [
    ['pso', 'gwo'], ['de', 'woa'], ['mfo', 'ssa'], ['fa', 'ba'],
    ['gsa', 'abc'], ['cs', 'sma'], ['iwo', 'sa'],
])
@pytest.mark.parametrize('objective', ['sphere', 'rastrigin'])
def test_audit_all_fourteen_algorithms(algorithms, objective):
    result = run_dimensional(DimensionalRequest(algorithms=algorithms,
        dimensions=5, objective=objective, population_size=8, iterations=5, trials=2))
    report = audit_dimensional(result)
    assert report['status'] == 'passed', report['issues']
    assert not report['issues']
    assert report['evaluations_per_run'] == 48
    assert report['expected_total_evaluations'] == 48 * 2 * 2
    assert len(report['groups']) == 2
    assert len(report['paired_comparisons']) == 1
    for group in report['groups']:
        assert group['nfe_per_run'] == 48
        assert group['p95_duration_ms'] >= group['median_duration_ms'] > 0
        assert group['ci95_low'] <= group['mean_error'] <= group['ci95_high']


@pytest.mark.parametrize('dimension', [2, 5, 10, 30])
def test_reference_objectives_at_analytically_known_points(dimension):
    zeros = np.zeros(dimension)
    ones = np.ones(dimension)
    for objective in ('sphere', 'rastrigin', 'ackley', 'rosenbrock', 'griewank'):
        optimum = ones if objective == 'rosenbrock' else zeros
        assert abs(float(objective_nd(objective, optimum)[0])) < 1e-10
    assert objective_nd('sphere', ones)[0] == pytest.approx(dimension)
    assert objective_nd('rastrigin', ones)[0] == pytest.approx(dimension)
    assert objective_nd('rosenbrock', zeros)[0] == pytest.approx(dimension-1)
    assert objective_nd('ackley', ones)[0] == pytest.approx(20*(1-exp(-.2)),abs=1e-10)
    assert objective_nd('griewank', ones)[0] == pytest.approx(
        1+dimension/4000-np.prod([cos(1/sqrt(i)) for i in range(1,dimension+1)]),abs=1e-10)


@pytest.mark.parametrize('tamper,fragment', [
    (lambda r: setattr(r.groups[0].trials[0], 'function_evaluations', 4), 'NFE bütçesi'),
    (lambda r: setattr(r.groups[0].trials[0], 'best_error', 999), 'optimum hata'),
    (lambda r: setattr(r.groups[0].trials[0], 'duration_ms', -1), 'süre geçersiz'),
    (lambda r: setattr(r.groups[0].trials[0].trajectory[1], 'best_error', 999), 'yakınsama'),
    (lambda r: r.groups[0].trials[0].trajectory[2].best_position.pop(), 'yakınsama vektörü'),
    (lambda r: setattr(r, 'total_evaluations', 1), 'Toplam NFE'),
    (lambda r: setattr(r.groups[0], 'mean_error', 1e8), 'ortalama hata'),
    (lambda r: setattr(r.groups[0].trials[0], 'seed', 991), 'tohum listesi'),
    (lambda r: setattr(r.groups[0].trials[0], 'first_success_nfe', 100000), 'ilk başarı NFE'),
])
def test_archive_corruption_is_detected(sample, tamper, fragment):
    tamper(sample)
    audit = audit_dimensional(sample)
    assert audit['status'] == 'attention'
    assert any(fragment in message for message in audit['issues']), audit['issues']


def test_empirical_quantile_linear_interpolation():
    assert _quantile([1,3],.95) == pytest.approx(2.9)
    assert _quantile([7],.5) == 7
    with pytest.raises(ValueError):
        _quantile([], .95)


def test_more_replicates_without_removing_nfe_cap():
    cfg = DimensionalRequest(algorithms=['pso', 'de'], dimensions=2,
      population_size=8, iterations=5, trials=20)
    assert cfg.trials == 20
    with pytest.raises(ValidationError):
        DimensionalRequest(algorithms=['pso','de'], trials=21)
    with pytest.raises(ValidationError):
        DimensionalRequest(algorithms=['pso','de'], trials=20, population_size=64, iterations=200)


def test_audit_is_read_only_api_and_missing_record(tmp_path, monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR', str(tmp_path))
    with TestClient(app) as client:
        assert client.get('/api/health').json()['version'] == '3.0.0'
        missing = client.get('/api/science/dimensional/this-id-does-not-exist')
        assert missing.status_code == 404
        payload = {'algorithms':['pso','gwo'],'objective':'sphere','dimensions':5,
                   'population_size':8,'iterations':5,'trials':2,'seed_start':42}
        created = client.post('/api/dimensional', json=payload)
        assert created.status_code == 200, created.text
        experiment_id = created.json()['experiment_id']
        before = client.get(f'/api/dimensional/{experiment_id}').json()
        audit = client.get(f'/api/science/dimensional/{experiment_id}')
        assert audit.status_code == 200, audit.text
        result = audit.json()
        assert result['status'] == 'passed', result['issues']
        assert result['trials_per_algorithm'] == 2
        assert len(result['groups']) == 2
        assert client.get(f'/api/dimensional/{experiment_id}').json() == before
        assert audit.headers['cache-control'] == 'no-store'


def test_local_profile_generates_json_and_markdown_without_db(tmp_path, monkeypatch):
    source = ROOT/'scripts'/'scientific_profile.py'
    output = tmp_path/'profile'
    env = __import__('os').environ.copy()
    env['METAHEURISTIC_DATA_DIR'] = str(tmp_path/'database-should-not-appear')
    completed = subprocess.run([sys.executable, str(source),'--algorithms','pso','gwo',
        '--objectives','sphere','rastrigin','--dimensions','2','5',
        '--population','8','--iterations','5','--trials','2','--output-dir',str(output)],
        capture_output=True,text=True,env=env,timeout=60)
    assert completed.returncode == 0, completed.stderr
    report = json.loads((output/'scientific-profile.json').read_text(encoding='utf-8'))
    assert len(report['cells']) == 4
    assert all(c['audit_status'] == 'passed' for c in report['cells'])
    assert all(c['total_evaluations'] == 192 for c in report['cells'])
    assert 'NFE / koşu' in (output/'scientific-profile.md').read_text(encoding='utf-8')
    assert not (tmp_path/'database-should-not-appear').exists()
    repeated = subprocess.run([sys.executable, str(source),'--algorithms','pso','gwo',
        '--objectives','sphere','--dimensions','2','--population','8',
        '--iterations','5','--trials','2','--output-dir',str(output)],
        capture_output=True,text=True,env=env,timeout=60)
    assert repeated.returncode != 0
    assert 'Output files already exist' in repeated.stderr


def test_runner_rejects_invalid_duplicate_or_oversized_matrix():
    sys.path.insert(0,str(ROOT/'scripts'))
    from scientific_profile import run_matrix
    with pytest.raises(ValueError):
        run_matrix(['pso','pso'],['sphere'],[2],8,5,2,42)
    with pytest.raises(ValueError):
        run_matrix(['pso','gwo'],['sphere','sphere'],[2],8,5,2,42)
    with pytest.raises(ValidationError):
        run_matrix(['pso','gwo'],['sphere'],[30],64,200,20,42)


def test_invalid_float_is_reported_without_api_failure(sample):
    sample.groups[0].trials[0].best_error = float('nan')
    audit = audit_dimensional(sample)
    assert audit['status'] == 'attention'
    assert any('sonlu' in item or 'geçersiz sayısal' in item for item in audit['issues'])


def test_group_curve_corruption_is_detected(sample):
    sample.groups[0].curve[0]['mean_error'] = 999
    audit = audit_dimensional(sample)
    assert audit['status'] == 'attention'
    assert any('grup ortalama yakınsama' in item for item in audit['issues'])


def test_truncated_final_vector_reported_instead_of_crashing(sample):
    sample.groups[0].trials[0].best_position.pop()
    report = audit_dimensional(sample)
    assert report['status'] == 'attention'
    assert any('vektör' in issue for issue in report['issues'])
