> **2026-11-11 — v1.5.0:** SA Tavlama Benzetimi: Metropolis kabulü, geometrik soğuma, tek çözümlü hareket ve aday telemetrisi; 11 yeni test, toplam 141 backend testi.

> **2026-11-11 — v1.4.0:** IWO İstilacı Yabani Ot: değişken popülasyon, uygunluğa göre üreme, azalan Gaussian saçılım, rekabetçi eleme, gerçek NFE ve 10 yeni IWO testi (130 backend testi).

> **2026-11-11 — v1.3.0:** SMA Cıvık Mantar Algoritması: uyarlamalı sıra ağırlıkları; gerçek yaklaşma, büzülme, yeniden başlangıç; hareket seçimi telemetrisi ve orijin yanlılığı uyarısı.

> **2026-11-11 — v1.2.0:** SSA Salp Swarm Algorithm: 2B lider/besin ve sıralı takipçi zinciri, c1/c2/c3 telemetrisi, seçilebilir salp ve denetlenebilir matematiksel hareket kayıtları.

> **2026-11-11 — v1.1.0:** BA yarasa optimizasyonu: frekans/hız, ses ve darbe kontrolü, denetlenebilir kabul/ret kararı ve 9 yeni test (101 backend testi).

> **2026-11-11 — v1.0.0:** WOA balina optimizasyonu: 3 davranış dalı, A/C vektörleri, spiral katsayısı, denetlenebilir eski/hedef konumları ve 9 yeni test (92 backend testi).

> **2026-11-11 — v0.9.0:** GWO alpha/beta/delta hiyerarşisi, gerçek üç-lider kuşatma denklemleri, leader telemetry, sabit NFE ve 9 yeni backend testi.

> **2026-11-11 — v0.8.0:** MFO rank-tabanlı alevler, spiral hareket telemetrisi, gerçek NFE ve 8 yeni backend testi.

> **2026-11-11 — v0.7.0:** CS Cuckoo Search: Mantegna Lévy uçuşları, sabit-oranlı yuva terk etme, gerçek NFE ve 66 backend testi.

> **2026-11-11 — v0.6.0:** ACO Ant System on a separate discrete symmetric TSP workspace, pheromone/route inspection, distinct geometry/algorithm seeds and tests.

> **2026-11-11 — v0.5.0:** FA/PSO/ABC three-way comparison, true evaluation budget cutoff and NFE-aligned synchronized playback, backward-compatible SQLite history and 52 backend tests.

> **2026-11-11 — v0.4.0:** Basic Artificial Bee Colony (ABC), employed/onlooker/scout food-source views, exact objective evaluation accounting and 44 backend tests.

> **2026-11-11 — v0.3.0:** Equal-budget FA/PSO comparison, repeated seeds, synchronized playback, SQLite history, and expanded backend tests (36 passing).

> **2026-11-11 — v0.2.0:** FA ve PSO hesaplama motorları, PSO görselleştirme ve testleri eklendi. Frontend üretim derlemesi kullanıcı ortamında doğrulanmalıdır.

# Development plan

## Milestone 1 — working, reproducible FA laboratory (completed)
- [x] 15-entry algorithm catalog with truthful implementation status
- [x] Python optimization engine with deterministic seed, bounded variables
- [x] 8 objective functions (v1.9.0)
- [x] API for validation, catalog and simulations
- [x] Agent trajectories, relative brightness, best-ever archive
- [x] React simulation layout, Canvas terrain map, play/pause/scrub/speed
- [x] Parameters, interactive agent inspection, convergence chart
- [x] Session experiment listing, JSON and CSV export
- [x] Backend unit and API tests
- [x] Docker / GitHub Actions scaffold
- [x] v0.3.0 frontend production build verified on the Windows host
- [x] v0.4.0 production build verified on Windows host (hotfix applied)
- [x] v0.5.0 production build verified on the Windows host
- [x] v0.6.0 production build verified on Windows host
- [x] v0.7.0 production build verified on Windows host
- [x] v0.8.0 production build verified on Windows host
- [x] v0.9.0 production build verified on Windows host
- [x] v1.0.0 frontend production build verified on Windows host
- [x] v1.1.0 frontend production build verified on Windows host
- [x] v1.2.0 frontend production build verification on Windows host (user-reported build passed)
- [x] v1.3.0 frontend production build verification on Windows host (user-reported)
- [x] v1.4.0 frontend production build verification on Windows host (user-reported)
- [ ] v1.5.0 frontend production build verification on Windows host

