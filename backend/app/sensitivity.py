"""One-factor-at-a-time, paired-seed parameter sensitivity studies.

The objective, evaluation checkpoints and all non-swept parameters remain fixed.
This is a descriptive OFAT experiment, not automatic hyperparameter tuning.
"""
from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean, median, stdev
from typing import Literal, Callable

from .dimensional import JobInterrupted
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import RunResponse
from .comparison import Algorithm, ComparisonRequest, _run
from .objectives import OBJECTIVES


class ParameterSpec(BaseModel):
    key: str
    label: str
    minimum: float
    maximum: float
    default: float
    suggested: list[float]
    integral: bool = False


# Display names and curated, physically meaningful parameter sweeps.
# Parameter bounds are also enforced by ComparisonRequest / RunRequest.
PARAMETERS: dict[str, list[ParameterSpec]] = {
    'fa': [ParameterSpec(key='fa_alpha', label='Rastgelelik (α)', minimum=0, maximum=1, default=.18, suggested=[.05,.18,.5]),
           ParameterSpec(key='fa_gamma',label='Soğurulma (γ)', minimum=0, maximum=5, default=.12, suggested=[.05,.12,.8]),
           ParameterSpec(key='fa_beta0',label='Çekicilik (β₀)',minimum=0,maximum=3,default=1,suggested=[.5,1,2])],
    'pso':[ParameterSpec(key='pso_inertia_weight',label='Atalet ağırlığı (w)',minimum=0,maximum=1.2,default=.72,suggested=[.4,.72,1]),
           ParameterSpec(key='pso_cognitive_coefficient',label='Bilişsel katsayı (c₁)',minimum=0,maximum=4,default=1.49,suggested=[.5,1.49,2.5]),
           ParameterSpec(key='pso_social_coefficient',label='Sosyal katsayı (c₂)',minimum=0,maximum=4,default=1.49,suggested=[.5,1.49,2.5])],
    'abc':[ParameterSpec(key='abc_limit',label='Kaynak terk etme limiti',minimum=1,maximum=500,default=30,suggested=[10,30,60],integral=True)],
    'cs':[ParameterSpec(key='cs_discovery_rate',label='Terk edilme oranı (pₐ)',minimum=0,maximum=1,default=.25,suggested=[.1,.25,.5]),
          ParameterSpec(key='cs_step_scale',label='Lévy adım ölçeği',minimum=.001,maximum=.5,default=.08,suggested=[.03,.08,.2])],
    'mfo':[ParameterSpec(key='mfo_spiral_b',label='Spiral şekil katsayısı (b)',minimum=.1,maximum=3,default=1,suggested=[.5,1,2])],
    'gwo':[ParameterSpec(key='gwo_initial_a',label='Başlangıç kuşatma katsayısı',minimum=.25,maximum=3,default=2,suggested=[.8,2,2.8])],
    'woa':[ParameterSpec(key='woa_spiral_probability',label='Spiral hareket olasılığı',minimum=0,maximum=1,default=.5,suggested=[.2,.5,.8]),
           ParameterSpec(key='woa_spiral_b',label='Spiral şekil katsayısı',minimum=.1,maximum=3,default=1,suggested=[.5,1,2])],
    'ba':[ParameterSpec(key='ba_initial_loudness',label='Başlangıç ses şiddeti',minimum=.05,maximum=1,default=.9,suggested=[.3,.6,.9]),
          ParameterSpec(key='ba_loudness_decay',label='Ses azalması katsayısı',minimum=.05,maximum=1,default=.9,suggested=[.5,.9,.99])],
    'ssa':[ParameterSpec(key='ssa_c1_initial',label='Başlangıç lider katsayısı',minimum=.25,maximum=3,default=2,suggested=[.8,2,2.8])],
    'sma':[ParameterSpec(key='sma_restart_probability',label='Yeniden başlangıç olasılığı',minimum=0,maximum=1,default=.03,suggested=[0,.03,.15])],
    'iwo':[ParameterSpec(key='iwo_sigma_initial',label='Başlangıç yayılımı (σ₀)',minimum=.03,maximum=10,default=1.5,suggested=[.5,1.5,3]),
           ParameterSpec(key='iwo_modulation_index',label='Azalma üssü (m)',minimum=1,maximum=6,default=3,suggested=[1,3,5])],
    'sa':[ParameterSpec(key='sa_initial_temperature',label='Başlangıç sıcaklığı (T₀)',minimum=.01,maximum=100,default=10,suggested=[1,10,30]),
          ParameterSpec(key='sa_cooling_rate',label='Soğuma oranı (r)',minimum=.01,maximum=1,default=.95,suggested=[.8,.95,.99])],
    'gsa':[ParameterSpec(key='gsa_initial_gravity',label='Başlangıç çekimi (G₀)',minimum=.01,maximum=500,default=100,suggested=[25,100,250]),
           ParameterSpec(key='gsa_decay',label='Çekim sönümü (α)',minimum=0,maximum=40,default=20,suggested=[5,20,35])],
    'de':[ParameterSpec(key='de_mutation_factor',label='Mutasyon ölçeği (F)',minimum=0,maximum=2,default=.75,suggested=[.3,.75,1.2]),
          ParameterSpec(key='de_crossover_rate',label='Çaprazlama olasılığı (CR)',minimum=0,maximum=1,default=.9,suggested=[.3,.6,.9])],
}


class SensitivityRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    algorithm: Algorithm = 'pso'
    objective: Literal['sphere','rastrigin','ackley','rosenbrock','griewank','himmelblau','beale','booth'] = 'rastrigin'
    parameter: str = 'pso_inertia_weight'
    values: list[float] = Field(default_factory=lambda: [.4,.72,1],min_length=2,max_length=5)
    population_size: int = Field(default=24,ge=5,le=32)
    iterations: int = Field(default=60,ge=1,le=120)
    trials: int = Field(default=3,ge=2,le=5)
    seed_start: int = Field(default=42,ge=0,le=2_147_483_642)
    success_tolerance: float = Field(default=.001,gt=0,le=100)

    @model_validator(mode='after')
    def validate_sweep(self):
        parameter = next((p for p in PARAMETERS[self.algorithm] if p.key == self.parameter),None)
        if parameter is None:
            raise ValueError('Seçilen parametre bu algoritma için desteklenmiyor')
        if len(set(self.values)) != len(self.values):
            raise ValueError('Parametre değerleri birbirinden farklı olmalıdır')
        for value in self.values:
            if not (parameter.minimum <= value <= parameter.maximum):
                raise ValueError(f'{self.parameter} için değer aralığı: {parameter.minimum}–{parameter.maximum}')
            if parameter.integral and not float(value).is_integer():
                raise ValueError('Bu parametre tam sayı olmalıdır')
            args = dict(algorithms=[self.algorithm, 'fa' if self.algorithm != 'fa' else 'pso'],
                        population_size=self.population_size,iterations=self.iterations,
                        trials=self.trials,seed_start=self.seed_start,objective=self.objective)
            args[self.parameter] = int(value) if parameter.integral else value
            # Includes cross-parameter invariants (e.g. IWO sigma bounds).
            ComparisonRequest(**args)
        return self


class SensitivityTrial(BaseModel):
    seed: int
    best_value: float
    absolute_error: float
    function_evaluations: int
    first_success_nfe: int | None
    duration_ms: float


class SensitivityCurve(BaseModel):
    evaluations: int
    mean_error: float
    std_error: float


class SensitivityGroup(BaseModel):
    parameter_value: float
    mean_error: float
    median_error: float
    std_error: float
    min_error: float
    max_error: float
    success_rate: float
    mean_duration_ms: float
    trials: list[SensitivityTrial]
    curve: list[SensitivityCurve]


class SensitivityResult(BaseModel):
    sensitivity_id: str
    created_at: str
    parameters: SensitivityRequest
    optimum_value: float
    seeds: list[int]
    evaluations_per_run: int
    total_evaluations: int
    methodology: str
    groups: list[SensitivityGroup]


