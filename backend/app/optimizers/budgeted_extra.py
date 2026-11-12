"""Exact evaluation-budget comparison adapters for CS, IWO and SA.

These adapters are intentionally separate from the educational standalone
simulators: standalone generation semantics remain unchanged. Comparison
snapshots are emitted at common NFE checkpoints, which can be mid-generation.
SA uses a budget-normalized cooling horizon, IWO uses a budget-progress sigma
schedule. They are labelled explicitly as budgeted variants, not identical
90-generation standalone runs. Every objective evaluation is counted once.
"""
from __future__ import annotations

from math import floor
from time import perf_counter
from uuid import uuid4

import numpy as np

from ..models import AgentState, RunRequest, RunResponse, SimulationFrame
from ..objectives import OBJECTIVES
from .annealing import metropolis_probability
from .cuckoo import _levy
from .iwo import seed_counts


def _setup(request: RunRequest, target_evaluations: int):
    n = request.population_size
    if target_evaluations < n or target_evaluations % n:
        raise ValueError('NFE hedefi popülasyonun pozitif bir katı olmalı')
    objective = OBJECTIVES[request.objective]
    return n, objective, np.random.default_rng(request.seed)


def _finish(request: RunRequest, frames: list[SimulationFrame], t0: float,
            variant: str) -> RunResponse:
    objective = OBJECTIVES[request.objective]
    return RunResponse(
        run_id=str(uuid4()), algorithm=request.algorithm, objective=request.objective,
        seed=request.seed, bounds=objective.bounds, optimum=objective.optimum,
        frames=frames, duration_ms=round((perf_counter() - t0)*1000, 2),
        variant=variant, parameters=request.model_dump(),
    )


def _expected_frames(n: int, target: int) -> list[int]:
    return list(range(n, target+1, n))


def simulate_cs_budgeted(request: RunRequest, target_evaluations: int) -> RunResponse:
    """Cut off candidate/abandonment evaluations exactly at the shared NFE cap."""
    n, obj, rng = _setup(request, target_evaluations)
    lo, hi = obj.bounds
    t0 = perf_counter()
    pos = rng.uniform(lo, hi, (n, 2))
    fit = np.array([obj.evaluate(*p) for p in pos], dtype=float)
    evaluations = n
    winner = int(np.argmin(fit))
    archived = float(fit[winner]); archived_pos = pos[winner].copy()
    abandonment = min(n-1, int(floor(request.cs_discovery_rate*n+.5)))
    frames: list[SimulationFrame] = []
    actions = ['retained'] * n
    lengths = [0.0]*n
    acc = abandoned = 0

    def record():
        nonlocal actions, lengths, acc, abandoned
        best = float(fit.min()); scale = max(float(fit.max())-best, 1e-12)
        center = pos.mean(axis=0)
        frames.append(SimulationFrame(
            iteration=len(frames), agents=[AgentState(id=i, x=float(p[0]), y=float(p[1]),
                fitness=float(fit[i]), brightness=float(np.clip(1-(fit[i]-best)/scale,0,1)),
                move_kind=actions[i], proposed_flight_length=lengths[i])
                for i,p in enumerate(pos)],
            current_best=best, best_so_far=archived,
            best_position=tuple(map(float,archived_pos)),
            mean_fitness=float(fit.mean()),
            diversity=float(np.linalg.norm(pos-center,axis=1).mean()),
            function_evaluations=evaluations,
            abandoned_this_iteration=abandoned,
            accepted_levy_this_iteration=acc))
        actions = ['retained']*n; lengths = [0.0]*n
        acc = abandoned = 0

    def after_evaluation():
        if evaluations % n == 0:
            record()

    record()
    while evaluations < target_evaluations:
        # Candidate eggs use original source/host rules; checkpoints may interrupt.
        for _ in range(n):
            if evaluations == target_evaluations:
                break
            source = int(rng.integers(n)); host = int(rng.integers(n))
            step = _levy(rng, request.cs_levy_exponent, (2,))
            direction = pos[source]-archived_pos + .02*(hi-lo)*rng.standard_normal(2)
            displacement = request.cs_step_scale*step*direction
            candidate = np.clip(pos[source]+displacement,lo,hi)
            value = float(obj.evaluate(*candidate)); evaluations += 1
            lengths[host] = float(np.linalg.norm(displacement))
            if value < fit[host]:
                pos[host] = candidate; fit[host] = value
                actions[host] = 'levy'; acc += 1
                if value < archived:
                    archived = value; archived_pos = candidate.copy()
            after_evaluation()
        if evaluations == target_evaluations:
            break
        if abandonment:
            worst = np.argsort(fit)[::-1]; elite = int(np.argmin(fit))
            targets = [int(j) for j in worst if int(j)!=elite][:abandonment]
            for j in targets:
                if evaluations == target_evaluations:
                    break
                candidate = rng.uniform(lo,hi,2)
                value = float(obj.evaluate(*candidate)); evaluations += 1
                pos[j] = candidate; fit[j] = value
                actions[j] = 'abandoned'; lengths[j]=0.0; abandoned += 1
                if value < archived:
                    archived=value; archived_pos=candidate.copy()
                after_evaluation()
    assert [f.function_evaluations for f in frames] == _expected_frames(n,target_evaluations)
    return _finish(request,frames,t0,
        'Budgeted CS: original Levy egg and worst-nest abandonment evaluations; '
        'NFE checkpoints can stop inside the egg/abandonment phases.')


