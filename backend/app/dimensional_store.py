"""Compact, durable local archive for true high-dimensional runs."""
import json
import sqlite3
import zlib
from .comparison_store import _database
from .dimensional import DimensionalResult


def _connect():
    conn=sqlite3.connect(_database(),timeout=10)
    conn.execute('''CREATE TABLE IF NOT EXISTS dimensional_experiments(
        id TEXT PRIMARY KEY, created_at TEXT NOT NULL, summary TEXT NOT NULL, payload BLOB NOT NULL)''')
    return conn


def save_dimensional(result:DimensionalResult)->None:
    summary={'experiment_id':result.experiment_id,'created_at':result.created_at,
             'algorithms':result.parameters.algorithms,'objective':result.parameters.objective,
             'dimensions':result.parameters.dimensions,'trials':result.parameters.trials,
             'evaluations_per_run':result.evaluations_per_run}
    with _connect() as con:
        con.execute('INSERT INTO dimensional_experiments VALUES(?,?,?,?)',
                    (result.experiment_id,result.created_at,json.dumps(summary),
                     zlib.compress(result.model_dump_json().encode('utf-8'),level=6)))


def list_dimensional(limit:int=20)->list[dict]:
    with _connect() as con:
        rows=con.execute('SELECT summary FROM dimensional_experiments ORDER BY created_at DESC LIMIT ?',(limit,)).fetchall()
    return [json.loads(row[0]) for row in rows]


def load_dimensional(experiment_id:str)->DimensionalResult|None:
    with _connect() as con:
        row=con.execute('SELECT payload FROM dimensional_experiments WHERE id=?',(experiment_id,)).fetchone()
    return DimensionalResult.model_validate_json(zlib.decompress(row[0])) if row else None
