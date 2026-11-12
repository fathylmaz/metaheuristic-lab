"""Auditable, print-ready scientific reports from saved experimental data.

The reporting pipeline is read-only: results are loaded from the existing
SQLite experiment archive and never recomputed or re-ranked across problems.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from html import escape
from json import dumps
from .report_stats import bootstrap_mean_interval, paired_seed_statistics
from typing import Literal

from pydantic import BaseModel, Field

from .comparison_store import list_saved, load
from .benchmark_store import list_benchmarks, load_benchmark
from .sensitivity_store import list_sensitivity, load_sensitivity
from .dimensional_store import list_dimensional, load_dimensional

ReportKind = Literal['comparison', 'benchmark', 'sensitivity', 'dimensional']
KINDS = {
    'comparison': 'Algoritma Karşılaştırması',
    'benchmark': 'Çoklu Benchmark',
    'sensitivity': 'Parametre Duyarlılığı',
    'dimensional': 'Yüksek Boyutlu Optimizasyon',
}


def _fmt(x: float | int | None) -> str:
    if x is None:
        return '—'
    if isinstance(x, int):
        return str(x)
    return f'{float(x):.7g}'


def _pct(x: float) -> str:
    return f'{x * 100:.1f}%'


def _source_hash(result: BaseModel) -> str:
    # Report provenance, not a cryptographic attestation of the program itself.
    return sha256(result.model_dump_json().encode('utf-8')).hexdigest()


class ReportTable(BaseModel):
    caption: str
    headers: list[str]
    rows: list[list[str]]


def _table(caption: str, headers: list[str], rows: list[list[str]]) -> ReportTable:
    return ReportTable(caption=caption, headers=headers, rows=rows)


class ReportSection(BaseModel):
    heading: str
    paragraphs: list[str] = Field(default_factory=list)
    tables: list[ReportTable] = Field(default_factory=list)


class ScientificReport(BaseModel):
    report_version: str = '1.1'
    source_kind: ReportKind
    source_id: str
    experiment_created_at: str
    report_generated_at: str
    source_sha256: str
    title: str
    subtitle: str
    highlights: list[str]
    caveats: list[str]
    methodology: str
    parameters: dict
    sections: list[ReportSection]


def list_reports(limit: int = 20) -> list[dict]:
    sources = (
        ('comparison', 'comparison_id', list_saved),
        ('benchmark', 'benchmark_id', list_benchmarks),
        ('sensitivity', 'sensitivity_id', list_sensitivity),
        ('dimensional', 'experiment_id', list_dimensional),
    )
    entries = []
    for kind, key, function in sources:
        for entry in function(limit):
            entries.append({
                'kind': kind,
                'source_id': entry[key],
                'created_at': entry['created_at'],
                'title': KINDS[kind],
                'description': _summary(kind, entry),
            })
    return sorted(entries, key=lambda item: item['created_at'], reverse=True)[:limit]


def _summary(kind: str, source: dict) -> str:
    if kind == 'comparison':
        return f"{source['objective']} · {source['trials_per_algorithm']} tekrar · {source['evaluations_per_run']} NFE"
    if kind == 'benchmark':
        return f"{len(source['objectives'])} fonksiyon · {len(source['algorithms'])} algoritma"
    if kind == 'sensitivity':
        return f"{source['algorithm']} · {source['parameter']} · {len(source['values'])} değer"
    return f"{source['objective']} · {source['dimensions']}D · {len(source['algorithms'])} algoritma"


def _uncertainty_table(groups: list[tuple[str, list[float]]], source_key: str) -> ReportTable:
    """Descriptive intervals from stored independent trial outcomes."""
    rows = []
    for name, values in groups:
        low, high = bootstrap_mean_interval(values, source_key + ':' + name)
        rows.append([name, str(len(values)), _fmt(sum(values)/len(values)), _fmt(low), _fmt(high),
                     _fmt(min(values)), _fmt(max(values))])
    return _table('Tekrarlardaki belirsizlik · keşifsel %95 bootstrap ortalama aralığı',
                  ['Varyant', 'n', 'Ortalama', 'Alt %2,5', 'Üst %97,5', 'Min', 'Maks'], rows)


def _paired_table(groups: list[tuple[str, dict[int, float]]]) -> ReportTable:
    rows = paired_seed_statistics(groups)
    return _table('Ortak tohum etiketleriyle ikili etki ve tam işaret testi',
                  ['İkili', 'n', 'A kazandı', 'B kazandı', 'Eşit',
                   'Medyan log₁₀(A/B)', 'p (tam)', 'p (Holm)'],
                  [[r['pair'], str(r['n']), str(r['a_wins']), str(r['b_wins']),
                    str(r['ties']), _fmt(r['median_log10_ratio']),
                    _fmt(r['p_raw']), _fmt(r['p_holm'])] for r in rows])


def _comparison_report(result) -> tuple[list[str], list[str], list[ReportSection]]:
    winner = min(result.groups, key=lambda item: item.mean_best)
    nfe = result.evaluations_per_run
    total = nfe * result.trials_per_algorithm * len(result.groups)
    highlights = [
        f"{len(result.groups)} algoritma, {result.trials_per_algorithm} eşleştirilmiş tohum; "
        f"koşu başına {nfe} NFE (toplam {total}).",
        f"Bu sınırlı örnekte en düşük ortalama amaç değeri: "
        f"{winner.algorithm.upper()} ({_fmt(winner.mean_best)}).",
    ]
    caveats = [
        'Yalnızca seçilen fonksiyon, parametreler ve tohumlara ait tanımlayıcı sonuçlar sunulmuştur.',
        'Aynı tohum etiketleri, farklı algoritmaların özdeş başlangıç popülasyonlarına sahip olduğunu garanti etmez.',
        'Az sayıda tekrarda p değerleri ve başarı yüzdeleri güçlü üstünlük iddiası sağlamaz.',
        'Algoritma iç döngüleri ve saniye cinsinden işlem süreleri farklı olabilir; eşitlenen maliyet NFE sayısıdır.',
    ]
    stats = _table('Koşu sonuçlarının özeti',
        ['Algoritma', 'Ort. en iyi', 'Medyan', 'Std. sapma', 'Başarı', 'Ort. süre (ms)'],
        [[g.algorithm.upper(), _fmt(g.mean_best), _fmt(g.median_best), _fmt(g.std_best),
          _pct(g.success_rate), _fmt(g.mean_duration_ms)] for g in result.groups])
    trials = _table('Tohum bazında gerçek değerlendirme ve sonuçlar',
        ['Algoritma', 'Tohum', 'En iyi amaç değeri', 'NFE', 'İlk başarı NFE'],
        [[g.algorithm.upper(), _fmt(t.seed), _fmt(t.best_value), _fmt(t.function_evaluations),
          _fmt(t.first_success_evaluations)] for g in result.groups for t in g.trials])
    sections = [ReportSection(heading='Karşılaştırmalı sonuçlar', tables=[stats, trials])]
    if result.pairwise:
        pair = _table('Eşleştirilmiş karşılaştırmalar ve Holm düzeltmesi',
            ['Algoritmalar', 'A kazandı', 'B kazandı', 'Eşit', 'Ham p', 'Holm p', 'Yöntem'],
            [[f'{p.algorithm_a.upper()} / {p.algorithm_b.upper()}', _fmt(p.a_wins),
              _fmt(p.b_wins), _fmt(p.ties), _fmt(p.p_value), _fmt(p.p_holm), p.method]
             for p in result.pairwise])
        sections.append(ReportSection(heading='İstatistiksel inceleme',
            paragraphs=['p değerleri keşifseldir. Çoklu sınamalarda Holm düzeltmesi uygulanmıştır; '
                        'düzeltilmiş p değeri bir etki büyüklüğü veya genel üstünlük ölçüsü değildir.'],
            tables=[pair]))
    sections.append(ReportSection(heading='Belirsizlik ve etki büyüklüğü', paragraphs=[
        'Bootstrap yüzdelik aralıkları 4096 deterministik yeniden örneklemeyle hesaplandı. '
        'Özellikle n < 10 için aralıklar kırılgandır; doğrulanmış anlamlılık sonucu sayılmaz.',
        'İkili medyan log₁₀(A/B) negatifse A daha düşük hata elde etmiştir. '
        'Tam iki yönlü işaret testi, eş tohum etiketlerindeki kazanımları sayar ve Holm düzeltmesi uygulanır. '
        'Rastgele sayı akışlarının / başlangıç popülasyonlarının aynı olduğu varsayılmaz.'
    ], tables=[
        _uncertainty_table([(g.algorithm.upper(), [t.best_value for t in g.trials]) for g in result.groups],
                           result.comparison_id),
        _paired_table([(g.algorithm.upper(), {t.seed: t.best_value for t in g.trials})
                       for g in result.groups]),
    ]))
    caveats.append('Bootstrap aralıkları küçük n ile kararsızdır; p değerleri keşifseldir ve etki büyüklüğünün yerine geçmez.')
    return highlights, caveats, sections


def _benchmark_report(result) -> tuple[list[str], list[str], list[ReportSection]]:
    best = min(result.summary, key=lambda item: item.mean_rank)
    highlights = [
        f"{len(result.objectives)} farklı fonksiyon üzerinde {len(result.algorithms)} algoritma, "
        f"{len(result.seeds)} tekrar ve toplam {result.total_evaluations} NFE.",
        f"Seçilen fonksiyonlar için en küçük ortalama sıra: {best.algorithm.upper()} "
        f"({_fmt(best.mean_rank)}).",
    ]
    caveats = [
        'Farklı amaç fonksiyonlarının ham değerleri toplanmaz veya tek bir ortalamaya indirgenmez.',
        'Her problemde bilinen optimuma mutlak hata hesaplanır; sıralamalar her fonksiyon içinde belirlenir.',
        'Ortalama sıra yalnızca seçilen problemler için tanımlayıcıdır ve istatistiksel üstünlük kanıtı değildir.',
        'Bu benchmark sabit boyutlu problem örneklerini kapsar; tüm problem sınıflarına genellenemez.',
    ]
    summary = _table('Fonksiyonlar arası göreli sıralama',
        ['Algoritma', 'Ort. sıra', 'Ort. başarı', 'Birincilik sayısı', 'Problem sayısı'],
        [[s.algorithm.upper(), _fmt(s.mean_rank), _pct(s.mean_success_rate),
          _fmt(s.objective_wins), _fmt(s.objectives_measured)] for s in result.summary])
    matrix = _table('Her fonksiyon içindeki mutlak optimum hatası ve sıra',
        ['Fonksiyon', 'Bilinen f*', 'Algoritma', 'Ort. mutlak hata', 'Std.', 'Sıra', 'Başarı'],
        [[row.objective, _fmt(row.optimum_value), c.algorithm.upper(),
          _fmt(c.mean_error), _fmt(c.std_error), _fmt(c.rank), _pct(c.success_rate)]
         for row in result.rows for c in row.cells])
    trials = _table('Fonksiyon, algoritma ve tohum bazlı ham sonuçlar',
        ['Fonksiyon', 'Algoritma', 'Tohum', 'Mutlak hata', 'NFE'],
        [[row.objective, c.algorithm.upper(), _fmt(t.seed), _fmt(t.absolute_error),
          _fmt(t.function_evaluations)]
         for row in result.rows for c in row.cells for t in c.trials])
    uncertainty = _uncertainty_table([
        (f'{row.objective} / {cell.algorithm.upper()}', [t.absolute_error for t in cell.trials])
        for row in result.rows for cell in row.cells
    ], result.benchmark_id)
    caveats.append('Yüzdelik bootstrap aralıkları her fonksiyonun kendi tekrarlarından hesaplanır; '
                   'farklı fonksiyonlardaki ham hatalar birleştirilmez.')
    return highlights, caveats, [ReportSection(heading='Problem bazlı benchmark sonuçları',
        tables=[summary, matrix, trials]), ReportSection(heading='Problem bazlı belirsizlik',
            paragraphs=['Bu aralıklar algoritma / problem hücreleri içinde tanımlayıcıdır; '
                        'fonksiyonlar arası istatistiksel üstünlük testi değildir.'], tables=[uncertainty])]


def _sensitivity_report(result) -> tuple[list[str], list[str], list[ReportSection]]:
    best = min(result.groups, key=lambda item: item.mean_error)
    name = result.parameters.parameter
    highlights = [
        f"{result.parameters.algorithm.upper()} algoritmasında {name} için "
        f"{len(result.groups)} değer, {len(result.seeds)} tohum ve "
        f"toplam {result.total_evaluations} NFE.",
        f"Bu deneyde en küçük ortalama mutlak hata: {_fmt(best.parameter_value)} "
        f"değerinde {_fmt(best.mean_error)}.",
    ]
    caveats = [
        'Bu çalışma OFAT (tek değişkeni bir defada değiştirme) tasarımıdır; parametre etkileşimlerini ölçmez.',
        'En düşük ortalama hataya sahip değer, gözlenen örnek için en iyi değerdir; evrensel optimum değildir.',
        'Parametre değişmesi rassal sayı tüketimini değiştirebilir; eş tohum etiketi eş yörünge demek değildir.',
        'Az sayıdaki tekrar, belirsizlik tahminlerinin sağlamlığı için yeterli olmayabilir.',
    ]
    summary = _table('Varyantların performans özeti',
        ['Parametre değeri', 'Ort. hata', 'Medyan', 'Std.', 'Başarı', 'NFE / koşu'],
        [[_fmt(g.parameter_value), _fmt(g.mean_error), _fmt(g.median_error),
          _fmt(g.std_error), _pct(g.success_rate), _fmt(result.evaluations_per_run)]
         for g in result.groups])
    trials = _table('Tohum ve varyant bazlı sonuçlar',
        ['Parametre değeri', 'Tohum', 'Mutlak hata', 'NFE', 'İlk başarı NFE'],
        [[_fmt(g.parameter_value), _fmt(t.seed), _fmt(t.absolute_error),
          _fmt(t.function_evaluations), _fmt(t.first_success_nfe)]
         for g in result.groups for t in g.trials])
    return highlights, caveats, [ReportSection(heading='Tek değişkenli parametre incelemesi',
        tables=[summary, trials]), ReportSection(heading='Parametre duyarlılığı · belirsizlik',
            paragraphs=['Aynı tohum etiketleriyle karşılaştırma yapıldı. Parametre değişimi '
                        'rastgele sayı tüketimini de değiştirebilir; bootstrap aralıkları n azsa kırılgandır.'],
            tables=[
                _uncertainty_table([(str(g.parameter_value), [t.absolute_error for t in g.trials])
                                    for g in result.groups],result.sensitivity_id),
                _paired_table([(str(g.parameter_value),{t.seed:t.absolute_error for t in g.trials})
                               for g in result.groups]),
            ])]


def _dimensional_report(result) -> tuple[list[str], list[str], list[ReportSection]]:
    best = min(result.groups, key=lambda item: item.mean_error)
    dim = result.parameters.dimensions
    highlights = [
        f"{dim} boyutlu {result.parameters.objective} fonksiyonunda "
        f"{len(result.groups)} algoritma, {len(result.seeds)} tohum; "
        f"koşu başına {result.evaluations_per_run} NFE, toplam {result.total_evaluations} NFE.",
        f"Bu deneyde en düşük ortalama optimum hatası: "
        f"{best.algorithm.upper()} ({_fmt(best.mean_error)}).",
    ]
    caveats = [
        f'Optimizasyon gerçek {dim} koordinat üzerinden yürütülmüştür; ilk iki koordinat izdüşümü çözüm uzayının tamamı değildir.',
        'Farklı algoritmalar aynı etiketli tohumları kullanır; başlangıç konumlarının özdeş olduğu garanti edilmez.',
        'SA tek çözüm kullanır; IWO değişken sayıda birey üretir. Bazı algoritmalarda NFE takvimine uyarlanmış varyantlar bulunur.',
        'SMA sıfıra büzülme davranışı bazı merkez-optimumlu fonksiyonlarda tam sıfır hata oluşturabilir; bu genel üstünlük değildir.',
        'Az sayıda tekrar ve tek problem sınıfı güçlü istatistiksel veya genel üstünlük çıkarımı için yeterli değildir.',
    ]
    summary = _table('Gerçek D-boyutlu karşılaştırma',
        ['Algoritma', 'Ort. mutlak hata', 'Medyan', 'Std.', 'Başarı', 'NFE / koşu'],
        [[g.algorithm.upper(), _fmt(g.mean_error), _fmt(g.median_error),
          _fmt(g.std_error), _pct(g.success_rate), _fmt(result.evaluations_per_run)]
         for g in result.groups])
    trials = _table('Tam D-boyutlu nihai çözümler (özet vektör)',
        ['Algoritma', 'Tohum', 'Mutlak hata', 'NFE', f'Çözüm vektörü ({dim} bileşen)'],
        [[g.algorithm.upper(), _fmt(t.seed), _fmt(t.best_error),
          _fmt(t.function_evaluations), '['+', '.join(_fmt(x) for x in t.best_position)+']']
         for g in result.groups for t in g.trials])
    caveats.append('95% bootstrap aralıkları küçük örneklemle oynaktır; ortak tohum etiketleri '
                   'aynı başlangıç dağılımı veya aynı rastgele sayı akışı anlamına gelmez.')
    return highlights, caveats, [ReportSection(heading='Yüksek boyutlu sonuçlar',
        tables=[summary, trials]), ReportSection(heading='Belirsizlik ve eşleştirilmiş etki',
            paragraphs=['Bootstrap yüzdelik aralıkları 4096 deterministik yeniden örnekleme dayanır. '
                        'İkili medyan log₁₀(A/B) negatifse A daha düşük hata bulmuştur. '
                        'İki yönlü tam işaret testi, Holm düzeltmesiyle verilir; '
                        'üç tekrar güçlü çıkarım için yetersizdir.'], tables=[
                _uncertainty_table([(g.algorithm.upper(),[t.best_error for t in g.trials])
                                    for g in result.groups],result.experiment_id),
                _paired_table([(g.algorithm.upper(),{t.seed:t.best_error for t in g.trials})
                               for g in result.groups])
            ])]


_BUILDERS = {
    'comparison': (load, _comparison_report),
    'benchmark': (load_benchmark, _benchmark_report),
    'sensitivity': (load_sensitivity, _sensitivity_report),
    'dimensional': (load_dimensional, _dimensional_report),
}


def build_report(kind: ReportKind, source_id: str) -> ScientificReport | None:
    loader, builder = _BUILDERS[kind]
    source = loader(source_id)
    if source is None:
        return None
    highlights, caveats, sections = builder(source)
    return ScientificReport(
        source_kind=kind, source_id=source_id,
        experiment_created_at=source.created_at,
        report_generated_at=datetime.now(timezone.utc).isoformat(),
        source_sha256=_source_hash(source),
        title=f'Metaheuristic Lab | {KINDS[kind]}',
        subtitle=f'Deney kayıt kimliği: {source_id}',
        highlights=highlights, caveats=caveats,
        methodology=source.methodology,
        parameters=source.parameters.model_dump(mode='json') if isinstance(source.parameters, BaseModel) else source.parameters,
        sections=sections,
    )


def as_markdown(report: ScientificReport) -> str:
    output = [f'# {report.title}', report.subtitle, '',
              f'- Deney tarihi (UTC): {report.experiment_created_at}',
              f'- Rapor üretim tarihi (UTC): {report.report_generated_at}',
              f'- Arşiv kaynak SHA-256: `{report.source_sha256}`',
              '', '## Araştırma özeti', '']
    output.extend('- ' + item for item in report.highlights)
    output += ['', '## Metodoloji', '', report.methodology, '', '## Deney parametreleri', '',
               '```json', dumps(report.parameters, indent=2, ensure_ascii=False, allow_nan=False), '```', '']
    for section in report.sections:
        output.extend([f'## {section.heading}', ''])
        output.extend(section.paragraphs)
        for table in section.tables:
            output.extend(['', f'### {table.caption}', '',
                           '| ' + ' | '.join(h.replace('|', r'\|') for h in table.headers) + ' |',
                           '| ' + ' | '.join(['---'] * len(table.headers)) + ' |'])
            output.extend('| ' + ' | '.join(str(v).replace('|', r'\|').replace('\n', ' ') for v in row) + ' |' for row in table.rows)
            output.append('')
    output.extend(['## Sınırlılıklar', ''])
    output.extend('- ' + note for note in report.caveats)
    output += ['', '---', 'Bu belge yalnızca mevcut kayıtlı deneyden üretilmiştir; deney yeniden çalıştırılmamıştır.', '']
    return '\n'.join(output)


_CSS = '''
:root{font-family:Inter,'Segoe UI',Arial,sans-serif;color:#152536;background:#f4f7fa}
body{box-sizing:border-box;max-width:1030px;padding:36px 42px;margin:auto;background:#fff;line-height:1.48}
h1{font-size:27px;line-height:1.18;margin-bottom:6px}h2{font-size:19px;margin-top:23px;border-bottom:1px solid #dce6e9;padding-bottom:6px}
h3{font-size:13px;margin:15px 0 7px}p,li{font-size:12px}header p,.meta{color:#567282}
.chips{display:grid;grid-template-columns:1fr 1fr;gap:10px}.chip{border:1px solid #d6e5e9;padding:10px;border-radius:8px;background:#f6fbfa;font-size:12px}
.note{border-left:3px solid #d58e37;padding:7px 12px;background:#fff9f0;margin:9px 0}
.param-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:4px 15px;font-size:11px}
.param-item{display:flex;justify-content:space-between;gap:10px;border-bottom:1px solid #edf3f4;padding:4px 2px}
.param-item span{overflow-wrap:anywhere}.param-item strong{white-space:normal;text-align:right;overflow-wrap:anywhere}
table{width:100%;border-collapse:collapse;font-size:10px;margin:10px 0 18px;table-layout:auto}
th,td{padding:6px 7px;text-align:left;vertical-align:top;border-bottom:1px solid #dce7ea;overflow-wrap:anywhere}
th{background:#e7f2f2}tr:nth-child(even){background:#f8fbfc}
.vector-table{table-layout:fixed}.vector-table th:last-child{width:57%}.vector-table td:last-child{font-family:Consolas,monospace;font-size:9px;line-height:1.45;overflow-wrap:anywhere}
pre{background:#eef4f5;padding:11px;border-radius:6px;white-space:pre-wrap;overflow-wrap:anywhere;font-size:10px}
.hash{overflow-wrap:anywhere;font-size:10px;color:#526773}
@media print{
 @page{size:A4;margin:14mm}
 body{max-width:none;padding:0;line-height:1.33}
 h1{font-size:23px}h2{font-size:16px}h3{font-size:12px}
 h2,h3{break-after:avoid}thead{display:table-header-group}tr{break-inside:avoid}
 .no-print{display:none!important}.chips,.param-item{break-inside:avoid}
 table{font-size:8px;page-break-inside:auto}th,td{padding:4px 5px}
 .vector-table td:last-child{font-size:7px;line-height:1.35}
 .param-grid{font-size:9px;gap:2px 9px}
 p,li{font-size:10px}.chip{font-size:10px}.note{margin:6px 0;padding:5px 9px}
}
'''


_ALGO_PREFIXES = ('fa','pso','abc','cs','mfo','gwo','woa','ba','ssa','sma','iwo','sa','gsa','de')
_ALGO_CODES = {code:code for code in _ALGO_PREFIXES}
_ALGO_CODES.update({'bat':'ba','firefly':'fa'})


def _visible_parameters(report: ScientificReport) -> list[tuple[str, str]]:
    values = report.parameters
    selected = values.get('algorithms') or ([values['algorithm']] if 'algorithm' in values else [])
    prefixes = tuple(_ALGO_CODES.get(str(a),str(a))+'_' for a in selected)
    common = {'algorithms','algorithm','objective','objectives','dimensions','population_size',
              'iterations','trials','seed_start','success_tolerance','parameter','values'}
    # Sensitivity reports may carry request details in 'comparison'. Keep it visible.
    items = []
    for key,val in values.items():
        if key in common or key.startswith(prefixes) or (key=='comparison'):
            val_str = dumps(val,ensure_ascii=False) if isinstance(val,(list,dict)) else str(val)
            items.append((key,val_str))
    return items



def as_html(report: ScientificReport) -> str:
    e = lambda s: escape(str(s), quote=True)
    output = ['<!doctype html><html lang="tr"><head><meta charset="utf-8">',
              '<meta name="viewport" content="width=device-width,initial-scale=1">',
              f'<title>{e(report.title)}</title><style>{_CSS}</style></head><body>',
              f'<header><h1>{e(report.title)}</h1><p>{e(report.subtitle)}</p>',
              f'<p class="meta">Deney tarihi: {e(report.experiment_created_at)} · Rapor: {e(report.report_generated_at)}</p></header>',
              '<div class="no-print"><p>PDF kaydetmek için tarayıcının Yazdır komutunu (Ctrl+P) kullanın ve “PDF olarak kaydet” seçin.</p></div>',
              '<h2>Araştırma özeti</h2><div class="chips">']
    output.extend(f'<div class="chip">{e(h)}</div>' for h in report.highlights)
    output += ['</div>', '<h2>Metodoloji</h2>', f'<p>{e(report.methodology)}</p>',
               '<h2>Deney parametreleri · etkin ayarlar</h2>',
               '<p>Yalnızca bu deneyde seçilen algoritma ve ortak parametreler basılı raporda özetlenir. '
               'Tüm varsayılan alanlar ve eksiksiz parametre JSON, JSON/Markdown aktarımında korunur.</p>',
               '<div class="param-grid">']
    output.extend(f'<div class="param-item"><span>{e(key)}</span><strong>{e(value)}</strong></div>'
                  for key,value in _visible_parameters(report))
    output.extend(['</div>', '<details class="no-print"><summary>Tüm parametreleri JSON olarak göster</summary>',
                   '<pre>' + e(dumps(report.parameters,ensure_ascii=False,indent=2,allow_nan=False)) + '</pre></details>'])
    for section in report.sections:
        output.append(f'<h2>{e(section.heading)}</h2>')
        output.extend(f'<p>{e(p)}</p>' for p in section.paragraphs)
        for table in section.tables:
            is_vector = any('Çözüm vektörü' in h for h in table.headers)
            table_class = ' class="vector-table"' if is_vector else ''
            output.extend([f'<h3>{e(table.caption)}</h3>', f'<table{table_class}><thead><tr>'])
            output.extend(f'<th scope="col">{e(h)}</th>' for h in table.headers)
            output.append('</tr></thead><tbody>')
            for row in table.rows:
                output.append('<tr>')
                output.extend(f'<td>{e(c)}</td>' for c in row)
                output.append('</tr>')
            output.append('</tbody></table>')
    output.append('<h2>Sınırlılıklar</h2>')
    output.extend(f'<p class="note">{e(note)}</p>' for note in report.caveats)
    output.extend([f'<p class="hash">Kaynak veri SHA-256: {e(report.source_sha256)}</p>',
                   '<p class="meta">Bu belge arşiv verisinden hazırlanmıştır; deney yeniden çalıştırılmamıştır.</p>',
                   '</body></html>'])
    return '\n'.join(output)
