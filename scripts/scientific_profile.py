"""Run a controlled LOCAL factorial profile over D-dimensional objectives.

Examples (from the project root):
  py -3.13 scripts/scientific_profile.py --algorithms pso gwo de --objectives sphere rastrigin --dimensions 2 5 10 --trials 10 --population 16 --iterations 30

Descriptive timing only: independent-run durations are not cross-machine results,
and optimization measurements are not an independent reference implementation.
No user database is read or written by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

import numpy as np
from pydantic import ValidationError

from app.dimensional import DimensionalRequest, run_dimensional
from app.scientific_validation import audit_dimensional

ALGORITHMS = ['pso', 'gwo', 'de', 'woa', 'mfo', 'ssa', 'fa', 'ba', 'gsa', 'abc', 'cs', 'sma', 'iwo', 'sa']
OBJECTIVES = ['sphere', 'rastrigin', 'ackley', 'rosenbrock', 'griewank']


def run_matrix(algorithms: list[str], objectives: list[str], dimensions: list[int],
               population: int, iterations: int, trials: int, seed: int) -> dict:
    if not (2 <= len(algorithms) <= 4) or len(set(algorithms)) != len(algorithms):
        raise ValueError('Select 2 to 4 distinct algorithms')
    if any(a not in ALGORITHMS for a in algorithms):
        raise ValueError('Unknown algorithm')
    if len(set(objectives)) != len(objectives) or any(o not in OBJECTIVES for o in objectives):
        raise ValueError('Unknown or repeated objective')
    if len(set(dimensions)) != len(dimensions) or any(d not in (2, 5, 10, 30) for d in dimensions):
        raise ValueError('Dimensions must be distinct members of 2, 5, 10, 30')
    if not objectives or not dimensions:
        raise ValueError('At least one objective and dimension required')

    source = ROOT / 'backend' / 'app' / 'dimensional.py'
    report = {
        'protocol_version': '1.0', 'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'environment': {
            'python_version': platform.python_version(), 'numpy_version': np.__version__,
            'platform': platform.system(), 'machine': platform.machine(),
            'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        },
        'protocol': {
            'algorithms': algorithms, 'objectives': objectives, 'dimensions': dimensions,
            'population_size': population, 'iterations': iterations,
            'trials_per_cell': trials, 'seed_start': seed,
            'objective_evaluation_budget': 'Identical NFE per algorithm within each cell',
            'runtime_scope': 'Optimizer trial duration excluding frontend/network and archive IO',
            'tuning': 'Default algorithm parameters, no cross-problem tuning performed',
        },
        'cells': [],
        'limitations': [
            'Each cell is a separate D-dimensional optimization experiment; raw errors are not pooled across functions.',
            'Timing is local to the machine and software load. It is not normalized across hardware or guaranteed reproducible.',
            'Shared seed identifiers do not imply identical initial populations among algorithms.',
            'No algorithm superiority claim follows from these descriptive results alone.',
        ],
    }
    for objective in objectives:
        for dimension in dimensions:
            request = DimensionalRequest(algorithms=algorithms, objective=objective,
                dimensions=dimension, population_size=population, iterations=iterations,
                trials=trials, seed_start=seed)
            result = run_dimensional(request)  # Explicitly does NOT call save_dimensional.
            audit = audit_dimensional(result)
            if audit['status'] != 'passed':
                raise RuntimeError('Scientific audit failed: ' + '; '.join(audit['issues']))
            report['cells'].append({
                'objective': objective, 'dimensions': dimension,
                'evaluations_per_run': result.evaluations_per_run,
                'total_evaluations': result.total_evaluations,
                'audit_status': audit['status'], 'groups': audit['groups'],
                'paired_comparisons': audit['paired_comparisons'],
            })
    return report


def markdown_report(report: dict) -> str:
    protocol = report['protocol']
    lines = [
        '# Metaheuristic Lab — Yerel bilimsel profil', '',
        f"Üretim (UTC): {report['generated_at_utc']}", '',
        f"Python: {report['environment']['python_version']} · NumPy: {report['environment']['numpy_version']} · Platform: {report['environment']['platform']} ({report['environment']['machine']})", '',
        f"Motor SHA-256: `{report['environment']['source_sha256']}`", '',
        f"Algoritmalar: {', '.join(a.upper() for a in protocol['algorithms'])}",
        f"Fonksiyonlar: {', '.join(protocol['objectives'])}",
        f"Boyutlar: {', '.join(str(d) for d in protocol['dimensions'])}",
        f"Birey: {protocol['population_size']} · İterasyon: {protocol['iterations']} · Tekrar: {protocol['trials_per_cell']} · İlk tohum: {protocol['seed_start']}", '',
        '## Hücre bazlı ölçümler', '',
        '| Fonksiyon | D | Algoritma | n | NFE / koşu | Ort. mutlak hata | %95 keşifsel alt–üst | Medyan süre (ms) | p95 süre (ms) | Başarı |',
        '|---|---:|---|---:|---:|---:|---|---:|---:|---:|',
    ]
    for cell in report['cells']:
        for g in cell['groups']:
            lines.append(f"| {cell['objective']} | {cell['dimensions']} | {g['algorithm'].upper()} | {g['trials']} | {g['nfe_per_run']} | {g['mean_error']:.6g} | {g['ci95_low']:.6g} – {g['ci95_high']:.6g} | {g['median_duration_ms']:.3f} | {g['p95_duration_ms']:.3f} | {g['success_rate']:.1%} |")
    lines += ['', '## Yorumlama sınırları', '']
    lines += [f'- {warning}' for warning in report['limitations']]
    lines += ['', 'Tüm NFE bütçeleri ve arşiv vektörleri aynı kaynak motoruyla denetlendi; algoritmaların dış referansla doğruluğu kanıtlanmaz.', '']
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--algorithms', nargs='+', default=['pso', 'gwo', 'de'], choices=ALGORITHMS)
    parser.add_argument('--objectives', nargs='+', default=['sphere', 'rastrigin'], choices=OBJECTIVES)
    parser.add_argument('--dimensions', nargs='+', type=int, default=[2, 5, 10], choices=[2, 5, 10, 30])
    parser.add_argument('--population', type=int, default=16)
    parser.add_argument('--iterations', type=int, default=30)
    parser.add_argument('--trials', type=int, default=10)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'outputs' / 'scientific_profile')
    args = parser.parse_args()
    try:
        report = run_matrix(args.algorithms, args.objectives, args.dimensions,
                            args.population, args.iterations, args.trials, args.seed)
    except (ValueError, ValidationError) as exc:
        parser.error(str(exc))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / 'scientific-profile.json'
    md_path = args.output_dir / 'scientific-profile.md'
    if json_path.exists() or md_path.exists():
        parser.error('Output files already exist. Supply a new --output-dir to avoid overwriting a prior experiment.')
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    md_path.write_text(markdown_report(report), encoding='utf-8')
    print(f'Scientific profile: {len(report["cells"])} problem×dimension cells; verified NFE.')
    print(f'JSON: {json_path}\nMarkdown: {md_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
