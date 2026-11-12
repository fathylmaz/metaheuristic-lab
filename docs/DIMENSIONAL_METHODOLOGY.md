# Metaheuristic Lab v2.5.0 — Gerçek D-boyutlu optimizasyon

## Kapsam

**PSO, GWO, DE, WOA, MFO, SSA, FA, BA, GSA, ABC, CS, SMA, IWO ve SA** `D = 2, 5, 10, 30` boyutlarını destekler. Eski 2B motorlar ve 15 algoritmalık simülasyon kataloğu değiştirilmedi. Son beş algoritmanın yüksek boyutlu sürümleri gerçek NFE denetleyen, nesil sayıları farklı **bütçe-adaptörleri** olarak açıkça belgelenmiştir. ACO ayrık TSP'dir.

Amaç fonksiyonları: Sphere, Rastrigin, Ackley, Rosenbrock ve Griewank. Genel D boyutunda klasik formüller kullanılır. Her birinin optimum **amaç değeri** sıfırdır; Rosenbrock optimum vektörü `(1,1,...,1)`, diğerlerinin `(0,0,...,0)` şeklindedir. Fonksiyonlara verilen aday vektörlerin **tamamı D bileşenlidir**; değerlendirme yalnızca ilk iki koordinat üzerinden yapılmaz.

## Algoritma varyantları

