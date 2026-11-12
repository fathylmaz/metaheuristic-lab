"""Persistence, cancellation, progress, and API tests for the local queue."""
import sqlite3
import time
from contextlib import closing

from fastapi.testclient import TestClient

from app.dimensional import DimensionalRequest
from app.job_queue import JobQueue, QueueFull, JobNotFound
from app.main import app


def config(**updates):
    return DimensionalRequest(**({
        'algorithms':['pso', 'de'], 'dimensions':5, 'objective':'sphere',
        'population_size':10, 'iterations':5, 'trials':2,
    } | updates))


def until_terminal(queue, job_id, seconds=10):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        state=queue.read(job_id)
        if state['state'] in {'completed','cancelled','failed'}:
            return state
        time.sleep(.02)
    raise AssertionError(f'Job still active: {queue.read(job_id)}')


def test_completed_job_is_archived_and_progress_is_exact(tmp_path):
    queue=JobQueue(tmp_path/'comparisons.sqlite3')
    job=queue.submit(config())
    assert job['state']=='queued'
    assert job['completed_units']==0
    assert job['total_units']==4
    queue.start()
    result=until_terminal(queue,job['id'])
    assert result['state']=='completed',result
    assert result['completed_units']==4
    assert result['progress_percent']==100
    assert result['result_id']==job['id']
    from app.dimensional_store import load_dimensional
    import os
    prior=os.environ.get('METAHEURISTIC_DATA_DIR')
    os.environ['METAHEURISTIC_DATA_DIR']=str(tmp_path)
    try:
        archive=load_dimensional(job['id'])
        assert archive is not None
        assert archive.total_evaluations==4*10*6
        assert archive.experiment_id==job['id']
        assert len(archive.groups)==2
        assert {t.seed for g in archive.groups for t in g.trials}=={42,43}
    finally:
        if prior is None: os.environ.pop('METAHEURISTIC_DATA_DIR',None)
        else: os.environ['METAHEURISTIC_DATA_DIR']=prior
        queue.stop()


def test_pending_job_can_be_cancelled_without_execution(tmp_path):
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    job=q.submit(config())
    status=q.cancel(job['id'])
    assert status['state']=='cancelled' and status['cancel_requested']
    q.start()
    time.sleep(.1)
    assert q.read(job['id'])['state']=='cancelled'
    q.stop()


def test_cancellation_is_idempotent_and_completed_stays_completed(tmp_path):
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    id_=q.submit(config())['id']
    assert q.cancel(id_)['state']=='cancelled'
    assert q.cancel(id_)['state']=='cancelled'
    q.start()
    id2=q.submit(config())['id']
    assert until_terminal(q,id2)['state']=='completed'
    assert q.cancel(id2)['state']=='completed'
    q.stop()


def test_pending_jobs_survive_restart(tmp_path):
    path=tmp_path/'comparisons.sqlite3'
    first=JobQueue(path)
    id_=first.submit(config())['id']
    second=JobQueue(path)
    second.start()
    assert until_terminal(second,id_)['state']=='completed'
    second.stop()


def test_running_is_recovered_and_cancelled_is_respected(tmp_path):
    path=tmp_path/'comparisons.sqlite3'
    q=JobQueue(path)
    id_=q.submit(config())['id']
    id2=q.submit(config())['id']
    with closing(sqlite3.connect(path)) as db:
        db.execute("UPDATE background_jobs SET state='running', completed_units=3 WHERE id=?",(id_,))
        db.execute("UPDATE background_jobs SET state='cancelling',cancel_requested=1 WHERE id=?",(id2,))
        db.commit()
    other=JobQueue(path)
    other.start()
    assert until_terminal(other,id_)['state']=='completed'
    assert other.read(id2)['state']=='cancelled'
    other.stop()


