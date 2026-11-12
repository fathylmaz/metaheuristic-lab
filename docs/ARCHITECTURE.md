# Metaheuristic Lab — Architecture (Milestone 4)

## Guiding principles
- **Truthful visualization:** the visual layer only renders positions and metrics calculated by the backend. It does not invent optimization movements.
- **Reproducibility:** same algorithm, seed, objective, parameters and implementation version => same fitness and location traces; runtime is excluded.
- **Clear distinction:** an algorithm is marked `ready` only when it has an executable implementation and tests.
- **Explicit constraints:** current experiments are 2D unconstrained bounded *minimization* with four known benchmark objectives.

## Data flow

```text
React UI (TypeScript)              FastAPI (Python)
┌────────────────────────┐        ┌─────────────────────────┐
│ Catalog & algorithm nav│  GET   │ catalog.py              │
│ Parameter controls     │ ─────▶ │ RunRequest validation   │
│ Playback controls      │ POST   │ optimizers/firefly.py   │
│                        │        │ optimizers/pso.py       │
│                        │        │ optimizers/abc.py       │
│ Canvas landscape       │ ◀───── │ objective functions     │
│ Convergence graph      │ frames │ seeded NumPy RNG        │
│ JSON / CSV export      │        │ RunResponse + frame data│
└────────────────────────┘        └─────────────────────────┘
```

`POST /api/simulations` computes a complete bounded run and returns frames. The client replays the recorded trajectories at user-selected speed. **It does not currently stream iteration results in real time over WebSocket.** Actual incremental WebSocket streaming and background worker queues are future milestones.

## API
- `GET /api/health` — liveness and API version.
- `GET /api/catalog` — algorithm list/statuses, test objective metadata.
- `POST /api/simulations` — validated experiment configuration in, complete reproducible frame history out.
- `POST /api/comparisons` — two or three optimizer groups, shared evaluation budget and seed list, replicate statistics, mean convergence curves, representative motion traces; writes SQLite record.
- `GET /api/comparisons` — list saved comparison summary records (newest first, maximum 20).
- `GET /api/comparisons/{comparison_id}` — reopen a complete comparison including representative run trajectories.
- Interactive OpenAPI docs at `http://127.0.0.1:8000/docs`.

### Example request
```json
{
  "algorithm":"fa", "objective":"rastrigin", "population_size":24,
  "iterations":90, "alpha":0.18, "beta0":1.0, "gamma":0.12, "seed":42
}
```

### Example PSO request
```json
{
  "algorithm":"pso", "objective":"sphere", "population_size":24,
  "iterations":90, "inertia_weight":0.72,
  "cognitive_coefficient":1.49, "social_coefficient":1.49,
  "velocity_limit":0.20, "seed":42
}
```
The response includes `parameters` (the full validated request), `frames`, and PSO-specific agent fields (`vx`, `vy`, `pbest_x`, `pbest_y`, `pbest_fitness`).

### ABC request
```json
{ "algorithm": "abc", "objective": "sphere", "population_size": 24, "iterations": 90, "abc_limit": 30, "seed": 42 }
```
ABC agents represent food sources. Each frame includes `role`, `trials`, `selection_probability`; frame-level `scouts_this_iteration` and exact `function_evaluations` are recorded. The standalone ABC endpoint counts all scout overhead. The v0.5.0 comparison endpoint has a distinct exact-NFE ABC adapter, so FA/PSO/ABC can be compared at identical checkpoints without assuming equal ABC cycle counts.

### Safety bounds
- population_size: 5..60
- iterations: 1..250
- alpha: 0..1
- beta0: 0..3
- gamma: 0..5
- inertia_weight: 0..1.2
- cognitive_coefficient / social_coefficient: 0..4
- velocity_limit: (0,1]
- abc_limit: 1..500
- seed: 0..2,147,483,647

## Controlled comparison and persistence (v0.3)
Comparison constraints: 5..40 agents, 1..150 iterations, 2..8 trials, and 2D continuous bounded minimization. For each method and trial, the number of objective evaluations is exactly `population_size * (iterations + 1)`. The x-axis of the multi-run mean convergence chart is NFE (number of function evaluations). Means and **sample** standard deviations are computed across independent seeds, with the same seed list in FA and PSO. Success is defined as historical best objective value ≤ user-selected tolerance (all four current objectives have theoretical optimum value 0).

Stored in `backend/data/comparisons.sqlite3` (or custom `METAHEURISTIC_DATA_DIR`). The store uses compressed JSON for the full comparison payload and saves summary metadata separately for fast retrieval. No account or network sync exists. The `backend/data/` folder must not be included in source ZIP releases or Git.

## Extension interface (future)
Each optimizer module takes a shared validated run configuration and return `SimulationFrame` records with shared metrics and algorithm-specific optional inspection fields. Avoid shoehorning different populations, route/path algorithms (ACO), and single-solution methods (SA) into misleading one-size-fits-all animations.

## Current limitations
- Comparison experiments are persisted locally in SQLite, but ordinary single simulations remain session-only; there are no user accounts.
- Client session holds at most 6 runs in memory, then discards older results; JSON/CSV downloads persist only where the user saves them.
- Long runs block until completed; future streaming will decouple execution and animation.
- React frontend wasn't compiled in the artifact creation environment due unavailable external npm registry: user should run `npm.cmd install && npm.cmd run build` to verify the frontend on their machine.


### Comparison milestone v0.5.0

`ComparisonRequest.algorithms` accepts 2–3 unique entries from `fa`, `pso`, `abc`; omitted values preserve legacy FA+PSO behavior. The React interface requests all three by default.

The chosen evaluation cap is `population_size × (reference_steps + 1)`. In `app/optimizers/abc.py`, `simulate_budgeted` charges one NFE per employed, onlooker or scout objective calculation and stops at the cap, including during a phase. Comparison frames correspond to equal NFE thresholds, not equal numbers of colony cycles. The standalone ABC function still records completed cycles.

SQLite results retain the original JSON payload, so historical two-algorithm results remain loadable and are rendered using their saved `groups` list.

### DE/rand/1/bin (v1.7.0)

The new `differential.py` returns audited mutation donor positions, trial vectors, crossover masks and acceptance events per agent. Selection is synchronous on an unchanged previous population. NFE = N×(T+1). Standard `POST /api/simulations` supports `algorithm="de"`, `de_mutation_factor` and `de_crossover_rate`. See `docs/DE_METHODOLOGY.md`. ACO remains a separate discrete TSP domain; comparison remains FA/PSO/ABC only.
