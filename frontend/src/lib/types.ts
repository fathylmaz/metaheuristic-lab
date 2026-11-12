export type Algorithm = { id: string; name: string; english: string; category: string; description: string; status: 'ready' | 'planned' };
export type Objective = { id: string; name: string; description: string; bounds: [number, number]; optimum: [number, number] };
export type Catalog = { algorithms: Algorithm[]; objectives: Objective[] };
export type Agent = { id: number; x: number; y: number; fitness: number; brightness: number; target_id: number | null; vx?: number | null; vy?: number | null; pbest_x?: number | null; pbest_y?: number | null; pbest_fitness?: number | null; role?: 'employed' | 'onlooker' | 'scout' | null; trials?: number | null; selection_probability?: number | null; move_kind?: 'levy' | 'abandoned' | 'retained' | null; proposed_flight_length?: number | null; flame_x?: number | null; flame_y?: number | null; flame_rank?: number | null; spiral_t_x?: number | null; spiral_t_y?: number | null; wolf_role?: 'alpha' | 'beta' | 'delta' | 'omega' | null; gwo_x1?: [number,number] | null; gwo_x2?: [number,number] | null; gwo_x3?: [number,number] | null; woa_move_kind?: 'search' | 'encircle' | 'spiral' | null; woa_previous?: [number,number] | null; woa_target?: [number,number] | null; woa_target_id?: number | null; woa_A?: [number,number] | null; woa_C?: [number,number] | null; woa_p?: number | null; woa_l?: number | null; ba_frequency?: number | null; ba_loudness?: number | null; ba_pulse_rate?: number | null; ba_move_kind?: 'global' | 'local' | null; ba_accepted?: boolean | null; ba_previous?: [number,number] | null; ba_candidate?: [number,number] | null; ba_reference_best?: [number,number] | null; ba_local_epsilon?: [number,number] | null; ba_mean_loudness?: number | null; ba_candidate_fitness?: number | null; ba_pulse_draw?: number | null; ba_accept_draw?: number | null; ssa_role?: 'leader' | 'follower' | null; ssa_previous?: [number,number] | null; ssa_target?: [number,number] | null; ssa_c2?: [number,number] | null; ssa_c3?: [number,number] | null; sma_move_kind?: 'restart' | 'approach' | 'contract' | null; sma_weight?: number | null; sma_probability?: number | null; sma_previous?: [number,number] | null; sma_best_reference?: [number,number] | null; sma_source_a?: number | null; sma_source_b?: number | null; sma_source_a_position?: [number,number] | null; sma_source_b_position?: [number,number] | null; sma_vb?: [number,number] | null; sma_vc?: [number,number] | null; sma_branch_draw?: number | null; sma_restart_draw?: number | null; sma_raw_position?: [number,number] | null; iwo_origin?: 'survivor'|'offspring'|null; iwo_parent_id?: number | null; iwo_parent_position?: [number,number] | null; iwo_raw_step?: [number,number] | null; iwo_seeds_produced?: number | null; iwo_birth_generation?: number | null; sa_previous?: [number,number] | null; sa_candidate?: [number,number] | null; sa_step?: [number,number] | null; sa_candidate_fitness?: number | null; sa_delta?: number | null; sa_accept_probability?: number | null; sa_accept_draw?: number | null; sa_accepted?: boolean | null; gsa_mass?: number | null; gsa_force_mass?: number | null; gsa_previous?: [number,number] | null; gsa_previous_velocity?: [number,number] | null; gsa_acceleration?: [number,number] | null; gsa_force?: [number,number] | null; gsa_attractor?: [number,number] | null; gsa_velocity_draw?: [number,number] | null;
 de_parent?: [number,number] | null; de_donors?: [number,number,number] | null;
 de_donor_positions?: [number,number][] | null; de_mutant_raw?: [number,number] | null;
 de_mutant?: [number,number] | null; de_trial?: [number,number] | null;
 de_trial_fitness?: number | null; de_crossover_draws?: [number,number] | null;
 de_crossover_mask?: [boolean,boolean] | null; de_j_rand?: number | null;
 de_accepted?: boolean | null };
