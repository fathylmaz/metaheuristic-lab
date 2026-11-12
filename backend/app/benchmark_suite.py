"""Multi-objective, replicated benchmark suite over the v1.8 fixed-NFE runners.

Scores are translated to known-optimum absolute error within each objective,
then turned into per-objective ranks. Never average raw objectives with different
scales or interpret algorithm ranks across a small sample as universal superiority.
"""
from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean, median, stdev
from typing import Literal, Callable
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .comparison import Algorithm, ComparisonRequest, compare
from .models import RunResponse
from .objectives import OBJECTIVES

ObjectiveId = Literal['sphere', 'rastrigin', 'ackley', 'rosenbrock',
                      'griewank', 'himmelblau', 'beale', 'booth']


class BenchmarkSuiteRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    objectives: list[ObjectiveId] = Field(default_factory=lambda: ['sphere', 'rastrigin', 'ackley'], min_length=2, max_length=5)
    comparison: ComparisonRequest = Field(default_factory=lambda: ComparisonRequest(algorithms=['pso','gwo','de']))

    @model_validator(mode='after')
    def validate_experiment(self):
        if len(set(self.objectives)) != len(self.objectives):
            raise ValueError('Benchmark fonksiyonları benzersiz olmalıdır')
        if len(self.comparison.algorithms) > 4:
            raise ValueError('Benchmark matrisi en fazla dört algoritmayı destekler')
        total = (len(self.objectives) * len(self.comparison.algorithms) *
                 self.comparison.trials * self.comparison.population_size *
                 (self.comparison.iterations + 1))
        if total > 200_000:
            raise ValueError('Toplam NFE 200.000 sınırını aşıyor; deney boyutunu azalt')
        return self


class BenchmarkTrial(BaseModel):
    seed: int
    best_value: float
    absolute_error: float
    function_evaluations: int
    first_success_evaluations: int | None
    duration_ms: float


class BenchmarkCell(BaseModel):
    algorithm: Algorithm
    mean_error: float
    median_error: float
    std_error: float
    best_error: float
    success_rate: float
    mean_duration_ms: float
    rank: float
    trials: list[BenchmarkTrial]


class BenchmarkRow(BaseModel):
    objective: ObjectiveId
    optimum: tuple[float, float]
    optimum_value: float
    cells: list[BenchmarkCell]


class BenchmarkSummary(BaseModel):
    algorithm: Algorithm
    mean_rank: float
    mean_success_rate: float
    objective_wins: int
    objectives_measured: int


class BenchmarkSuiteResult(BaseModel):
    benchmark_id: str
    created_at: str
    objectives: list[ObjectiveId]
    algorithms: list[Algorithm]
    seeds: list[int]
    evaluations_per_run: int
    total_evaluations: int
    success_tolerance: float
    parameters: dict
    methodology: str
    rows: list[BenchmarkRow]
    summary: list[BenchmarkSummary]


def average_ranks(values: list[float]) -> list[float]:
    """Average positions for exact equal values, with rank 1 best (lower)."""
    order = sorted(range(len(values)), key=lambda j: (values[j], j))
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        rank = (start + 1 + end) / 2
        for k in order[start:end]:
            ranks[k] = rank
        start = end
    return ranks


