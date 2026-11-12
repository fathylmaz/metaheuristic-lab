"""Test live SQLite backup and explicit integrity validation without Docker."""
from pathlib import Path
from contextlib import closing
import importlib.util
import json
import sqlite3
import zipfile

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts' / 'backup_experiments.py'
spec = importlib.util.spec_from_file_location('backup_experiments', SCRIPT)
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


def sample_db(path: Path):
    conn = sqlite3.connect(path)
    conn.execute('CREATE TABLE comparisons(id TEXT PRIMARY KEY, result TEXT)')
    conn.execute('INSERT INTO comparisons VALUES(?, ?)', ('study-42', 'saved'))
    conn.commit()
    return conn


def test_backup_and_verify_without_mutating_source(tmp_path):
    db = tmp_path / 'comparisons.sqlite3'
    con = sample_db(db)
    try:
        archive = tmp_path / 'snapshot.zip'
        details = backup.create_backup(db, archive)
        assert len(details['sha256']) == 64
        assert backup.verify_backup(archive) == details
        with zipfile.ZipFile(archive) as z:
            assert set(z.namelist()) == {'manifest.json', 'comparisons.sqlite3'}
        assert con.execute('SELECT result FROM comparisons WHERE id=?', ('study-42',)).fetchone()[0] == 'saved'
    finally:
        con.close()


def test_existing_backup_is_not_overwritten(tmp_path):
    db = tmp_path / 'comparisons.sqlite3'
    with closing(sample_db(db)):
        pass
    dest = tmp_path / 'snapshot.zip'
    backup.create_backup(db, dest)
    before = dest.read_bytes()
    with pytest.raises(FileExistsError):
        backup.create_backup(db, dest)
    assert dest.read_bytes() == before


def test_missing_database_is_an_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        backup.create_backup(tmp_path/'missing.sqlite3', tmp_path/'out.zip')
    assert not (tmp_path/'out.zip').exists()


def test_tampered_backup_is_detected(tmp_path):
    db = tmp_path / 'comparisons.sqlite3'
    with closing(sample_db(db)):
        pass
    good = tmp_path/'good.zip'
    backup.create_backup(db, good)
    bad = tmp_path/'bad.zip'
    with zipfile.ZipFile(good) as origin, zipfile.ZipFile(bad, 'w') as archive:
        archive.writestr('comparisons.sqlite3', b'not a valid sqlite database')
        archive.writestr('manifest.json', origin.read('manifest.json'))
    with pytest.raises(ValueError, match='SHA-256'):
        backup.verify_backup(bad)


def test_backup_command_fails_cleanly_on_missing_file(tmp_path):
    assert backup.main(['--source', str(tmp_path/'doesnotexist.sqlite3'), '--output', str(tmp_path/'no.zip')]) == 1


def test_backup_explicitly_closes_sqlite_connections(tmp_path, monkeypatch):
    """Windows cleanup requires closed handles, not only committed transactions."""
    db = tmp_path / 'comparisons.sqlite3'
    with closing(sample_db(db)):
        pass

    actual_connect = sqlite3.connect
    opened = []

    class TrackedConnection(sqlite3.Connection):
        close_count = 0

        def close(self):
            self.close_count += 1
            return super().close()

    def tracked_connect(*args, **kwargs):
        kwargs['factory'] = TrackedConnection
        con = actual_connect(*args, **kwargs)
        opened.append(con)
        return con

    monkeypatch.setattr(backup.sqlite3, 'connect', tracked_connect)
    backup.create_backup(db, tmp_path / 'snapshot.zip')
    assert len(opened) >= 4  # live source, snapshot, plus integrity checks
    assert all(con.close_count == 1 for con in opened)
