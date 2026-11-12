#!/usr/bin/env python3
"""Offline, read-only pre-publication checks for the local Metaheuristic Lab checkout.

No shell execution, npm installs, SQLite access, or network access.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    'README.md','README_TR.md','README_EN.md','SECURITY.md',
    'docs/FINAL_ARCHITECTURE.md','docs/REPRODUCIBILITY.md',
    'docs/RESEARCH_LIMITATIONS.md','docs/RELEASE_CHECKLIST.md',
    'docs/RELEASE_v3.0.0.md','docs/SCREENSHOTS.md','docs/PORTFOLIO_KIT_TR.md',
]
DANGEROUS_SUFFIXES = {'.sqlite', '.sqlite3', '.db', '.env', '.pem', '.key', '.pfx'}

def checks(root: Path = ROOT) -> list[str]:
    problems: list[str] = []
    pkg = json.loads((root / 'frontend/package.json').read_text(encoding='utf-8'))
    version = pkg['version']
    api = (root / 'backend/app/main.py').read_text(encoding='utf-8')
    workflow = (root / '.github/workflows/ci.yml').read_text(encoding='utf-8')
    for expected in (f"version='{version}'", f"'version': '{version}'"):
        if expected not in api:
            problems.append(f'Missing FastAPI version string: {expected}')
    if 'frontend/package.json' not in workflow:
        problems.append('CI Docker health assertion is not tied to frontend/package.json')
    if '"version":"2.9.0"' in workflow:
        problems.append('Obsolete hard-coded 2.9.0 CI assertion')
    for f in REQUIRED_DOCS:
        if not (root / f).is_file():
            problems.append(f'Missing document: {f}')
    required_ignores = ('backend/data/', 'backups/', 'node_modules/', 'outputs/', 'test-results/')
    ignore = (root / '.gitignore').read_text(encoding='utf-8')
    for pattern in required_ignores:
        if pattern not in ignore:
            problems.append(f'Missing gitignore rule: {pattern}')
    if pkg['devDependencies'].get('rollup','').startswith('npm:@rollup/wasm-node@') is False:
        problems.append('Windows Rollup WASM alias has been lost')
    if not (root/'frontend/scripts/capture_screenshots.mjs').is_file():
        problems.append('Real screenshot capture helper missing')
    if (root/'LICENSE').exists():
        print('INFO: LICENSE present: confirm owner permission before publishing')
    # Only inspect source ZIP-like release files, not ignored local user data.
    for folder in (root/'docs',root/'frontend/src',root/'backend/app'):
        for f in folder.rglob('*'):
            if f.is_file() and f.suffix.lower() in DANGEROUS_SUFFIXES:
                problems.append(f'Sensitive-looking file among sources: {f.relative_to(root)}')
    return problems

if __name__ == '__main__':
    errors = checks()
    if errors:
        for error in errors: print('FAIL:', error)
        raise SystemExit(1)
    print('Release audit passed: version, CI, docs, WASM dependency, and source hygiene.')
    print('Still required: user-run Windows/Playwright/Docker tests, license decision, real screenshots, and GitHub CI.')