def benchmark_suite(request: BenchmarkSuiteRequest, *,
                    on_trial: Callable[[int, int, str, int], None] | None = None,
                    should_cancel: Callable[[], bool] | None = None,
                    load_run: Callable[[str, str, int], RunResponse | None] | None = None,
                    save_run: Callable[[str, str, int, RunResponse], None] | None = None) -> BenchmarkSuiteResult:
    comparison = request.comparison
    seeds = list(range(comparison.seed_start, comparison.seed_start + comparison.trials))
    budget = comparison.population_size * (comparison.iterations + 1)
    rows: list[BenchmarkRow] = []
    total_units = len(request.objectives) * len(comparison.algorithms) * comparison.trials
    for objective_index, objective_id in enumerate(request.objectives):
        objective = OBJECTIVES[objective_id]
        optimum_value = objective.evaluate(*objective.optimum)
        # Use exactly the same default/explicit algorithm parameters, seed
        # labels, NFE cap, and trial count for each objective.
        # A local comparison gets a fresh 0..N trial counter; offset into the
        # complete multi-objective matrix and keep the objective in status text.
        def report_trial(done: int, _local_total: int, algorithm: str, seed: int):
            if on_trial is not None:
                offset = objective_index * len(comparison.algorithms) * comparison.trials
                on_trial(offset + done, total_units, f'{objective_id}/{algorithm}', seed)
        one = compare(comparison.model_copy(update={'objective': objective_id}),
                      on_trial=report_trial, should_cancel=should_cancel,
                      load_run=(lambda a, s: load_run(objective_id, a, s)) if load_run else None,
                      save_run=(lambda a, s, run: save_run(objective_id, a, s, run)) if save_run else None)
        cells = []
        for group in one.groups:
            trials = [BenchmarkTrial(
                seed=run.seed, best_value=run.best_value,
                absolute_error=abs(run.best_value - optimum_value),
                function_evaluations=run.function_evaluations,
                first_success_evaluations=run.first_success_evaluations,
                duration_ms=run.duration_ms,
            ) for run in group.trials]
            # Existing comparison success is f <= tolerance (valid for all
            # built-in nonnegative functions, all known optima have f*=0).
            errors = [x.absolute_error for x in trials]
            cells.append(BenchmarkCell(
                algorithm=group.algorithm,
                mean_error=mean(errors), median_error=median(errors),
                std_error=stdev(errors), best_error=min(errors),
                success_rate=sum(x.absolute_error <= comparison.success_tolerance for x in trials) / len(trials),
                mean_duration_ms=mean(x.duration_ms for x in trials),
                rank=0, trials=trials,
            ))
        ranks = average_ranks([x.mean_error for x in cells])
        for cell, rank in zip(cells, ranks):
            cell.rank = rank
        rows.append(BenchmarkRow(objective=objective_id,
                                 optimum=objective.optimum, optimum_value=optimum_value, cells=cells))

    summary = []
    for algorithm in comparison.algorithms:
        cells = [next(cell for cell in row.cells if cell.algorithm == algorithm) for row in rows]
        summary.append(BenchmarkSummary(
            algorithm=algorithm,
            mean_rank=mean(cell.rank for cell in cells),
            mean_success_rate=mean(cell.success_rate for cell in cells),
            objective_wins=sum(cell.rank == 1.0 for cell in cells),
            objectives_measured=len(cells),
        ))
    summary.sort(key=lambda item: (item.mean_rank, -item.mean_success_rate, item.algorithm))
    return BenchmarkSuiteResult(
        benchmark_id=str(uuid4()), created_at=datetime.now(timezone.utc).isoformat(),
        objectives=request.objectives, algorithms=comparison.algorithms, seeds=seeds,
        evaluations_per_run=budget,
        total_evaluations=budget*len(request.objectives)*len(comparison.algorithms)*comparison.trials,
        success_tolerance=comparison.success_tolerance,
        parameters=request.model_dump(), rows=rows, summary=summary,
        methodology=(
            'Her benchmark fonksiyonu iki boyutludur. Seçilen algoritmalar aynı fonksiyon üzerinde '
            'aynı NFE bütçesi ve aynı rastgele tohum etiketleriyle çalışır; '
            'tohum etiketi aynı olsa da ilk ajan konumları algoritmalar arasında aynı değildir. '
            'Fonksiyonlar arasında yalnızca optimumdan mutlak hata, fonksiyon içi sıra '
            've başarı oranı özetlenir; farklı fonksiyonların ham amaç değerleri ortalanmaz. '
            'Ortalama sıra yalnızca seçilen problem kümesini betimler; istatistiksel anlamlılık '
            've genel üstünlük iddiası değildir. Bağımsızlık için her koşu kendi rastgele tohumunu '
            'kullanır. Süreler yerel donanıma bağlıdır. SA tek çözüm, IWO değişken popülasyon '
            'kullanır; CS/IWO/SA için bütçe uyarlamalı varyantlar kullanılmıştır. '
            'ACO ayrık TSP olduğundan bu benchmarkın dışındadır.'
        ),
    )
