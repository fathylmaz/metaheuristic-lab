"""v2.12: retained history, recovery audit, retry and API safety contracts."""
import sqlite3
import time
from contextlib import closing

import pytest
from fastapi.testclient import TestClient

from app.dimensional import DimensionalRequest
from app.benchmark_suite import BenchmarkSuiteRequest
from app.sensitivity import SensitivityRequest
from app.job_queue import JobQueue, JobConflict, JobNotFound, QueueFull
from app.main import app


def config(**updates):
    return DimensionalRequest(**({
        'algorithms':['pso','gwo'], 'dimensions':5,'objective':'sphere',
        'population_size':8,'iterations':5,'trials':2,'seed_start':42,
    } | updates))


def wait(q,job_id,timeout=10):
    stop=time.monotonic()+timeout
    while time.monotonic()<stop:
        job=q.read(job_id)
        if job['state'] in {'completed','failed','cancelled'}:
            return job
        time.sleep(.02)
    raise AssertionError(q.read(job_id))


def test_new_job_audit_contains_queued_start_progress_completion(tmp_path):
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    job=q.submit(config())
    assert job['attempts']==0 and job['restart_count']==0
    assert q.events(job['id'])[0]['event']=='queued'
    q.start()
    try:
        assert wait(q,job['id'])['state']=='completed'
        events=q.events(job['id'])
        assert events[0]['event']=='queued'
        assert events[1]['event']=='started'
        assert [e['event'] for e in events].count('progress')==4
        assert events[-1]['event']=='completed'
        assert events[-1]['completed_units']==4
        assert q.read(job['id'])['attempts']==1
    finally:q.stop()


def test_old_queue_database_adds_columns_without_losing_jobs(tmp_path):
    path=tmp_path/'comparisons.sqlite3'
    with closing(sqlite3.connect(path)) as db:
        db.execute('''CREATE TABLE background_jobs (
            id TEXT PRIMARY KEY,kind TEXT,created_at TEXT,updated_at TEXT,state TEXT,
            request_json TEXT,completed_units INTEGER,total_units INTEGER,
            cancel_requested INTEGER,result_id TEXT,error TEXT,
            active_algorithm TEXT,active_seed INTEGER)''')
        db.execute('INSERT INTO background_jobs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                   ('old','dimensional','2026-01-01','2026-01-01','completed',
                    config().model_dump_json(),4,4,0,'old',None,None,None))
        db.commit()
    q=JobQueue(path)
    old=q.read('old')
    assert old['state']=='completed' and old['result_id']=='old'
    assert old['restart_count']==0 and old['retry_of'] is None
    assert q.events('old')==[]
    q.start();q.stop()
    assert q.read('old')['state']=='completed'


def test_recovery_replays_from_zero_and_reports_lost_progress(tmp_path):
    path=tmp_path/'comparisons.sqlite3'
    q=JobQueue(path)
    job=q.submit(config())
    with closing(sqlite3.connect(path)) as db:
        db.execute("UPDATE background_jobs SET state='running',completed_units=3,attempts=1 WHERE id=?",(job['id'],))
        db.commit()
    recovered=JobQueue(path)
    recovered.start()
    try:
        assert wait(recovered,job['id'])['state']=='completed'
        status=recovered.read(job['id'])
        assert status['restart_count']==1 and status['attempts']==2
        assert status['last_recovered_at'] is not None
        events=recovered.events(job['id'])
        assert any(e['event']=='recovered' and '3 koşunun' in e['message'] for e in events)
        assert len([e for e in events if e['event']=='progress'])==4
    finally:recovered.stop()


def test_restart_cancelling_not_replayed(tmp_path):
    path=tmp_path/'comparisons.sqlite3'
    q=JobQueue(path)
    id_=q.submit(config())['id']
    with closing(sqlite3.connect(path)) as db:
        db.execute("UPDATE background_jobs SET state='cancelling',cancel_requested=1 WHERE id=?",(id_,))
        db.commit()
    q2=JobQueue(path)
    q2.start()
    try:
        assert q2.read(id_)['state']=='cancelled'
        assert q2.read(id_)['attempts']==0
        assert q2.events(id_)[-1]['event']=='cancelled'
    finally:q2.stop()


def test_cancel_idempotency_only_one_cancelled_event(tmp_path):
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    job=q.submit(config())['id']
    q.cancel(job);q.cancel(job)
    assert [e['event'] for e in q.events(job)].count('cancelled')==1


def test_failed_retry_preserves_original_and_reports_link(tmp_path,monkeypatch):
    import app.dimensional as dim
    orig=dim._run_one
    failures=[0]
    def fails_once(*args):
        failures[0]+=1
        if failures[0]==1:raise ValueError('once')
        return orig(*args)
    monkeypatch.setattr(dim,'_run_one',fails_once)
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    first=q.submit(config())['id']
    q.start()
    try:
        assert wait(q,first)['state']=='failed'
        second=q.retry(first)
        assert second['id'] != first and second['retry_of']==first
        assert wait(q,second['id'])['state']=='completed'
        assert q.read(first)['state']=='failed'
        assert q.events(first)[-1]['event']=='retried'
        assert q.events(second['id'])[0]['event']=='queued'
    finally:q.stop()


