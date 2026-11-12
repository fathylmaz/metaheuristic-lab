"""Read-only report generation, provenance and safe offline print exports."""
import re

import pytest
from fastapi.testclient import TestClient

from app.benchmark_suite import BenchmarkSuiteRequest, benchmark_suite
from app.benchmark_store import save_benchmark
from app.comparison import ComparisonRequest, compare
from app.comparison_store import save
from app.dimensional import DimensionalRequest, run_dimensional
from app.dimensional_store import save_dimensional
from app.main import app
from app.reports import as_html, as_markdown, build_report, list_reports
from app.sensitivity import SensitivityRequest, sensitivity
from app.sensitivity_store import save_sensitivity


@pytest.fixture()
def archive(monkeypatch, tmp_path):
    monkeypatch.setenv('METAHEURISTIC_DATA_DIR', str(tmp_path))
    comp = compare(ComparisonRequest(algorithms=['pso', 'gwo'], population_size=8,
                                     iterations=3, trials=2, seed_start=20))
    save(comp)
    bench = benchmark_suite(BenchmarkSuiteRequest(objectives=['sphere', 'rastrigin'],
        comparison=ComparisonRequest(algorithms=['pso','de'], population_size=8,
                                     iterations=2, trials=2, seed_start=20)))
    save_benchmark(bench)
    sens = sensitivity(SensitivityRequest(algorithm='pso', objective='sphere',
        parameter='pso_inertia_weight', values=[.4, .72], population_size=8,
        iterations=2, trials=2, seed_start=20))
    save_sensitivity(sens)
    high = run_dimensional(DimensionalRequest(algorithms=['pso','abc'], objective='sphere',
        dimensions=10, population_size=8, iterations=5, trials=2, seed_start=20))
    save_dimensional(high)
    return {'comparison':comp.comparison_id, 'benchmark':bench.benchmark_id,
            'sensitivity':sens.sensitivity_id, 'dimensional':high.experiment_id}


@pytest.mark.parametrize('kind', ['comparison', 'benchmark', 'sensitivity', 'dimensional'])
def test_reports_built_from_saved_results_only(archive, kind):
    record = build_report(kind,archive[kind])
    assert record is not None
    assert record.source_kind == kind
    assert re.fullmatch(r'[a-f0-9]{64}', record.source_sha256)
    assert record.sections and record.methodology and record.parameters
    assert all(len(row) == len(table.headers)
               for section in record.sections for table in section.tables for row in table.rows)
    markdown = as_markdown(record)
    html = as_html(record)
    assert 'Metodoloji' in markdown and 'Sınırlılıklar' in html
    assert archive[kind] in markdown
    assert '<!doctype html>' in html
    assert 'Yazdır' in html


def test_report_history_includes_four_archives_without_mutating(archive):
    client = TestClient(app)
    records = client.get('/api/reports')
    assert records.status_code == 200
    items = records.json()['reports']
    assert {e['kind'] for e in items} == set(archive)
    assert all(e['created_at'] and e['source_id'] for e in items)
    for kind, source_id in archive.items():
        r = client.get(f'/api/reports/{kind}/{source_id}')
        assert r.status_code == 200, r.text
        assert r.json()['source_id'] == source_id
        assert r.json()['source_kind'] == kind
        assert r.json()['report_version'] == '1.1'
    assert len(client.get('/api/reports').json()['reports']) == 4


def test_printable_html_and_markdown_no_active_script(archive):
    client=TestClient(app)
    id=archive['comparison']
    path=f'/api/reports/comparison/{id}'
    html=client.get(path+'?format=html')
    assert html.status_code==200
    assert html.headers['content-type'].startswith('text/html')
    assert 'script-src' not in html.headers['content-security-policy']
    assert "default-src 'none'" in html.headers['content-security-policy']
    assert 'archive' not in html.headers.get('content-disposition', '')
    md=client.get(path+'?format=md')
    assert md.status_code==200
    assert 'attachment;' in md.headers['content-disposition']
    assert '## Sınırlılıklar' in md.text
    assert client.get(path+'?format=xml').status_code==422


def test_missing_and_invalid_source_never_generates_report(archive):
    client=TestClient(app)
    assert client.get('/api/reports/dimensional/unknown').status_code==404
    assert client.get('/api/reports/comparison/unknown?format=html').status_code==404
    assert client.get('/api/reports/not-a-kind/123').status_code==422


def test_html_escaping_untrusted_saved_methodology(archive):
    from app.comparison_store import _connect
    import json,zlib
    source_id=archive['comparison']
    # Simulate a file/database record containing hostile text. Never execute it.
    with _connect() as c:
        blob=c.execute('SELECT payload FROM comparisons WHERE id=?',(source_id,)).fetchone()[0]
        data=json.loads(zlib.decompress(blob))
        data['methodology']='<img src=x onerror=alert(1)> report & notes'
        c.execute('UPDATE comparisons SET payload=? WHERE id=?',
                  (zlib.compress(json.dumps(data).encode()),source_id))
    report=build_report('comparison',source_id)
    html=as_html(report)
    assert '&lt;img src=x onerror=alert(1)&gt;' in html
    assert '<img src=x' not in html
    assert 'report &amp; notes' in html


def test_dimensional_report_uses_real_d_component_vectors(archive):
    report=build_report('dimensional',archive['dimensional'])
    table=report.sections[0].tables[1]
    assert '10 bileşen' in table.headers[-1]
    assert table.rows and all(row[-1].count(',') == 9 for row in table.rows)
    assert any('izdüşüm' in note for note in report.caveats)


def test_source_digest_stable_as_long_as_record_unchanged(archive):
    a=build_report('benchmark',archive['benchmark'])
    b=build_report('benchmark',archive['benchmark'])
    assert a.source_sha256 == b.source_sha256
    assert a.experiment_created_at == b.experiment_created_at
