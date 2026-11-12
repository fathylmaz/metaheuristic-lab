"""Classical Ant System for a symmetric, Euclidean travelling-salesperson problem.

The geometry is fixed by ``city_seed``; ``seed`` independently controls stochastic
route construction. Every tour is a genuine closed Hamiltonian cycle. We count
complete constructed tours, rather than continuous-objective evaluations.
"""
from __future__ import annotations

from math import isfinite, pi
from time import perf_counter
from uuid import uuid4

import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class ACORequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    city_count: int = Field(default=16, ge=6, le=32)
    ant_count: int = Field(default=24, ge=4, le=60)
    iterations: int = Field(default=80, ge=1, le=150)
    alpha: float = Field(default=1.0, ge=0, le=5)
    beta: float = Field(default=3.0, ge=0, le=8)
    evaporation: float = Field(default=0.35, ge=0.01, le=0.99)
    deposit_q: float = Field(default=20.0, gt=0, le=100)
    seed: int = Field(default=42, ge=0, le=2_147_483_647)
    city_seed: int = Field(default=7, ge=0, le=2_147_483_647)
    layout: Literal['uniform', 'circle', 'clusters'] = 'uniform'


class City(BaseModel):
    id: int
    x: float
    y: float


class AntTour(BaseModel):
    id: int
    route: list[int]
    length: float


class ACOFrame(BaseModel):
    iteration: int
    best_length: float
    iteration_best: float
    mean_length: float
    best_route: list[int]
    iteration_best_route: list[int]
    tours_evaluated: int
    unique_tours: int
    pheromone: list[list[float]]
    ant_tours: list[AntTour]


class ACOResponse(BaseModel):
    run_id: str
    algorithm: Literal['aco'] = 'aco'
    problem: Literal['symmetric_euclidean_tsp'] = 'symmetric_euclidean_tsp'
    parameters: ACORequest
    cities: list[City]
    frames: list[ACOFrame]
    duration_ms: float
    variant: str = 'Ant System (AS): all-ant deposition, symmetric TSP, no local search'


def _cities(cfg: ACORequest) -> np.ndarray:
    rng = np.random.default_rng(cfg.city_seed)
    n = cfg.city_count
    if cfg.layout == 'circle':
        angles = np.arange(n) * (2 * pi / n)
        points = np.column_stack((0.5 + .39 * np.cos(angles), 0.5 + .39 * np.sin(angles)))
    elif cfg.layout == 'clusters':
        centers = np.array([[.20, .24], [.79, .30], [.53, .81]], dtype=float)
        points = np.clip(centers[np.arange(n) % 3] + rng.normal(0, .092, size=(n, 2)), .045, .955)
    else:
        points = rng.uniform(.07, .93, size=(n, 2))
    return points


def _normalized_cycle(route: list[int]) -> tuple[int, ...]:
    """Canonical orientation / rotation for symmetric cycles."""
    offset = route.index(min(route))
    rotated = route[offset:] + route[:offset]
    reverse = [rotated[0]] + rotated[:0:-1]
    return min(tuple(rotated), tuple(reverse))


def simulate_aco(cfg: ACORequest) -> ACOResponse:
    start_time = perf_counter()
    rng = np.random.default_rng(cfg.seed)
    coords = _cities(cfg)
    n = cfg.city_count
    distance = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=2)
    # A nonzero positive floor also supports coincident city coordinates safely.
    safe_dist = np.maximum(distance, 1e-12)
    tau = np.ones((n, n), dtype=float)
    np.fill_diagonal(tau, 0.0)
    best_length = float('inf')
    best_route: list[int] = []
    frames: list[ACOFrame] = []

    for iteration in range(1, cfg.iterations + 1):
        tours: list[AntTour] = []
        deposited = np.zeros_like(tau)
        for ant in range(cfg.ant_count):
            first = int(rng.integers(0, n))
            route = [first]
            unvisited = set(range(n))
            unvisited.remove(first)
            while unvisited:
                here = route[-1]
                choices = sorted(unvisited)
                pheromone = np.maximum(tau[here, choices], 1e-300)
                desirability = cfg.alpha * np.log(pheromone) - cfg.beta * np.log(safe_dist[here, choices])
                # Stable normalized roulette probabilities, including alpha=beta=0.
                desirability -= np.max(desirability)
                weights = np.exp(desirability)
                probabilities = weights / np.sum(weights)
                nxt = choices[int(rng.choice(len(choices), p=probabilities))]
                route.append(nxt)
                unvisited.remove(nxt)
            ids = np.asarray(route, dtype=int)
            nxt_ids = np.roll(ids, -1)
            length = float(np.sum(distance[ids, nxt_ids]))
            if not isfinite(length) or length <= 0:
                raise ValueError('Invalid tour length')
            tours.append(AntTour(id=ant, route=route, length=length))
            if length < best_length:
                best_length = length
                best_route = route.copy()
            amount = cfg.deposit_q / length
            for u, v in zip(ids, nxt_ids):
                deposited[u, v] += amount
                deposited[v, u] += amount

        # Edges are symmetric; diagonal is excluded by construction.
        tau = (1 - cfg.evaporation) * tau + deposited
        np.fill_diagonal(tau, 0.0)
        tau = np.maximum(tau, 0.0)
        best_tour = min(tours, key=lambda t: t.length)
        frames.append(ACOFrame(
            iteration=iteration,
            best_length=best_length,
            iteration_best=best_tour.length,
            mean_length=float(np.mean([tour.length for tour in tours])),
            best_route=best_route.copy(),
            iteration_best_route=best_tour.route.copy(),
            tours_evaluated=iteration * cfg.ant_count,
            unique_tours=len({_normalized_cycle(t.route) for t in tours}),
            pheromone=tau.tolist(),
            ant_tours=tours,
        ))
    return ACOResponse(
        run_id=str(uuid4()), parameters=cfg,
        cities=[City(id=i, x=float(p[0]), y=float(p[1])) for i, p in enumerate(coords)],
        frames=frames, duration_ms=(perf_counter() - start_time) * 1000,
    )
