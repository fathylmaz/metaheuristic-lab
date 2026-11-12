import type { ComparisonConfig } from './types';

export const COMPARISON_DEFAULT_CONFIG: ComparisonConfig = {
  objective:'sphere', population_size:24, iterations:90, trials:3, seed_start:42,
  success_tolerance:.001, algorithms:['fa','pso','abc'],
  fa_alpha:.18,fa_beta0:1,fa_gamma:.12,
  pso_inertia_weight:.72,pso_cognitive_coefficient:1.49,
  pso_social_coefficient:1.49,pso_velocity_limit:.2,abc_limit:30,
  cs_discovery_rate:.25,cs_step_scale:.08,cs_levy_exponent:1.5,
  iwo_max_population:60,iwo_min_seeds:0,iwo_max_seeds:5,
  iwo_sigma_initial:1.5,iwo_sigma_final:.02,iwo_modulation_index:3,
  sa_initial_temperature:10,sa_cooling_rate:.95,sa_step_scale:.1,
  mfo_spiral_b:1, gwo_initial_a:2, woa_initial_a:2, woa_spiral_b:1, woa_spiral_probability:.5,
  ba_frequency_min:0, ba_frequency_max:2, ba_initial_loudness:.9,
  ba_loudness_decay:.9, ba_initial_pulse_rate:.5, ba_pulse_growth:.9,
  ssa_c1_initial:2, sma_restart_probability:.03,
  gsa_initial_gravity:100, gsa_decay:20, gsa_epsilon:.01,
  de_mutation_factor:.75, de_crossover_rate:.9,
};
