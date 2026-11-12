# Multi-Objective Benchmark Suite — v2.0.0

## Scope

Benchmark Studio is a separate **two-dimensional** controlled experiment module. Select **2–5** functions and **2–4** compatible continuous-optimization algorithms, 2–8 repeated seed labels, and a common evaluation budget. The UI offers 8 2D objectives; the backend accepts a maximum of **200,000 total NFE** per experiment request to prevent accidentally expensive runs.

Supported functions with the canonical optimum and plotted square domain:

| ID | Function | Optimum position | Optimum value | Bounds |
|---|---|---|---|---|
| sphere | x² + y² | (0, 0) | 0 | [-5.12, 5.12] |
| rastrigin | 20 + x² + y² − 10(cos(2πx)+cos(2πy)) | (0, 0) | 0 | [-5.12, 5.12] |
| ackley | classic 2D Ackley | (0, 0) | approximately zero (floating point) | [-5, 5] |
| rosenbrock | (1−x)² + 100(y−x²)² | (1, 1) | 0 | [-3, 3] |
| griewank | 1 + (x²+y²)/4000 − cos(x)cos(y/√2) | (0, 0) | 0 | [-6, 6] |
| himmelblau | (x²+y−11)² + (x+y²−7)² | (3, 2) (one of four global minima) | 0 | [-5, 5] |
| beale | (1.5−x+xy)² + (2.25−x+xy²)² + (2.625−x+xy³)² | (3, 0.5) | 0 | [-4.5, 4.5] |
| booth | (x+2y−7)² + (2x+y−5)² | (1, 3) | 0 | [-10, 10] |

All these are unconstrained 2D box-bounded benchmark simulations. The terms “Himmelblau four minima” and “Griewank multimodal” refer to their mathematical properties; algorithm convergence varies by parameters and seeds.

## Method

1. Every trial receives its own deterministic seed label (`seed_start, seed_start+1, ...`). The seed labels match across algorithms, **not** initial populations, which are drawn differently by the different methods.
2. Every selected algorithm completes the same number of true objective evaluations within **each** objective. The NFE cap is `N × (reference_steps+1)` and includes candidate evaluations; ABC/CS can stop inside phases, IWO has variable population, and SA is a single-state optimizer with one evaluation per neighbor proposal. IWO dispersal and SA cooling are normalized to the shared NFE horizon (not identical to standalone generation schedules).
3. For each final trial result, compute **absolute error to a known global optimal value**, not raw final fitness. The global optimum is calculated from the function metadata (for Ackley, floating point epsilon is possible).
4. **Per-objective** statistics: mean and median absolute error, sample standard deviation (n−1), best error, and success fraction (`error <= success_tolerance`).
5. **Per-objective ranking**: sort algorithm mean absolute errors, with equal values receiving average (fractional) ranks. **Mean rank** and average success rate across objectives are reported as descriptive summaries. These are not tests of significance and do not guarantee success on unseen problems.
6. Raw values from different objectives must **not be averaged together**: the scales, geometries, and bounds are not interchangeable. We only average ranks and success rates across the selected objectives.
7. Timing is machine dependent. Results are stored in a **new SQLite table `benchmark_suites`** in the same database, without changing the old `comparisons` table.
8. Available exports: trial-by-trial CSV, complete JSON with config and metrics. Neither includes all per-iteration agent frames; those belong to the individual Comparison Laboratory.

## Limitations

- This is not COCO/BBOB certification: no rotated/randomized instances, dimension scaling, target-based ERT benchmark suite, confidence intervals, or robust external validation yet.
- Default optimizer parameters are shared with the single-function Comparison Laboratory; separate parameter-tuning across problems is not included in this release.
- The global optimum positions are known for the eight included functions, but the finite search domains and their range widths vary.
- TSP/ACO is excluded as a discrete optimization family. CS, IWO and SA use documented budgeted variants in the continuous-function comparison and benchmark modules; standalone modules remain independent.
- If the number of objectives or algorithms is too large, requests are rejected before running. The API is synchronous; streamed background progress is not implemented.

## Tests

`python -m pytest -q` — objective optima, API validation, exact NFE for all trials, ranks and ties, fixed-seed repeatability, SQLite persistence, backward compatibility with the comparison archive, and existing optimizer tests.
