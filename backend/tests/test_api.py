from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_catalog_and_health():
    assert client.get('/api/health').json()['status'] == 'ok'
    algos = client.get('/api/catalog').json()['algorithms']
    assert len(algos) == 15
    assert [a['id'] for a in algos if a['status'] == 'ready'] == ['fa', 'pso', 'abc', 'aco', 'cs', 'mfo', 'gwo', 'woa', 'ba', 'ssa', 'sma', 'iwo', 'sa', 'gsa', 'de']


def test_run_api_contract():
    resp = client.post('/api/simulations', json={'iterations': 3, 'population_size': 5, 'seed': 11})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body['frames']) == 4
    assert body['frames'][-1]['function_evaluations'] == 20


def test_validation():
    assert client.post('/api/simulations', json={'iterations': 10000}).status_code == 422
    assert client.post('/api/simulations', json={'algorithm': 'invalid'}).status_code == 422
    assert client.post('/api/simulations', json={'seed': -1}).status_code == 422
    assert client.post('/api/simulations', content='{"alpha": NaN}', headers={'Content-Type':'application/json'}).status_code == 422


def test_pso_api_contract_and_validation():
    result = client.post('/api/simulations', json={
        'algorithm': 'pso', 'objective': 'sphere', 'seed': 5,
        'iterations': 5, 'population_size': 7, 'inertia_weight': 0.7,
    })
    assert result.status_code == 200, result.text
    body = result.json()
    assert body['algorithm'] == 'pso'
    assert body['parameters']['inertia_weight'] == 0.7
    assert body['frames'][5]['function_evaluations'] == 42
    assert body['frames'][3]['agents'][0]['pbest_fitness'] is not None
    assert client.post('/api/simulations', json={
        'algorithm': 'pso', 'velocity_limit': 0,
    }).status_code == 422
