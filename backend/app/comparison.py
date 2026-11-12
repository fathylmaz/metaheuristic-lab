"""Controlled multi-algorithm benchmarking on one 2D objective.

The algorithms share an exact NFE cap. FA and PSO evaluate N candidates per
iteration; budgeted ABC samples its food-source state after every N candidate
calls, potentially ending inside a colony phase. Frame indices are common NFE
checkpoints, NOT equal algorithm iterations. Historical FA+PSO comparisons
remain compatible with the database.
"""
from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean, median, stdev
from itertools import combinations, product
from math import log10
from typing import Literal, Callable

from .dimensional import JobInterrupted
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import RunRequest, RunResponse
from .optimizers.abc import simulate_budgeted as simulate_abc_budgeted
from .optimizers.budgeted_extra import (simulate_cs_budgeted, simulate_iwo_budgeted, simulate_sa_budgeted)
from .optimizers.firefly import simulate as simulate_fa
from .optimizers.pso import simulate as simulate_pso
from .optimizers.mfo import simulate as simulate_mfo
from .optimizers.gwo import simulate as simulate_gwo
from .optimizers.woa import simulate as simulate_woa
from .optimizers.bat import simulate as simulate_ba
from .optimizers.ssa import simulate as simulate_ssa
from .optimizers.sma import simulate as simulate_sma
from .optimizers.gravitational import simulate as simulate_gsa
from .optimizers.differential import simulate as simulate_de

Algorithm = Literal['fa', 'pso', 'abc', 'mfo', 'gwo', 'woa', 'ba', 'ssa', 'sma', 'gsa', 'de', 'cs', 'iwo', 'sa']

FIXED_NFE_SIMULATORS = {'fa': simulate_fa, 'pso': simulate_pso, 'mfo': simulate_mfo,
                        'gwo': simulate_gwo, 'woa': simulate_woa, 'ba': simulate_ba,
                        'ssa': simulate_ssa, 'sma': simulate_sma, 'gsa': simulate_gsa,
                        'de': simulate_de}


class ComparisonRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    objective: Literal['sphere', 'rastrigin', 'ackley', 'rosenbrock', 'griewank', 'himmelblau', 'beale', 'booth'] = 'sphere'
    population_size: int = Field(default=24, ge=5, le=40)
    iterations: int = Field(default=90, ge=1, le=150)
    trials: int = Field(default=3, ge=2, le=8)
    seed_start: int = Field(default=42, ge=0, le=2_147_483_639)
    success_tolerance: float = Field(default=1e-3, gt=0, le=100)
    # API defaults remain backward compatible; the new frontend enables ABC.
    algorithms: list[Algorithm] = Field(default_factory=lambda: ['fa', 'pso'], min_length=2, max_length=6)
    fa_alpha: float = Field(default=.18, ge=0, le=1)
    fa_beta0: float = Field(default=1, ge=0, le=3)
    fa_gamma: float = Field(default=.12, ge=0, le=5)
    pso_inertia_weight: float = Field(default=.72, ge=0, le=1.2)
    pso_cognitive_coefficient: float = Field(default=1.49, ge=0, le=4)
    pso_social_coefficient: float = Field(default=1.49, ge=0, le=4)
    pso_velocity_limit: float = Field(default=.2, gt=0, le=1)
    abc_limit: int = Field(default=30, ge=1, le=500)
    cs_discovery_rate: float = Field(default=.25, ge=0, le=1)
    cs_step_scale: float = Field(default=.08, gt=0, le=.5)
    cs_levy_exponent: float = Field(default=1.5, ge=1.1, le=1.9)
    iwo_max_population: int = Field(default=60, ge=5, le=100)
    iwo_min_seeds: int = Field(default=0, ge=0, le=8)
    iwo_max_seeds: int = Field(default=5, ge=1, le=8)
    iwo_sigma_initial: float = Field(default=1.5, gt=0, le=10)
    iwo_sigma_final: float = Field(default=.02, gt=0, le=5)
    iwo_modulation_index: float = Field(default=3.0, ge=1, le=6)
    sa_initial_temperature: float = Field(default=10.0, gt=0, le=100)
    sa_cooling_rate: float = Field(default=.95, gt=0, le=1)
    sa_step_scale: float = Field(default=.1, gt=0, le=1)
    mfo_spiral_b: float = Field(default=1.0, ge=0.1, le=3.0)
    gwo_initial_a: float = Field(default=2.0, ge=0.25, le=3.0)
    woa_initial_a: float = Field(default=2.0, ge=0.25, le=3.0)
    woa_spiral_b: float = Field(default=1.0, ge=0.1, le=3.0)
    woa_spiral_probability: float = Field(default=0.5, ge=0, le=1)
    ba_frequency_min: float = Field(default=0.0, ge=0, le=4)
    ba_frequency_max: float = Field(default=2.0, gt=0, le=5)
    ba_initial_loudness: float = Field(default=0.9, gt=0, le=1)
    ba_loudness_decay: float = Field(default=0.9, gt=0, le=1)
    ba_initial_pulse_rate: float = Field(default=0.5, ge=0, le=1)
    ba_pulse_growth: float = Field(default=0.9, gt=0, le=5)
    ssa_c1_initial: float = Field(default=2.0, ge=0.25, le=3)
    sma_restart_probability: float = Field(default=0.03, ge=0, le=1)
    gsa_initial_gravity: float = Field(default=100.0, gt=0, le=500)
    gsa_decay: float = Field(default=20.0, ge=0, le=40)
    gsa_epsilon: float = Field(default=0.01, ge=1e-6, le=1)
    de_mutation_factor: float = Field(default=0.75, ge=0, le=2)
    de_crossover_rate: float = Field(default=0.9, ge=0, le=1)

    @model_validator(mode='after')
    def unique_algorithms(self):
        if len(set(self.algorithms)) != len(self.algorithms):
            raise ValueError('Algoritma seçimleri benzersiz olmalıdır')
        if 'ba' in self.algorithms and self.ba_frequency_min > self.ba_frequency_max:
            raise ValueError('BA frekans aralığı geçersiz')
        if 'iwo' in self.algorithms and (
            self.iwo_max_population < self.population_size or
            self.iwo_max_seeds < self.iwo_min_seeds or
            self.iwo_sigma_final > self.iwo_sigma_initial
        ):
            raise ValueError('IWO population/seed/sigma parameters invalid')
        return self


class TrialMetric(BaseModel):
    seed: int
    best_value: float
    duration_ms: float
    function_evaluations: int
    first_success_evaluations: int | None


class CurvePoint(BaseModel):
    evaluations: int
    mean_best: float
    std_best: float


class ComparisonGroup(BaseModel):
    algorithm: Algorithm
    mean_best: float
    median_best: float
    std_best: float
    min_best: float
    max_best: float
    success_rate: float
    mean_duration_ms: float
    trials: list[TrialMetric]
    curve: list[CurvePoint]
    representative_run: RunResponse


class PairwiseStatistic(BaseModel):
    algorithm_a: Algorithm
    algorithm_b: Algorithm
    a_wins: int
    b_wins: int
    ties: int
    median_log10_difference: float
    p_value: float
    p_holm: float
    method: str = 'paired_exact_sign_flip_log10'


class ComparisonResponse(BaseModel):
    comparison_id: str
    created_at: str
    objective: str
    seeds: list[int]
    trials_per_algorithm: int
    evaluations_per_run: int
    success_tolerance: float
    parameters: dict[str, str | int | float | list[str]]
    methodology: str
    groups: list[ComparisonGroup]
    pairwise: list[PairwiseStatistic] = Field(default_factory=list)