## Milestone 2 — polished core and second optimizer
- [ ] Frontend end-to-end tests (Playwright) and accessibility pass
- [x] PSO engine, actual velocity arrows, particle pBest/gBest inspection
- [ ] Shared incremental iterator protocol and WebSocket streaming
- [x] SQLite persistence and re-open for benchmark comparisons (single-run persistence pending)
- [ ] 2D vs N-dimensional model with fair budgets
- [x] FA/PSO mathematical explanations and algorithm-specific parameters
- [ ] Per-step numerical term decomposition and systematic parameter sensitivity experiments

## Milestone 3 — algorithm families
- [x] ABC (continuous 2D source visualization, scout count, tests)
- [x] CS
- [x] MFO
- [x] GWO
- [x] WOA
- [x] BA
- [x] SSA
- [x] SMA, IWO
- [x] SA
- [x] DE, GSA
- [x] ACO on graph/TSP workspace (separate problem domain)

## Milestone 4 — scientific experiments and release
- [x] Equal objective evaluation budgets for FA/PSO/ABC 2D benchmarks (exact-NFE cutoff)
- [x] Multiple seeds, mean/median, sample standard deviation and success rate; uncertainty intervals and distribution plots pending
- [ ] COCO-compatible benchmarks where feasible
- [ ] Parameter grid and sensitivity studies
- [ ] Per-algorithm academic source list and tests against references
- [ ] 3D surfaces (where mathematically appropriate)
- [ ] Docker production build, monitoring, docs, demo videos

Never label a not-yet-implemented optimizer as a working simulation.

> **2026-11-11 — v1.6.0:** GSA: kuvvet/kütle/ivme, azalan G(t) ve Kbest, ajan odaklı görselleştirme; 10 yeni matematiksel test. DE tek planlanan algoritmadır.
- [ ] v1.6.0 frontend production build verification on Windows host

> **2026-11-11 — v1.7.0:** DE/rand/1/bin: donör mutasyonu, zorunlu çaprazlama, dondurulmuş nesil ve kabul/ret analizi. 15/15 algoritma modülü etkin; bilimsel karşılaştırma genişletmesi, N boyut ve end-to-end testler devam edecek.
- [ ] v1.7.0 frontend production build verification on Windows host

> **2026-11-12 — v1.8.0:** 11 sürekli optimizasyon algoritmasına kadar genişletilmiş eşit-NFE karşılaştırma motoru (seçimde en fazla 6), algoritmaya özel parametre panelleri, ortak NFE senkronizasyonu, 2–8 tohum, çiftler için log10 farkına tam sign-flip ve Holm düzeltmesi. Eski SQLite arşivi geriye uyumludur. **CS/IWO/SA bütçe uyarlayıcıları eksik** ve ACO hâlâ ayrı ayrık TSP'dir. Daha geniş benchmark, yüksek boyut, bağımsız CI/browser testleri açık işlerdir.
- [ ] v1.8.0 frontend production build verification on Windows host
- [x] CS/IWO/SA için gerçek NFE sınırlandırma uygulaması (v2.0.0)
- [ ] 10–30 bağımsız tohum, etki büyüklüğü, güven aralığı ve çoklu benchmark ailesi