def test_cancelled_retry_starts_new_job_and_reuses_parameters(tmp_path):
    path=tmp_path/'comparisons.sqlite3'
    q=JobQueue(path)
    first=q.submit(config())['id']
    q.cancel(first)
    other=q.retry(first)
    q.start()
    try:
        assert wait(q,other['id'])['state']=='completed'
        assert q.read(first)['state']=='cancelled'
        with closing(sqlite3.connect(path)) as db:
            assert db.execute('SELECT COUNT(*) FROM background_jobs').fetchone()[0]==2
    finally:q.stop()


def test_retry_conflicts_and_missing_id(tmp_path):
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    job=q.submit(config())['id']
    with pytest.raises(JobConflict):q.retry(job)
    with pytest.raises(JobConflict):q.delete_history(job)
    with pytest.raises(JobNotFound):q.retry('missing')
    with pytest.raises(JobNotFound):q.delete_history('missing')
    with pytest.raises(JobNotFound):q.events('missing')
    q.start()
    try:
        assert wait(q,job)['state']=='completed'
        with pytest.raises(JobConflict):q.retry(job)
    finally:q.stop()


def test_history_delete_preserves_archived_scientific_data(tmp_path):
    path=tmp_path/'comparisons.sqlite3'
    q=JobQueue(path)
    job=q.submit(config())['id']
    q.start()
    try:assert wait(q,job)['state']=='completed'
    finally:q.stop()
    with closing(sqlite3.connect(path)) as db:
        before=db.execute('SELECT payload FROM dimensional_experiments WHERE id=?',(job,)).fetchone()[0]
    q.delete_history(job)
    with pytest.raises(JobNotFound):q.read(job)
    with closing(sqlite3.connect(path)) as db:
        after=db.execute('SELECT payload FROM dimensional_experiments WHERE id=?',(job,)).fetchone()[0]
        assert db.execute('SELECT COUNT(*) FROM background_job_events WHERE job_id=?',(job,)).fetchone()[0]==0
    assert before==after


def test_max_queue_limits_retry_too(tmp_path):
    q=JobQueue(tmp_path/'comparisons.sqlite3',max_active=1)
    first=q.submit(config())['id']
    q.cancel(first)
    waiting=q.submit(config())['id']
    with pytest.raises(QueueFull):q.retry(first)
    assert q.read(waiting)['state']=='queued'


def test_event_pagination_bounds_recent_progress(tmp_path):
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    jid=q.submit(config())['id']
    for i in range(150):
        q._update_progress(jid,i,150,'pso',42)
    assert len(q.events(jid))==80
    assert len(q.events(jid,limit=100000))==100
    assert len(q.events(jid,limit=-1))==1
    assert q.events(jid,limit=2)[0]['completed_units']==148


@pytest.mark.parametrize('kind,payload',[
    ('benchmark',{'objectives':['sphere','rastrigin'],
                  'comparison':{'algorithms':['pso','gwo'],'population_size':8,
                                'iterations':1,'trials':2,'seed_start':42}}),
    ('sensitivity',{'algorithm':'pso','objective':'sphere',
                    'parameter':'pso_inertia_weight','values':[0.4,0.8],
                    'population_size':8,'iterations':1,'trials':2,'seed_start':42}),
])
def test_retry_for_other_experiment_kinds(tmp_path,kind,payload):
    model={'benchmark':BenchmarkSuiteRequest,'sensitivity':SensitivityRequest}[kind]
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    initial=q.submit(model.model_validate(payload),kind=kind)['id']
    q.cancel(initial)
    again=q.retry(initial)
    assert again['kind']==kind and again['retry_of']==initial
    q.start()
    try:assert wait(q,again['id'])['state']=='completed'
    finally:q.stop()


def test_api_events_retry_delete_contract_and_archive_retained(tmp_path,monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    with TestClient(app) as client:
        original=client.post('/api/jobs/dimensional',json=config().model_dump()).json()['id']
        stop=time.monotonic()+10
        while time.monotonic()<stop:
            state=client.get(f'/api/jobs/{original}').json()['state']
            if state=='completed':break
            time.sleep(.03)
        assert state=='completed'
        assert client.get(f'/api/jobs/{original}/events').status_code==200
        assert client.post(f'/api/jobs/{original}/retry').status_code==409
        assert client.delete('/api/jobs/unknown').status_code==404
        assert client.post('/api/jobs/unknown/retry').status_code==404
        assert client.get('/api/jobs/unknown/events').status_code==404
        archived_before=client.get(f'/api/dimensional/{original}').json()
        assert client.delete(f'/api/jobs/{original}').status_code==204
        assert client.get(f'/api/jobs/{original}').status_code==404
        assert client.get(f'/api/dimensional/{original}').json()==archived_before


def test_api_cancel_then_retry_and_delete_active_conflict(tmp_path,monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    with TestClient(app) as client:
        # Queued test uses q.stop? Avoid racing with the running worker by
        # choosing a sizeable job, but assertions allow running -> cancelling.
        original=client.post('/api/jobs/dimensional',json=config(iterations=100,trials=4).model_dump()).json()['id']
        assert client.delete(f'/api/jobs/{original}').status_code==409
        response=client.post(f'/api/jobs/{original}/cancel')
        assert response.status_code==200
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            if client.get(f'/api/jobs/{original}').json()['state']=='cancelled':break
            time.sleep(.03)
        else:raise AssertionError('Cancellation did not settle')
        new=client.post(f'/api/jobs/{original}/retry')
        assert new.status_code==202,new.text
        assert new.json()['retry_of']==original
        client.post(f'/api/jobs/{new.json()["id"]}/cancel')
