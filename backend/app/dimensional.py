"""True D-dimensional benchmark engine (2/5/10/30) for PSO, GWO, DE, WOA, MFO, SSA, FA, BA, GSA, ABC, CS, SMA, IWO and SA.

Independent of the legacy 2D animation API.  Tracks actual objective evaluations,
retains an incumbent best and returns a truthful *first-two-coordinate projection*.
All results are minimization errors relative to a known global optimum of value zero.
"""
from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean, median, stdev
from time import perf_counter
from typing import Literal, Callable
from uuid import uuid4

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

AlgorithmD = Literal['pso', 'gwo', 'de', 'woa', 'mfo', 'ssa', 'fa', 'ba', 'gsa', 'abc', 'cs', 'sma', 'iwo', 'sa']
ObjectiveD = Literal['sphere', 'rastrigin', 'ackley', 'rosenbrock', 'griewank']
_BOUNDS = {'sphere': (-5.12, 5.12), 'rastrigin': (-5.12, 5.12),
           'ackley': (-5., 5.), 'rosenbrock': (-3., 3.), 'griewank': (-6., 6.)}


class DimensionalRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    algorithms: list[AlgorithmD] = Field(default_factory=lambda: ['pso', 'gwo', 'de'], min_length=2, max_length=4)
    objective: ObjectiveD = 'rastrigin'
    dimensions: Literal[2, 5, 10, 30] = 10
    population_size: int = Field(default=24, ge=8, le=64)
    iterations: int = Field(default=90, ge=5, le=200)
    trials: int = Field(default=3, ge=2, le=20)
    seed_start: int = Field(default=42, ge=0, le=2147483640)
    success_tolerance: float = Field(default=0.001, gt=0, le=100)
    pso_inertia_weight: float = Field(default=.72, ge=0, le=1.2)
    pso_cognitive_coefficient: float = Field(default=1.49, ge=0, le=4)
    pso_social_coefficient: float = Field(default=1.49, ge=0, le=4)
    pso_velocity_limit: float = Field(default=.20, gt=0, le=1)
    gwo_initial_a: float = Field(default=2.0, ge=.25, le=3)
    de_mutation_factor: float = Field(default=.75, ge=0, le=2)
    de_crossover_rate: float = Field(default=.90, ge=0, le=1)
    woa_initial_a: float = Field(default=2.0, ge=.25, le=3)
    woa_spiral_b: float = Field(default=1.0, ge=.1, le=3)
    woa_spiral_probability: float = Field(default=.5, ge=0, le=1)
    mfo_spiral_b: float = Field(default=1.0, ge=.1, le=3)
    ssa_c1_initial: float = Field(default=2.0, ge=.25, le=3)
    fa_alpha: float = Field(default=.18, ge=0, le=1)
    fa_beta0: float = Field(default=1.0, ge=0, le=3)
    fa_gamma: float = Field(default=.12, ge=0, le=5)
    ba_min_frequency: float = Field(default=0.0, ge=0, le=5)
    ba_max_frequency: float = Field(default=2.0, gt=0, le=5)
    ba_initial_loudness: float = Field(default=.9, gt=0, le=1)
    ba_loudness_decay: float = Field(default=.9, gt=0, le=1)
    ba_initial_pulse_rate: float = Field(default=.5, ge=0, le=1)
    ba_pulse_growth: float = Field(default=.9, gt=0, le=5)
    gsa_initial_gravity: float = Field(default=100.0, gt=0, le=500)
    gsa_decay: float = Field(default=20.0, ge=0, le=40)
    gsa_epsilon: float = Field(default=.01, ge=.001, le=1)
    abc_limit: int = Field(default=30, ge=1, le=200)
    cs_discovery_rate: float = Field(default=.25, ge=0, le=1)
    cs_step_scale: float = Field(default=.08, gt=0, le=.5)
    cs_levy_exponent: float = Field(default=1.5, ge=1.1, le=1.9)
    sma_restart_probability: float = Field(default=.03, ge=0, le=1)
    iwo_max_population: int = Field(default=60, ge=8, le=128)
    iwo_min_seeds: int = Field(default=0, ge=0, le=8)
    iwo_max_seeds: int = Field(default=5, ge=1, le=8)
    iwo_sigma_initial: float = Field(default=1.5, gt=0, le=5)
    iwo_sigma_final: float = Field(default=.02, gt=0, le=5)
    iwo_modulation_index: float = Field(default=3.0, gt=0, le=6)
    sa_initial_temperature: float = Field(default=10.0, gt=0, le=100)
    sa_cooling_rate: float = Field(default=.95, gt=0, le=1)
    sa_step_scale: float = Field(default=.10, gt=0, le=1)


    @model_validator(mode='after')
    def check_budget(self):
        if len(set(self.algorithms)) != len(self.algorithms):
            raise ValueError('Algoritma seçimleri benzersiz olmalıdır')
        if self.ba_min_frequency >= self.ba_max_frequency:
            raise ValueError('BA en büyük frekans en küçük frekanstan büyük olmalıdır')
        if self.population_size < 8 and 'de' in self.algorithms:
            raise ValueError('DE için en az sekiz birey gerekir')
        if 'iwo' in self.algorithms and (self.iwo_max_population < self.population_size
            or self.iwo_min_seeds > self.iwo_max_seeds or self.iwo_sigma_initial < self.iwo_sigma_final):
            raise ValueError('IWO parameters: maximum population, seed range and dispersal deviations must be ordered')
        budget = self.population_size * (self.iterations + 1) * self.trials * len(self.algorithms)
        if budget > 160_000:
            raise ValueError('Toplam fonksiyon değerlendirmesi 160.000 sınırını aşıyor')
        return self


