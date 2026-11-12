"""Persistent compact parameter sensitivity studies; independent of old tables."""
import json
import sqlite3
import zlib
from .comparison_store import _database
from .sensitivity import SensitivityResult


def _connect():
    conn=sqlite3.connect(_database(),timeout=10)
    conn.execute('''CREATE TABLE IF NOT EXISTS sensitivity_studies (
        id TEXT PRIMARY KEY, created_at TEXT NOT NULL,
        summary TEXT NOT NULL, payload BLOB NOT NULL)''')
    return conn


def save_sensitivity(result:SensitivityResult)->None:
    summary={'sensitivity_id':result.sensitivity_id,'created_at':result.created_at,
             'algorithm':result.parameters.algorithm,'objective':result.parameters.objective,
             'parameter':result.parameters.parameter,'values':result.parameters.values,
             'trials':result.parameters.trials,'evaluations_per_run':result.evaluations_per_run}
    with _connect() as conn:
        conn.execute('INSERT INTO sensitivity_studies VALUES (?,?,?,?)',
                     (result.sensitivity_id,result.created_at,json.dumps(summary),
                      zlib.compress(result.model_dump_json().encode(),6)))


def list_sensitivity(limit:int=20)->list[dict]:
    with _connect() as conn:
        rows=conn.execute('SELECT summary FROM sensitivity_studies ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
    return [json.loads(row[0]) for row in rows]


def load_sensitivity(id:str)->SensitivityResult|None:
    with _connect() as conn:
        row=conn.execute('SELECT payload FROM sensitivity_studies WHERE id=?',(id,)).fetchone()
    return SensitivityResult.model_validate_json(zlib.decompress(row[0])) if row else None
