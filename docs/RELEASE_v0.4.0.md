# Metaheuristic Lab v0.4.0 — ABC module

Release date: 2026-11-11

## New in this release
- Executable, seeded 2D Artificial Bee Colony algorithm using employed, onlooker, and scout stages.
- Source selection by normalized positive nectar fitness; single-coordinate neighbor step; greedy choice; source abandonment after a configurable failure limit.
- Per-source visual telemetry (last operation, trials, selection probability) and per-frame scout/NFE counts.
- Academic ABC explanation and transparent evaluation accounting.
- Existing FA and PSO simulators, and equal-budget FA–PSO comparison and SQLite archive, remain unchanged.
- 44 backend unit/API tests passed in the release environment.

## Scope and limitations
- Canvas shows **food-source positions**, not bee bodies. Role means last operation associated with each food source.
- All frames are calculated by FastAPI first, then played back in the browser. No WebSocket live computation yet.
- ABC uses ~2N evaluations per cycle plus scouts; FA/PSO use N per iteration. Therefore the ABC results are **not yet included** in the equal-NFE comparison.
- New frontend code was syntax-checked with TypeScript compiler parsing; the local production build on Windows remains to be verified.

## Install into existing workspace
Stop both running terminals and back up personal source changes if any. Download `metaheuristic-lab-v0.4.0.zip` into Downloads; execute in PowerShell:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v0.4.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
```

The ZIP contains a single top-level `metaheuristic-lab` directory; it updates this existing workspace without deleting `.venv`, `node_modules`, Git history, or user SQLite data. Reinstall requirements, run tests and build frontend after upgrade.