export type Frame = { iteration: number; agents: Agent[]; current_best: number; best_so_far: number; best_position: [number, number]; mean_fitness: number; diversity: number; function_evaluations: number; scouts_this_iteration?: number; abandoned_this_iteration?: number; accepted_levy_this_iteration?: number; flame_count?: number; gwo_a?: number | null; gwo_leader_ids?: number[] | null; gwo_leader_positions?: [number,number][] | null; woa_a?: number | null; woa_search_count?: number; woa_encircle_count?: number; woa_spiral_count?: number; ba_global_proposals?: number; ba_local_proposals?: number; ba_accepted_count?: number; ba_mean_loudness?: number | null; ba_mean_pulse_rate?: number | null; ssa_c1?: number | null; ssa_food_position?: [number,number] | null; ssa_chain_length?: number | null; ssa_leader_distance?: number | null; sma_a?: number | null; sma_b?: number | null; sma_restart_probability?: number | null; sma_restart_count?: number; sma_approach_count?: number; sma_contract_count?: number; sma_mean_weight?: number | null; iwo_sigma?: number | null; iwo_initial_population?: number; iwo_population_before?: number; iwo_population_after?: number; iwo_seeds_generated?: number; iwo_seeds_survived?: number; iwo_competitive_exclusions?: number; sa_temperature?: number | null; sa_accepted_total?: number; sa_uphill_accepted_total?: number; sa_rejected_total?: number; sa_last_accepted?: boolean | null; gsa_gravity?: number | null; gsa_kbest?: number; gsa_max_mass?: number | null; gsa_mean_acceleration?: number | null; de_accepted_count?: number; de_rejected_count?: number; de_forced_crossover_count?: number };
export type Run = { run_id: string; algorithm: string; objective: string; seed: number; bounds: [number, number]; optimum: [number, number]; frames: Frame[]; duration_ms: number; variant: string; parameters: Partial<Config> };
export type Config = { algorithm: 'fa' | 'pso' | 'abc' | 'cs' | 'mfo' | 'gwo' | 'woa' | 'ba' | 'ssa' | 'sma' | 'iwo' | 'sa' | 'gsa' | 'de'; objective: string; population_size: number; iterations: number; alpha: number; beta0: number; gamma: number; seed: number; inertia_weight: number; cognitive_coefficient: number; social_coefficient: number; velocity_limit: number; abc_limit: number; cs_discovery_rate: number; cs_step_scale: number; cs_levy_exponent: number; mfo_spiral_b: number; gwo_initial_a: number; woa_initial_a: number; woa_spiral_b: number; woa_spiral_probability: number; ba_frequency_min: number; ba_frequency_max: number; ba_initial_loudness: number; ba_loudness_decay: number; ba_initial_pulse_rate: number; ba_pulse_growth: number; ssa_c1_initial: number; sma_restart_probability: number; iwo_max_population: number; iwo_min_seeds: number; iwo_max_seeds: number; iwo_sigma_initial: number; iwo_sigma_final: number; iwo_modulation_index: number; sa_initial_temperature: number; sa_cooling_rate: number; sa_step_scale: number; gsa_initial_gravity: number; gsa_decay: number; gsa_epsilon: number; de_mutation_factor: number; de_crossover_rate: number };

export type ComparisonAlgorithm = 'fa' | 'pso' | 'abc' | 'mfo' | 'gwo' | 'woa' | 'ba' | 'ssa' | 'sma' | 'gsa' | 'de' | 'cs' | 'iwo' | 'sa';
export type ComparisonConfig = {
  objective: string; population_size: number; iterations: number; trials: number;
  seed_start: number; success_tolerance: number; algorithms: ComparisonAlgorithm[]; abc_limit: number;
  cs_discovery_rate: number; cs_step_scale: number; cs_levy_exponent: number;
  iwo_max_population: number; iwo_min_seeds: number; iwo_max_seeds: number;
  iwo_sigma_initial: number; iwo_sigma_final: number; iwo_modulation_index: number;
  sa_initial_temperature: number; sa_cooling_rate: number; sa_step_scale: number;
  fa_alpha: number; fa_beta0: number; fa_gamma: number;
  pso_inertia_weight: number; pso_cognitive_coefficient: number;
  pso_social_coefficient: number; pso_velocity_limit: number;
  mfo_spiral_b: number; gwo_initial_a: number;
  woa_initial_a: number; woa_spiral_b: number; woa_spiral_probability: number;
  ba_frequency_min: number; ba_frequency_max: number; ba_initial_loudness: number;
  ba_loudness_decay: number; ba_initial_pulse_rate: number; ba_pulse_growth: number;
  ssa_c1_initial: number; sma_restart_probability: number;
  gsa_initial_gravity: number; gsa_decay: number; gsa_epsilon: number;
  de_mutation_factor: number; de_crossover_rate: number;
};
export type ComparisonTrial = { seed: number; best_value: number; duration_ms: number; function_evaluations: number; first_success_evaluations: number | null };
export type ComparisonCurvePoint = { evaluations: number; mean_best: number; std_best: number };
export type ComparisonGroup = {
  algorithm: ComparisonAlgorithm; mean_best: number; median_best: number; std_best: number;
  min_best: number; max_best: number; success_rate: number; mean_duration_ms: number;
  trials: ComparisonTrial[]; curve: ComparisonCurvePoint[]; representative_run: Run;
};
export type PairwiseStatistic = {
  algorithm_a: ComparisonAlgorithm; algorithm_b: ComparisonAlgorithm;
  a_wins: number; b_wins: number; ties: number;
  median_log10_difference: number; p_value: number; p_holm: number; method: string;
};
export type ComparisonResult = {
  comparison_id: string; created_at: string; objective: string; seeds: number[];
  trials_per_algorithm: number; evaluations_per_run: number; success_tolerance: number;
  parameters: ComparisonConfig; methodology: string; groups: ComparisonGroup[]; pairwise?: PairwiseStatistic[];
};
export type SavedComparison = {
  comparison_id: string; created_at: string; objective: string;
  trials_per_algorithm: number; evaluations_per_run: number;
  mean_best: Record<string, number>;
};

