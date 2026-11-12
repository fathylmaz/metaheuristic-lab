"""Validated, explicit API contracts."""
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class RunRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    algorithm: Literal['fa', 'pso', 'abc', 'cs', 'mfo', 'gwo', 'woa', 'ba', 'ssa', 'sma', 'iwo', 'sa', 'gsa', 'de'] = 'fa'
    objective: Literal['sphere', 'rastrigin', 'ackley', 'rosenbrock', 'griewank', 'himmelblau', 'beale', 'booth'] = 'rastrigin'
    population_size: int = Field(default=24, ge=5, le=60)
    iterations: int = Field(default=90, ge=1, le=250)
    alpha: float = Field(default=0.18, ge=0, le=1)
    beta0: float = Field(default=1, ge=0, le=3)
    gamma: float = Field(default=0.12, ge=0, le=5)
    seed: int = Field(default=42, ge=0, le=2_147_483_647)
    # PSO-only settings: the FA optimizer ignores them.
    inertia_weight: float = Field(default=0.72, ge=0, le=1.2)
    cognitive_coefficient: float = Field(default=1.49, ge=0, le=4)
    social_coefficient: float = Field(default=1.49, ge=0, le=4)
    velocity_limit: float = Field(default=0.2, gt=0, le=1)
    # ABC source-abandonment threshold (failed candidate updates)
    abc_limit: int = Field(default=30, ge=1, le=500)
    # Cuckoo Search: fraction of host nests abandoned, flight scale, stable exponent.
    cs_discovery_rate: float = Field(default=0.25, ge=0, le=1)
    cs_step_scale: float = Field(default=0.08, gt=0, le=1)
    cs_levy_exponent: float = Field(default=1.5, ge=1.1, le=1.9)
    # MFO: logarithmic spiral shape; exponent b.
    mfo_spiral_b: float = Field(default=1.0, ge=0.1, le=3.0)
    # GWO: initial (linearly decreasing) encircling coefficient a. Default 2 is canonical.
    gwo_initial_a: float = Field(default=2.0, ge=0.25, le=3.0)
    # WOA (original whale optimization): initial a, spiral b, probability of spiral choice.
    woa_initial_a: float = Field(default=2.0, ge=0.25, le=3.0)
    woa_spiral_b: float = Field(default=1.0, ge=0.1, le=3.0)
    woa_spiral_probability: float = Field(default=0.5, ge=0, le=1)
    # Bat Algorithm (Yang-style): frequency range, loudness and pulse adaptation.
    ba_frequency_min: float = Field(default=0, ge=0, le=4)
    ba_frequency_max: float = Field(default=2, gt=0, le=5)
    ba_initial_loudness: float = Field(default=0.9, gt=0, le=1)
    ba_loudness_decay: float = Field(default=0.9, gt=0, le=1)
    ba_initial_pulse_rate: float = Field(default=0.5, ge=0, le=1)
    ba_pulse_growth: float = Field(default=0.9, gt=0, le=5)
    # SSA: canonical c1(0)=2, scaled exploration-to-exploitation schedule.
    ssa_c1_initial: float = Field(default=2.0, ge=0.25, le=3.0)
    # SMA: probability of random independent reinitialization (canonical z=0.03).
    sma_restart_probability: float = Field(default=0.03, ge=0, le=1)
    # IWO: variable population; seeds follow quality and Gaussian dispersal.
    iwo_max_population: int = Field(default=60, ge=5, le=100)
    iwo_min_seeds: int = Field(default=0, ge=0, le=8)
    iwo_max_seeds: int = Field(default=5, ge=0, le=8)
    iwo_sigma_initial: float = Field(default=1.5, gt=0, le=10)
    iwo_sigma_final: float = Field(default=0.02, gt=0, le=5)
    iwo_modulation_index: float = Field(default=3.0, ge=1, le=6)
    # SA: one neighbor candidate per generation, not a population algorithm.
    sa_initial_temperature: float = Field(default=10.0, gt=0, le=100)
    sa_cooling_rate: float = Field(default=0.95, gt=0, le=1)
    sa_step_scale: float = Field(default=0.10, gt=0, le=1)
    # GSA: original-style Newtonian force and decaying gravitational constant.
    gsa_initial_gravity: float = Field(default=100.0, gt=0, le=500)
    gsa_decay: float = Field(default=20.0, ge=0, le=40)
    gsa_epsilon: float = Field(default=0.01, ge=1e-6, le=1)
    # DE/rand/1/bin (Storn & Price): mutation F and crossover CR.
    de_mutation_factor: float = Field(default=0.75, ge=0, le=2)
    de_crossover_rate: float = Field(default=0.90, ge=0, le=1)



