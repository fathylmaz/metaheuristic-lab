# Metaheuristic Lab — Scientific Reporting (v2.6.0)

## Purpose

The new **Akademik Raporlar** page produces a readable, auditable research summary **without re-running the optimization algorithms**. It reads persisted, previously completed experiments from the existing SQLite archive. The original archived payload remains unchanged; no new database table or migration is required.

## Supported archived study types

| Study | Source API | Report content |
|---|---|---|
| Equal-NFE comparison | `/api/comparisons/{id}` | summary metrics, per-seed results, paired tests with Holm correction where available |
| Multi-objective benchmark | `/api/benchmarks/{id}` | per-problem optimum errors, per-problem ranks, mean rank, per-seed data |
| One-factor-at-a-time sensitivity | `/api/sensitivity/{id}` | changed parameter and observed values, summary statistics, per-seed data |
| True D-dimensional comparison | `/api/dimensional/{id}` | exact evaluation budgets, full D-dimensional final solution vectors, summary and per-seed data |

The report API exposes:

- `GET /api/reports` — 20 most recently saved studies across the four categories.
- `GET /api/reports/{kind}/{id}` — report in structured JSON.
- `GET /api/reports/{kind}/{id}?format=md` — downloadable UTF-8 Markdown.
- `GET /api/reports/{kind}/{id}?format=html` — self-contained, print-ready HTML (light print style).

### PDF workflow

1. Open a previously saved study from **Akademik Raporlar**.
2. Choose **Yazdır / PDF**, which opens the self-contained HTML report in a new browser tab.
3. Press **Ctrl+P** and select **Save as PDF / PDF olarak kaydet**.
4. The output contains methodology, metadata, raw result tables and explicit interpretation warnings.

**PDFs are not generated server-side in v2.6.0.** This avoids a new PDF library dependency. Browser print rendering and fonts depend on the local browser and OS. The original source data is also available via JSON.

## Reproducibility & provenance

Every report contains the unique saved experiment ID, the saved experiment creation timestamp, a report generation timestamp, original user parameters, a SHA-256 digest of the normalized saved result model, method description and per-seed outcomes. The SHA digest helps identify changes in the stored result representation, but **is not a digital signature or a guarantee of software correctness**. The data and algorithm are not automatically reproducible across Python/library versions or CPU architectures unless the environment is also pinned and documented.

## Scientific limitations

1. Equal number of objective-function evaluations (NFE) is not equal execution time, identical starting populations, or equal internal algorithm iterations.
2. The same seed label does not enforce identical RNG streams across different optimizers.
3. Pairwise p values (if recorded by the source experiment) are presented with their original Holm adjustment and are not re-computed by the report layer. Few seeds are insufficient to claim robust superiority.
4. A benchmark compares algorithms **within each problem**; raw objective-function scores from different test problems must not be averaged together.
5. The D-dimensional output uses the entire final solution vector. Its first-two-coordinate projection is not a view of the complete optimization surface.
6. Parameter sensitivity is OFAT and cannot detect multi-parameter interactions.
7. Results are descriptive evidence for a specific experimental setup, not assertions of universal performance.

## Security & backward compatibility

- Reports are rendered by escaping all saved text before inserting it into HTML. A restrictive Content-Security-Policy disallows active scripts, remote images and forms in the printable view.
- Reports only read the archive. Previously saved comparison, benchmark, sensitivity and dimensional results remain valid.
- There are no new `npm` dependencies or Python production requirements.
- The local backend should remain bound to `127.0.0.1` for personal research. The reporting endpoint has **no user authentication** and is not intended to be exposed publicly without additional access control.

## Automated tests

Run `python -m pytest -q` in `backend`. The v2.6.0 release adds 10 tests for four source types, HTTP formats, archived sample counts, escaping, missing records and full-D vector reporting.


## v2.7.0 ek istatistikler ve baskı düzeni

- Keşifsel aralıklar arşivdeki bağımsız tekrarların ortalamasına 4096 sabit tohumlu bootstrap örneklemesiyle elde edilen yüzde 2.5 / yüzde 97.5 persentilleridir. **n=2–8 aralıkların güvenilirliği sınırlıdır**; güçlü bir parametrik veya asimptotik kapsama vaadi yoktur.
- Aynı seed etiketindeki iki algoritma/parametre varyantı için ham hata kazançları, eşitlikler ve medyan log10 hata oranı raporlanır. Tam iki yönlü işaret testi bağ sıfırlamasını doğru yapar; tüm çiftler Holm sıralı düzeltmesine tabidir.
- Farklı benchmark fonksiyonlarının hammadde hataları bir araya getirilmez; aralıklar yalnızca aynı problem/algoritma hücrelerinde hesaplanır.
- Baskı sürümü seçili algoritmaların etkin parametrelerini özetler. İlgisiz algoritmaların hazır varsayılanları ve tam parametre dökümü **JSON/Markdown** çıktısında mevcuttur.
- Eski deneyler `ScientificReport` yapısında `report_version=1.1` olarak aynı SQLite verileri üzerinden yeniden raporlanır; deney yeniden koşturulmaz.
