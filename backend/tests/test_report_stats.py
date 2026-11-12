"""Exact finite-sample calculations, deterministic intervals, safety and print audits."""
import pytest

from app.report_stats import bootstrap_mean_interval, exact_sign_p, holm_adjust, paired_seed_statistics
from app.reports import ScientificReport, ReportSection, ReportTable, as_html, as_markdown


def test_bootstrap_deterministic_and_within_range():
    values = [2.5, 4.5, 6.5, 10.0]
    low, high = bootstrap_mean_interval(values, 'frozen-source-a')
    assert (low, high) == bootstrap_mean_interval(values, 'frozen-source-a')
    assert min(values) <= low <= high <= max(values)


def test_bootstrap_constant_and_invalid():
    assert bootstrap_mean_interval([3.,3.,3.], 'same') == (3.,3.)
    with pytest.raises(ValueError):
        bootstrap_mean_interval([1.], 'not-enough')
    with pytest.raises(ValueError):
        bootstrap_mean_interval([1.,float('nan')], 'invalid')


@pytest.mark.parametrize('wins,losses,p',[
    (3,0,.25),(0,3,.25),(2,1,1.0),(5,0,.0625),(0,0,1.),
])
def test_exact_sign_distribution(wins,losses,p):
    assert exact_sign_p(wins,losses) == p


def test_holm_monotonic_and_order_preserving():
    assert holm_adjust([.04,.01,.03]) == pytest.approx([.06,.03,.06])
    assert holm_adjust([1.,.7]) == [1.,1.]
    assert holm_adjust([]) == []


def test_pairwise_uses_seed_labels_excludes_ties_and_adjusts():
    pairs = [
        ('A', {1: 1.0, 2: 2.0, 3: 3.0}),
        ('B', {1: 2.0, 2: 3.0, 3: 3.0}),
        ('C', {1: 4.0, 2: 5.0, 3: 6.0}),
    ]
    results = paired_seed_statistics(pairs)
    ab = next(result for result in results if result['pair']=='A / B')
    assert (ab['n'],ab['a_wins'],ab['b_wins'],ab['ties']) == (3,2,0,1)
    assert ab['p_raw'] == .5
    assert 0 <= ab['p_holm'] <= 1
    assert ab['median_log10_ratio'] < 0


def test_small_sample_p_cannot_claim_significance():
    groups = [('A',{42:1.,43:2.,44:3.}),('B',{42:4.,43:5.,44:6.})]
    observed=paired_seed_statistics(groups)[0]
    assert observed['p_raw'] == .25
    assert observed['p_holm'] == .25


def _synthetic_report() -> ScientificReport:
    return ScientificReport(source_kind='dimensional', source_id='test-record',
        experiment_created_at='2026-11-12T00:00:00+00:00',
        report_generated_at='2026-11-12T00:01:00+00:00',
        source_sha256='a'*64, title='Deney', subtitle='Test',
        highlights=['3 tekrar'],caveats=['Genel sonuç çıkarılamaz'],
        methodology='Gerçek D-boyutlu hesaplama.',
        parameters={'algorithms':['abc','cs','iwo','sa'], 'dimensions':10,
                    'objective':'rastrigin','population_size':24,'trials':3,
                    'abc_limit':30,'cs_step_scale':.08,'iwo_sigma_initial':1.5,
                    'sa_cooling_rate':.95,'fa_alpha':.18,'de_mutation_factor':.75},
        sections=[ReportSection(heading='Sonuçlar',tables=[ReportTable(
            caption='Çözümler',headers=['Algoritma','Çözüm vektörü (10 bileşen)'],
            rows=[['ABC','[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]']])])])


def test_html_print_parameters_and_vectors_from_synthetic_report():
    report=_synthetic_report()
    html=as_html(report)
    assert 'param-grid' in html
    assert 'vector-table' in html
    assert '<details class="no-print">' in html
    assert 'abc_limit' in html and 'sa_cooling_rate' in html
    assert 'fa_alpha</span>' not in html  # irrelevant default is not shown in print grid
    assert '<script' not in html.lower()
    assert '## Sınırlılıklar' in as_markdown(report)


def test_full_json_fields_kept_in_markdown():
    report=_synthetic_report()
    assert 'fa_alpha' in as_markdown(report)
    assert 'de_mutation_factor' in as_markdown(report)


def test_near_zero_nonidentical_errors_are_not_artificial_ties():
    result=paired_seed_statistics([('A',{42:1e-42,43:1e-37,44:1e-40}),
                                   ('B',{42:1e-15,43:1e-16,44:1e-14})])[0]
    assert result['a_wins'] == 3 and result['ties'] == 0
    assert result['median_log10_ratio'] < -20
    assert result['p_raw'] == .25
