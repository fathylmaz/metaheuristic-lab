# Metaheuristic Lab v1.4.0 — Invasive Weed Optimization

- **12th working optimizer:** IWO (Invasive Weed Optimization), fitness-dependent seed reproduction, Gaussian dispersal with decaying standard deviation, and global competitive exclusion.
- **Variable-size population** capped by independent `iwo_max_population`; the initial population, live population and produced seeds are never conflated.
- **Accurate computation accounting:** objective function evaluations count every seed, even if discarded by competition. Parents retaining their positions are not re-evaluated.
- **Reproducible full telemetry:** persistent weed IDs, actual parent coordinates, raw sampled Gaussian steps, birth generation, reproduction and elimination totals, and sigma on every frame.
- **Dedicated visual exploration:** surviving offspring drawn with authentic birth-to-parent connections, selectable plants, sigma and colony population metrics; per-algorithm controls and learning guide.
- **Scope:** retains all earlier eleven working algorithms and the existing FA/PSO/ABC equal-NFE comparison / SQLite history unchanged. IWO is not yet a member of that comparison because its evaluation schedule differs.
- **Tests:** 130 backend tests passed in the build environment (including 10 new IWO tests). Frontend TSX syntax checked; full production Vite build must be verified on the user's Windows workstation.
- **Upgrade:** ZIP contains one `metaheuristic-lab/` directory; unpack to the parent folder with `Expand-Archive -Force`. ZIP never contains `.git`, `.venv`, `node_modules` or SQLite user data.

Research background: Mehrabian and Lucas (2006), *Ecological Informatics* 1(4), 355–366; DOI: 10.1016/j.ecoinf.2006.07.003. See `docs/IWO_METHODOLOGY.md` for exact implementation details.