def _run(algorithm: Algorithm, request: ComparisonRequest, seed: int, budget: int) -> RunResponse:
    params: dict = dict(algorithm=algorithm, objective=request.objective,
                        population_size=request.population_size,
                        iterations=request.iterations, seed=seed)
    parameter_fields = {
        'fa': ('alpha', 'beta0', 'gamma'),
        'pso': ('inertia_weight', 'cognitive_coefficient', 'social_coefficient', 'velocity_limit'),
        'abc': ('abc_limit',),
        'mfo': ('mfo_spiral_b',), 'gwo': ('gwo_initial_a',),
        'woa': ('woa_initial_a', 'woa_spiral_b', 'woa_spiral_probability'),
        'ba': ('ba_frequency_min', 'ba_frequency_max', 'ba_initial_loudness',
               'ba_loudness_decay', 'ba_initial_pulse_rate', 'ba_pulse_growth'),
        'ssa': ('ssa_c1_initial',), 'sma': ('sma_restart_probability',),
        'gsa': ('gsa_initial_gravity', 'gsa_decay', 'gsa_epsilon'),
        'de': ('de_mutation_factor', 'de_crossover_rate'),
        'cs': ('cs_discovery_rate', 'cs_step_scale', 'cs_levy_exponent'),
        'iwo': ('iwo_max_population', 'iwo_min_seeds', 'iwo_max_seeds',
                'iwo_sigma_initial', 'iwo_sigma_final', 'iwo_modulation_index'),
        'sa': ('sa_initial_temperature', 'sa_cooling_rate', 'sa_step_scale'),
    }
    for key in parameter_fields[algorithm]:
        # The early FA / PSO field names are intentionally prefixed in the
        # comparison request for compatibility with previous experiment JSON.
        comparison_key = (f'{algorithm}_{key}' if algorithm in ('fa', 'pso') else key)
        if algorithm == 'fa':
            comparison_key = f'fa_{key}'
        params[key] = getattr(request, comparison_key)
    run_request = RunRequest(**params)
    if algorithm == 'abc':
        return simulate_abc_budgeted(run_request, target_evaluations=budget)
    if algorithm == 'cs':
        return simulate_cs_budgeted(run_request, budget)
    if algorithm == 'iwo':
        return simulate_iwo_budgeted(run_request, budget)
    if algorithm == 'sa':
        return simulate_sa_budgeted(run_request, budget)
    return FIXED_NFE_SIMULATORS[algorithm](run_request)


def exact_paired_sign_flip(log_differences: list[float]) -> float:
    """Exact two-sided sign-flip test of mean paired log10 differences.

    Descriptive/exploratory; not a claim that independent algorithms have
    normally distributed or exchangeable outcomes. Same seed labels pair runs.
    """
    nonzero = [abs(x) for x in log_differences if abs(x) > 1e-12]
    if not nonzero:
        return 1.0
    observed = abs(sum(log_differences))
    total = 1 << len(nonzero)
    extreme = sum(abs(sum(a * s for a, s in zip(nonzero, signs))) >= observed - 1e-12
                  for signs in product((-1, 1), repeat=len(nonzero)))
    return min(1.0, extreme / total)


def pairwise_statistics(groups: list[ComparisonGroup]) -> list[PairwiseStatistic]:
    """Matched-seed exploratory pairwise comparisons + Holm adjustment."""
    results: list[PairwiseStatistic] = []
    for a, b in combinations(groups, 2):
        av = [t.best_value for t in a.trials]
        bv = [t.best_value for t in b.trials]
        diffs = [log10(max(x, 1e-60)) - log10(max(y, 1e-60))
                 for x, y in zip(av, bv)]
        results.append(PairwiseStatistic(
            algorithm_a=a.algorithm, algorithm_b=b.algorithm,
            a_wins=sum(x < y for x, y in zip(av, bv)),
            b_wins=sum(x > y for x, y in zip(av, bv)),
            ties=sum(x == y for x, y in zip(av, bv)),
            median_log10_difference=median(diffs),
            p_value=exact_paired_sign_flip(diffs), p_holm=1.0))
    # Holm-Bonferroni step-down for the complete pairwise family.
    ordered = sorted(range(len(results)), key=lambda i: results[i].p_value)
    running_max = 0.0
    for rank, idx in enumerate(ordered):
        running_max = max(running_max, min(1.0, (len(ordered) - rank) * results[idx].p_value))
        results[idx].p_holm = running_max
    return results


