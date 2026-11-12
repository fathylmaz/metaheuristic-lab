"""SQLite-backed, local single-worker queue with persisted jobs and event audit.

Three job types: dimensional, benchmark, OFAT sensitivity. Each completed
independent trial is checkpointed in SQLite before progress is acknowledged.
A restarted worker reuses verified trial snapshots and computes only missing
units. Final archive insertion, checkpoint cleanup and job completion are in
one transaction. Cancellation applies only between complete trials.

Never run multiple Uvicorn workers/processes on the same queue database.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sqlite3
import threading
import zlib
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np

from .dimensional import DimensionalRequest, DimensionalResult, DimensionalTrial, run_dimensional, JobInterrupted
from .models import RunResponse
from .benchmark_suite import BenchmarkSuiteRequest, BenchmarkSuiteResult, benchmark_suite
from .sensitivity import SensitivityRequest, SensitivityResult, sensitivity

TERMINAL = {'completed', 'cancelled', 'failed'}
ACTIVE = {'queued', 'running', 'cancelling'}
KINDS = {'dimensional': DimensionalRequest, 'benchmark': BenchmarkSuiteRequest,
         'sensitivity': SensitivityRequest}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class QueueFull(Exception):
    pass


class JobNotFound(Exception):
    pass


class JobConflict(Exception):
    """Action cannot be applied in this job state."""
    pass


class CheckpointCorrupted(Exception):
    """A saved trial failed its checksum or structural validation."""
    pass


class JobQueue:
    def __init__(self, database: Path, *, max_active: int = 8):
        self.database = Path(database)
        self.max_active = max_active
        self.stop_event = threading.Event()
        self.wake = threading.Event()
        self.lock = threading.RLock()
        self.worker: threading.Thread | None = None
        self.engine_fingerprint = self._fingerprint_engine()
        self._initialize()

    @staticmethod
    def _fingerprint_engine() -> str:
        """Guard against mixing checkpoints from different numerical code/runtime."""
        hasher = hashlib.sha256()
        source_root = Path(__file__).parent
        # Numerical runners, objective definitions and stochastic optimizers.
        source_files = [source_root / name for name in (
            'dimensional.py', 'dimensional_budgeted.py', 'comparison.py',
            'benchmark_suite.py', 'sensitivity.py', 'models.py', 'objectives.py')]
        source_files.extend(sorted((source_root / 'optimizers').glob('*.py')))
        for source_file in source_files:
            hasher.update(str(source_file.relative_to(source_root)).encode())
            hasher.update(source_file.read_bytes())
        hasher.update(platform.python_version().encode())
        hasher.update(np.__version__.encode())
        return hasher.hexdigest()

    def _connect(self):
        conn = sqlite3.connect(str(self.database), timeout=20)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA busy_timeout=20000')
        return conn

    def _initialize(self):
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as con:
            con.execute('''CREATE TABLE IF NOT EXISTS background_jobs (
              id TEXT PRIMARY KEY, kind TEXT NOT NULL, created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL, state TEXT NOT NULL, request_json TEXT NOT NULL,
              completed_units INTEGER NOT NULL, total_units INTEGER NOT NULL,
              cancel_requested INTEGER NOT NULL DEFAULT 0, result_id TEXT, error TEXT,
              active_algorithm TEXT, active_seed INTEGER,
              attempts INTEGER NOT NULL DEFAULT 0,
              restart_count INTEGER NOT NULL DEFAULT 0,
              last_recovered_at TEXT, retry_of TEXT,
              checkpoint_units INTEGER NOT NULL DEFAULT 0,
              reused_units INTEGER NOT NULL DEFAULT 0)''')
            # Backward-compatible migration from v2.10 / v2.11 on existing data.
            columns = {row['name'] for row in con.execute('PRAGMA table_info(background_jobs)')}
            for column, definition in (
                ('attempts', 'INTEGER NOT NULL DEFAULT 0'),
                ('restart_count', 'INTEGER NOT NULL DEFAULT 0'),
                ('last_recovered_at', 'TEXT'),
                ('retry_of', 'TEXT'),
                ('checkpoint_units', 'INTEGER NOT NULL DEFAULT 0'),
                ('reused_units', 'INTEGER NOT NULL DEFAULT 0'),
            ):
                if column not in columns:
                    con.execute(f'ALTER TABLE background_jobs ADD COLUMN {column} {definition}')
            con.execute('''CREATE TABLE IF NOT EXISTS background_job_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                event TEXT NOT NULL,
                message TEXT NOT NULL,
                completed_units INTEGER NOT NULL DEFAULT 0,
                total_units INTEGER NOT NULL DEFAULT 0)''')
            con.execute('CREATE INDEX IF NOT EXISTS idx_job_events_job_id ON background_job_events(job_id, id)')
            con.execute('''CREATE TABLE IF NOT EXISTS background_job_checkpoints (
                job_id TEXT NOT NULL, unit_key TEXT NOT NULL,
                created_at TEXT NOT NULL, payload BLOB NOT NULL,
                sha256 TEXT NOT NULL, engine_fingerprint TEXT NOT NULL,
                PRIMARY KEY(job_id,unit_key))''')
            con.execute('CREATE INDEX IF NOT EXISTS idx_job_checkpoints_job_id ON background_job_checkpoints(job_id)')
            con.commit()

    @staticmethod
    def _event(con, job_id: str, event: str, message: str,
               completed: int = 0, total: int = 0):
        """Record an audit event in the transaction that changes the job."""
        con.execute('''INSERT INTO background_job_events
            (job_id,created_at,event,message,completed_units,total_units)
            VALUES(?,?,?,?,?,?)''',
            (job_id, utc_now(), event, message[:300], completed, total))

    def start(self):
        with self.lock:
            if self.worker is not None and self.worker.is_alive():
                return
            self.stop_event.clear()
            with closing(self._connect()) as con:
                con.execute('BEGIN IMMEDIATE')
                interrupted = con.execute('''SELECT id,completed_units,total_units,cancel_requested
                    FROM background_jobs WHERE state IN ('running','cancelling')''').fetchall()
                for row in interrupted:
                    now = utc_now()
                    saved = con.execute('SELECT COUNT(*) FROM background_job_checkpoints WHERE job_id=?',
                                        (row['id'],)).fetchone()[0]
                    # A previous v2.12 progress counter alone is not a checkpoint.
                    # Never advertise unsaved units as reusable work.
                    if row['cancel_requested']:
                        con.execute('''UPDATE background_jobs SET state='cancelled',updated_at=?,
                            checkpoint_units=?,active_algorithm=NULL,active_seed=NULL WHERE id=?''',
                            (now,saved,row['id']))
                        self._event(con,row['id'],'cancelled',
                            'Önceki oturumdaki iptal isteği tamamlandı.',
                            row['completed_units'],row['total_units'])
                    else:
                        con.execute('''UPDATE background_jobs SET state='queued', completed_units=?,
                            checkpoint_units=?,reused_units=0,
                            active_algorithm=NULL,active_seed=NULL,restart_count=restart_count+1,
                            last_recovered_at=?,updated_at=? WHERE id=?''',
                            (saved,saved,now,now,row['id']))
                        if saved:
                            message = (f'Önceki oturum kesildi. {saved} doğrulanabilir ara koşu korundu; '
                                       f'kalan {row["total_units"]-saved} koşu hesaplanacak.')
                        else:
                            message = (f'Önceki oturum kesildi. {row["completed_units"]} koşunun '
                                       'ilerlemesi sıfırlandı; bütün tohumlar yeniden hesaplanacak.')
                        self._event(con,row['id'],'recovered',message,saved,row['total_units'])
                con.execute('''UPDATE background_jobs SET state='cancelled',updated_at=?
                    WHERE state='queued' AND cancel_requested=1''', (utc_now(),))
                con.commit()
            self.worker = threading.Thread(target=self._loop,name='metaheuristic-jobs',daemon=True)
            self.worker.start()
            self.wake.set()

    def stop(self, timeout: float = 2):
        self.stop_event.set()
        self.wake.set()
        worker = self.worker
        if worker and worker.is_alive():
            worker.join(timeout)

    @staticmethod
    def _public(row):
        fields = ('id','kind','created_at','updated_at','state','completed_units',
                  'total_units','result_id','error','active_algorithm','active_seed',
                  'attempts','restart_count','last_recovered_at','retry_of',
                  'checkpoint_units','reused_units')
        obj = {field: row[field] for field in fields}
        obj['progress_percent'] = round(100*row['completed_units']/max(1,row['total_units']),1)
        obj['cancel_requested'] = bool(row['cancel_requested'])
        return obj

    def submit(self, config: DimensionalRequest | BenchmarkSuiteRequest | SensitivityRequest,
               *, kind: str = 'dimensional', retry_of: str | None = None):
        if kind not in KINDS or not isinstance(config,KINDS[kind]):
            raise ValueError('Job kind and request schema must match')
        with self.lock, closing(self._connect()) as con:
            n = con.execute("SELECT COUNT(*) FROM background_jobs WHERE state IN ('queued','running','cancelling')").fetchone()[0]
            if n >= self.max_active:
                raise QueueFull('Güvenli kapasite sınırına ulaşıldı; önceki işleri tamamla veya iptal et')
            job_id = str(uuid4())
            now = utc_now()
            total = (len(config.algorithms)*config.trials if kind=='dimensional' else
                     len(config.objectives)*len(config.comparison.algorithms)*config.comparison.trials
                     if kind=='benchmark' else len(config.values)*config.trials)
            con.execute('''INSERT INTO background_jobs
                (id,kind,created_at,updated_at,state,request_json,completed_units,total_units,retry_of)
                VALUES(?,?,?,?,?,?,0,?,?)''',
                (job_id,kind,now,now,'queued',config.model_dump_json(),total,retry_of))
            self._event(con,job_id,'queued',
                        f'{retry_of[:8]} kaynaklı yeni deneme kuyruğa alındı.' if retry_of else 'Görev kuyruğa alındı.',
                        0,total)
            con.commit()
            row = con.execute('SELECT * FROM background_jobs WHERE id=?',(job_id,)).fetchone()
        self.wake.set()
        return self._public(row)

    def list(self, limit: int = 30):
        with closing(self._connect()) as con:
            rows=con.execute('SELECT * FROM background_jobs ORDER BY created_at DESC, rowid DESC LIMIT ?',
                             (min(max(limit,1),100),)).fetchall()
        return [self._public(row) for row in rows]

    def read(self,job_id: str):
        with closing(self._connect()) as con:
            row=con.execute('SELECT * FROM background_jobs WHERE id=?',(job_id,)).fetchone()
        if row is None:
            raise JobNotFound(job_id)
        return self._public(row)

    def events(self,job_id: str, limit: int = 80):
        self.read(job_id)
        with closing(self._connect()) as con:
            rows=con.execute('''SELECT id,created_at,event,message,completed_units,total_units
                FROM background_job_events WHERE job_id=? ORDER BY id DESC LIMIT ?''',
                (job_id,min(max(limit,1),100))).fetchall()
        return [dict(row) for row in reversed(rows)]

    def retry(self,job_id: str):
        with self.lock:
            with closing(self._connect()) as con:
                row=con.execute('SELECT * FROM background_jobs WHERE id=?',(job_id,)).fetchone()
            if row is None:
                raise JobNotFound(job_id)
            if row['state'] not in {'cancelled','failed'}:
                raise JobConflict('Yalnızca iptal edilmiş veya başarısız görev yeniden denenebilir')
            config=KINDS[row['kind']].model_validate_json(row['request_json'])
            new_job=self.submit(config,kind=row['kind'],retry_of=job_id)
            with closing(self._connect()) as con:
                self._event(con,job_id,'retried',
                            f'Yeni bir görev oluşturuldu: {new_job["id"]}.',
                            row['completed_units'],row['total_units'])
                con.commit()
            return new_job

    def delete_history(self,job_id: str):
        """Remove terminal queue metadata and events, preserving archived results."""
        with self.lock, closing(self._connect()) as con:
            row=con.execute('SELECT state FROM background_jobs WHERE id=?',(job_id,)).fetchone()
            if row is None:
                raise JobNotFound(job_id)
            if row['state'] not in TERMINAL:
                raise JobConflict('Çalışan veya bekleyen görev geçmişten kaldırılamaz')
            con.execute('DELETE FROM background_job_events WHERE job_id=?',(job_id,))
            con.execute('DELETE FROM background_job_checkpoints WHERE job_id=?',(job_id,))
            con.execute('DELETE FROM background_jobs WHERE id=?',(job_id,))
            con.commit()

    def cancel(self,job_id: str):
        with self.lock, closing(self._connect()) as con:
            row=con.execute('SELECT * FROM background_jobs WHERE id=?',(job_id,)).fetchone()
            if row is None:
                raise JobNotFound(job_id)
            if row['state']=='queued':
                con.execute("UPDATE background_jobs SET state='cancelled',cancel_requested=1,updated_at=? WHERE id=?",
                            (utc_now(),job_id))
                self._event(con,job_id,'cancelled','Bekleyen görev iptal edildi.',
                            row['completed_units'],row['total_units'])
            elif row['state']=='running':
                con.execute("UPDATE background_jobs SET state='cancelling',cancel_requested=1,updated_at=? WHERE id=?",
                            (utc_now(),job_id))
                self._event(con,job_id,'cancel_requested','Mevcut koşudan sonra iptal uygulanacak.',
                            row['completed_units'],row['total_units'])
            con.commit()
            updated=con.execute('SELECT * FROM background_jobs WHERE id=?',(job_id,)).fetchone()
        self.wake.set()
        return self._public(updated)

    def _is_cancelled(self,job_id: str) -> bool:
        if self.stop_event.is_set():
            return True
        with closing(self._connect()) as con:
            row=con.execute('SELECT cancel_requested FROM background_jobs WHERE id=?',(job_id,)).fetchone()
        return row is None or bool(row[0])

    @staticmethod
    def _unit_key(*coordinates: str | int) -> str:
        # JSON arrays prevent delimiter collisions in objective/algorithm labels.
        return json.dumps(coordinates, ensure_ascii=False, separators=(',', ':'))

    def _save_checkpoint(self, job_id: str, unit_key: str, result: DimensionalTrial | RunResponse):
        """Persist complete trial and checksum atomically; never store partial frames."""
        payload = zlib.compress(result.model_dump_json().encode('utf-8'), level=6)
        digest = hashlib.sha256(payload).hexdigest()
        with closing(self._connect()) as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT state FROM background_jobs WHERE id=?', (job_id,)).fetchone()
            if row is None or row['state'] not in {'running', 'cancelling'}:
                con.rollback()
                raise JobInterrupted()
            con.execute('''INSERT INTO background_job_checkpoints
                (job_id,unit_key,created_at,payload,sha256,engine_fingerprint) VALUES(?,?,?,?,?,?)''',
                (job_id,unit_key,utc_now(),payload,digest,self.engine_fingerprint))
            count = con.execute('SELECT COUNT(*) FROM background_job_checkpoints WHERE job_id=?',
                                (job_id,)).fetchone()[0]
            con.execute('UPDATE background_jobs SET checkpoint_units=?,updated_at=? WHERE id=?',
                        (count,utc_now(),job_id))
            con.commit()

    def _load_checkpoint(self, job_id: str, unit_key: str,
                         model: type[DimensionalTrial] | type[RunResponse],
                         *, seed: int, algorithm: str | None = None,
                         objective: str | None = None):
        with closing(self._connect()) as con:
            row = con.execute('SELECT payload,sha256,engine_fingerprint FROM background_job_checkpoints '
                              'WHERE job_id=? AND unit_key=?', (job_id,unit_key)).fetchone()
        if row is None:
            return None
        try:
            if row['engine_fingerprint'] != self.engine_fingerprint:
                raise ValueError('Numerical engine fingerprint mismatch; retry as a new job')
            if hashlib.sha256(row['payload']).hexdigest() != row['sha256']:
                raise ValueError('SHA-256 checksum mismatch')
            result = model.model_validate_json(zlib.decompress(row['payload']))
            if result.seed != seed or (algorithm is not None and result.algorithm != algorithm) or (objective is not None and result.objective != objective):
                raise ValueError('trial identity mismatch')
        except Exception as exc:
            raise CheckpointCorrupted(f'Checkpoint doğrulaması başarısız ({unit_key}): {type(exc).__name__}') from exc
        with closing(self._connect()) as con:
            con.execute('UPDATE background_jobs SET reused_units=reused_units+1 WHERE id=?',(job_id,))
            con.commit()
        return result

    def _update_progress(self,job_id: str,completed: int,total: int,algorithm: str,seed: int):
        with closing(self._connect()) as con:
            con.execute('''UPDATE background_jobs SET completed_units=?,total_units=?,
                active_algorithm=?,active_seed=?,updated_at=? WHERE id=?''',
                (completed,total,algorithm,seed,utc_now(),job_id))
            self._event(con,job_id,'progress',f'{algorithm} · tohum {seed}: {completed}/{total} koşu.',
                        completed,total)
            con.commit()

    def _set_state(self,job_id: str,state: str,*,error: str | None = None):
        with closing(self._connect()) as con:
            con.execute('''UPDATE background_jobs SET state=?,updated_at=?,error=?,
                active_algorithm=NULL,active_seed=NULL WHERE id=?''',(state,utc_now(),error,job_id))
            row=con.execute('SELECT completed_units,total_units FROM background_jobs WHERE id=?',(job_id,)).fetchone()
            if row:
                self._event(con,job_id,state,error if error else 'Görev iptal edildi.',
                            row['completed_units'],row['total_units'])
            con.commit()

    def _take_next(self):
        with self.lock, closing(self._connect()) as con:
            row=con.execute("SELECT * FROM background_jobs WHERE state='queued' ORDER BY created_at LIMIT 1").fetchone()
            if row is None:
                return None
            con.execute("UPDATE background_jobs SET state='running',attempts=attempts+1,updated_at=? WHERE id=? AND state='queued'",
                        (utc_now(),row['id']))
            self._event(con,row['id'],'started',f'Görev başlatıldı (deneme {row["attempts"]+1}).',
                        row['completed_units'],row['total_units'])
            con.commit()
            return row['id'],row['kind'],row['request_json']

    def _store_success(self,job_id: str,
                       result: DimensionalResult | BenchmarkSuiteResult | SensitivityResult,
                       kind: str):
        # Result archive insertion and queue completion MUST commit together.
        if kind=='dimensional':
            assert isinstance(result,DimensionalResult)
            result.experiment_id=job_id
            table='dimensional_experiments'
            summary={'experiment_id':job_id,'created_at':result.created_at,
                     'algorithms':result.parameters.algorithms,'objective':result.parameters.objective,
                     'dimensions':result.parameters.dimensions,'trials':result.parameters.trials,
                     'evaluations_per_run':result.evaluations_per_run}
        elif kind=='benchmark':
            assert isinstance(result,BenchmarkSuiteResult)
            result.benchmark_id=job_id
            table='benchmark_suites'
            summary={'benchmark_id':job_id,'created_at':result.created_at,
                     'objectives':result.objectives,'algorithms':result.algorithms,
                     'trials_per_algorithm':len(result.seeds),
                     'evaluations_per_run':result.evaluations_per_run}
        elif kind=='sensitivity':
            assert isinstance(result,SensitivityResult)
            result.sensitivity_id=job_id
            table='sensitivity_studies'
            summary={'sensitivity_id':job_id,'created_at':result.created_at,
                     'algorithm':result.parameters.algorithm,'objective':result.parameters.objective,
                     'parameter':result.parameters.parameter,'values':result.parameters.values,
                     'trials':result.parameters.trials,
                     'evaluations_per_run':result.evaluations_per_run}
        else:
            raise ValueError('Unsupported queued experiment kind')
        with self.lock, closing(self._connect()) as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT cancel_requested,total_units FROM background_jobs WHERE id=?',(job_id,)).fetchone()
            if row is None or row['cancel_requested'] or self.stop_event.is_set():
                con.rollback()
                raise JobInterrupted()
            con.execute(f'''CREATE TABLE IF NOT EXISTS {table} (
                id TEXT PRIMARY KEY,created_at TEXT NOT NULL,summary TEXT NOT NULL,payload BLOB NOT NULL)''')
            con.execute(f'INSERT INTO {table} VALUES(?,?,?,?)',
                        (job_id,result.created_at,json.dumps(summary),
                         zlib.compress(result.model_dump_json().encode('utf-8'),level=6)))
            con.execute('''UPDATE background_jobs SET state='completed',result_id=?,
                completed_units=total_units,updated_at=?,active_algorithm=NULL,
                active_seed=NULL WHERE id=?''',(job_id,utc_now(),job_id))
            self._event(con,job_id,'completed','Deney tamamlandı ve arşive kaydedildi.',
                        row['total_units'],row['total_units'])
            # The full scientific archive is the durable result. Free the
            # redundant compressed per-trial payloads in the same transaction.
            con.execute('DELETE FROM background_job_checkpoints WHERE job_id=?',(job_id,))
            con.execute('UPDATE background_jobs SET checkpoint_units=0 WHERE id=?',(job_id,))
            con.commit()

    def _execute(self,job_id: str,kind: str,request_json: str):
        try:
            kwargs=dict(on_trial=lambda done,total,algo,seed:self._update_progress(job_id,done,total,algo,seed),
                        should_cancel=lambda:self._is_cancelled(job_id))
            if kind=='dimensional':
                result=run_dimensional(DimensionalRequest.model_validate_json(request_json),**kwargs,
                    load_trial=lambda algo,seed:self._load_checkpoint(
                        job_id,self._unit_key(algo,seed),DimensionalTrial,seed=seed),
                    save_trial=lambda algo,seed,run:self._save_checkpoint(
                        job_id,self._unit_key(algo,seed),run))
            elif kind=='benchmark':
                result=benchmark_suite(BenchmarkSuiteRequest.model_validate_json(request_json),**kwargs,
                    load_run=lambda obj,algo,seed:self._load_checkpoint(
                        job_id,self._unit_key(obj,algo,seed),RunResponse,
                        seed=seed,algorithm=algo,objective=obj),
                    save_run=lambda obj,algo,seed,run:self._save_checkpoint(
                        job_id,self._unit_key(obj,algo,seed),run))
            elif kind=='sensitivity':
                cfg=SensitivityRequest.model_validate_json(request_json)
                result=sensitivity(cfg,**kwargs,
                    load_run=lambda value,seed:self._load_checkpoint(
                        job_id,self._unit_key(float(value).hex(),seed),RunResponse,
                        seed=seed,algorithm=cfg.algorithm,objective=cfg.objective),
                    save_run=lambda value,seed,run:self._save_checkpoint(
                        job_id,self._unit_key(float(value).hex(),seed),run))
            else:
                raise ValueError('Unsupported queued experiment kind')
            self._store_success(job_id,result,kind)
        except JobInterrupted:
            if self.stop_event.is_set() and not self._is_user_cancelled(job_id):
                # Graceful server shutdown: recovery on next process start.
                return
            self._set_state(job_id,'cancelled')
        except Exception as exc:
            self._set_state(job_id,'failed',error=f'{type(exc).__name__}: {str(exc)[:300]}')

    def _is_user_cancelled(self,job_id: str):
        with closing(self._connect()) as con:
            row=con.execute('SELECT cancel_requested FROM background_jobs WHERE id=?',(job_id,)).fetchone()
        return bool(row and row[0])

    def _loop(self):
        while not self.stop_event.is_set():
            item=self._take_next()
            if item:
                self._execute(*item)
                continue
            self.wake.wait(.25)
            self.wake.clear()