def sensitivity(request: SensitivityRequest, *,
                on_trial: Callable[[int, int, str, int], None] | None = None,
                should_cancel: Callable[[], bool] | None = None,
                load_run: Callable[[float, int], RunResponse | None] | None = None,
                save_run: Callable[[float, int, RunResponse], None] | None = None) -> SensitivityResult:
    budget = request.population_size*(request.iterations+1)
    expected_nfe = [request.population_size*(i+1) for i in range(request.iterations+1)]
    seeds = list(range(request.seed_start,request.seed_start+request.trials))
    objective=OBJECTIVES[request.objective]
    optimum_value=objective.evaluate(*objective.optimum)
    groups=[]
    spec=next(p for p in PARAMETERS[request.algorithm] if p.key==request.parameter)
    completed = 0
    total_units = len(request.values) * request.trials
    for v in request.values:
        param=int(v) if spec.integral else v
        settings = ComparisonRequest(algorithms=[request.algorithm,'fa' if request.algorithm!='fa' else 'pso'],
                                     objective=request.objective,population_size=request.population_size,
                                     iterations=request.iterations,trials=request.trials,
                                     seed_start=request.seed_start,success_tolerance=request.success_tolerance,
                                     **{request.parameter:param})
        runs=[]
        samples=[]
        for seed in seeds:
            if should_cancel is not None and should_cancel():
                raise JobInterrupted()
            run = load_run(v, seed) if load_run else None
            if run is None:
                run = _run(request.algorithm, settings, seed, budget)
                if save_run:
                    save_run(v, seed, run)
            if [frame.function_evaluations for frame in run.frames]!=expected_nfe:
                raise RuntimeError('Algoritmanın NFE kayıtları beklenen kontrol noktalarıyla eşleşmiyor')
            last=max(0,run.frames[-1].best_so_far-optimum_value)
            success=next((f.function_evaluations for f in run.frames
                          if max(0,f.best_so_far-optimum_value)<=request.success_tolerance),None)
            samples.append(SensitivityTrial(seed=seed,best_value=run.frames[-1].best_so_far,
                                            absolute_error=last,function_evaluations=budget,
                                            first_success_nfe=success,duration_ms=run.duration_ms))
            runs.append(run)
            completed += 1
            if on_trial is not None:
                on_trial(completed, total_units, f'{request.algorithm}/{request.parameter}={v:g}', seed)
        errors=[sample.absolute_error for sample in samples]
        curve=[]
        for i,nfe in enumerate(expected_nfe):
            vals=[max(0,run.frames[i].best_so_far-optimum_value) for run in runs]
            curve.append(SensitivityCurve(evaluations=nfe,mean_error=mean(vals),std_error=stdev(vals)))
        groups.append(SensitivityGroup(parameter_value=v,mean_error=mean(errors),
                 median_error=median(errors),std_error=stdev(errors),min_error=min(errors),
                 max_error=max(errors),success_rate=sum(s.first_success_nfe is not None for s in samples)/len(samples),
                 mean_duration_ms=mean(s.duration_ms for s in samples),trials=samples,curve=curve))
    return SensitivityResult(sensitivity_id=str(uuid4()),created_at=datetime.now(timezone.utc).isoformat(),
        parameters=request,optimum_value=optimum_value,seeds=seeds,evaluations_per_run=budget,
        total_evaluations=budget*len(request.values)*request.trials,
        methodology=('Tek değişkenli (OFAT) parametre duyarlılığı: algoritma, iki boyutlu amaç fonksiyonu, '
                     'diğer algoritma parametreleri, NFE bütçesi ve tohum etiketleri sabit tutulur. '
                     'Her parametre değeri için aynı rastgele tohum etiketleri kullanılır; farklı parametreler '
                     'rastgele sayı tüketimini etkileyebileceğinden aynı başlangıç yörüngesi garanti değildir. '
                     'Başarı, f(x)-f* mutlak hatasının eşikten küçük/eşit olmasıdır. '
                     'Ortalamalar bağımsız koşularda; std örneklem (n−1) olarak hesaplanır. '
                     'NFE noktaları ortaktır; farklı algoritmalar farklı sayıda iç iterasyon yapabilir. '
                     'OFAT etkileşimleri ortaya çıkarmaz; veri yalnızca seçilen fonksiyon, değerler ve tohumlara aittir. '
                     'En küçük ortalama hatayı veren değer bu sınırlı deney için tanımlayıcıdır; '
                     'genelleme veya istatistiksel üstünlük kanıtı değildir.'),groups=groups)