// ACO is a separate discrete TSP problem, not a continuous objective function.
export type AcoConfig = {
  city_count: number; ant_count: number; iterations: number; alpha: number; beta: number;
  evaporation: number; deposit_q: number; seed: number; city_seed: number;
  layout: 'uniform' | 'circle' | 'clusters';
};
export type AcoCity = { id: number; x: number; y: number };
export type AcoAntTour = { id: number; route: number[]; length: number };
export type AcoFrame = {
  iteration: number; best_length: number; iteration_best: number; mean_length: number;
  best_route: number[]; iteration_best_route: number[]; tours_evaluated: number;
  unique_tours: number; pheromone: number[][]; ant_tours: AcoAntTour[];
};
export type AcoRun = {
  run_id: string; algorithm: 'aco'; problem: 'symmetric_euclidean_tsp';
  parameters: AcoConfig; cities: AcoCity[]; frames: AcoFrame[];
  duration_ms: number; variant: string;
};


export type BenchmarkRequest = { objectives: string[]; comparison: ComparisonConfig };
export type BenchmarkTrial = {
  seed: number; best_value: number; absolute_error: number;
  function_evaluations: number; first_success_evaluations: number | null; duration_ms: number;
};
export type BenchmarkCell = {
  algorithm: ComparisonAlgorithm; mean_error: number; median_error: number;
  std_error: number; best_error: number; success_rate: number;
  mean_duration_ms: number; rank: number; trials: BenchmarkTrial[];
};
export type BenchmarkRow = {
  objective: string; optimum: [number, number]; optimum_value: number;
  cells: BenchmarkCell[];
};
export type BenchmarkSummary = {
  algorithm: ComparisonAlgorithm; mean_rank: number; mean_success_rate: number;
  objective_wins: number; objectives_measured: number;
};
export type BenchmarkResult = {
  benchmark_id: string; created_at: string; objectives: string[];
  algorithms: ComparisonAlgorithm[]; seeds: number[]; evaluations_per_run: number;
  total_evaluations: number; success_tolerance: number;
  parameters: BenchmarkRequest; methodology: string;
  rows: BenchmarkRow[]; summary: BenchmarkSummary[];
};
export type SavedBenchmark = {
  benchmark_id: string; created_at: string; objectives: string[];
  algorithms: ComparisonAlgorithm[]; trials_per_algorithm: number; evaluations_per_run: number;
};

// v2.1.0 — One-factor-at-a-time parameter sensitivity studies.
export type ParameterSpec = {key:string;label:string;minimum:number;maximum:number;default:number;suggested:number[];integral:boolean};
export type SensitivityConfig = {
  algorithm:ComparisonAlgorithm;objective:string;parameter:string;values:number[];
  population_size:number;iterations:number;trials:number;seed_start:number;success_tolerance:number;
};
export type SensitivityTrial = {seed:number;best_value:number;absolute_error:number;function_evaluations:number;first_success_nfe:number|null;duration_ms:number};
export type SensitivityCurve = {evaluations:number;mean_error:number;std_error:number};
export type SensitivityGroup = {
  parameter_value:number;mean_error:number;median_error:number;std_error:number;min_error:number;
  max_error:number;success_rate:number;mean_duration_ms:number;trials:SensitivityTrial[];
  curve:SensitivityCurve[];
};
export type SensitivityResult = {
  sensitivity_id:string;created_at:string;parameters:SensitivityConfig;
  optimum_value:number;seeds:number[];evaluations_per_run:number;total_evaluations:number;
  methodology:string;groups:SensitivityGroup[];
};
export type SavedSensitivity = {
  sensitivity_id:string;created_at:string;algorithm:ComparisonAlgorithm;objective:string;
  parameter:string;values:number[];trials:number;evaluations_per_run:number;
};