- **PSO:** `v ← wv + c₁r₁(pBest−x) + c₂r₂(gBest−x)`; her boyutta bağımsız rassal terimler, hıza uygulanan aralık sınırı, pozisyon kırpma ve sınırda hız sıfırlama. Başlangıç hızı sıfırdır.
- **GWO:** Üç güncel lider (alfa/beta/delta) seçilir. Her lider için koordinat bazında `A = 2ar₁−a`, `C = 2r₂`; `X = leader−A|C·leader−position|` hesaplanır, üç adayın koordinat bazlı ortalaması alınır. `a` nesiller boyunca azalır. `a₀=2` varsayılandır.
- **WOA:** Her balina için olasılıkla en iyiyi kuşatma veya rastgele akran arama (koordinat bazlı A/C), aksi halde tek bir `ℓ` ile en iyi çözüme göre spiral. Ajanların eski konumları ve en iyi konum nesil boyunca dondurulmuştur. Keşfe geçişte `max(|A_j|) >= 1` kuralı kullanılır. `a` ilk nesilde `a₀` ve son nesilde 0'dır.
- **MFO:** Uygunluk sıralı güveler, azalan sayıda elit alevle logaritmik spiral `X = F + |F-X| exp(b t) cos(2πt)` üzerinden eşleştirilir. Her boyut bağımsız `t` kullanır; eski alev arşivi ile güncel nüfustan en iyi benzersiz değerlendirilmiş konumlar saklanır. Herkes aynı konuma toplanırsa alev dizisi değerlendirilmemiş noktalar üretmeden en iyi mevcut alevin kopyalarıyla tamamlanır.
- **SSA:** Lider bileşen bazında `F_j ± c₁((u-l)c₂ + l)` ile besin kaynağına göre yönlenir; `c₁(t)=c₁₀ exp(-(4t/T)²)`. Takipçiler eski kendi ve **yeni güncellenmiş öncül** konumlarının ortalamasını alarak sıra ile güncellenir. Liderin besin noktası önceki tarihsel en iyidir.
- **FA:** Başlangıç neslindeki uygunluk sıralaması her adım için dondurulur. Daha parlak her firefly, mevcut çalışma konumu ile `β₀exp(-γ||x_j-x_i||²)` çekimini ve bağımsız `α (u-l) U(-0.5,0.5)^D` keşif terimini kullanarak ardışık hareket ettirir. Çekim yoksa yalnız bir keşif adımı atılır; her bireyin son konumu nesilde bir kez değerlendirilir. Bu örneklenmiş parlaklık sırası, dokümante edilmiş eğitim varyantıdır.
- **BA:** `f_i~U(fmin,fmax)`, `v_i ← v_i + (x_i-gBest) f_i`, `x_trial ← x_i + v_i`; `U > r_i` olduğunda eski global en iyi çevresinde ortalama ses şiddetli yerel aday üretilir. Aday, **bir kez** değerlendirilir; yalnız iyileştiriyorsa ve bağımsız rassal değer `A_i` altında ise kabul edilir. Reddedilen adayın değerlendirmesi de NFE'ye dahildir. Kabulde ses şiddeti azalır, darbe oranı `r₀(1-exp(-γt))` ile güncellenir. Hız reddedilen adımda dahi güncellenir, global en iyi arşivlenir.
- **GSA:** Kütle `M_i ∝ (worst - f_i)/(worst-best)` şeklinde normalize edilir (eşitlikte eşit dağıtılır); `G(t)=G₀exp(-αt/T)` ve `Kbest=ceil(N-(N-1)t/T)`. Önceki neslin konumları ve kütleleriyle, D-koordinatlı rastgele çekim katkıları, `a_i=F_i/max(M_i,10⁻¹²)`, `v_i←U^D·v_i+a_i`, `x_i←clip(x_i+v_i)` kuralları kullanılır. Sınırı aşan hız bileşenleri sıfırlanır, tek yeni konum değerlendirilir.
- **DE:** `DE/rand/1/bin`. Hedef dışında üç farklı donör, `F` fark mutasyonu, her hedef için **zorunlu en az bir mutant koordinat**, `CR` binom çaprazlaması ve açgözlü seçim. Donörler aynı neslin **dondurulmuş** popülasyonundan alınır.
- **ABC:** D-boyutta tek bileşenli komşu üretimi, işçi–gözlemci–keşifçi aşamaları ve deneme limiti. Tüm denemeler NFE'ye dahildir; limit sonrası keşifçi yeniden değerlendirilir.
- **CS:** Mantegna Lévy uçuşları, rastgele ev sahibi yuvaya yumurta bırakma, açgözlü yer değiştirme, en kötülere sabit oranda yeniden başlangıç; tüm adaylar sayılır.
- **SMA:** Ağırlık W, p olasılığı, vb/vc katsayılı D-boyutlu besine yaklaşma/büzülme, z ile yeniden başlangıç. Son büzülmede vc sıfıra inebilir; Rastrigin/Sphere optimumunun orijin olması yapay biçimde çok düşük hatalara yol açabilir. Bütün fonksiyonlara genelleme yapılmaz.
- **IWO:** Uygunluğa bağlı tohum sayısı, D-boyutlu Gaussian dağılım, rekabetçi maksimum nüfus ve **NFE-bazlı** yayılım σ zamanlaması. Başlangıç ve maksimum popülasyon ayrı ayarlanır.
- **SA:** Tek güncel çözüm ve Metropolis kabulü. Başlangıç bir kez değerlendirilir; kalan tüm NFE tek tek adaylardan gelir. Soğutma **Tref ufkuna göre NFE-normalize** edilir; `N` SA popülasyonu değildir.

İlk dokuz sabit popülasyonlu algoritmada her nesilde N yeni aday değerlendirilir. Son beş algoritmanın farklı değerlendirme düzenlerinde tam **NFE/koşu = N × (Tref + 1)** hedeflenir; ortak kaydedilen NFE noktaları gerçek nesil/döngü sayısı değildir. SA bir tek çözümden başlar ve ilk NFE kontrol noktasında N−1 komşuyu zaten değerlendirmiştir; ABC/CS/IWO aynı bütçeye iç aşamalarının ortasında ulaşabilir. Her algoritma için aynı sayıda, aynı etiketli bağımsız tohum kullanılır. Sabit tohumla aynı sonuç ve aynı konum geçmişi tekrar üretilir. Aynı tohum etiketi, bütün varyantların rastgele sayı tüketimi aynı olacağı anlamına gelmez.

