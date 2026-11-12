"""Regression tests for queued benchmark/OFAT jobs and existing dimensional jobs."""
import sqlite3
import time
from contextlib import closing
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.job_queue import JobQueue, JobInterrupted
from app.benchmark_suite import BenchmarkSuiteRequest, benchmark_suite
from app.comparison import ComparisonRequest
from app.sensitivity import SensitivityRequest, sensitivity
from app.benchmark_store import load_benchmark
from app.sensitivity_store import load_sensitivity


def bench():
    return BenchmarkSuiteRequest(objectives=['sphere', 'rastrigin'], comparison=ComparisonRequest(
        algorithms=['pso', 'gwo'], population_size=5, iterations=1, trials=2, seed_start=42))


def sens():
    return SensitivityRequest(algorithm='pso', parameter='pso_inertia_weight', values=[.4, .72],
                              population_size=5, iterations=1, trials=2, seed_start=42)


def terminal(queue, job_id, seconds=15):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        record=queue.read(job_id)
        if record['state'] in ('completed', 'cancelled', 'failed'):
            return record
        time.sleep(.025)
    raise AssertionError(queue.read(job_id))


@pytest.mark.parametrize(('kind','factory','expected','loader'), [
    ('benchmark',bench,8,load_benchmark), ('sensitivity',sens,4,load_sensitivity)])
def test_queue_archives_three_kinds_and_progress(tmp_path, monkeypatch, kind, factory, expected, loader):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    job=q.submit(factory(),kind=kind)
    assert job['kind']==kind and job['total_units']==expected
    assert job['progress_percent']==0
    q.start()
    try:
        record=terminal(q, job['id'])
        assert record['state']=='completed',record
        assert record['completed_units']==expected
        assert record['progress_percent']==100
        saved=loader(job['id'])
        assert saved is not None and saved.total_evaluations>0
        assert {t.seed for g in (saved.groups if kind=='sensitivity' else saved.rows) for t in (
            g.trials if kind=='sensitivity' else (trial for cell in g.cells for trial in cell.trials))}=={42,43}
        if kind=='benchmark': assert saved.benchmark_id==job['id']
        else: assert saved.sensitivity_id==job['id']
        assert job['id'] in {j['id'] for j in q.list()}
    finally:
        q.stop()


@pytest.mark.parametrize(('kind','factory'), [('benchmark',bench),('sensitivity',sens)])
def test_running_job_replays_from_original_seed_after_restart(tmp_path, monkeypatch, kind, factory):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    db=tmp_path/'comparisons.sqlite3'
    q=JobQueue(db)
    job=q.submit(factory(),kind=kind)
    with closing(sqlite3.connect(db)) as con:
        con.execute("UPDATE background_jobs SET state='running',completed_units=2 WHERE id=?",(job['id'],))
        con.commit()
    restarted=JobQueue(db)
    restarted.start()
    try:
        result=terminal(restarted,job['id'])
        assert result['state']=='completed'
        assert result['completed_units']==result['total_units']
    finally:restarted.stop()


@pytest.mark.parametrize(('kind','factory'), [('benchmark',bench),('sensitivity',sens)])
def test_cancelled_job_is_not_archived(tmp_path, monkeypatch, kind, factory):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    job=q.submit(factory(),kind=kind)
    assert q.cancel(job['id'])['state']=='cancelled'
    q.start()
    try:
        assert q.read(job['id'])['result_id'] is None
        with closing(sqlite3.connect(q.database)) as con:
            name='benchmark_suites' if kind=='benchmark' else 'sensitivity_studies'
            found=con.execute("SELECT name FROM sqlite_master WHERE name=?",(name,)).fetchone()
            if found: assert con.execute(f'SELECT count(*) FROM {name} WHERE id=?',(job['id'],)).fetchone()[0]==0
    finally:q.stop()


@pytest.mark.parametrize(('kind','factory','expected_archive'), [
    ('benchmark',bench,'/api/benchmarks/'), ('sensitivity',sens,'/api/sensitivity/')])
