# Metaheuristic Lab v1.9.0 — Multi-Objective Benchmark Studio

## Additions

- New **Benchmark Stüdyosu** tab; benchmark 2–5 objective functions and 2–4 optimization algorithms on common NFE and seed labels.
- Four new functions: Griewank, Himmelblau, Beale, Booth; available in single-algorithm simulations and comparison experiments too.
- Per-function error matrix, tie-aware ranks, aggregate mean-rank and success-rate summaries, seed-level detail, CSV/JSON export.
- Persistent SQLite `benchmark_suites` table alongside old `comparisons` history. Existing archives untouched.
- 7 new test cases covering optima, deterministic experiments, fair NFE, validation and archive.

## Installation

Stop both development servers and save/backup any local source edits, then from PowerShell:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v1.9.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
```

Archive root includes `metaheuristic-lab/`, so the destination is the **parent directory**, not the project itself. `.git`, `.venv`, `node_modules` and locally created `backend/data/` are not in the archive.

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

In a second terminal:

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd run build
npm.cmd run dev
```

## Acceptance check

Benchmark Studio: choose Sphere, Rastrigin, Ackley, Rosenbrock; PSO, GWO, DE; N=24, reference steps=90, repeat count=3, first seed=42. Expected **2,184 NFE per algorithm/objective/run** and **78,624 total NFE**. Results depend on selected algorithm settings and should be deterministic for a fixed configuration. Verify rows, per-objective ranks, CSV/JSON downloads, saved experiment re-opening, and continued access to prior `Karşılaştırma Laboratuvarı` and simulations.

Backend automated tests passed in the build environment. React full Vite production build requires Windows host verification because dependencies were not available in the build environment.
