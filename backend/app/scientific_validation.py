"""Read-only scientific audit of archived D-dimensional experiments.

This is a consistency audit, NOT an independent certification of optimizer
implementations or a claim of superiority. Times come from the original host.
"""
from __future__ import annotations

from math import isfinite
from statistics import mean, median, stdev
from typing import Any

import numpy as np

from .dimensional import DimensionalResult, objective_nd
from .report_stats import bootstrap_mean_interval, paired_seed_statistics


def _quantile(values: list[float], fraction: float) -> float:
    """Linearly interpolated empirical quantile, no optional dependencies."""
    ordered = sorted(values)
    if not ordered:
        raise ValueError('An empty sample has no quantile')
    position = (len(ordered) - 1) * fraction
    lo = int(position)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)


def audit_dimensional(result: DimensionalResult) -> dict[str, Any]:
    """Check archive consistency and summarize measured durations and uncertainty.

    In particular, a historical best is evaluated with the same objective_nd
    implementation used by the engine; reference point tests in the test suite
    are separate.  An audit cannot establish implementation equivalence to a
    published reference algorithm.
    """
    cfg = result.parameters
    budget = cfg.population_size * (cfg.iterations + 1)
    seeds = list(range(cfg.seed_start, cfg.seed_start + cfg.trials))
    issues: list[str] = []
    warnings: list[str] = []
    groups: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    valid_pair_groups: list[tuple[str, dict[int, float]]] = []

    if result.evaluations_per_run != budget:
        issues.append('Arşiv NFE / koşu bilgisi deney parametreleriyle uyuşmuyor.')
    if result.total_evaluations != budget * cfg.trials * len(cfg.algorithms):
        issues.append('Toplam NFE hesaplanan bütçeyle uyuşmuyor.')
    if result.seeds != seeds:
        issues.append('Arşivdeki tohum dizisi deney parametreleriyle uyuşmuyor.')
    if [g.algorithm for g in result.groups] != cfg.algorithms:
        issues.append('Algoritma listesi arşiv başlığıyla uyuşmuyor.')
    if len(result.optimum_position) != cfg.dimensions:
        issues.append('Referans optimum vektörünün boyutu yanlış.')
    else:
        optimum_expected = [1. if cfg.objective == 'rosenbrock' else 0.] * cfg.dimensions
        if not np.allclose(result.optimum_position, optimum_expected, rtol=0, atol=1e-12):
            issues.append('Referans optimum vektörü beklenen konumda değil.')
    if abs(result.optimum_value) > 1e-10:
        issues.append('Referans optimum değeri sıfır değil.')

    for group in result.groups:
        name = group.algorithm.upper()
        if [t.seed for t in group.trials] != seeds:
            issues.append(f'{name}: tohum listesi eksik veya beklenen sırada değil.')
        values: list[float] = []
        durations: list[float] = []
        for trial in group.trials:
            tag = f'{name} / {trial.seed}'
            if not isfinite(trial.best_error) or trial.best_error < -1e-8:
                issues.append(f'{tag}: hata sonlu veya sıfırdan büyük değil.')
            if not isfinite(trial.duration_ms) or trial.duration_ms <= 0:
                issues.append(f'{tag}: süre geçersiz.')
            if trial.function_evaluations != budget:
                issues.append(f'{tag}: NFE bütçesi eşit değil.')
            if len(trial.best_position) != cfg.dimensions:
                issues.append(f'{tag}: çözüm vektörünün boyutu yanlış.')
            elif all(isfinite(z) for z in trial.best_position):
                observed = float(objective_nd(cfg.objective, np.array(trial.best_position))[0])
                if not np.isclose(max(0., observed), trial.best_error, atol=1e-6, rtol=1e-7):
                    issues.append(f'{tag}: optimum hata ve kaydedilen vektör uyuşmuyor.')
            else:
                issues.append(f'{tag}: çözüm vektöründe sonlu olmayan değer var.')
            expected_nfes = list(range(cfg.population_size, budget + 1, cfg.population_size))
            actual_nfes = [point.evaluations for point in trial.trajectory]
            if actual_nfes != expected_nfes:
                issues.append(f'{tag}: yakınsama NFE kontrol noktaları uyumsuz.')
            for point in trial.trajectory:
                if len(point.best_position) != cfg.dimensions or any(not isfinite(v) for v in point.best_position):
                    issues.append(f'{tag}: yakınsama vektörü geçersiz.')
                    break
                check = float(objective_nd(cfg.objective, np.array(point.best_position))[0])
                if not np.isclose(max(0., check), point.best_error, atol=1e-6, rtol=1e-7):
                    issues.append(f'{tag}: yakınsama vektörü / hata uyuşmuyor.')
                    break
            best_errors = [point.best_error for point in trial.trajectory]
            if any(not isfinite(v) or v < -1e-8 for v in best_errors):
                issues.append(f'{tag}: yakınsama hataları geçersiz.')
            if any(nxt > prev + 1e-8 for prev, nxt in zip(best_errors, best_errors[1:])):
                issues.append(f'{tag}: arşivlenmiş en iyi hata artmış.')
            if trial.trajectory:
                last = trial.trajectory[-1]
                if not np.isclose(last.best_error, trial.best_error, rtol=1e-7, atol=1e-7):
                    issues.append(f'{tag}: son yakınsama kaydı nihai sonuçla uyumsuz.')
                if (len(last.best_position) != cfg.dimensions or
                    len(trial.best_position) != cfg.dimensions or
                    not np.allclose(last.best_position, trial.best_position, atol=1e-8, rtol=0)):
                    issues.append(f'{tag}: son yakınsama vektörü farklı.')
            if trial.first_success_nfe is not None:
                if not (cfg.population_size <= trial.first_success_nfe <= budget):
                    issues.append(f'{tag}: ilk başarı NFE sınırların dışında.')
                if trial.best_error > cfg.success_tolerance + 1e-9:
                    issues.append(f'{tag}: başarı eşiğine ulaşmadan başarı NFE kaydedilmiş.')
            elif trial.best_error <= cfg.success_tolerance:
                issues.append(f'{tag}: başarı eşiğine ulaşılmış fakat ilk başarı NFE eksik.')
            values.append(trial.best_error)
            durations.append(trial.duration_ms)

        if len(values) != cfg.trials:
            issues.append(f'{name}: tekrar sayısı beklenen değerden farklı.')
        if not values or not durations:
            continue
        if any(not isfinite(x) or x < 0 for x in values) or any(not isfinite(x) or x <= 0 for x in durations):
            issues.append(f'{name}: geçersiz sayısal değerler nedeniyle istatistik özeti oluşturulamadı.')
            continue
        valid_pair_groups.append((name, {t.seed: t.best_error for t in group.trials}))
        if len(group.curve) != cfg.iterations + 1:
            issues.append(f'{name}: grup yakınsama noktalarının sayısı uyuşmuyor.')
        else:
            for k, point in enumerate(group.curve):
                expected_nfe = cfg.population_size * (k + 1)
                if int(point['evaluations']) != expected_nfe:
                    issues.append(f'{name}: grup yakınsama NFE noktası uyuşmuyor.')
                    break
                if any(len(t.trajectory) <= k for t in group.trials):
                    issues.append(f'{name}: grup eğrisi ve tekil yörüngeler uyuşmuyor.')
                    break
                expected_mean = mean(t.trajectory[k].best_error for t in group.trials)
                if not np.isclose(float(point['mean_error']), expected_mean, rtol=1e-7, atol=1e-7):
                    issues.append(f'{name}: grup ortalama yakınsama hatası uyuşmuyor.')
                    break
        calculated_mean = mean(values)
        calculated_std = stdev(values) if len(values) > 1 else 0.
        if not np.isclose(group.mean_error, calculated_mean, atol=1e-6, rtol=1e-7):
            issues.append(f'{name}: ortalama hata kayıtlı tohumlardan hesaplanamıyor.')
        if not np.isclose(group.std_error, calculated_std, atol=1e-6, rtol=1e-7):
            issues.append(f'{name}: standart sapma kayıtlı tohumlardan hesaplanamıyor.')
        if not np.isclose(group.mean_duration_ms, mean(durations), atol=1e-5, rtol=1e-7):
            issues.append(f'{name}: ortalama süre kayıtlı sürelerle uyuşmuyor.')
        success = sum(x <= cfg.success_tolerance for x in values) / len(values)
        if not np.isclose(group.success_rate, success, atol=1e-8):
            issues.append(f'{name}: başarı oranı kayıtlı koşularla uyuşmuyor.')

        low, high = (bootstrap_mean_interval(values, result.experiment_id + ':' + group.algorithm)
                     if len(values) >= 2 else (values[0], values[0]))
        groups.append({
            'algorithm': group.algorithm, 'trials': len(values), 'mean_error': calculated_mean,
            'median_error': median(values), 'std_error': calculated_std,
            'success_rate': success, 'ci95_low': low, 'ci95_high': high,
            'mean_duration_ms': mean(durations), 'median_duration_ms': median(durations),
            'p95_duration_ms': _quantile(durations, .95),
            'median_nfe_per_second': median([budget * 1000 / ms for ms in durations if ms > 0])
                if all(ms > 0 for ms in durations) else None,
            'nfe_per_run': budget,
        })
    if len(valid_pair_groups) >= 2:
        comparisons = paired_seed_statistics(valid_pair_groups)
    if cfg.trials < 10:
        warnings.append(f'Yalnızca {cfg.trials} bağımsız tekrar: güven aralıkları ve p değerleri kırılgandır.')
    else:
        warnings.append('Tek problem sınıfındaki tekrarlar, diğer problem sınıflarına üstünlük kanıtı değildir.')
    warnings.extend([
        'Aynı tohum etiketi, algoritmaların özdeş rastgele başlangıçlar kullandığı anlamına gelmez.',
        'Süre ölçümleri deneyin çalıştığı makineden gelir; CPU yükü, ortam ve donanım denetlenmeden makineler arasında karşılaştırılmamalıdır.',
        'Süreler algoritma koşularının mevcut kaydından gelir; API, ağ, grafik çizimi ve disk erişimi dahil değildir.',
        'SHA-256 checkpoint bütünlüğü ve bu audit, yayınlanan referans algoritmalarla bağımsız eşdeğerlik kanıtlamaz.',
    ])
    return {
        'audit_version': '1.0', 'experiment_id': result.experiment_id,
        'objective': cfg.objective, 'dimensions': cfg.dimensions,
        'algorithm_count': len(cfg.algorithms), 'trials_per_algorithm': cfg.trials,
        'evaluations_per_run': budget, 'expected_total_evaluations': budget * cfg.trials * len(cfg.algorithms),
        'status': 'passed' if not issues else 'attention', 'issues': issues,
        'warnings': warnings, 'groups': groups, 'paired_comparisons': comparisons,
        'scope': 'Kayıtlı çözüm ve NFE tutarlılığı; kaydedilmiş süreler üzerinden tanımlayıcı profil. Algoritma kanıtı değildir.',
    }
