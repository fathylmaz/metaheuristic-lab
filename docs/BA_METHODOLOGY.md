# BA / Yarasa Algoritması — Matematiksel Yöntem

**Sürüm:** Metaheuristic Lab v1.1.0 · **Problem:** 2B sınırlı sürekli minimizasyon.

## Bilimsel kaynak ve uygulama sınırı

- Xin-She Yang (2010), *A New Metaheuristic Bat-Inspired Algorithm*, Studies in Computational Intelligence, 284, DOI [10.1007/978-3-642-12538-6_6](https://doi.org/10.1007/978-3-642-12538-6_6).
- Ön baskı: [arXiv:1004.4170](https://arxiv.org/abs/1004.4170).

Yang'ın standart Bat Algorithm (BA) hareket kuralları esas alınır. Aşağıda belirtilen eşzamanlı değerlendirme, başlangıç darbe oranı, rastgele örnekleme ve sınır uygulaması **bu uygulamanın açık varyant kararlarıdır**. Animasyon biyolojik ekolokasyonun gerçek zamanlı fiziksel simülasyonu değil, sayısal optimizasyon adımlarının görselleştirilmesidir.

## Ajan durumları ve parametreler

Her yarasa `i` için konum `xᵢ ∈ R²`, hız `vᵢ ∈ R²`, frekans `fᵢ`, ses şiddeti `Aᵢ` ve güncel darbe oranı `rᵢ` tutulur. `r0`, yaklaşılacak üst darbe oranıdır; `f` ve `r` farklı kavramlardır.

Başlangıç: `xᵢ` arama uzayında uniform; `vᵢ=0`, `Aᵢ=A0`, `rᵢ=0`. Bir kere değerlendirilen başlangıç uygunluklarından `x_best` arşivi kurulur. Tohum NumPy `default_rng(seed)` tarafından alınır.

## Güncelleme ve kabul

Her iterasyon başında tarihsel en iyi konum ve ortalama ses şiddeti **dondurulur**, böylece yeni adaylar aynı neslin önceden hesaplanmış durumlarını kullanır.

1. `fᵢ = fmin + (fmax − fmin) * U(0,1)`
2. `vᵢ(t) = vᵢ(t−1) + (xᵢ(t−1) − x_best(t−1)) * fᵢ`
3. Global öneri: `zᵢ = clip(xᵢ(t−1) + vᵢ(t))`
4. Eğer `U(0,1) > rᵢ` ise **global önerinin yerine** yerel öneri kurulur: `zᵢ = clip(x_best(t−1) + ε * mean(A(t−1)))`, `ε∈U(−1,1)²`. Frekans ve hız güncellemesi yerel arama halinde de yapılır.
5. `F(zᵢ)` **tam bir kez** hesaplanır (aday reddedilse bile). Yalnızca `F(zᵢ) < F(xᵢ)` ve bağımsız `U(0,1) < Aᵢ` olduğunda konum `zᵢ` ile değiştirilir.
6. **Yalnızca kabulde**: `Aᵢ ← α Aᵢ`, `rᵢ ← r0 (1 − exp(−γ t))`. Ret halinde `xᵢ`, `Aᵢ`, `rᵢ` korunur; hesaplanmış `vᵢ` korunmaya devam eder.
7. Güncel en iyi ile tarihsel en iyi arşivi karşılaştırılır. Arşiv elit olarak popülasyona zorla eklenmez.

`A0, α ∈ (0,1]`, `r0 ∈ [0,1]`, `γ>0`, `0≤fmin≤fmax`. Kullanıcıya sunulan kontroller doğrulanır. `fmax=fmin` sabit frekans olarak geçerlidir.

### Değerlendirme bütçesi

Başlangıç N adet değerlendirme + her adımda N adet kabul/ret öncesi aday değerlendirmesi:

**NFE = N × (T + 1)**.

Kabul edilmeyen adaylar değerlendirme sayacından çıkarılmaz. `ba_candidate` değerlendirilmiş ve sınırlandırılmış **aday konumunu**; `AgentState.x/y` ise kabul sonrası **gerçek mevcut konumu** gösterir. Animasyon ret halinde eski noktadan aday noktaya hareket olmuş gibi göstermemelidir: kesikli bağlantı yalnızca *hesaplanan öneriyi* gösterir.

### Denetlenebilir telemetri

- `ba_previous`, `ba_reference_best`, `ba_frequency`, `vx/vy`: hız denkleminin yeniden hesaplanması
- `ba_move_kind`, `ba_local_epsilon`, `ba_mean_loudness`: global/yerel önerinin yeniden hesaplanması
- `ba_candidate`, `ba_candidate_fitness`, `ba_accept_draw`, `ba_accepted`: sonuç ve kabul denetimi
- `ba_pulse_draw`, `ba_loudness`, `ba_pulse_rate`: son durumun karar/ses/güncelleme denetimi
- `ba_global_proposals`, `ba_local_proposals`, `ba_accepted_count`: her karede işlem sayıları

Frekans bir ses titreşiminin fiziksel ölçüm Hz değeri değildir; amaç fonksiyonu uzayındaki sayısal arama katsayısıdır.

## Testler ve kapsam

`backend/tests/test_bat.py`: özdeş tohumla özdeş tarihçe, dört fonksiyonun matematiksel değerleri, sınır kontrolü, kabul ve ret denklemleri, global ve yerel adayların yeniden kurulması, gerçek NFE ve API girdi doğrulaması.

Bu sürümde BA yalnızca bağımsız simülasyon laboratuvarındadır. FA/PSO/ABC karşılaştırması aynen korunmuştur; daha geniş laboratuvara BA dahil etmek için ortak NFE kesme ve çoklu tohum istatistikleri ayrıca uygulanmalıdır. Aynı tohum/amaç üzerinde tek koşunun yüksek performansı istatistiksel üstünlük kanıtı değildir.