def test_http_create_and_result_with_report(tmp_path, monkeypatch, kind, factory, expected_archive):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    with TestClient(app) as client:
        invalid=client.post(f'/api/jobs/{kind}',json={'unexpected':True})
        assert invalid.status_code==422
        res=client.post(f'/api/jobs/{kind}',json=factory().model_dump())
        assert res.status_code==202,res.text
        job=res.json()
        assert job['kind']==kind
        assert client.get(f'/api/jobs/{job["id"]}/result').status_code in (200,409)
        q=client.app.state.job_queue
        row=terminal(q, job['id'])
        assert row['state']=='completed',row
        result=client.get(f'/api/jobs/{job["id"]}/result')
        assert result.status_code==200,result.text
        assert result.json()['parameters']
        assert client.get(expected_archive+job['id']).status_code==200
        report_kind='benchmark' if kind=='benchmark' else 'sensitivity'
        assert client.get(f'/api/reports/{report_kind}/{job["id"]}').status_code==200


def test_comparison_progress_notifies_per_seed_and_cancel_guard():
    from app.comparison import compare
    config=bench().comparison
    events=[]
    result=compare(config,on_trial=lambda *args:events.append(args), should_cancel=lambda:False)
    assert len(events)==len(config.algorithms)*config.trials
    assert [e[0] for e in events]==list(range(1,len(events)+1))
    assert events[-1][1]==len(events)
    assert len(result.groups)==2
    with pytest.raises(JobInterrupted):compare(config,should_cancel=lambda:True)


def test_benchmark_progress_counts_across_objectives_and_cancellation():
    data=[]
    request=bench()
    result=benchmark_suite(request,on_trial=lambda *args:data.append(args))
    assert len(result.rows)==2
    assert len(data)==8 and [item[0] for item in data]==list(range(1,9))
    assert data[0][2]=='sphere/pso' and data[-1][2]=='rastrigin/gwo'
    with pytest.raises(JobInterrupted):
        benchmark_suite(request,should_cancel=lambda:True)


def test_ofat_progress_counts_by_parameter_and_cancellation():
    entries=[]
    result=sensitivity(sens(),on_trial=lambda *args:entries.append(args))
    assert len(result.groups)==2
    assert [entry[0] for entry in entries]==[1,2,3,4]
    assert entries[0][2]=='pso/pso_inertia_weight=0.4'
    with pytest.raises(JobInterrupted):sensitivity(sens(),should_cancel=lambda:True)


def test_kind_validation_avoids_mismatched_serialization(tmp_path):
    queue=JobQueue(tmp_path/'experiments.sqlite3')
    with pytest.raises(ValueError):queue.submit(sens(),kind='benchmark')
    with pytest.raises(ValueError):queue.submit(sens(),kind='not-a-kind')

@pytest.mark.parametrize(('kind','factory','patch_target'), [
    ('benchmark',bench,'app.comparison._run'),
    ('sensitivity',sens,'app.sensitivity._run')])
def test_running_cancel_stops_after_current_seed(tmp_path, monkeypatch, kind, factory, patch_target):
    from importlib import import_module
    import threading
    module_name, function_name=patch_target.rsplit('.',1)
    module=import_module(module_name)
    original=getattr(module,function_name)
    entered=threading.Event()
    release=threading.Event()
    calls=[]

    def slow(*args,**kwargs):
        calls.append((args,kwargs))
        if len(calls)==1:
            entered.set()
            assert release.wait(5)
        return original(*args,**kwargs)

    monkeypatch.setattr(module,function_name,slow)
    queue=JobQueue(tmp_path/'comparisons.sqlite3')
    job=queue.submit(factory(),kind=kind)
    queue.start()
    try:
        assert entered.wait(5)
        assert queue.cancel(job['id'])['state']=='cancelling'
        release.set()
        row=terminal(queue,job['id'])
        assert row['state']=='cancelled',row
        assert row['result_id'] is None
        assert len(calls)==1
    finally:
        release.set()
        queue.stop()


def test_mixed_kinds_are_executed_in_order(tmp_path, monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    queue=JobQueue(tmp_path/'comparisons.sqlite3')
    jobs=[queue.submit(bench(),kind='benchmark'),queue.submit(sens(),kind='sensitivity')]
    queue.start()
    try:
        for job in jobs:
            record=terminal(queue,job['id'])
            assert record['state']=='completed',record
        assert queue.read(jobs[0]['id'])['updated_at']<=queue.read(jobs[1]['id'])['updated_at']
    finally:queue.stop()
