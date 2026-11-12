# Slime Mould Algorithm (SMA) – mathematical and UI methodology

**Metaheuristic Lab v1.3.0** • Two-dimensional continuous **minimization** • Auditable 2020 original-style update rule.

## Scientific basis

Li, S., Chen, H., Wang, M., Heidari, A. A., & Mirjalili, S. (2020). *Slime mould algorithm: A new method for stochastic optimization*. Future Generation Computer Systems, 111, 300–323. [https://doi.org/10.1016/j.future.2020.03.055](https://doi.org/10.1016/j.future.2020.03.055).

This is a mathematical optimizer inspired by a slime mould's biological oscillations, not an actual biophysical network-growth model. The method has three position updates: exploration/restart; approach food; contraction.

## Formal state

Each individual `i` stores `x_i(t)` in the 2-D objective domain `[lower,upper]^2`. The **entire previous generation** is frozen for computing new positions; the best historical fitness `DF` and best historical position `X_b` are frozen at the beginning of each generation. Fitness values refer to **minimization**.

1. **Adaptive ranking and feedback**: sort the previous population by ascending fitness. Let `bF` and `wF` be the minimum and maximum fitness of the frozen population, respectively. Draw independent `u_i` in `[0,1]`. Define

   `q_i = log(1 + (wF - f_i)/max(wF - bF, 1e-12))` (dimensionless normalized gap).

   For the top `ceil(N/2)` individuals, `W_i = 1 + u_i*q_i`; otherwise, `W_i = 1 - u_i*q_i`. When all fitness values are identical, every `W_i = 1`. This is the stable, rank-ordered original-style weight law.

2. **Food-approach probability and schedules**:

   `p_i = tanh(|f_i - DF|)`, `a_t = atanh(1 - t/T)`, `b_t = 1 - t/T`, for `t=1,...,T`.

   Vectors `v_b ~ Uniform(-a_t, a_t)^2` and `v_c ~ Uniform(-b_t, b_t)^2` are independently sampled per individual and per coordinate. At `t=T`, both schedules reach zero.

3. **Movement choice**: choose two distinct random source indices `A`, `B` and sample `r_restart`, `r_branch` independently from `[0,1]`. With user-defined restart probability `z` (default `0.03`):

   - `r_restart < z`: sample `X_i' ~ Uniform(lower, upper)^2` (**restart**, global exploration).
   - Otherwise, if `r_branch < p_i`: `X_i' = X_b + v_b * (W_i X_A - X_B)` (**approach**).
   - Otherwise: `X_i' = v_c * X_i` (**contract**).

   Here `*` on 2-D vectors denotes component-wise multiplication. The raw candidate is clipped coordinate-wise to the objective bounds.

4. **Evaluation and archive**: evaluate all `N` new candidates exactly once; update the archived best only if a lower objective value is found. Each original initialization uses `N` evaluations. The `t`-th frame has `NFE = N*(t+1)` and there are `T+1` frames.

## Reproducibility / telemetry

For each recorded agent state, `sma_move_kind` identifies its actual chosen movement. The JSON includes old position, best archive used **before** movement, source indices *and their frozen coordinates*, adaptive `W`, probability `p`, random draws, `v_b`, `v_c`, and unclipped candidate. These permit independently reconstructing the on-screen new position. Frame statistics include the three branch counts, `a`, `b`, `z` and mean adaptive weight. Repeated runs with the same configuration and seed have identical frames; run IDs and wall-clock duration may differ.

The position plot draws **model states**, not physical cytoplasmic flow. When an individual is selected, dashed links show prior state, previous best, and (for approach) actual source positions from the preceding iteration. Color codes: amber approach, blue contraction, green restart. We do not draw a fictitious continuous slime tube network.

## Scientific cautions

- The original contraction equation `v_c * X_i` has an **origin bias**: as `b_t` goes to zero, contracting candidates collapse toward **(0,0)**, even when the true objective minimum is elsewhere. On Sphere, Rastrigin and Ackley, (0,0) happens to be a known minimum; a tiny numerical result is **not a universal quality claim**. In particular, at `t=T`, every contracting candidate is exactly (0,0). For Rosenbrock the minimizer is (1,1), so this contraction can work against the optimum.
- The default `z=0.03` follows the standard form; changing it intentionally creates a parameter variant. The two sampled source indices are required to be distinct for this educational implementation. Other SMA implementations may choose random indices differently or use variants of vector/scalar sampling; this is documented rather than silently equating all variants.
- Animated trajectories and single-seed results do not establish algorithm rankings. Controlled comparisons must use matched objective, budget (real NFE) and multiple seeds, and be explicit about algorithm variants.
- SMA is **not yet in the FA/PSO/ABC comparison engine**. It runs in its own simulation module until the fair NFE comparison adapter is implemented.

## Verification

`backend/tests/test_sma.py` independently checks every recorded movement equation and its clipping, schedule limits, adaptive weights, real NFE, bounds, seed reproducibility, and API schema. Run `python -m pytest -q` in `backend/`.
