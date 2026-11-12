"""Separate local SQLite table for compact benchmark matrices; old archives untouched."""
import json
import sqlite3
import zlib

from .comparison_store import _database
from .benchmark_suite import BenchmarkSuiteResult


def _connect():
    conn = sqlite3.connect(_database(), timeout=10)
    conn.execute('''CREATE TABLE IF NOT EXISTS benchmark_suites (
        id TEXT PRIMARY KEY, created_at TEXT NOT NULL,
        summary TEXT NOT NULL, payload BLOB NOT NULL
    )''')
    return conn


def save_benchmark(result: BenchmarkSuiteResult):
    summary = {
        'benchmark_id': result.benchmark_id, 'created_at': result.created_at,
        'objectives': result.objectives, 'algorithms': result.algorithms,
        'trials_per_algorithm': len(result.seeds), 'evaluations_per_run': result.evaluations_per_run,
    }
    payload = zlib.compress(result.model_dump_json().encode('utf-8'), level=6)
    with _connect() as conn:
        conn.execute('INSERT INTO benchmark_suites(id,created_at,summary,payload) VALUES (?,?,?,?)',
                     (result.benchmark_id, result.created_at, json.dumps(summary), payload))


def list_benchmarks(limit: int = 20) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute('SELECT summary FROM benchmark_suites ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
    return [json.loads(row[0]) for row in rows]


def load_benchmark(benchmark_id: str) -> BenchmarkSuiteResult | None:
    with _connect() as conn:
        row = conn.execute('SELECT payload FROM benchmark_suites WHERE id=?', (benchmark_id,)).fetchone()
    return BenchmarkSuiteResult.model_validate_json(zlib.decompress(row[0])) if row else None