> **2026-11-12 — v1.9.0:** 8 ayrı 2B amaç fonksiyonu (4 yeni), çoklu problem benchmark matrisi, fonksiyona özgü mutlak hata/sıra, otomatik tekrarlar, CSV/JSON ve ayrı SQLite `benchmark_suites` arşivi. Tek fonksiyonlu 11 algoritmalık eşit-NFE laboratuvarı korunur.
- [x] Multiple objective benchmark matrix with per-objective metrics and mean ranks
- [x] SQLite storage of compact benchmark results, backward-compatible with historical comparisons
- [ ] v1.9.0 frontend production build verification on Windows host
- [ ] Benchmark suites beyond 2D, rotated/shifted functions, uncertainty intervals and unbiased parameter tuning

> **2026-11-12 — v2.0.0:** CS, IWO, SA için tam NFE sınırında durabilen ayrı karşılaştırma adaptörleri; sabit NFE kareleri, bütçeye göre ölçeklenen sigma/soğuma, 14 algoritmalı karşılaştırma ve çoklu benchmark desteği; 207 backend testi. Windows frontend production build ve etkileşim testi kullanıcı ortamında doğrulanacaktır.

- [x] v2.1.0: Tek-parametreli duyarlılık deneyleri, eşit NFE, ortak tohum etiketleri, 14 algoritma için parametrik kayıt ve SQLite arşivi
- [ ] Çok parametreli etkileşimleri kontrollü faktöriyel/doğrulama deneylerinde inceleme
- [ ] CEC/COCO referans benchmarkları ile doğrulama, bellek ve performans sınırları
- [ ] 2B arayüzü koruyarak isteğe bağlı yüksek boyutlu matematiksel motor

> **2026-11-12 — v2.1.0:** Parametre Duyarlılığı Laboratuvarı eklendi; 215 backend testi başarılı. Frontend TypeScript sözdizimi kontrol edildi, Windows `npm.cmd run build` ayrıca yapılmalı.


## v2.2.0 — Yüksek Boyut Araştırması
- [x] Gerçek 2/5/10/30 boyut PSO, GWO ve DE motorları; aynı NFE ve çoklu tohum analizi
- [x] 5 boyutlanabilir test fonksiyonu, yakınsama ve tam vektör incelemesi
- [x] SQLite arşivi, CSV/JSON, API doğrulaması, testler
- [ ] Kalan 11 sürekli algoritmanın D-boyutlu varyantları
- [ ] Üretim ortamında browser/E2E ve yük testleri
- [ ] Çok boyutlu global benchmark ve istatistiksel sağlamlık analizi


## v2.3.0 — Yüksek boyutlu algoritma kapsamı
- [x] WOA, MFO, SSA için gerçek D-boyutlu hesaplama; PSO/GWO/DE korundu (6/14 sürekli algoritma)
- [x] 2–4 algoritma seçimi; aynı gerçek NFE, sabit tohum, tam D-koordinatlı sonuçlar
- [x] WOA kuşatma/spiral, MFO alev arşivi, SSA lider–takipçi denklemlerinin bağımsız testleri
- [x] Geriye dönük v2.2.0 deney arşivi uyumluluğu
- [ ] Diğer sekiz sürekli algoritmanın D boyut desteği, akademik raporlar ve ölçek performans testleri


## v2.4.0 — Üç yeni yüksek boyutlu matematiksel motor
- [x] FA (eşzamanlı parlaklık/ardışık çekim), BA (frekans, ses, darbe, aday kabulü), GSA (kütle, kuvvet/ivme, Kbest) gerçek D boyutta
- [x] 9/14 sürekli algoritma; 2/5/10/30 boyut, gerçek NFE, v2.2–v2.3 arşiv geriye uyumluluğu
- [x] 35 yeni matematiksel ve API regresyon testi; 315 toplam backend testi
- [x] Yeni algoritmalara özgü parametre seçimleri ve deney verisi dışa aktarma
- [ ] Diğer beş sürekli algoritmanın D boyut desteği (ABC, CS, SMA, IWO, SA)
- [ ] Üretim için uçtan uca tarayıcı testleri, performans ölçümü ve kapsamlı bilimsel raporlama

