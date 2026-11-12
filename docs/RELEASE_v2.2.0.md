# Metaheuristic Lab v2.2.0 — High-Dimensional Laboratory

- New page: `Yüksek Boyut Laboratuvarı`.
- True 2, 5, 10 and 30-dimensional PSO, GWO and DE implementations; five objective functions.
- Multi-seed convergence under exact objective-evaluation budgets, coordinate-vector inspector and explicitly labeled first-two-coordinate projections.
- Persisted, reloadable experiments and JSON/CSV export.
- New endpoints: `POST /api/dimensional`, `GET /api/dimensional`, `GET /api/dimensional/{experiment_id}`.
- 15 existing standalone 2D algorithm modules and old comparison/benchmark/sensitivity pages retained.
- This is an initial D-dimensional subset: support for the other 11 continuous optimizers is future work.
- See `docs/DIMENSIONAL_METHODOLOGY.md`.

## Installation / Windows

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v2.2.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
```

Then restart backend and frontend. Run `python -m pytest -q` and `npm.cmd run build`.
