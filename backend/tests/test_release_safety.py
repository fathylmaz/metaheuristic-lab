"""Release-level API contracts, defensive behavior and archive integration."""
import re

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR', str(tmp_path))
    with TestClient(app) as api:
        yield api


@pytest.mark.parametrize('endpoint', ['/api/health', '/api/catalog', '/api/comparisons',
                                      '/api/benchmarks', '/api/sensitivity',
                                      '/api/dimensional', '/api/reports'])
def test_safe_headers_on_read(client, endpoint):
    response = client.get(endpoint)
    assert response.status_code == 200
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['referrer-policy'] == 'no-referrer'
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['x-frame-options'] == 'DENY'


@pytest.mark.parametrize('endpoint', ['/api/simulations', '/api/comparisons', '/api/benchmarks',
                                      '/api/sensitivity', '/api/dimensional', '/api/aco/simulations'])
def test_oversized_json_rejected(client, endpoint):
    response = client.post(endpoint, content=b' ' * (1024 * 1024 + 1),
                           headers={'Content-Type': 'application/json'})
    assert response.status_code == 413
    assert response.headers['x-content-type-options'] == 'nosniff'


def test_chunked_oversized_request_is_rejected(client):
    def chunks():
        for _ in range(3):
            yield b' ' * (400 * 1024)
    response = client.post('/api/simulations', content=chunks(),
                           headers={'Content-Type': 'application/json'})
    assert response.status_code == 413


def test_cors_is_only_enabled_for_local_frontend(client):
    allowed = client.options('/api/simulations', headers={
        'Origin': 'http://127.0.0.1:5173', 'Access-Control-Request-Method': 'POST'})
    assert allowed.status_code == 200
    assert allowed.headers['access-control-allow-origin'] == 'http://127.0.0.1:5173'
    denied = client.options('/api/simulations', headers={
        'Origin': 'https://example.com', 'Access-Control-Request-Method': 'POST'})
    assert denied.status_code == 400
    assert 'access-control-allow-origin' not in denied.headers


@pytest.mark.parametrize('body', [
    {'iterations': 0}, {'population_size': 999}, {'alpha': -0.1},
    {'algorithm': 'not-an-algorithm'}, {'objective': 'unknown'}, {'seed': -1},
    {'unknown_field': 'anything'},
])
def test_invalid_simulation_input_rejected(client, body):
    response = client.post('/api/simulations', json=body)
    assert response.status_code == 422


def test_no_internal_traceback_leaked_on_validation(client):
    response = client.post('/api/simulations', content='{"gamma":NaN}',
                           headers={'Content-Type': 'application/json'})
    assert response.status_code == 422
    assert 'Traceback' not in response.text
    assert all(set(item) <= {'loc', 'msg', 'type'} for item in response.json()['detail'])


@pytest.mark.parametrize('kind', ['comparison', 'benchmark', 'sensitivity', 'dimensional'])
def test_missing_report_not_found(client, kind):
    response = client.get(f'/api/reports/{kind}/' + '0' * 36)
    assert response.status_code == 404


def test_report_invalid_format_rejected(client):
    response = client.get('/api/reports/dimensional/example?format=javascript')
    assert response.status_code == 422


def test_smoke_simulation_and_aco(client):
    body = client.post('/api/simulations', json={
        'algorithm': 'pso', 'objective': 'sphere', 'iterations': 2,
        'population_size': 5, 'seed': 42,
    })
    assert body.status_code == 200, body.text
    result = body.json()
    assert result['algorithm'] == 'pso'
    assert result['frames'][-1]['function_evaluations'] == 15
    aco = client.post('/api/aco/simulations', json={'iterations': 2, 'seed': 42})
    assert aco.status_code == 200, aco.text


def test_dimensional_archive_and_report_formats(client):
    response = client.post('/api/dimensional', json={
        'algorithms': ['pso', 'gwo'], 'dimensions': 5, 'objective': 'sphere',
        'population_size': 8, 'iterations': 5, 'trials': 2, 'seed_start': 42,
    })
    assert response.status_code == 200, response.text
    payload = response.json()
    experiment_id = payload['experiment_id']
    assert re.fullmatch(r'[a-zA-Z0-9-]{20,}', experiment_id)
    assert client.get('/api/dimensional/' + experiment_id).status_code == 200
    archive = client.get('/api/reports').json()['reports']
    assert any(item['source_id'] == experiment_id for item in archive)
    for fmt, content_type in [('json', 'application/json'), ('md', 'text/markdown'), ('html', 'text/html')]:
        output = client.get(f'/api/reports/dimensional/{experiment_id}?format={fmt}')
        assert output.status_code == 200
        assert content_type in output.headers['content-type']
        assert 'Metaheuristic Lab' in output.text
        assert output.headers['x-content-type-options'] == 'nosniff'
        if fmt == 'html':
            assert "default-src 'none'" in output.headers['content-security-policy']
            assert '<script' not in output.text.lower()
