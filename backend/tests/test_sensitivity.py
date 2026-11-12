"""Scientific parameter-sensitivity contract tests."""
from math import isclose
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.sensitivity import PARAMETERS, SensitivityRequest, sensitivity


def req(**kwargs):
    base=dict(algorithm='pso', objective='sphere',parameter='pso_inertia_weight',
              values=[.4,.72,1.0],population_size=6,iterations=5,trials=2,
              seed_start=42,success_tolerance=.001)
    return SensitivityRequest(**(base|kwargs))


def test_all_14_continuous_algorithms_have_scannable_valid_parameters():
    assert len(PARAMETERS)==14
    assert 'aco' not in PARAMETERS
    for algorithm, options in PARAMETERS.items():
        assert options and len({o.key for o in options})==len(options)
        for item in options:
            assert item.minimum<=item.default<=item.maximum
            assert all(item.minimum<=v<=item.maximum for v in item.suggested)


def test_invalid_parameter_value_and_duplicate_rejected():
    for options in [dict(values=[.4,.4]),dict(values=[.4]),
                    dict(values=[.4,20]),dict(parameter='woa_spiral_b'),
                    dict(values=[float('nan'),.7])]:
        with pytest.raises(ValidationError):req(**options)
    with pytest.raises(ValidationError):
        req(algorithm='abc',parameter='abc_limit',values=[2.5,30])


def test_equal_real_nfe_and_reproducibility():
    data=sensitivity(req())
    assert data.evaluations_per_run==36
    assert data.total_evaluations==216
    assert len(data.groups)==3
    assert data.seeds==[42,43]
    again=sensitivity(req())
    for a,b in zip(data.groups,again.groups):
        assert [x.absolute_error for x in a.trials]==[x.absolute_error for x in b.trials]
        assert [x.mean_error for x in a.curve]==[x.mean_error for x in b.curve]
        assert [p.evaluations for p in a.curve]==[6,12,18,24,30,36]
        assert all(t.function_evaluations==36 for t in a.trials)
        assert isclose(a.mean_error,sum(t.absolute_error for t in a.trials)/2)
        assert 0<=a.success_rate<=1


def test_ofat_parameter_effect_varies_with_shared_seeds():
    data=sensitivity(req())
    assert len({tuple(t.best_value for t in g.trials) for g in data.groups})>1


def test_budgeted_single_solution_and_variable_population():
    for algorithm, parameter, values in [('sa','sa_cooling_rate',[.8,.99]),
                                         ('cs','cs_discovery_rate',[.1,.4]),
                                         ('iwo','iwo_modulation_index',[1,5])]:
        data=sensitivity(req(algorithm=algorithm,parameter=parameter,values=values))
        assert len(data.groups)==2
        assert all(t.function_evaluations==36 for g in data.groups for t in g.trials)
        assert all(len(g.curve)==6 for g in data.groups)


def test_api_parameter_catalog_and_archive_roundtrip(tmp_path,monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    client=TestClient(app)
    response=client.get('/api/sensitivity/parameters')
    assert response.status_code==200
    assert len(response.json()['parameters'])==14
    data=client.post('/api/sensitivity',json=req().model_dump())
    assert data.status_code==200,data.text
    payload=data.json()
    assert payload['total_evaluations']==216
    assert len(payload['groups'][0]['trials'])==2
    listing=client.get('/api/sensitivity').json()['studies']
    assert len(listing)==1 and listing[0]['parameter']=='pso_inertia_weight'
    opened=client.get('/api/sensitivity/'+payload['sensitivity_id'])
    assert opened.status_code==200
    assert opened.json()['groups']==payload['groups']
    assert client.get('/api/sensitivity/not-found').status_code==404
    # Existing archives are not modified by this endpoint.
    assert client.get('/api/benchmarks').json()['benchmarks']==[]
    assert client.get('/api/comparisons').json()['comparisons']==[]


def test_api_validation_is_422():
    client=TestClient(app)
    for change in [{'parameter':'invalid'}, {'values':[.1,.1]},
                   {'values':[.1,4]}, {'values':[.1]},
                   {'population_size':60}, {'algorithm':'aco'}]:
        payload=req().model_dump()|change
        assert client.post('/api/sensitivity',json=payload).status_code==422


def test_parameter_registry_pydantic_cross_constraints():
    # The new sweep must not bypass an optimizer's existing invariants.
    with pytest.raises(ValidationError):
        req(algorithm='iwo',parameter='iwo_sigma_initial',values=[.001,1.5])