class DimensionalPoint(BaseModel):
    evaluations: int
    best_error: float
    best_position: list[float]


class DimensionalTrial(BaseModel):
    seed: int
    best_error: float
    best_position: list[float]
    function_evaluations: int
    first_success_nfe: int | None
    duration_ms: float
    trajectory: list[DimensionalPoint]


class DimensionalGroup(BaseModel):
    algorithm: AlgorithmD
    mean_error: float
    median_error: float
    std_error: float
    min_error: float
    success_rate: float
    mean_duration_ms: float
    curve: list[dict[str, float | int]]
    trials: list[DimensionalTrial]


class DimensionalResult(BaseModel):
    experiment_id: str
    created_at: str
    parameters: DimensionalRequest
    optimum_position: list[float]
    optimum_value: float
    evaluations_per_run: int
    total_evaluations: int
    seeds: list[int]
    methodology: str
    groups: list[DimensionalGroup]


def objective_nd(name: ObjectiveD, x: np.ndarray) -> np.ndarray:
    """Vectorized over candidates, scalar per candidate, with canonical D definitions."""
    a = np.asarray(x, dtype=np.float64)
    if a.ndim == 1:
        a = a[np.newaxis, :]
    d = a.shape[1]
    if name == 'sphere':
        return np.sum(a*a, axis=1)
    if name == 'rastrigin':
        return 10*d + np.sum(a*a - 10*np.cos(2*np.pi*a), axis=1)
    if name == 'ackley':
        return -20*np.exp(-.2*np.sqrt(np.mean(a*a, axis=1))) - np.exp(np.mean(np.cos(2*np.pi*a), axis=1)) + 20 + np.e
    if name == 'rosenbrock':
        return np.sum(100*(a[:,1:]-a[:,:-1]**2)**2 + (1-a[:,:-1])**2, axis=1)
    if name == 'griewank':
        return 1 + np.sum(a*a, axis=1)/4000 - np.prod(np.cos(a/np.sqrt(np.arange(1, d+1))), axis=1)
    raise ValueError(f'Unknown function: {name}')


def _woa_generation(old: np.ndarray, best: np.ndarray, rng: np.random.Generator,
                    a: float, b: float, spiral_probability: float,
                    low: float, high: float) -> np.ndarray:
    """WOA: vector encircling/search or scalar-l bubble-net spiral, frozen peers."""
    n, d = old.shape
    result = np.empty_like(old)
    for i in range(n):
        p = float(rng.random())
        if p < 1 - spiral_probability:
            A = 2 * a * rng.random(d) - a
            C = 2 * rng.random(d)
            if np.max(np.abs(A)) >= 1:
                peer = int(rng.integers(n - 1))
                if peer >= i:
                    peer += 1
                target = old[peer]
            else:
                target = best
            candidate = target - A * np.abs(C * target - old[i])
        else:
            ell = float(rng.uniform(-1, 1))
            candidate = best + np.abs(best - old[i]) * np.exp(b * ell) * np.cos(2 * np.pi * ell)
        result[i] = np.clip(candidate, low, high)
    return result


