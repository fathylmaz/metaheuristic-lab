# Metaheuristic Lab v1.2.0 — SSA

- Ninth-to-tenth continuous optimizer addition: Salp Swarm Algorithm, distinct 2D leader/follower semantics.
- Frozen food location per iteration, c1 schedule and independent c2/c3 draws, sequential followers.
- Per-agent telemetry for actual previous position and leader-food or predecessor target; exact NFE accounting.
- Frontend SSA settings, distinct chain connections and leader/food reference, clickable salp mathematical details, SSA learning guide.
- No changes to the FA/PSO/ABC equal-NFE comparison scope; ACO remains separate TSP.
- Documentation: `docs/SSA_METHODOLOGY.md`.
- User Windows production build remains to be validated with `npm.cmd run build`.

Install with `Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v1.2.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force` after stopping both development servers. The ZIP has one top-level `metaheuristic-lab/` folder; runtime data / .venv / node_modules are not packaged. Back up locally edited source files before overwriting.
