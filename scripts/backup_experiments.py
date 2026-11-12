#!/usr/bin/env python3
"""Safely back up a *running* Metaheuristic Lab SQLite archive.

Uses SQLite's online backup API, never copies a live .sqlite3 file directly.
This tool is local-only; the result is a ZIP containing an integrity-tested SQLite
snapshot and a SHA-256 manifest. It does not modify existing experiments.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import zipfile

DB_NAME = 'comparisons.sqlite3'
MANIFEST_NAME = 'manifest.json'
MAX_VERIFY_BYTES = 1024 * 1024 * 1024  # reject unexpectedly huge/corrupted backup inputs


def default_source() -> Path:
    root = Path(__file__).resolve().parents[1]
    return Path(os.environ.get('METAHEURISTIC_DATA_DIR', str(root / 'backend' / 'data'))) / DB_NAME


def _integrity(db_path: Path) -> None:
    con = sqlite3.connect(db_path.as_posix())
    try:
        status = con.execute('PRAGMA integrity_check').fetchone()[0]
        if status != 'ok':
            raise ValueError(f'SQLite bütünlük hatası: {status}')
    finally:
        con.close()


def create_backup(source: Path, destination: Path) -> dict:
    source = Path(source)
    destination = Path(destination)
    if not source.is_file():
        raise FileNotFoundError(f'SQLite arşivi bulunamadı: {source}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f'Hedef zaten var, üzerine yazılmadı: {destination}')
    with tempfile.TemporaryDirectory(prefix='metaheuristic-backup-') as tmp:
        snapshot = Path(tmp) / DB_NAME
        # SQLite Connection.__exit__ only commits/rolls back; it does NOT close.
        # Explicit closure is essential before TemporaryDirectory cleanup on Windows.
        with closing(sqlite3.connect(f'file:{source.resolve().as_posix()}?mode=ro', uri=True, timeout=30)) as src:
            with closing(sqlite3.connect(snapshot, timeout=30)) as dst:
                src.backup(dst)
        _integrity(snapshot)
        contents = snapshot.read_bytes()
        digest = hashlib.sha256(contents).hexdigest()
        manifest = {
            'schema_version': 1,
            'created_at_utc': datetime.now(timezone.utc).isoformat(),
            'database_file': DB_NAME,
            'bytes': len(contents),
            'sha256': digest,
        }
        # Exclusive creation prevents accidental overwrites. Remove incomplete
        # outputs if the write fails, never replacing a previous backup.
        created = False
        try:
            with destination.open('xb') as fh:
                created = True
                with zipfile.ZipFile(fh, mode='w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                    archive.writestr(DB_NAME, contents)
                    archive.writestr(MANIFEST_NAME, json.dumps(manifest, indent=2, ensure_ascii=False))
            verify_backup(destination)
        except Exception:
            if created:
                destination.unlink(missing_ok=True)
            raise
    return manifest


def verify_backup(archive_path: Path) -> dict:
    with zipfile.ZipFile(archive_path, 'r') as archive:
        if set(archive.namelist()) != {DB_NAME, MANIFEST_NAME}:
            raise ValueError('Yedekte beklenmeyen veya eksik dosya var')
        manifest = json.loads(archive.read(MANIFEST_NAME))
        if manifest.get('schema_version') != 1 or manifest.get('database_file') != DB_NAME:
            raise ValueError('Yedek manifest sürümü veya adı hatalı')
        info = archive.getinfo(DB_NAME)
        if info.file_size > MAX_VERIFY_BYTES:
            raise ValueError('Yedek boyutu güvenlik sınırını aşıyor')
        data = archive.read(DB_NAME)
        if len(data) != manifest.get('bytes') or hashlib.sha256(data).hexdigest() != manifest.get('sha256'):
            raise ValueError('Yedek SHA-256/uzunluk doğrulaması başarısız')
        with tempfile.TemporaryDirectory(prefix='metaheuristic-verify-') as tmp:
            snapshot = Path(tmp) / DB_NAME
            snapshot.write_bytes(data)
            _integrity(snapshot)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='SQLite deney veritabanı online yedekleme / doğrulama')
    parser.add_argument('--source', type=Path, default=default_source(), help='Canlı SQLite dosyası')
    parser.add_argument('--output', type=Path, help='Oluşturulacak yeni ZIP dosyası')
    parser.add_argument('--verify', type=Path, help='Var olan ZIP dosyasını doğrula; hiçbir veri değiştirilmez')
    args = parser.parse_args(argv)
    try:
        if args.verify:
            manifest = verify_backup(args.verify)
            print(f"YEDEK DOĞRULANDI: {args.verify} ({manifest['bytes']} byte, SHA-256 {manifest['sha256']})")
            return 0
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        output = args.output or Path(__file__).resolve().parents[1] / 'backups' / f'metaheuristic-experiments-{timestamp}.zip'
        manifest = create_backup(args.source, output)
        print(f"YEDEK BAŞARILI: {output}\nSHA-256: {manifest['sha256']}")
        return 0
    except (OSError, ValueError, sqlite3.Error, zipfile.BadZipFile, KeyError, TypeError) as error:
        print(f'YEDEK HATASI: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
