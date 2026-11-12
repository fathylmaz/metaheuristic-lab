"""Measure local API response times without imposing hardware-dependent thresholds.

Usage from repository root:
  cd backend
  python ../scripts/profile_api.py --repeats 5 --iterations 20

Output is descriptive; do not compare across machines without controlled hardware.
"""
from __future__ import annotations

import argparse
import json
import statistics
from time import perf_counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))

from fastapi.testclient import TestClient
from app.main import app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--iterations', type=int, default=20)
    parser.add_argument('--population', type=int, default=12)
    parser.add_argument('--algorithms', nargs='+', default=['fa', 'pso', 'abc', 'gwo', 'de'])
    args = parser.parse_args()
    if not (1 <= args.repeats <= 30 and 1 <= args.iterations <= 250 and 5 <= args.population <= 60):
        parser.error('Repeat/iteration/population arguments out of bounds')
    result = {}
    with TestClient(app) as client:
        for algorithm in args.algorithms:
            durations = []
            nfe = None
            for i in range(args.repeats):
                payload = {'algorithm': algorithm, 'objective': 'sphere',
                           'iterations': args.iterations, 'population_size': args.population,
                           'seed': 42 + i}
                started = perf_counter()
                response = client.post('/api/simulations', json=payload)
                duration = (perf_counter() - started) * 1000
                if response.status_code != 200:
                    raise RuntimeError(f'{algorithm}: HTTP {response.status_code}: {response.text[:300]}')
                durations.append(duration)
                nfe = response.json()['frames'][-1]['function_evaluations']
            result[algorithm] = {
                'repeats': args.repeats,
                'evaluations_last_run': nfe,
                'mean_ms': round(statistics.mean(durations), 3),
                'median_ms': round(statistics.median(durations), 3),
                'max_ms': round(max(durations), 3),
            }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