def _mfo_generation(pos: np.ndarray, fitness: np.ndarray, flames: np.ndarray,
                    step: int, iterations: int, rng: np.random.Generator,
                    b: float, low: float, high: float) -> tuple[np.ndarray, int]:
    """MFO: sorted moth-to-flame matches, one spiral draw per D coordinate."""
    n, d = pos.shape
    flame_count = max(1, min(n, int(np.floor(n - step * (n - 1) / iterations + .5))))
    r = -1.0 - step / iterations
    result = np.empty_like(pos)
    for rank, idx in enumerate(np.argsort(fitness, kind='stable')):
        target = flames[min(rank, flame_count - 1)]
        t = rng.uniform(r, 1, size=d)
        result[idx] = np.clip(target + np.abs(target - pos[idx]) *
                              np.exp(b*t) * np.cos(2*np.pi*t), low, high)
    return result, flame_count


def _mfo_flames(old_flames: np.ndarray, old_fit: np.ndarray,
                pos: np.ndarray, fitness: np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Best evaluated distinct locations from archive+population; pad if all coalesce."""
    all_pos = np.vstack((old_flames, pos))
    all_fit = np.concatenate((old_fit, fitness))
    order = np.argsort(all_fit, kind='stable')
    indices: list[int] = []
    seen: set[tuple[float, ...]] = set()
    for raw in order:
        idx = int(raw)
        key = tuple(float(z) for z in all_pos[idx])
        if key not in seen:
            indices.append(idx)
            seen.add(key)
        if len(indices) == n:
            break
    # When fewer than N distinct evaluated points remain, repeat the best
    # evaluated flame rather than fabricating an uncounted objective evaluation.
    if len(indices) < n:
        indices.extend([indices[0]] * (n - len(indices)))
    return all_pos[indices].copy(), all_fit[indices].copy()


def _ssa_generation(old: np.ndarray, food: np.ndarray, rng: np.random.Generator,
                    c1: float, low: float, high: float) -> np.ndarray:
    """SSA: per-coordinate leader draw and ordered, updated-predecessor chain."""
    n, d = old.shape
    result = np.empty_like(old)
    c2 = rng.random(d)
    c3 = rng.random(d)
    sign = np.where(c3 >= .5, 1.0, -1.0)
    result[0] = np.clip(food + sign*c1*((high-low)*c2 + low), low, high)
    for i in range(1,n):
        result[i] = np.clip(.5*(old[i]+result[i-1]), low, high)
    return result


def _fa_generation(old: np.ndarray, fitness: np.ndarray, rng: np.random.Generator,
                   alpha: float, beta0: float, gamma: float,
                   low: float, high: float) -> np.ndarray:
    """D-dimensional, frozen brightness + sequential attraction, one evaluation/agent.

    The whole old generation supplies targets. An agent updates its working position
    against every strictly better firefly and receives a random U(-.5,.5) D-vector
    per attraction. Unattracted agents receive one random exploration step.
    """
    n, d = old.shape
    nxt = np.empty_like(old)
    step_scale = alpha * (high - low)
    for i in range(n):
        working = old[i].copy()
        attracted = False
        for j in range(n):
            if fitness[j] >= fitness[i]:
                continue
            delta = old[j] - working
            beta = beta0 * np.exp(-gamma * float(np.dot(delta, delta)))
            working = np.clip(working + beta*delta + step_scale*(rng.random(d)-.5),low,high)
            attracted = True
        if not attracted:
            working = np.clip(working + step_scale*(rng.random(d)-.5),low,high)
        nxt[i] = working
    return nxt


def _ba_generation(old: np.ndarray, velocities: np.ndarray, fitness: np.ndarray,
                   incumbent: np.ndarray, loudness: np.ndarray, pulse_rates: np.ndarray,
                   rng: np.random.Generator, cfg: DimensionalRequest, step: int,
                   low: float, high: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray,
                                                        np.ndarray, np.ndarray, np.ndarray]:
    """Yang-style BA: one evaluated candidate per bat even when rejected.

    All local proposals use the old global best and old mean loudness. Velocities
    change even if proposed positions are not accepted. No artificial objective
    evaluations are added for rejected proposals.
    Returns positions, velocities, fitness, loudness, pulse rates, candidates, acceptance mask.
    """
    n, d = old.shape
    nxt = old.copy()
    vel = velocities.copy()
    new_fitness = fitness.copy()
    new_loudness = loudness.copy()
    new_pulse = pulse_rates.copy()
    candidates = np.empty_like(old)
    accepted = np.zeros(n, dtype=bool)
    avg_loudness = float(loudness.mean())
    for i in range(n):
        frequency = float(rng.uniform(cfg.ba_min_frequency, cfg.ba_max_frequency))
        vel[i] = velocities[i] + (old[i]-incumbent)*frequency
        candidate = old[i] + vel[i]
        if float(rng.random()) > pulse_rates[i]:
            candidate = incumbent + rng.uniform(-1,1,size=d)*avg_loudness
        candidate = np.clip(candidate,low,high)
        candidates[i] = candidate
        candidate_fit = float(objective_nd(cfg.objective,candidate)[0])
        draw = float(rng.random())
        if candidate_fit < fitness[i] and draw < loudness[i]:
            nxt[i] = candidate
            new_fitness[i] = candidate_fit
            new_loudness[i] *= cfg.ba_loudness_decay
            new_pulse[i] = cfg.ba_initial_pulse_rate*(1-np.exp(-cfg.ba_pulse_growth*step))
            accepted[i] = True
    return nxt,vel,new_fitness,new_loudness,new_pulse,candidates,accepted


def _gsa_masses(fitness: np.ndarray) -> np.ndarray:
    """Normalized minimization masses; numerical ties distribute equal mass."""
    best, worst = float(np.min(fitness)), float(np.max(fitness))
    if np.isclose(best,worst,rtol=0,atol=1e-15):
        return np.full(len(fitness),1.0/len(fitness))
    raw = np.maximum((worst-fitness)/(worst-best),0.)
    return raw/float(raw.sum()) if raw.sum() > 0 else np.full(len(fitness),1.0/len(fitness))


def _gsa_generation(old: np.ndarray, velocities: np.ndarray, fitness: np.ndarray,
                    rng: np.random.Generator, cfg: DimensionalRequest, step: int,
                    low: float, high: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, int]:
    """GSA mass-weighted Kbest gravitational forces in arbitrary dimensions.

    Uses prior-generation mass and positions; coordinate-wise random source
    weights, distance smoothing, and a random velocity inertia multiplier.
    """
    n, d = old.shape
    masses = _gsa_masses(fitness)
    g = float(cfg.gsa_initial_gravity*np.exp(-cfg.gsa_decay*step/cfg.iterations))
    kbest = max(1,min(n,int(np.ceil(n-(n-1)*step/cfg.iterations))))
    elite = np.argsort(-masses,kind='stable')[:kbest]
    force = np.zeros_like(old)
    for i in range(n):
        for j in elite:
            j = int(j)
            if j == i:
                continue
            delta = old[j] - old[i]
            distance = float(np.linalg.norm(delta))
            force[i] += (rng.random(d)*g*masses[i]*masses[j]/(distance+cfg.gsa_epsilon))*delta
    acceleration = force/np.maximum(masses[:,None],1e-12)
    proposed_velocity = rng.random((n,d))*velocities + acceleration
    proposed_pos = old + proposed_velocity
    pos = np.clip(proposed_pos,low,high)
    vel = proposed_velocity.copy()
    vel[pos != proposed_pos] = 0.0
    return pos,vel,masses,acceleration,g,kbest


def _run_one(cfg: DimensionalRequest, algorithm: AlgorithmD, seed: int) -> DimensionalTrial:
    if algorithm in ('abc','cs','sma','iwo','sa'):
        from .dimensional_budgeted import run_budgeted_nd
        return run_budgeted_nd(cfg,algorithm,seed)
    started = perf_counter()
    rng = np.random.default_rng(seed)
    n, d = cfg.population_size, cfg.dimensions
    low, high = _BOUNDS[cfg.objective]
    pos = rng.uniform(low, high, size=(n, d))
    fitness = objective_nd(cfg.objective, pos)
    evaluations = n
    best_idx = int(np.argmin(fitness))
    incumbent = pos[best_idx].copy()
    best = float(fitness[best_idx])
    first_success = evaluations if best <= cfg.success_tolerance else None
    trajectory = [DimensionalPoint(evaluations=evaluations, best_error=max(0., best), best_position=incumbent.tolist())]

    if algorithm == 'mfo':
        order = np.argsort(fitness, kind='stable')
        flames = pos[order].copy()
        flame_fitness = fitness[order].copy()

    if algorithm in ('pso','ba','gsa'):
        velocities = np.zeros((n, d))
        if algorithm == 'pso':
            pbest = pos.copy()
            pbest_fit = fitness.copy()
            limit = cfg.pso_velocity_limit * (high - low)
        if algorithm == 'ba':
            loudness = np.full(n,cfg.ba_initial_loudness)
            pulse_rates = np.zeros(n)

    for step in range(1, cfg.iterations + 1):
        if algorithm == 'pso':
            v = (cfg.pso_inertia_weight*velocities +
                 cfg.pso_cognitive_coefficient*rng.random((n,d))*(pbest-pos) +
                 cfg.pso_social_coefficient*rng.random((n,d))*(incumbent-pos))
            v = np.clip(v, -limit, limit)
            proposed = pos+v
            pos = np.clip(proposed, low, high)
            velocities = np.where(pos == proposed, v, 0.)
            fitness = objective_nd(cfg.objective, pos)
            improved = fitness < pbest_fit
            pbest[improved] = pos[improved]
            pbest_fit[improved] = fitness[improved]
        elif algorithm == 'gwo':
            leaders = pos[np.argsort(fitness, kind='stable')[:3]].copy()
            a = cfg.gwo_initial_a * (1 - (step-1)/cfg.iterations)
            candidates = []
            for leader in leaders:
                A = 2*a*rng.random((n,d))-a
                C = 2*rng.random((n,d))
                candidates.append(leader-A*np.abs(C*leader-pos))
            pos = np.clip(np.mean(candidates,axis=0),low,high)
            fitness = objective_nd(cfg.objective,pos)
        elif algorithm == 'woa':
            a = cfg.woa_initial_a * (1 - (step-1) / max(1,cfg.iterations-1))
            pos = _woa_generation(pos.copy(), incumbent.copy(), rng, a, cfg.woa_spiral_b,
                                  cfg.woa_spiral_probability, low, high)
            fitness = objective_nd(cfg.objective, pos)
        elif algorithm == 'mfo':
            pos, flame_count = _mfo_generation(pos, fitness, flames, step, cfg.iterations, rng,
                                               cfg.mfo_spiral_b, low, high)
            fitness = objective_nd(cfg.objective, pos)
            flames, flame_fitness = _mfo_flames(flames, flame_fitness, pos, fitness, n)
        elif algorithm == 'ssa':
            c1 = cfg.ssa_c1_initial * np.exp(-((4 * step/cfg.iterations)**2))
            pos = _ssa_generation(pos.copy(), incumbent.copy(), rng, c1, low, high)
            fitness = objective_nd(cfg.objective, pos)
        elif algorithm == 'fa':
            pos = _fa_generation(pos.copy(), fitness.copy(), rng,
                                 cfg.fa_alpha,cfg.fa_beta0,cfg.fa_gamma,low,high)
            fitness = objective_nd(cfg.objective,pos)
        elif algorithm == 'ba':
            pos,velocities,fitness,loudness,pulse_rates,_,_ = _ba_generation(
                pos.copy(),velocities.copy(),fitness.copy(),incumbent.copy(),
                loudness,pulse_rates,rng,cfg,step,low,high)
        elif algorithm == 'gsa':
            pos,velocities,_,_,_,_ = _gsa_generation(
                pos.copy(),velocities.copy(),fitness.copy(),rng,cfg,step,low,high)
            fitness = objective_nd(cfg.objective,pos)
        else:  # DE/rand/1/bin, all donors from frozen previous generation
            prior = pos.copy()
            trial_pos = np.empty_like(prior)
            for i in range(n):
                pool = np.concatenate((np.arange(i), np.arange(i+1,n)))
                r1,r2,r3 = rng.choice(pool,size=3,replace=False)
                mutant = np.clip(prior[r1]+cfg.de_mutation_factor*(prior[r2]-prior[r3]),low,high)
                crossover = rng.random(d) < cfg.de_crossover_rate
                crossover[int(rng.integers(d))] = True
                trial_pos[i] = np.where(crossover,mutant,prior[i])
            trial_fitness = objective_nd(cfg.objective,trial_pos)
            improve = trial_fitness <= fitness
            pos[improve] = trial_pos[improve]
            fitness[improve] = trial_fitness[improve]

        evaluations += n  # one real evaluation per candidate per generation
        idx = int(np.argmin(fitness))
        if float(fitness[idx]) < best:
            best = float(fitness[idx])
            incumbent = pos[idx].copy()
        if first_success is None and best <= cfg.success_tolerance:
            first_success = evaluations
        trajectory.append(DimensionalPoint(evaluations=evaluations,
                                           best_error=max(0.,best),best_position=incumbent.tolist()))

    return DimensionalTrial(seed=seed,best_error=max(0.,best),best_position=incumbent.tolist(),
                            function_evaluations=evaluations, first_success_nfe=first_success,
                            duration_ms=(perf_counter()-started)*1000, trajectory=trajectory)


class JobInterrupted(Exception):
    """Cooperative cancellation between complete algorithm/seed trials."""


def run_dimensional(cfg: DimensionalRequest,
                    on_trial: Callable[[int, int, str, int], None] | None = None,
                    should_cancel: Callable[[], bool] | None = None,
                    load_trial: Callable[[str, int], DimensionalTrial | None] | None = None,
                    save_trial: Callable[[str, int, DimensionalTrial], None] | None = None) -> DimensionalResult:
    seeds = list(range(cfg.seed_start,cfg.seed_start+cfg.trials))
    budget = cfg.population_size*(cfg.iterations+1)
    groups = []
    completed = 0
    total_units = len(cfg.algorithms) * len(seeds)
    for algorithm in cfg.algorithms:
        trials = []
        for seed in seeds:
            if should_cancel and should_cancel():
                raise JobInterrupted()
            trial = load_trial(algorithm, seed) if load_trial else None
            if trial is None:
                trial = _run_one(cfg, algorithm, seed)
                if save_trial:
                    save_trial(algorithm, seed, trial)
            trials.append(trial)
            completed += 1
            if on_trial:
                on_trial(completed, total_units, algorithm, seed)
            if should_cancel and should_cancel():
                raise JobInterrupted()
        vals = [t.best_error for t in trials]
        curve = [{'evaluations':budget_point.evaluations,
                  'mean_error':mean(t.trajectory[k].best_error for t in trials),
                  'std_error':stdev(t.trajectory[k].best_error for t in trials)}
                 for k,budget_point in enumerate(trials[0].trajectory)]
        groups.append(DimensionalGroup(algorithm=algorithm,mean_error=mean(vals),median_error=median(vals),
                                       std_error=stdev(vals),min_error=min(vals),
                                       success_rate=sum(v<=cfg.success_tolerance for v in vals)/len(vals),
                                       mean_duration_ms=mean(t.duration_ms for t in trials),curve=curve,trials=trials))
    optimum = [1.0 if cfg.objective=='rosenbrock' else 0.0]*cfg.dimensions
    return DimensionalResult(experiment_id=str(uuid4()),created_at=datetime.now(timezone.utc).isoformat(),
                             parameters=cfg,optimum_position=optimum,optimum_value=0.0,
                             evaluations_per_run=budget,total_evaluations=budget*len(cfg.algorithms)*cfg.trials,
                             seeds=seeds,
                             methodology=('Gerçek D-boyutlu matematiksel optimizasyon: PSO, GWO, DE, WOA, MFO, SSA, FA, BA ve GSA. '
                               'NFE=N×(Tref+1), fakat ABC/CS/IWO/SA için ortak kayıt noktaları nesil demek değildir; '
                               'SA tek çözümlüdür, ABC işçi/gözlemci/keşifçi döngüleri; CS yuva terk etme; '
                               'IWO değişken popülasyon, NFE-normalize yayılma; SMA adaptif W/p/vb/vc uygular. '
                               'Tohumlar her algoritmada aynı etiketle '
                               'kullanılır ancak eş başlangıç popülasyonu garantisi değildir. '
                               'Optimumdan mutlak hata, bağımsız tekrarların ortalamasıdır. '
                               'WOA: senkron kuşatma/arama/spiral; MFO: benzersiz elit alev arşivi ve azalan alev sayısı; '
                               'SSA: lider ve sıralı takipçi zinciri; FA: eski parlaklığa göre ardışık çekim; '
                               'BA: donmuş en iyiye göre tek aday/yarasa ve olasılıksal kabul; '
                               'GSA: normalize kütle, Kbest çekim ve kuvvet/ivme. '
                               'İlk iki koordinat izdüşümü optimizasyon yüzeyi değildir. '
                               'Küçük tekrar sayıları istatistiksel üstünlük kanıtlamaz.'),groups=groups)