class AgentState(BaseModel):
    id: int
    x: float
    y: float
    fitness: float
    brightness: float
    target_id: int | None = None
    vx: float | None = None
    vy: float | None = None
    pbest_x: float | None = None
    pbest_y: float | None = None
    pbest_fitness: float | None = None
    # ABC-specific food-source telemetry. Roles describe last action on this source.
    role: Literal['employed', 'onlooker', 'scout'] | None = None
    trials: int | None = None
    selection_probability: float | None = None
    # CS nests: last successful action and the latest proposed flight length.
    move_kind: Literal['levy', 'abandoned', 'retained'] | None = None
    proposed_flight_length: float | None = None
    # MFO-specific flame position (flames are elite memories, not moth IDs).
    flame_x: float | None = None
    flame_y: float | None = None
    flame_rank: int | None = None
    spiral_t_x: float | None = None
    spiral_t_y: float | None = None
    # GWO ranking in current generation + three equation-based candidate positions.
    wolf_role: Literal['alpha', 'beta', 'delta', 'omega'] | None = None
    gwo_x1: tuple[float, float] | None = None
    gwo_x2: tuple[float, float] | None = None
    gwo_x3: tuple[float, float] | None = None
    # WOA telemetry: actual prior-generation location and target used in the step.
    woa_move_kind: Literal['search', 'encircle', 'spiral'] | None = None
    woa_previous: tuple[float, float] | None = None
    woa_target: tuple[float, float] | None = None
    woa_target_id: int | None = None
    woa_A: tuple[float, float] | None = None
    woa_C: tuple[float, float] | None = None
    woa_p: float | None = None
    woa_l: float | None = None
    # BA telemetry: candidate may be rejected even though it consumes one NFE.
    ba_frequency: float | None = None
    ba_loudness: float | None = None
    ba_pulse_rate: float | None = None
    ba_move_kind: Literal['global', 'local'] | None = None
    ba_accepted: bool | None = None
    ba_previous: tuple[float, float] | None = None
    ba_candidate: tuple[float, float] | None = None
    ba_reference_best: tuple[float, float] | None = None
    ba_local_epsilon: tuple[float, float] | None = None
    ba_mean_loudness: float | None = None
    ba_candidate_fitness: float | None = None
    ba_pulse_draw: float | None = None
    ba_accept_draw: float | None = None
    # SSA ordered chain update: recorded predecessor is already updated.
    ssa_role: Literal['leader', 'follower'] | None = None
    ssa_previous: tuple[float, float] | None = None
    ssa_target: tuple[float, float] | None = None
    ssa_c2: tuple[float, float] | None = None
    ssa_c3: tuple[float, float] | None = None
    # SMA: old state and all input factors of the selected movement equation.
    sma_move_kind: Literal['restart', 'approach', 'contract'] | None = None
    sma_weight: float | None = None
    sma_probability: float | None = None
    sma_previous: tuple[float, float] | None = None
    sma_best_reference: tuple[float, float] | None = None
    sma_source_a: int | None = None
    sma_source_b: int | None = None
    sma_source_a_position: tuple[float, float] | None = None
    sma_source_b_position: tuple[float, float] | None = None
    sma_vb: tuple[float, float] | None = None
    sma_vc: tuple[float, float] | None = None
    sma_branch_draw: float | None = None
    sma_restart_draw: float | None = None
    sma_raw_position: tuple[float, float] | None = None
    # IWO: stable IDs (not indices); seeds inherit a true parent coordinate.
    iwo_origin: Literal['survivor', 'offspring'] | None = None
    iwo_parent_id: int | None = None
    iwo_parent_position: tuple[float, float] | None = None
    iwo_raw_step: tuple[float, float] | None = None
    iwo_seeds_produced: int | None = None
    iwo_birth_generation: int | None = None
    # SA: the current point may stay put after rejecting the evaluated candidate.
    sa_previous: tuple[float, float] | None = None
    sa_candidate: tuple[float, float] | None = None
    sa_step: tuple[float, float] | None = None
    sa_candidate_fitness: float | None = None
    sa_delta: float | None = None
    sa_accept_probability: float | None = None
    sa_accept_draw: float | None = None
    sa_accepted: bool | None = None
    # GSA: current mass and prior-generation force inputs for reproducibility.
    gsa_mass: float | None = None
    gsa_force_mass: float | None = None
    gsa_previous: tuple[float, float] | None = None
    gsa_previous_velocity: tuple[float, float] | None = None
    gsa_acceleration: tuple[float, float] | None = None
    gsa_force: tuple[float, float] | None = None
    gsa_attractor: tuple[float, float] | None = None
    gsa_velocity_draw: tuple[float, float] | None = None
    # DE frozen donor population and evaluated (possibly rejected) trial.
    de_parent: tuple[float, float] | None = None
    de_donors: tuple[int, int, int] | None = None
    de_donor_positions: list[tuple[float, float]] | None = None
    de_mutant_raw: tuple[float, float] | None = None
    de_mutant: tuple[float, float] | None = None
    de_trial: tuple[float, float] | None = None
    de_trial_fitness: float | None = None
    de_crossover_draws: tuple[float, float] | None = None
    de_crossover_mask: tuple[bool, bool] | None = None
    de_j_rand: int | None = None
    de_accepted: bool | None = None


