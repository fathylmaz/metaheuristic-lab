# v1.3.0 – Slime Mould Algorithm

- 11th ready optimizer: two-dimensional Slime Mould Algorithm (SMA), original-style adaptive rank weights and three movement branches (approach, contract, random restart).
- New parameter `sma_restart_probability` default `0.03` and `sma` in the shared `/api/simulations` contract.
- Detailed per-agent telemetry: frozen source locations, old and elite positions, weighted feedback, decision probability, draw values, `vb/vc` vectors, raw and clipped candidate.
- Purpose-built interface: agent selection, branch-specific colors and lines, feedback metrics, mathematical learning view, and CSV/JSON export.
- Preserves FA, PSO, ABC, ACO, CS, MFO, GWO, WOA, BA, SSA, and the existing FA/PSO/ABC comparison module with SQLite storage.
- Full backend test suite: **120 passed** locally. The full React/Vite production build should be verified on Windows as usual.
- Research note: original `vc * X_i` contraction biases candidates toward the origin, especially at final iteration, and this is surfaced explicitly rather than concealed.
- No changes or deletions to Git metadata, Python virtualenv, npm dependencies, or the user's local data are included in this source ZIP.

See `docs/SMA_METHODOLOGY.md` for exact formulas and implementation conventions.
