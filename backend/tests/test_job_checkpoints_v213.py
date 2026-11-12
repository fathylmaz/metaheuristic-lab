"""v2.13: persisted per-trial checkpoints, deterministic recovery, integrity and archival."""
import hashlib
import sqlite3
import time
from contextlib import closing

import pytest

from app.job_queue import JobQueue, JobNotFound
from app.dimensional import DimensionalRequest, _run_one
from app.comparison import ComparisonRequest, _run as comparison_run
from app.sensitivity import SensitivityRequest, _run as sensitivity_run, PARAMETERS
from app.benchmark_suite import BenchmarkSuiteRequest
from app.comparison_store import load as load_comparison
from app.dimensional_store import load_dimensional
from app.benchmark_store import load_benchmark
from app.sensitivity_store import load_sensitivity


def dimensional():
    return DimensionalRequest(algorithms=['pso','gwo'],dimensions=5,objective='sphere',
                              population_size=8,iterations=5,trials=2,seed_start=42)


def benchmark():
    return BenchmarkSuiteRequest(objectives=['sphere','rastrigin'], comparison=ComparisonRequest(
        algorithms=['pso','gwo'], population_size=5, iterations=1,trials=2, seed_start=42))


def ofat():
    return SensitivityRequest(algorithm='pso',parameter='pso_inertia_weight',
        objective='sphere',values=[.4,.72], population_size=5,iterations=1,trials=2,seed_start=42)


def finish(q, job, seconds=15):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        status=q.read(job)
        if status['state'] in {'completed','failed','cancelled'}:
            return status
        time.sleep(.02)
    raise AssertionError(q.read(job))


def mark_running(q, job):
    with closing(sqlite3.connect(q.database)) as con:
        con.execute("UPDATE background_jobs SET state='running',attempts=1 WHERE id=?",(job,))
        con.commit()


def checkpoint_count(q, job):
    with closing(sqlite3.connect(q.database)) as con:
        return con.execute('SELECT COUNT(*) FROM background_job_checkpoints WHERE job_id=?',(job,)).fetchone()[0]


@pytest.mark.parametrize('kind,make,prefix,calls_expected,load',[
    ('dimensional',dimensional,2,2,load_dimensional),
    ('benchmark',benchmark,3,5,load_benchmark),
    ('sensitivity',ofat,2,2,load_sensitivity),
])
def test_restart_reuses_only_complete_saved_trials(tmp_path,monkeypatch,kind,make,prefix,calls_expected,load):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    cfg=make()
    job=q.submit(cfg,kind=kind)['id']
    mark_running(q,job)
    # Independently persist real completed trial snapshots, simulating a crash
    # between a committed checkpoint and its ordinary progress callback.
    if kind=='dimensional':
        for seed in [42,43]:
            q._save_checkpoint(job,q._unit_key('pso',seed),_run_one(cfg,'pso',seed))
        import app.dimensional as engine
        original=engine._run_one
    elif kind=='benchmark':
        for seed in [42,43]:
            q._save_checkpoint(job,q._unit_key('sphere','pso',seed),
                comparison_run('pso',cfg.comparison.model_copy(update={'objective':'sphere'}),seed,10))
        q._save_checkpoint(job,q._unit_key('sphere','gwo',42),
            comparison_run('gwo',cfg.comparison.model_copy(update={'objective':'sphere'}),42,10))
        import app.comparison as engine
        original=engine._run
    else:
        for seed in [42,43]:
            settings=ComparisonRequest(algorithms=['pso','fa'],objective='sphere',
                population_size=5, iterations=1,trials=2,seed_start=42,pso_inertia_weight=.4)
            q._save_checkpoint(job,q._unit_key(float(.4).hex(),seed),
                sensitivity_run('pso',settings,seed,10))
        import app.sensitivity as engine
        original=engine._run

    observed=[]
    def counting(*args,**kwargs):
        observed.append(args)
        return original(*args,**kwargs)
    monkeypatch.setattr(engine, '_run_one' if kind=='dimensional' else '_run', counting)
    restarted=JobQueue(q.database)
    restarted.start()
    try:
        status=finish(restarted,job)
        assert status['state']=='completed',status
        assert status['completed_units']==status['total_units']
        assert status['reused_units']==prefix
        assert status['checkpoint_units']==0
        assert len(observed)==calls_expected, observed
        assert checkpoint_count(q,job)==0
        saved=load(job)
        assert saved is not None and saved.total_evaluations>0
        events=restarted.events(job)
        assert any(e['event']=='recovered' and f'{prefix} doğrulanabilir' in e['message'] for e in events)
        assert len([e for e in events if e['event']=='progress'])==status['total_units']
    finally: restarted.stop()


