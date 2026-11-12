"""Local SQLite persistence for comparison experiments; no cloud required."""
from __future__ import annotations

import json
import os
import sqlite3
import zlib
from pathlib import Path

from .comparison import ComparisonResponse


def _database() -> Path:
    root = Path(os.environ.get('METAHEURISTIC_DATA_DIR',
                               str(Path(__file__).resolve().parents[1] / 'data')))
    root.mkdir(parents=True, exist_ok=True)
    return root / 'comparisons.sqlite3'


def _connect():
    con = sqlite3.connect(_database(), timeout=10)
    con.execute('''CREATE TABLE IF NOT EXISTS comparisons (
        id TEXT PRIMARY KEY, created_at TEXT NOT NULL, summary TEXT NOT NULL, payload BLOB NOT NULL
    )''')
    return con


def save(result: ComparisonResponse) -> None:
    summary = {
        'comparison_id': result.comparison_id,
        'created_at': result.created_at,
        'objective': result.objective,
        'trials_per_algorithm': result.trials_per_algorithm,
        'evaluations_per_run': result.evaluations_per_run,
        'mean_best': {g.algorithm: g.mean_best for g in result.groups},
    }
    payload = zlib.compress(result.model_dump_json().encode('utf-8'), level=6)
    with _connect() as conn:
        conn.execute('INSERT INTO comparisons(id, created_at, summary, payload) VALUES (?, ?, ?, ?)',
                     (result.comparison_id, result.created_at, json.dumps(summary), payload))


def list_saved(limit: int = 20) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute('SELECT summary FROM comparisons ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
    return [json.loads(r[0]) for r in rows]


def load(comparison_id: str) -> ComparisonResponse | None:
    with _connect() as conn:
        row = conn.execute('SELECT payload FROM comparisons WHERE id = ?', (comparison_id,)).fetchone()
    if not row:
        return None
    return ComparisonResponse.model_validate_json(zlib.decompress(row[0]))