// v2.5.0 true D-dimensional (not a 2D projection used for optimization)
export type DimensionalAlgorithm = 'pso'|'gwo'|'de'|'woa'|'mfo'|'ssa'|'fa'|'ba'|'gsa'|'abc'|'cs'|'sma'|'iwo'|'sa';
export type DimensionalConfig = {
  algorithms:DimensionalAlgorithm[];objective:'sphere'|'rastrigin'|'ackley'|'rosenbrock'|'griewank';
  dimensions:2|5|10|30;population_size:number;iterations:number;trials:number;seed_start:number;
  success_tolerance:number;pso_inertia_weight:number;pso_cognitive_coefficient:number;
  pso_social_coefficient:number;pso_velocity_limit:number;gwo_initial_a:number;
  de_mutation_factor:number;de_crossover_rate:number;
  woa_initial_a:number;woa_spiral_b:number;woa_spiral_probability:number;
  mfo_spiral_b:number;ssa_c1_initial:number;
  fa_alpha:number;fa_beta0:number;fa_gamma:number;
  ba_min_frequency:number;ba_max_frequency:number;ba_initial_loudness:number;
  ba_loudness_decay:number;ba_initial_pulse_rate:number;ba_pulse_growth:number;
  gsa_initial_gravity:number;gsa_decay:number;gsa_epsilon:number;
  abc_limit:number;cs_discovery_rate:number;cs_step_scale:number;cs_levy_exponent:number;
  sma_restart_probability:number;iwo_max_population:number;iwo_min_seeds:number;
  iwo_max_seeds:number;iwo_sigma_initial:number;iwo_sigma_final:number;
  iwo_modulation_index:number;sa_initial_temperature:number;sa_cooling_rate:number;
  sa_step_scale:number;
};
export type DimensionalPoint = {evaluations:number;best_error:number;best_position:number[]};
export type DimensionalTrial = {seed:number;best_error:number;best_position:number[];
  function_evaluations:number;first_success_nfe:number|null;duration_ms:number;trajectory:DimensionalPoint[]};
export type DimensionalGroup = {algorithm:DimensionalAlgorithm;mean_error:number;median_error:number;
  std_error:number;min_error:number;success_rate:number;mean_duration_ms:number;
  curve:{evaluations:number;mean_error:number;std_error:number}[];trials:DimensionalTrial[]};
export type DimensionalResult = {experiment_id:string;created_at:string;parameters:DimensionalConfig;
  optimum_position:number[];optimum_value:number;evaluations_per_run:number;total_evaluations:number;
  seeds:number[];methodology:string;groups:DimensionalGroup[]};
export type SavedDimensional = {experiment_id:string;created_at:string;algorithms:DimensionalAlgorithm[];
  objective:string;dimensions:number;trials:number;evaluations_per_run:number};

// v2.6.0 — read-only scientific reports generated from archived experiments.
export type ReportKind = 'comparison' | 'benchmark' | 'sensitivity' | 'dimensional';
export type ReportEntry = {kind:ReportKind;source_id:string;created_at:string;title:string;description:string};
export type ScientificReport = {
  report_version:string;source_kind:ReportKind;source_id:string;experiment_created_at:string;
  report_generated_at:string;source_sha256:string;title:string;subtitle:string;
  highlights:string[];caveats:string[];methodology:string;parameters:Record<string,unknown>;
  sections:{heading:string;paragraphs:string[];tables:{caption:string;headers:string[];rows:string[][]}[]}[];
};

export type BackgroundJobKind = 'dimensional' | 'benchmark' | 'sensitivity';
export type BackgroundJobState = 'queued'|'running'|'cancelling'|'cancelled'|'completed'|'failed';
export type BackgroundJob = {
  id:string;kind:BackgroundJobKind;created_at:string;updated_at:string;
  state:BackgroundJobState;completed_units:number;total_units:number;progress_percent:number;
  result_id:string|null;error:string|null;active_algorithm:string|null;active_seed:number|null;
  cancel_requested:boolean;attempts:number;restart_count:number;
  checkpoint_units:number;reused_units:number;
  last_recovered_at:string|null;retry_of:string|null;
};
export type BackgroundJobEvent = {
  id:number;created_at:string;event:string;message:string;
  completed_units:number;total_units:number;
};

// v2.14.0 — read-only archived D-dimensional scientific audit.
export type ScienceAuditGroup = {
  algorithm:DimensionalAlgorithm;trials:number;mean_error:number;median_error:number;std_error:number;
  success_rate:number;ci95_low:number;ci95_high:number;mean_duration_ms:number;
  median_duration_ms:number;p95_duration_ms:number;median_nfe_per_second:number|null;nfe_per_run:number;
};
export type SciencePairedComparison = {pair:string;n:number;a_wins:number;b_wins:number;ties:number;median_log10_ratio:number;p_raw:number;p_holm:number};
export type ScienceAudit = {
  audit_version:string;experiment_id:string;objective:string;dimensions:number;algorithm_count:number;
  trials_per_algorithm:number;evaluations_per_run:number;expected_total_evaluations:number;
  status:'passed'|'attention';issues:string[];warnings:string[];groups:ScienceAuditGroup[];
  paired_comparisons:SciencePairedComparison[];scope:string;
};
