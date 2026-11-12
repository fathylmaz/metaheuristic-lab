# Numerical methodology and reproducibility

## Problem class
This milestone only solves a **bounded continuous minimization task** in **two dimensions**. Available functions are Sphere, Rastrigin, Ackley and Rosenbrock with their documented standard definitions. The domain is fixed per objective.

## Firefly mechanism
A firefly with worse objective value can move toward a better one. At distance `r`, attractiveness is

`beta(r) = beta0 * exp(-gamma * r^2)`.

A pairwise attraction update is:

`x_i ← clip(x_i + beta(r)*(x_j-x_i) + alpha*(high-low)*U(-0.5,0.5), low, high)`.

Details of **this implementation** (not an assertion that every original FA publication uses precisely this order):
1. Generate the entire initial 2D population using NumPy `default_rng(seed)`.
2. Evaluate each initial position exactly once. Archive the best seen position/value.
3. At each generation, take **a snapshot** of all current fitness values and target positions.
4. For each firefly `i`, visit every individual `j` that was brighter (`fitness_j < fitness_i`) in the snapshot. Apply sequential attraction and an independent uniform jitter vector at each encounter. Choose the strongest attraction target for visualization.
5. If an agent has no brighter peer, apply a single jitter vector to allow exploration. Clip every candidate to domain bounds.
6. Evaluate *once per agent* after all attraction steps, not after every pairwise move. Update archive if a better solution appears.
7. Record the exact agent positions, their objective values, per-generation relative brightness, strongest attraction target, diversity, best current solution, best historical solution, and total objective function evaluations.

The per-generation brightness normalization is `1-(fitness_i-min_fitness)/(max_fitness-min_fitness)` (or 1 for identical fitness). It is only a relative **display measure**, not a physical light energy estimate.

**Best-so-far** is a historical archive. **Current best** is the best member of the current generation. The archive is not always a member of the current generation.

**Diversity** is mean Euclidean distance to the current population centroid.

## Particle Swarm Optimization (PSO) — milestone 2

This is a **synchronous global-best PSO (gbest-PSO)** implementation, following Kennedy and Eberhart's velocity-position idea. For particle `i` at generation `t`:

`v_i[t+1] = w * v_i[t] + c1 * r1_i[t] * (pBest_i[t] - x_i[t]) + c2 * r2_i[t] * (gBest[t] - x_i[t])`

`x_i[t+1] = clip(x_i[t] + clip(v_i[t+1], -vMax, vMax), low, high)`

- `r1` and `r2` are **independent uniform [0,1) samples per particle and per coordinate**.
- `pBest` stores the best position *ever encountered* by the particle; `gBest` stores the best position *ever encountered* by the entire swarm.
- Initial velocity is zero (intentionally), and initial particle positions match the FA initialization for identical seed, population and objective.
- `vMax = velocity_limit * (high-low)` applies separately to each coordinate.
- After position clipping, any velocity coordinate that would have crossed the boundary is set to zero.
- All particles use the previous generation's `pBest` and `gBest` state; personal/global archives are updated **after** evaluating the new positions.
- Frame records include velocity components, personal-best coordinates/value, and the global-best archive coordinates/value. Blue velocity arrows in the visualizer are based directly on recorded velocities (scaled only for presentation).
- Defaults: `w = 0.72`, `c1 = c2 = 1.49`, `velocity_limit = 0.2`. These are user-adjustable, not universally optimal.

Each PSO generation has **O(n)** update cost plus `n` objective evaluations; FA's pairwise attraction calculations cost **O(n²)** even though both versions evaluate the objective `n` times per generation. Timing and evaluation count are both reported; direct ranking requires controlled repeated experiments.

## Artificial Bee Colony (ABC) — milestone 4

The implementation follows the basic Artificial Bee Colony (ABC) idea of Derviş Karaboğa (2005) for bounded **two-dimensional continuous minimization**. In this implementation, `population_size=N` is the number of **food sources**, NOT the number of bees. There are `N` employed-bee candidate evaluations and `N` onlooker-bee candidate evaluations per cycle; scouts are source replacements when the failure count exceeds `abc_limit`.

### Model and stages

For selected source `i`, a random distinct source `k`, and random coordinate `j ∈ {0,1}`:

`v[i,j] = clip(x[i,j] + φ · (x[i,j] - x[k,j]), low, high)`, where `φ ∼ U[-1,1)`.

The other coordinate remains unchanged. `v` is evaluated. If strictly better than the current source, it is accepted and its unsuccessful-attempt counter resets; otherwise the counter increments. This is **greedy selection**.

For onlooker selection, transform objective values `f_i` into positive nectar amounts:

`fit_i = 1/(1+f_i)` if `f_i >= 0`; otherwise `fit_i = 1 + |f_i|`.

`P(i) = fit_i / Σ fit_k`.

Draw `N` independent sources from this probability distribution (one draw per onlooker), each with a new randomized neighbor candidate. Probabilities are calculated **once, immediately after the employed phase**. This is an explicit roulette-wheel variant. One scout replaces the source having the maximum failed-trial count if that count is at least `abc_limit` (at most one replacement per cycle). Scout replacement uses a uniform random point in the bounded search domain. The historical best archive is retained after abandonment.