## v2.5.0 — Tam sürekli yüksek boyut algoritma kapsamı

- [x] ABC, CS, SMA, IWO, SA için gerçek D-boyutlu hesaplama adaptörleri
- [x] 14 sürekli algoritmanın tamamını aynı 2–4 seçimli yüksek boyut deney arayüzüne dahil etme
- [x] Gerçek NFE kontrol noktaları, tarihsel en iyi arşivi ve değişken algoritmik döngü sayısı
- [x] SA soğutma / IWO yayılım takvimlerini NFE-normalize varyant olarak belgeleme
- [x] API ve kalıcı SQLite deney arşivinde geriye dönük uyumluluk
- [x] 386 backend testi başarılı
- [ ] Windows'ta TypeScript/Vite üretim derlemesi ve tarayıcı testi
- [ ] Akademik PDF raporu, istatistiksel güç, deney planı, kullanıcı dokümantasyonu ve yayın hazırlığı


## v2.6.0 — Kalıcı deneylerden akademik raporlar

- [x] Önceki deneyleri yeniden koşturmadan veri kaynağı olarak kullan
- [x] Karşılaştırma, benchmark, duyarlılık ve yüksek boyut raporlarını üret
- [x] Parametre, yöntem, özgün arşiv ID ve SHA-256 kayıt bilgisini sun
- [x] JSON, Markdown ve baskıya uygun HTML çıkışı sağla
- [x] Deney sınırlamalarını ve yorumlama uyarılarını açıkça belirt
- [x] Geriye dönük SQLite arşiv uyumluluğunu koru
- [ ] Daha geniş çoklu tohum/benchmark deneyleriyle sağlam etki büyüklüğü ve belirsizlik analizi
- [ ] Tarayıcıdan bağımsız sunucu tarafı PDF üretimi ve indirilebilir grafikler
- [ ] E2E testler, performans profillemesi, güvenlik sertleştirmesi ve dağıtım


## v2.11.0 — Çok Türlü Deney Kuyruğu

- [x] 2D benchmark ve OFAT duyarlılık deneyleri kalıcı SQLite görev kuyruğunda
- [x] Tamamlanan deneyleri ilgili arşive aynı SQLite işleminde yazma
- [x] Fonksiyon/algoritma/tohum ve parametre-değer/tohum bazlı ilerleme + koşular arası iptal
- [x] Restart, karma görev kuyruğu ve hata davranışları için otomatik testler
- [ ] Windows Vite derlemesi, 7 Playwright testi ve Docker dağıtım doğrulaması
- [ ] Gelişmiş hesaplama checkpoint'leri, çok worker yönetimi, üretim güvenliği


## v2.12.0 — Görev durum dayanıklılığı

- [x] Başlatma/ilerleme/iptal/hata/tamamlanma ve yeniden başlatma olaylarının SQLite günlüğü
- [x] Eski arşivden veri kaybetmeden dört yeni görev meta alanına göç
- [x] İptal edilen/başarısız iş için yeni kimlikle tekrarlama
- [x] Yalnızca terminal görev geçmişini silme, bilimsel arşiv koruması
- [x] Yeni API ve web arayüzü, geçmiş filtresi, güvenli silme onayı
- [x] Backend regresyon testi (475 önceki + 15 yeni)
- [ ] Windows'ta 8 Playwright testi, Vite derlemesi ve Docker doğrulaması
- [ ] Ortadan kesilen trial'ın hesaplama checkpoint'i / kalan denemeden devam
- [ ] Birden fazla işçi, dağıtık görev yönetimi, internete açık üretim güvenliği


## v2.13.0 — Koşu-seviyesi checkpoint / recovery