def test_full_checkpoint_matrix_archives_without_rerunning_any_trial(tmp_path,monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    import app.dimensional as engine
    cfg=dimensional()
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    job=q.submit(cfg)['id']
    mark_running(q,job)
    for algorithm in cfg.algorithms:
        for seed in [42,43]:
            q._save_checkpoint(job,q._unit_key(algorithm,seed),_run_one(cfg,algorithm,seed))
    def unexpected(*_args,**_kw):
        raise AssertionError('cached trial must not be recomputed')
    monkeypatch.setattr(engine,'_run_one',unexpected)
    restarted=JobQueue(q.database)
    restarted.start()
    try:
        status=finish(restarted,job)
        assert status['state']=='completed',status
        assert status['reused_units']==status['total_units']==4
    finally:restarted.stop()


@pytest.mark.parametrize('corruption', ['sha', 'payload', 'seed'])
def test_corrupt_checkpoint_rejected_not_archived_and_retry_safe(tmp_path,monkeypatch,corruption):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    cfg=dimensional()
    job=q.submit(cfg)['id']
    mark_running(q,job)
    key=q._unit_key('pso',42)
    q._save_checkpoint(job,key,_run_one(cfg,'pso',42))
    with closing(sqlite3.connect(q.database)) as con:
        if corruption=='sha':
            con.execute('UPDATE background_job_checkpoints SET sha256=? WHERE job_id=?', ('0'*64,job))
        elif corruption=='payload':
            con.execute('UPDATE background_job_checkpoints SET payload=? WHERE job_id=?', (b'not zlib',job))
        else:
            run=_run_one(cfg,'pso',43)
            import zlib
            blob=zlib.compress(run.model_dump_json().encode('utf-8'))
            con.execute('UPDATE background_job_checkpoints SET payload=?,sha256=? WHERE job_id=?',
                        (blob,hashlib.sha256(blob).hexdigest(),job))
        con.commit()
    recovered=JobQueue(q.database)
    recovered.start()
    try:
        status=finish(recovered,job)
        assert status['state']=='failed',status
        assert 'Checkpoint' in status['error']
        assert load_dimensional(job) is None
        new=recovered.retry(job)
        assert new['id']!=job
        assert finish(recovered,new['id'])['state']=='completed'
        assert checkpoint_count(q,job)==1  # failed job retains forensic evidence
        recovered.delete_history(job)
        assert checkpoint_count(q,job)==0
        with pytest.raises(JobNotFound):recovered.read(job)
        assert load_dimensional(new['id']) is not None
    finally:recovered.stop()


def test_no_checkpoint_is_never_mistaken_for_finished_trial(tmp_path):
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    job=q.submit(dimensional())['id']
    with closing(sqlite3.connect(q.database)) as con:
        con.execute("UPDATE background_jobs SET state='running',completed_units=3 WHERE id=?",(job,))
        con.commit()
    recovered=JobQueue(q.database)
    recovered.start()
    try:
        assert finish(recovered,job)['state']=='completed'
        assert recovered.read(job)['reused_units']==0
        assert any('sıfırlandı' in e['message'] for e in recovered.events(job))
    finally: recovered.stop()


def test_partial_cancel_retains_checkpoints_until_history_delete(tmp_path):
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    job=q.submit(dimensional())['id']
    mark_running(q,job)
    q._save_checkpoint(job,q._unit_key('pso',42),_run_one(dimensional(),'pso',42))
    assert q.cancel(job)['state']=='cancelling'
    recovered=JobQueue(q.database)
    recovered.start()
    try:
        assert recovered.read(job)['state']=='cancelled'
        assert checkpoint_count(recovered,job)==1
        recovered.delete_history(job)
        assert checkpoint_count(recovered,job)==0
    finally:recovered.stop()


def test_old_v212_database_migration_preserves_all_records(tmp_path):
    db=tmp_path/'old.sqlite3'
    with closing(sqlite3.connect(db)) as con:
        con.execute('''CREATE TABLE background_jobs (
            id TEXT PRIMARY KEY, kind TEXT, created_at TEXT, updated_at TEXT,
            state TEXT,request_json TEXT,completed_units INTEGER,total_units INTEGER,
            cancel_requested INTEGER,result_id TEXT,error TEXT,active_algorithm TEXT,
            active_seed INTEGER,attempts INTEGER,restart_count INTEGER,
            last_recovered_at TEXT,retry_of TEXT)''')
        con.execute('INSERT INTO background_jobs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            ('older','dimensional','2026-01-01','2026-01-01','completed',
            dimensional().model_dump_json(),4,4,0,'older',None,None,None,1,0,None,None))
        con.commit()
    q=JobQueue(db)
    old=q.read('older')
    assert old['state']=='completed' and old['checkpoint_units']==0 and old['reused_units']==0
    assert old['result_id']=='older'


def test_changed_numerical_engine_fingerprint_never_mixes_old_and_new_trials(tmp_path,monkeypatch):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR',str(tmp_path))
    q=JobQueue(tmp_path/'comparisons.sqlite3')
    cfg=dimensional()
    job=q.submit(cfg)['id']
    mark_running(q,job)
    q._save_checkpoint(job,q._unit_key('pso',42),_run_one(cfg,'pso',42))
    restarted=JobQueue(q.database)
    restarted.engine_fingerprint='f'*64  # different optimizer/dependency environment
    restarted.start()
    try:
        result=finish(restarted,job)
        assert result['state']=='failed'
        assert 'CheckpointCorrupted' in result['error']
        assert load_dimensional(job) is None
    finally:restarted.stop()