## Kayıt ve görselleştirme

- Her nesilde en iyi-so-far **D-boyutlu vektör** ve amaç fonksiyonu hatası kaydedilir. Bunlar geri yüklenebilir SQLite kayıtlarında saklanır.
- Yakınsama grafiği farklı tohumların ortalama mutlak hatalarını gerçek NFE koordinatlarında gösterir. Yalnızca grafikte sıfır hatalar log ölçeği için 10⁻¹⁶ tabanıyla gösterilir; gerçek sayılar değiştirilmez.
- İzdüşüm grafiği **en iyi-so-far vektörünün ilk iki koordinatını** gösterir; tam bir D-boyutlu uzayın 2B çizimi veya gerçek popülasyonun tamamı değildir. Gösterilen görsel bilgi üzerinden D-boyutlu genel performans yorumu çıkarılamaz.
- Tam vektör listesi bütün D bileşenlerini gösterir. Tohum bazlı sonuçlar CSV ve JSON dışa aktarılabilir.
- Çok küçük koşu örneklerinden algoritmaların evrensel üstünlüğü sonucu çıkarılmaz. Aynı NFE, eşit işlem süresi veya eşdeğer başlangıç popülasyonu anlamına gelmez. Aynı parametreler ve rastgele tohumla tekrarlanabilirlik hedeflenir.

## Güvenlik/deney sınırlamaları

Deney API'si yalnızca beş önceden tanımlanmış amaç fonksiyonunu destekler; kullanıcıdan çalıştırılabilir matematiksel kod veya keyfi Python ifadesi almaz. Boyutlar `2/5/10/30`, tekrarlar `2..8`, popülasyon `8..64`, iterasyon `5..200` ve toplam NFE `≤ 160000` ile sınırlıdır. Sonuçlar yalnızca yerel SQLite veritabanında kalır.

Algoritma listesi en az 2, en fazla 4 benzersiz seçenek içerir; toplam NFE sınırı 160.000’dir. Eski v2.2.0–v2.4.0 SQLite kayıtlarının yeni istek parametreleri Pydantic varsayılanlarıyla okunur.

Bu sürüm, **üretim ortamı ve geniş ölçekli bilimsel benchmark sertifikasyonu** iddiası taşımaz. Tam frontend üretim derlemesi ve tarayıcı etkileşim testi kullanıcının Windows ortamında yapılır.

## Yüksek boyutlu varyantların referansları

- WOA: Mirjalili & Lewis, *The Whale Optimization Algorithm* (2016), https://doi.org/10.1016/j.advengsoft.2016.01.008. Eğitim amaçlı mevcut 2B uygulamayla eşleşen `max(abs(A)) >= 1` keşif kuralını kullanır.
- MFO: Mirjalili, *Moth-flame optimization algorithm: A novel nature-inspired heuristic paradigm* (2015), https://doi.org/10.1016/j.knosys.2015.07.006. Benzersiz elit arşivi bu projenin belgelenmiş uygulama tercihidir.
- SSA: Mirjalili et al., *Salp Swarm Algorithm: A bio-inspired optimizer for engineering design problems* (2017), https://doi.org/10.1016/j.advengsoft.2017.07.002. Ardışık öncül güncelleme kuralı aynen izlenir.

- FA: Yang, *Firefly Algorithms for Multimodal Optimization* (2009/2010), ilk 2B uygulamanın donmuş parlaklık ve ardışık çekim varyantı.
- BA: Yang, *A New Metaheuristic Bat-Inspired Algorithm* (2010), frekans–ses–darbe güncellemesinin mevcut 2B eğitim varyantı.
- GSA: Rashedi, Nezamabadi-pour & Saryazdi, *GSA: A Gravitational Search Algorithm* (2009), normalize kütle ve Kbest kuralının 2B uzantısı.