def simulate_iwo_budgeted(request: RunRequest, target_evaluations: int) -> RunResponse:
    """Evaluate seeds individually, retain best max_n, and sample exact NFE."""
    n, obj, rng = _setup(request,target_evaluations)
    if request.iwo_max_population < n or request.iwo_min_seeds > request.iwo_max_seeds:
        raise ValueError('Invalid IWO population/seed settings')
    if request.iwo_sigma_initial < request.iwo_sigma_final:
        raise ValueError('IWO sigma bounds must be descending')
    if request.iwo_max_seeds == 0 and target_evaluations > n:
        raise ValueError('IWO with zero max seeds cannot spend additional NFE')
    lo,hi = obj.bounds
    t0=perf_counter()
    pop = rng.uniform(lo,hi,(n,2))
    fitness=np.array([obj.evaluate(*p) for p in pop],dtype=float)
    ids=list(range(n)); next_id=n; evaluations=n
    winner=int(np.argmin(fitness)); archived=float(fitness[winner]); archived_pos=pop[winner].copy()
    frames: list[SimulationFrame] = []
    metadata: dict[int,dict] = {}
    last_counts: dict[int,int] = {}
    produced = exclusions = 0
    initial_size=n; generation=0

    def current_sigma() -> float:
        # NFE-based annealing ensures an identifiable trajectory even if a
        # generation is interrupted at the final evaluation cap.
        progress = (evaluations-n)/max(1,target_evaluations-n)
        return float(request.iwo_sigma_final + (request.iwo_sigma_initial-request.iwo_sigma_final)
                     * (1-progress)**request.iwo_modulation_index)

    def record():
        nonlocal produced, exclusions
        best=float(fitness.min()); denom=max(float(fitness.max())-best,1e-12)
        center=pop.mean(axis=0)
        frames.append(SimulationFrame(
            iteration=len(frames), agents=[AgentState(
                id=k,x=float(p[0]),y=float(p[1]),fitness=float(fitness[i]),
                brightness=float(np.clip(1-(fitness[i]-best)/denom,0,1)),
                iwo_origin='offspring' if k in metadata else 'survivor',
                iwo_parent_id=metadata[k]['parent_id'] if k in metadata else None,
                iwo_parent_position=metadata[k]['parent_pos'] if k in metadata else None,
                iwo_raw_step=metadata[k]['step'] if k in metadata else None,
                iwo_birth_generation=metadata[k]['generation'] if k in metadata else None,
                iwo_seeds_produced=last_counts.get(k,0),
                ) for i,(k,p) in enumerate(zip(ids,pop))],
            current_best=best,best_so_far=archived,
            best_position=tuple(map(float,archived_pos)),
            mean_fitness=float(fitness.mean()),
            diversity=float(np.linalg.norm(pop-center,axis=1).mean()),
            function_evaluations=evaluations,
            iwo_sigma=current_sigma(), iwo_initial_population=n,
            iwo_population_before=initial_size, iwo_population_after=len(ids),
            iwo_seeds_generated=produced,
            iwo_seeds_survived=sum(k in metadata for k in ids),
            iwo_competitive_exclusions=exclusions))
        produced = exclusions = 0

    record()
    while evaluations < target_evaluations:
        generation += 1
        # Freeze parents and seed allocations for this generation; do not allow
        # children to spawn until the next generation. Competitive exclusion
        # of an evaluated child is equivalent to selecting final top-max_n.
        parents=pop.copy(); parent_ids=ids.copy()
        counts=seed_counts(fitness,request.iwo_min_seeds,request.iwo_max_seeds)
        last_counts={k:int(v) for k,v in zip(parent_ids,counts)}
        if not int(counts.sum()):
            raise ValueError('IWO seed generation stalled before NFE cap')
        for parent_index,count in enumerate(counts):
            for _ in range(int(count)):
                if evaluations == target_evaluations:
                    break
                # Budget-normalized sigma is a documented comparison variant.
                sigma=current_sigma()
                step=rng.normal(0,sigma,size=2)
                candidate=np.clip(parents[parent_index]+step,lo,hi)
                value=float(obj.evaluate(*candidate)); evaluations+=1; produced+=1
                child=next_id; next_id+=1
                metadata[child]={
                    'parent_id':parent_ids[parent_index],
                    'parent_pos':tuple(map(float,parents[parent_index])),
                    'step':tuple(map(float,step)), 'generation':generation}
                pop=np.vstack((pop,candidate))
                fitness=np.concatenate((fitness,[value]))
                ids.append(child)
                if len(ids)>request.iwo_max_population:
                    survivors=np.argsort(fitness,kind='stable')[:request.iwo_max_population]
                    pop=pop[survivors].copy(); fitness=fitness[survivors].copy()
                    ids=[ids[i] for i in survivors]; exclusions+=1
                if value < archived:
                    archived=value; archived_pos=candidate.copy()
                if evaluations%n==0:
                    record()
            if evaluations == target_evaluations:
                break
    assert [f.function_evaluations for f in frames] == _expected_frames(n,target_evaluations)
    return _finish(request,frames,t0,
        'Budgeted IWO: frozen generation parents; offspring evaluated individually; '
        'incremental top-K competitive exclusion equivalent to full generation selection; '
        'Gaussian sigma decays by NFE fraction, not standalone iteration count.')