def compare(request: ComparisonRequest, *,
            on_trial: Callable[[int, int, str, int], None] | None = None,
            should_cancel: Callable[[], bool] | None = None,
            load_run: Callable[[str, int], RunResponse | None] | None = None,
            save_run: Callable[[str, int, RunResponse], None] | None = None) -> ComparisonResponse:
    seeds = list(range(request.seed_start, request.seed_start + request.trials))
    groups: list[ComparisonGroup] = []
    budget = request.population_size * (request.iterations + 1)
    expected_checkpoints = [request.population_size * (i + 1)
                            for i in range(request.iterations + 1)]

    completed = 0
    total = len(request.algorithms) * request.trials
    for algorithm in request.algorithms:
        runs = []
        trial_results = []
        for seed in seeds:
            if should_cancel is not None and should_cancel():
                raise JobInterrupted()
            result = load_run(algorithm, seed) if load_run else None
            if result is None:
                result = _run(algorithm, request, seed, budget)
                if save_run:
                    save_run(algorithm, seed, result)
            # Assertions protect this contract from optimizer changes.
            assert [f.function_evaluations for f in result.frames] == expected_checkpoints
            runs.append(result)
            completed += 1
            if on_trial is not None:
                on_trial(completed, total, algorithm, seed)
            first_success = next((f.function_evaluations for f in result.frames
                                  if f.best_so_far <= request.success_tolerance), None)
            trial_results.append(TrialMetric(
                seed=seed, best_value=result.frames[-1].best_so_far,
                duration_ms=result.duration_ms, function_evaluations=budget,
                first_success_evaluations=first_success))

        values = [t.best_value for t in trial_results]
        representative_idx = sorted(range(len(runs)),
                                    key=lambda i: (values[i], seeds[i]))[len(runs) // 2]
        curve = []
        for frame_index, checkpoint in enumerate(expected_checkpoints):
            bests = [r.frames[frame_index].best_so_far for r in runs]
            curve.append(CurvePoint(
                evaluations=checkpoint, mean_best=mean(bests), std_best=stdev(bests)))

        groups.append(ComparisonGroup(
            algorithm=algorithm, mean_best=mean(values), median_best=median(values),
            std_best=stdev(values), min_best=min(values), max_best=max(values),
            success_rate=sum(t.first_success_evaluations is not None for t in trial_results) / len(trial_results),
            mean_duration_ms=mean(t.duration_ms for t in trial_results),
            trials=trial_results, curve=curve, representative_run=runs[representative_idx]))

    return ComparisonResponse(
        comparison_id=str(uuid4()), created_at=datetime.now(timezone.utc).isoformat(),
        objective=request.objective, seeds=seeds, trials_per_algorithm=request.trials,
        evaluations_per_run=budget, success_tolerance=request.success_tolerance,
        parameters=request.model_dump(),
        methodology=(
            '14 desteklenen sürekli optimizasyon algoritması, aynı fonksiyon ve tohum etiketleri '
            'ile tam N × (referans iterasyon + 1) amaç fonksiyonu değerlendirmesi (NFE) kullanır. '
            'FA, PSO, MFO, GWO, WOA, BA, SSA, SMA, GSA ve DE nesil başına N değerlendirme yapar. '
            'CS uçuş ve yuva yenileme işlemlerini, IWO her üretilen tohumu ve SA tekil '
            'komşu adaylarını gerçek NFE olarak sayar. IWO sigma ve SA sıcaklık çizelgesi '
            'NFE ufkuna uyarlanır; bağımsız tekil simülasyondaki nesil/döngü çizelgesiyle '
            'aynı değildir. '
            'ABC gerçek işçi, gözlemci ve keşifçi değerlendirmelerini sayarak aynı NFE kontrol '
            'noktalarında kaydedilir; ABC döngüleri yarım kalabilir. Algoritmaların eşit döngü '
            'sayısında çalıştığı varsayılmaz. Rastgele tohum etiketleri eşlenmiştir, fakat '
            'aynı başlangıç popülasyonları garanti edilmez. Standart sapma n-1 ile hesaplanır. '
            'İkili analizlerde, log10 amaç değerinin eşleştirilmiş farklarına iki taraflı tam '
            'işaret-değiştirme testi ve tüm ikililere Holm düzeltmesi kullanılır. Az tekrar '
            'sayısında p değerleri keşifseldir; üstünlük garantisi değildir. Sıfır değerleri '
            'yalnızca logaritma için 1e-60 tabanıyla ele alınır. İleride bağımsız tekrarlı '
            'benchmarklar gereklidir. ACO ayrı TSP problemi çözer. İşlem '
            'süresi çalıştırılan makineye bağlıdır.'
        ),
        groups=groups, pairwise=pairwise_statistics(groups),
    )
