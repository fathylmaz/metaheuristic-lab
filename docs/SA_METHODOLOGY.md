# Simulated Annealing (SA) — mathematical method and implementation

## Model and source

This is an inspectable **two-dimensional, single-solution, Metropolis-style simulated annealing** implementation for continuous bounded minimization. The underlying acceptance principle is associated with Kirkpatrick, Gelatt & Vecchi (1983), *Optimization by Simulated Annealing*, **Science** 220(4598), pp. 671–680. DOI: [10.1126/science.220.4598.671](https://doi.org/10.1126/science.220.4598.671).

This software uses specific documented engineering choices rather than claiming to reproduce one universal SA implementation: a Gaussian neighbor, hard clipping at objective bounds, geometric cooling, one candidate per iteration, and a separately archived best-ever solution. The clipped proposal may not be symmetric at the boundary; this is a heuristic optimizer, **not an unbiased equilibrium Monte Carlo sampler**.

## Algorithm

For a selected 2D objective `f(x,y)` and domain `[lower,upper]²`:

1. Draw the initial current solution uniformly within bounds; evaluate `f(current)` once. Initialize best-ever to current.
2. At iteration `t ∈ {1,...,T}`, set `temperature = T0 × cooling_rate^(t-1)`. `T0 > 0`, `cooling_rate ∈ (0,1]`.
3. Sample a componentwise Gaussian displacement `step ~ Normal(0, (step_scale × (upper-lower))² I)`; construct `proposal = clip(current + step, lower, upper)`.
4. Evaluate the candidate exactly once, even if subsequently rejected. Set `delta = f(proposal) - f(current)`.
5. Accept with probability `1` if `delta <= 0`, otherwise `exp(-delta / temperature)`; draw `u ~ Uniform[0,1)` and accept when `u < p`.
6. On acceptance, replace current with candidate (even when candidate is worse). On rejection, current remains unchanged. Independently retain the global best-ever solution when an improved current is found.
7. Record current and candidate locations, evaluated objective, `delta`, probability, random draw, decision, temperature, NFE and cumulative event counts.

## Exact evaluation accounting

- Initial state: **1** objective evaluation, frame index **0**.
- Each iteration: **1** candidate evaluation, regardless of acceptance.
- With `T` iterations: **T+1** evaluations, **T+1** frames.
- `population_size` from the shared form is **ignored** for SA; it is not a population-based method. The UI intentionally hides the population slider.
- This means equal iteration counts between SA and swarm optimizers **are not equal computation budgets**. SA is not inserted into the existing FA/PSO/ABC equal-NFE comparison until a proper evaluation-budget adapter exists.

## Explainable telemetry and visualization

A `SimulationFrame` carries a single `AgentState` (id `0`) for **current** solution. For each step the agent contains `sa_previous`, `sa_candidate`, `sa_step`, `sa_candidate_fitness`, `sa_delta`, `sa_accept_probability`, `sa_accept_draw`, and `sa_accepted`. Frames also contain `sa_temperature`, cumulative `sa_accepted_total`, `sa_uphill_accepted_total`, and `sa_rejected_total`.

- A **green circle** marks an accepted evaluated candidate.
- An **orange crossed circle** marks a rejected candidate; the current point stays where it was.
- The green best-ever crosshair is independent of current. It may remain at a better historical solution after an uphill acceptance.
- The temperature history is plotted on a logarithmic ordinate, with acceptance/rejection event markers.
- The best-ever convergence chart is monotonically non-increasing; the current objective need not be.

## Verification

`backend/tests/test_annealing.py` checks the exact cooling endpoints, Metropolis probability, numerical edge cases, deterministic frames, bounded positions, arithmetic reconstruction of candidate positions and fitness, acceptance and rejection correctness, monotonic best archive, all four benchmark objectives, API schema, input validation, and exactly one NFE per proposal. Backend release tests: **141 passing** in the build environment.

## Limitations and next steps

- A fixed Gaussian neighbor may be inefficient on complex multimodal objectives; parameter tuning matters.
- The 2D renderer is for learning and does not establish general high-dimensional performance.
- For research-grade cross-algorithm evaluation use the same NFE budget, a set of random seeds, and multiple objective functions; wall-clock speed is hardware-dependent.
- Future candidates: adaptive reheating and separate temperature/step-schedule experiments, with each variant clearly labeled.
