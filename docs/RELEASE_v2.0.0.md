# Metaheuristic Lab v2.0.0 — 14 Continuous Algorithms, Exact NFE

## Added
- Exact shared NFE checkpoint adapters for Cuckoo Search (CS), Invasive Weed Optimization (IWO), and Simulated Annealing (SA).
- Comparator supports 14 continuous-objective algorithms, selecting 2–6 simultaneously; benchmark suite supports 2–4. ACO still uses its distinct symmetric TSP problem and is intentionally excluded.
- CS: each Lévy egg candidate and each abandoned nest replacement consumes exactly one NFE; checkpoints can stop between phases.
- IWO: seed evaluations are consumed one by one, parents are frozen for each generation, the top-K population is maintained after each candidate, NFE-normalized sigma schedule. Population sizes can vary.
- SA: 1 initialization and 1 objective evaluation per candidate; geometric temperature schedule distributed over the NFE horizon (not a 90-step standalone run); the current state can be worse than the archived best.
- More than 200 deterministic backend tests (exact NFE, archive monotonicity, objective fitness, bounds, seed replay, HTTP response/validation, benchmark persistence).
- Previous source-based single-algorithm simulations and SQLite records remain compatible.

## Known limitations
- All optimization/visualization remains in two dimensions.
- Equality of NFE does **not** imply equality of initial populations, iterations, wall time, or computational work in non-objective operations.
- The comparison variants of IWO and SA use a normalized budget schedule and must not be presented as identical to the standalone variants.
- The scientific p-values are exploratory, especially at 2–8 seeds.
- Browser production build and manual UI inspection require Windows-side validation.

## Windows update (existing project)
```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v2.0.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
```

Backend:
```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Frontend:
```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd run build
npm.cmd run dev
```

Sample comparison: choose **CS + IWO + SA**, Sphere, N=24, Tref=90, 3 seeds starting at 42. Each run must end with **2,184 NFE**, and all three curves must share 91 checkpoints at NFE 24,48,...,2184. Then test archive reopen and JSON/CSV exports.
