# Metaheuristic Lab v2.6.0 — Archived Scientific Report Studio

## Added

- New **Akademik Raporlar** sidebar tab with filterable read-only archive listing.
- Structured scientific reports from **comparison**, **multi-function benchmark**, **parameter sensitivity** and **true D-dimensional experiments**.
- Export in JSON and Markdown; standalone, print-ready HTML for browser **Save as PDF**.
- Parameter disclosures, seed-by-seed result tables, NFE budgets, stored methodology, source IDs and SHA-256 provenance hashes.
- Discussion of experimental limitations: unequal wall clock costs, common seed labels, limited repeats, OFAT assumptions and projection boundaries.
- 10 new backend tests and HTML escaping with Content-Security-Policy.

## Preserved

All 15 2D simulation algorithms, all 14 D-dimensional continuous optimizers, ACO TSP, existing benchmarks, sensitivity experiments, comparisons, SQLite archive and CLI/Docker configurations.

## Installation

Stop the current servers, then extract this ZIP into the parent directory that contains your existing `metaheuristic-lab` folder (with overwrite). **Do not delete the existing installation or SQLite database.** The ZIP contains no local database, `.venv`, `node_modules` or `.git` folder.

Test:

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Frontend in a separate shell:

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd run build
npm.cmd run dev
```

**Backend automated tests in build environment:** 396 passed. **Frontend production build:** TypeScript/TSX syntax checked; the full `tsc -b && vite build` must be verified on the Windows machine with installed `node_modules`.

## User acceptance

1. From the new **Akademik Raporlar** menu open an existing high-dimensional result.
2. Confirm that the report contains the true dimension, objective, selected algorithms, NFE, seeds and complete solution vectors.
3. Open **Yazdır / PDF**; confirm the standalone report and browser print layout.
4. Download **Markdown** and **JSON**.
5. Switch to a comparison, benchmark or sensitivity report and confirm that its source-specific statistics differ appropriately.
6. Revisit the earlier experiment and confirm the original saved results remain unchanged.