class SimulationFrame(BaseModel):
    iteration: int
    agents: list[AgentState]
    current_best: float
    best_so_far: float
    best_position: tuple[float, float]
    mean_fitness: float
    diversity: float
    function_evaluations: int
    scouts_this_iteration: int = 0
    abandoned_this_iteration: int = 0
    accepted_levy_this_iteration: int = 0
    flame_count: int = 0
    # GWO leaders used to produce THIS frame (initial frame shows initial leaders).
    gwo_a: float | None = None
    gwo_leader_positions: list[tuple[float, float]] | None = None
    gwo_leader_ids: list[int] | None = None
    # WOA: control value and exactly counted search / encircle / spiral moves.
    woa_a: float | None = None
    woa_search_count: int = 0
    woa_encircle_count: int = 0
    woa_spiral_count: int = 0
    # BA events; global/local count all proposals, accepted is the subset.
    ba_global_proposals: int = 0
    ba_local_proposals: int = 0
    ba_accepted_count: int = 0
    ba_mean_loudness: float | None = None
    ba_mean_pulse_rate: float | None = None
    ssa_c1: float | None = None
    ssa_food_position: tuple[float, float] | None = None
    ssa_chain_length: float | None = None
    ssa_leader_distance: float | None = None
    # SMA: per-frame original-style contraction and feedback state.
    sma_a: float | None = None
    sma_b: float | None = None
    sma_restart_probability: float | None = None
    sma_restart_count: int = 0
    sma_approach_count: int = 0
    sma_contract_count: int = 0
    sma_mean_weight: float | None = None
    iwo_sigma: float | None = None
    iwo_initial_population: int = 0
    iwo_population_before: int = 0
    iwo_population_after: int = 0
    iwo_seeds_generated: int = 0
    iwo_seeds_survived: int = 0
    iwo_competitive_exclusions: int = 0
    sa_temperature: float | None = None
    sa_accepted_total: int = 0
    sa_uphill_accepted_total: int = 0
    sa_rejected_total: int = 0
    sa_last_accepted: bool | None = None
    gsa_gravity: float | None = None
    gsa_kbest: int = 0
    gsa_max_mass: float | None = None
    gsa_mean_acceleration: float | None = None
    de_accepted_count: int = 0
    de_rejected_count: int = 0
    de_forced_crossover_count: int = 0


class RunResponse(BaseModel):
    run_id: str
    algorithm: str
    objective: str
    seed: int
    bounds: tuple[float, float]
    optimum: tuple[float, float]
    frames: list[SimulationFrame]
    duration_ms: float
    variant: str
    parameters: dict[str, str | float | int] = Field(default_factory=dict)