def test_bounded_queue_missing_id_and_listing(tmp_path):
    q=JobQueue(tmp_path/'comparisons.sqlite3',max_active=1)
    id_=q.submit(config())['id']
    assert q.list()[0]['id']==id_
    try:
        q.submit(config())
    except QueueFull:
        pass
    else:
        raise AssertionError('Active queue limit not enforced')
    try:
        q.read('missing')
    except JobNotFound:
        pass
    else:
        raise AssertionError('Missing job must return 404')
    q.cancel(id_)
    assert q.submit(config())['state']=='queued'


def test_api_submit_poll_archive_and_invalid_payload(tmp_path, monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    with TestClient(app) as client:
        payload=config().model_dump()
        r=client.post('/api/jobs/dimensional',json=payload)
        assert r.status_code==202,r.text
        id_=r.json()['id']
        assert client.post('/api/jobs/dimensional',json={'algorithms':['pso']}).status_code==422
        assert client.get('/api/jobs/not-found').status_code==404
        assert client.post('/api/jobs/not-found/cancel').status_code==404
        assert any(j['id']==id_ for j in client.get('/api/jobs').json()['jobs'])
        limit=time.monotonic()+10
        while time.monotonic()<limit:
            record=client.get(f'/api/jobs/{id_}').json()
            if record['state'] in {'completed','failed'}: break
            time.sleep(.03)
        assert record['state']=='completed',record
        output=client.get(f'/api/jobs/{id_}/result')
        assert output.status_code==200,output.text
        assert output.json()['experiment_id']==id_
        assert client.get(f'/api/dimensional/{id_}').status_code==200


def test_api_queued_cancellation_does_not_produce_result(tmp_path, monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    with TestClient(app) as client:
        # May start running immediately, but cancelling must prevent final archival.
        cfg=config(iterations=120, population_size=25, trials=4, dimensions=30)
        response=client.post('/api/jobs/dimensional',json=cfg.model_dump())
        assert response.status_code==202,response.text
        jid=response.json()['id']
        status=client.post(f'/api/jobs/{jid}/cancel')
        assert status.status_code==200
        limit=time.monotonic()+10
        while time.monotonic()<limit:
            row=client.get(f'/api/jobs/{jid}').json()
            if row['state']=='cancelled':break
            time.sleep(.04)
        assert row['state']=='cancelled',row
        assert client.get(f'/api/jobs/{jid}/result').status_code==409


def test_running_cancellation_is_cooperative_between_trials(tmp_path, monkeypatch):
    import threading
    import app.dimensional as dim
    entered = threading.Event()
    release = threading.Event()
    real = dim._run_one
    calls=[]

    def slow(cfg, algorithm, seed):
        calls.append((algorithm,seed))
        if len(calls) == 1:
            entered.set()
            assert release.wait(4)
        return real(cfg,algorithm,seed)

    monkeypatch.setattr(dim,'_run_one',slow)
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    job_id=q.submit(config())['id']
    q.start()
    try:
        assert entered.wait(4)
        assert q.cancel(job_id)['state']=='cancelling'
        release.set()
        record=until_terminal(q,job_id)
        assert record['state']=='cancelled'
        assert record['result_id'] is None
        assert len(calls)==1, 'No second algorithm/seed should start after cancellation'
    finally:
        release.set()
        q.stop()


def test_one_failed_job_does_not_stop_next_job(tmp_path, monkeypatch):
    import app.dimensional as dim
    real=dim._run_one
    count=[0]

    def error_first(cfg, algorithm, seed):
        count[0]+=1
        if count[0]==1:
            raise RuntimeError('intentional smoke test failure')
        return real(cfg,algorithm,seed)

    monkeypatch.setattr(dim,'_run_one',error_first)
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    first=q.submit(config())['id']
    second=q.submit(config())['id']
    q.start()
    try:
        assert until_terminal(q,first)['state']=='failed'
        assert until_terminal(q,second)['state']=='completed'
        assert 'RuntimeError' in q.read(first)['error']
    finally:
        q.stop()