def simulate_sa_budgeted(request: RunRequest, target_evaluations: int) -> RunResponse:
    """Single-state SA: one initialization, one objective evaluation per proposal.

    24 NFE first checkpoint contains initialization plus 23 proposals, while
    later checkpoints contain 24 proposals. Total SA proposals=target-1.
    Cooling is normalized to the common reference iteration horizon to avoid
    freezing exponentially faster solely due to a larger proposal count.
    """
    n,obj,rng=_setup(request,target_evaluations)
    lo,hi=obj.bounds
    t0=perf_counter()
    current=rng.uniform(lo,hi,size=2)
    current_fit=float(obj.evaluate(*current)); evaluations=1
    archived=current_fit; best=current.copy()
    accepted_total=uphill_total=rejected_total=0
    frames: list[SimulationFrame] = []
    last_previous=last_candidate=last_step=None
    last_candidate_fit=last_delta=last_probability=last_draw=None
    last_accepted=None
    # Cooling from T0 through r^Tref across target-1 candidate evaluations.
    horizon=request.iterations

    def pair(value:np.ndarray|None):
        return tuple(map(float,value)) if value is not None else None

    def temp() -> float:
        progress=(evaluations-1)/max(1,target_evaluations-1)
        return float(request.sa_initial_temperature * request.sa_cooling_rate**(horizon*progress))

    def record():
        frames.append(SimulationFrame(
            iteration=len(frames), agents=[AgentState(
                id=0,x=float(current[0]),y=float(current[1]),
                fitness=current_fit,brightness=1.0,
                sa_previous=pair(last_previous),sa_candidate=pair(last_candidate),
                sa_step=pair(last_step),sa_candidate_fitness=last_candidate_fit,
                sa_delta=last_delta,sa_accept_probability=last_probability,
                sa_accept_draw=last_draw,sa_accepted=last_accepted)],
            current_best=current_fit,best_so_far=archived,
            best_position=pair(best),mean_fitness=current_fit,diversity=0,
            function_evaluations=evaluations,sa_temperature=temp(),
            sa_accepted_total=accepted_total,sa_uphill_accepted_total=uphill_total,
            sa_rejected_total=rejected_total,sa_last_accepted=last_accepted))

    while evaluations < target_evaluations:
        last_previous=current.copy()
        last_step=rng.normal(0,request.sa_step_scale*(hi-lo),size=2)
        last_candidate=np.clip(current+last_step,lo,hi)
        last_candidate_fit=float(obj.evaluate(*last_candidate))
        evaluations+=1
        last_delta=last_candidate_fit-current_fit
        # Temperature is that at the moment this NFE was consumed.
        last_probability=metropolis_probability(last_delta,temp())
        last_draw=float(rng.random()); last_accepted=last_draw < last_probability
        if last_accepted:
            current=last_candidate.copy(); current_fit=last_candidate_fit
            accepted_total+=1
            if last_delta>0: uphill_total+=1
            if current_fit<archived:
                archived=current_fit; best=current.copy()
        else:
            rejected_total+=1
        if evaluations%n==0:
            record()
    assert [f.function_evaluations for f in frames] == _expected_frames(n,target_evaluations)
    return _finish(request,frames,t0,
        'Budgeted single-state SA: one objective evaluation per proposal, '
        'best archive independent of current state; temperature schedule '
        'normalized to Tref reference steps across the total NFE horizon. '
        'NFE-aligned snapshots do not imply equal SA and swarm iteration counts.')