- [x] Üç deney türünde tamamlanmış bağımsız koşular için kalıcı SQLite checkpoint
- [x] Kesinti sonrasında yalnızca eksik koşuları tekrar çalıştırma
- [x] SHA-256 içerik bütünlüğü, optimizer-kodu/Python/NumPy ortam parmak izi
- [x] Arşiv + görev durumu + ara kayıt temizliği için atomik tamamlanma
- [x] Eski v2.12 SQLite kuyruk verisine zarar vermeyen otomatik geçiş
- [ ] Tek algoritma koşusu içindeki iterasyon/ajan checkpoint'i (kapsam dışı)
- [ ] Windows, Playwright ve Docker üzerinde v2.13.0 testlerinin doğrulanması
- [ ] v2.14 bilimsel validasyon ve ölçümler; v2.15 arayüz cilası; v3.0.0 final yayın


## v2.14.0 — Bilimsel doğrulama ve kontrollü performans

- [x] Kaydedilmiş D-boyut sonuçları için arşiv vektörü, NFE, yakınsama ve grup istatistikleri denetimi
- [x] Kaydedilmiş koşu sürelerinden medyan/p95/NFE/s ve bilimsel sınırlamaları açıkça gösteren yeni laboratuvar
- [x] Amaç fonksiyonlarının analitik referans değerlerine karşı otomatik testler
- [x] Kontrollü 2/5/10/30D × beş amaç fonksiyonu yerel JSON/Markdown bilimsel profili
- [x] D-boyut tekrar sınırı 20; 160.000 toplam NFE üst sınırı korunur
- [ ] Kullanıcı Windows ortamında Vite/Playwright/Docker doğrulaması
- [ ] Dış referans algoritmaları / CEC-COCO ile bağımsız eşdeğerlik sınaması (gelecekteki araştırma)
- [ ] v2.15.0 arayüz ve erişilebilirlik cilası; v3.0.0 final yayın


## v2.15.0 — Final öncesi arayüz ve kullanılabilirlik

- [x] Laboratuvarların sayfa bazlı React.lazy/Suspense ile kod bölünmesi
- [x] Dinamik modül hata paneli ve yükleme durumu
- [x] Mobil drawer için ESC, odak iadesi, görünür kapatma ve aria-expanded
- [x] Klavye erişimi/skip link ve dar ekrana ek iyileştirmeler
- [x] Tek kaynaklı frontend sürüm etiketi (package.json)
- [x] Gerçek build için JS parça boyutu raporlama aracı
- [x] 540/540 backend regresyon testi (geliştirme ortamında)
- [ ] Windows üzerinde 12/12 Playwright, frontend build ve JS raporunun doğrulanması
- [ ] Docker doğrulaması: API 2.15.0, iki konteyner healthy
- [ ] v3.0.0 final yayın paketi, belge ve sunum, GitHub/LinkedIn/CV


## v3.0.0 — Final yerel araştırma ve portföy sürümü (2026-11-12)

- [x] Sürümün API, frontend ve CI denetiminde tekilleştirilmesi; sabit `2.9.0` Docker CI beklentisinin kaldırılması.
- [x] Kısa Türkçe/İngilizce README ve doğru kapsam/sınırlama belgeleri.
- [x] Mimari diyagram, bilimsel yöntem, tekrarlanabilir deney protokolü ve portföy yayın kiti.
- [x] Sürüm denetim betiği ve regresyon testleri.
- [ ] Kullanıcının Windows ortamında v3.0.0 backend + Playwright + Docker doğrulaması.
- [ ] Gerçek v3.0.0 ekran görüntülerinin güvenlik incelemesi sonrası GitHub'a eklenmesi.
- [ ] Kullanıcının seçtiği GitHub deposuna push ve paylaşım (otomatik yapılmadı).
- [ ] Harici benchmark implementasyonlarıyla bağımsız bilimsel eşdeğerlik testi (kapsam dışı).

**Önemli:** Final sürümü yerel/tek kullanıcı araştırma ve portföy yayını içindir;
internete açık, kimlik doğrulamalı çok kullanıcılı SaaS değildir.