The timeline records **source states at the end of each cycle**; `role` means the last operation applied to that source (`employed`, `onlooker`, `scout`), rather than indicating the presence of a physical bee at that position. `target_id` means the last neighbor source used in candidate formation, not a guaranteed vector of motion. `selection_probability` is the *end-of-cycle* source probability; onlooker sampling uses probabilities from earlier in the cycle, so those values may differ.

### Actual evaluation count and comparison caveat

`NFE = N + 2 × N × iterations + total scout replacements`.

All proposed candidates are charged one objective evaluation, even when rejected. Frame-wise NFE is measured rather than inferred. FA/PSO both use `N × (iterations+1)` NFE, therefore ABC **must not** be put on their existing fixed-iteration comparison graph as an equal-budget third algorithm. v0.5.0 implements a separate **NFE-budgeted comparison adapter** without changing standalone ABC semantics. See the comparison section below.

### Relevant ABC references

- D. Karaboğa, *An Idea Based on Honey Bee Swarm for Numerical Optimization* (2005), Technical Report TR06, Erciyes University.
- ABC methodology survey: https://people.sau.int/~jcbansal/uploads/6-ABC_a_survey.pdf
- ABC employed/onlooker/scout neighbor rule: https://dergipark.org.tr/en/download/article-file/1178874

## Experiment record metadata

From v0.2.0, each exported JSON contains `parameters` with the complete submitted configuration, including algorithm-specific parameters. Earlier v0.1.0 exports do **not** contain these fields: their `seed` and frame history remain available, but the full parameter configuration cannot be reconstructed from their JSON alone.

## Evaluations and compute costs
For FA and PSO, reported objective function evaluations are exactly `population_size*(1+iterations)` because there is one initial evaluation per agent and one evaluation per agent in each subsequent generation. Pairwise attraction calculations in FA are **not** objective evaluations, but add time complexity `O(iterations * population_size²)`. PSO updates are `O(iterations * population_size)`. Compare total wall-clock time separately from function evaluations.

## Repeatability
- Identical configuration and RNG seed → same frames, independently of operating system scheduling (floating point platform minor differences can occur).
- Changing seed changes initial positions and stochastic moves.
- Wall-clock `duration_ms` and run UUID are not expected to match.
- Repeated trials now exist for FA, PSO and ABC under a strict equal-NFE benchmark; confidence intervals and statistical significance tests are still future improvements.

## Benchmark functions
- Sphere: `x²+y²`, domain [-5.12,5.12], optimum (0,0) → 0
- Rastrigin: `20+x²+y²-10(cos(2πx)+cos(2πy))`, same domain, optimum (0,0) → 0
- Ackley: `-20 exp(-0.2 sqrt((x²+y²)/2))-exp((cos(2πx)+cos(2πy))/2)+20+e`, domain [-5,5], optimum (0,0) → 0
- Rosenbrock: `(1-x)² +100(y-x²)²`, domain [-3,3], optimum (1,1) → 0

## Sources
- J. Kennedy and R. Eberhart, *Particle Swarm Optimization* (1995), Proc. IEEE International Conference on Neural Networks, doi:10.1109/ICNN.1995.488968.
- Xin-She Yang, *Firefly Algorithms for Multimodal Optimization* (2009). https://arxiv.org/abs/1003.1466
- X.-S. Yang, *Multiobjective Firefly Algorithm for Continuous Optimization*, Engineering with Computers (2013). https://doi.org/10.1007/s00366-012-0253-6
- Firefly algorithm descriptions with distance-dependent attractiveness and movement: https://pmc.ncbi.nlm.nih.gov/articles/PMC9137854/
- Benchmark methodology reference, COCO: https://coco-platform.org/

These papers motivate the attraction dynamics; the specific numerical scheduling, scaling, boundary handling, and runtime protocol above are explicitly this project's implementation choices.


## v0.5.0 — exact-NFE three-way comparison protocol

The selected algorithms are FA, PSO and/or ABC (two or three). For `N` agents / food sources and `T` **reference steps**, the total allowed evaluation budget per run is `B = N × (T+1)`. Initial population evaluations consume `N` of that budget. The seed list is consecutive and shared across algorithms but does not imply the stochastic sequences are identical.

- FA/PSO complete exactly `T` generations because each costs exactly `N` objective evaluations.
- A dedicated `simulate_budgeted` path for ABC evaluates candidates individually, counts all successful and rejected employed/onlooker proposals and scout replacements, and **stops immediately** after the B-th evaluation. It may stop in the middle of an ABC employed/onlooker cycle. This truncation is deliberate and disclosed in the `variant` field. The ordinary standalone ABC simulation remains unchanged.
- Each of the `T+1` comparison visualization frames is sampled at exactly `N, 2N, …, (T+1)N` actual evaluations. These are **budget checkpoints**, not equal algorithm generations.
- Curves are average historical best solution at the exact same NFE checkpoints across repeated runs; the first-success metric gives the first *sampled checkpoint* meeting the threshold, not necessarily the exact proposal that first crossed it.
- Each trial contributes one result with actual NFE exactly B; sample standard deviation, median, mean and success rate are computed across trials. Runtime remains environment-dependent and is not an isolated algorithmic complexity measurement.
- For backward compatibility, API clients omitting `algorithms` still run FA+PSO; the new React interface selects all three by default. Historic SQLite comparisons (FA+PSO) can still be loaded.
- This is a small, bounded, **2D** benchmark; it is not evidence of universally superior algorithms. More seeds, multiple problem classes, parameter tuning controls, and uncertainty intervals are planned.
