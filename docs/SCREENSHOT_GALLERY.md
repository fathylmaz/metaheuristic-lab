# Metaheuristic Lab — Gerçek Uygulama Görselleri / Real Screenshot Gallery

[Ana README](../README.md) · [Türkçe](../README_TR.md) · [English](../README_EN.md)

> **23 gerçek ekran görüntüsü:** 22 planlı görünüm + ek mobil içerik. Bunlar kullanıcının çalışır v3.0.0 uygulamasından aldığı ekranlardır; kurgulanmış maket değildir. Görünen veriler örnek/pilot deneylerdir.
> **23 real user-captured v3.0.0 images**, not mockups. Pilot results must not be interpreted as global rankings.

## Kapak görseli / Hero
![Ateşböceği simülasyonu / Firefly dashboard](screenshots/final/01-firefly-overview.png)

## Simülasyon ve algoritma rehberi / Simulation and guide

| Ateşböceği simülasyonu | FA yakınsama analizi |
|:---:|:---:|
| [![Firefly simulation](screenshots/final/01-firefly-overview.png)](screenshots/final/01-firefly-overview.png) | [![Firefly convergence](screenshots/final/02-firefly-convergence.png)](screenshots/final/02-firefly-convergence.png) |
| *Simülasyon ve ölçümler* | *Dönemsel yakınsama* |

| Parçacık sürüsü simülasyonu | ACO ile TSP rota optimizasyonu |
|:---:|:---:|
| [![Particle Swarm simulation](screenshots/final/03-pso-simulation.png)](screenshots/final/03-pso-simulation.png) | [![ACO for discrete TSP](screenshots/final/04-aco-tsp-route.png)](screenshots/final/04-aco-tsp-route.png) |
| *PSO durum takibi* | *Ayrık problem: rota* |

### 05 — Algoritma rehberi / Algorithm guide
[![Algorithm guide](screenshots/final/05-algorithm-guide.png)](screenshots/final/05-algorithm-guide.png)
*Formüller ve çalışma prensibi / Equations & explanation*

## Karşılaştırma, benchmark ve OFAT / Comparison, benchmark & sensitivity

| NFE bazlı algoritma karşılaştırması | Karşılaştırma istatistikleri |
|:---:|:---:|
| [![NFE-controlled comparison](screenshots/final/06-comparison-convergence.png)](screenshots/final/06-comparison-convergence.png) | [![Comparison statistics](screenshots/final/07-comparison-statistics.png)](screenshots/final/07-comparison-statistics.png) |
| *Eşit bütçeli yakınsama* | *Tohum bazlı özetler* |

| Çoklu benchmark matrisi | Benchmark ayrıntıları |
|:---:|:---:|
| [![Multi-benchmark matrix](screenshots/final/08-benchmark-matrix.png)](screenshots/final/08-benchmark-matrix.png) | [![Benchmark detail view](screenshots/final/09-benchmark-details.png)](screenshots/final/09-benchmark-details.png) |
| *Fonksiyonlar arası değerlendirme* | *Fonksiyon başına sonuçlar* |

| OFAT parametre duyarlılığı | OFAT varyant ve tohum sonuçları |
|:---:|:---:|
| [![OFAT sensitivity chart](screenshots/final/10-sensitivity-chart.png)](screenshots/final/10-sensitivity-chart.png) | [![OFAT variant results](screenshots/final/11-sensitivity-results.png)](screenshots/final/11-sensitivity-results.png) |
| *Parametre değişkenleri* | *Varyant tablosu* |

## Yüksek boyutlu optimizasyon / High-dimensional optimization

| 10 boyutlu deney ayarları | 10 boyutlu yakınsama |
|:---:|:---:|
| [![10D experiment setup](screenshots/final/12-dimensional-setup.png)](screenshots/final/12-dimensional-setup.png) | [![10D convergence](screenshots/final/13-dimensional-results.png)](screenshots/final/13-dimensional-results.png) |
| *Parametre paneli kırpımı* | *Gerçek D-boyutlu hesaplama* |

### 14 — Tam 10 boyutlu çözüm vektörü / Complete 10D solution vector
[![Complete 10D solution vector](screenshots/final/14-dimensional-vectors.png)](screenshots/final/14-dimensional-vectors.png)
*İlk iki koordinat izdüşümü / First two coordinates projected*

## Görev kuyruğu ve checkpoint / Queue & checkpoints

| Çalışan deney ve checkpoint | Tamamlanan deney kuyruğu |
|:---:|:---:|
| [![Running job and checkpoints](screenshots/final/15-job-queue-running.png)](screenshots/final/15-job-queue-running.png) | [![Completed experiment jobs](screenshots/final/16-job-queue-completed.png)](screenshots/final/16-job-queue-completed.png) |
| *Kuyrukta canlı ilerleme* | *Kalıcı görev kaydı* |

### 17 — Görev olay geçmişi / Job event history
[![Job event history](screenshots/final/17-job-history.png)](screenshots/final/17-job-history.png)
*Olay paneli kırpımı / Event panel crop*

## Akademik rapor ve bilimsel denetim / Reports & scientific audit

| Akademik rapor genel görünüm | Bilimsel belirsizlik ve ikili etki |
|:---:|:---:|
| [![Academic report overview](screenshots/final/18-academic-report-overview.png)](screenshots/final/18-academic-report-overview.png) | [![Uncertainty and pairwise effects](screenshots/final/19-academic-report-statistics.png)](screenshots/final/19-academic-report-statistics.png) |
| *Arşivden üretilen rapor* | *Keşifsel testler* |

| Bilimsel tutarlılık denetimi | Algoritma süre ve performansı |
|:---:|:---:|
| [![Scientific consistency audit](screenshots/final/20-scientific-validation.png)](screenshots/final/20-scientific-validation.png) | [![Algorithm runtime analysis](screenshots/final/21-performance-analysis.png)](screenshots/final/21-performance-analysis.png) |
| *D-vektör ve NFE kontrolü* | *Medyan/p95 ve NFE/s* |

## Mobil kullanım / Mobile

| Mobil menü | Mobil laboratuvar içeriği |
|:---:|:---:|
| [![Mobile navigation](screenshots/final/22-mobile-responsive.png)](screenshots/final/22-mobile-responsive.png) | [![Mobile lab content](screenshots/final/22b-mobile-content.png)](screenshots/final/22b-mobile-content.png) |
| *Dar ekranda menü* | *390 piksel mobil görünüm* |

## Görsellerin sınırları / Presentation notes

- `12-dimensional-setup.png` **yalnızca ayar paneli kırpımıdır**, tüm ekran değildir. / This is intentionally a narrow setup-panel crop.
- `17-job-history.png` **görev ayrıntı paneli kırpımıdır**. / This is an event-detail crop.
- `14-dimensional-vectors.png` içindeki 2D grafik, **gerçek 10D amaç yüzeyi değil ilk iki koordinat izdüşümüdür**. / The 2D plot is a projection, not a 10D surface.
- `15-job-queue-running.png` çalışan görevde **2/9 koşu** gibi gerçek ilerleme gösterir; arşiv kimlikleri özel veri içeriyor olabilir. / Job IDs and archive identifiers must be reviewed before public upload.
- Genel algoritma üstünlüğü veya bağımsız dış doğrulama iddia edilmez. / No claim of general algorithm superiority or independent external verification.

**Yayın kontrolü:** GitHub herkese açık olmadan önce bu 23 görüntüdeki arşiv kimliklerini, özel kayıt başlıklarını ve deney ayrıntılarını gözden geçir. / Review every image for sensitive local metadata before publishing.
