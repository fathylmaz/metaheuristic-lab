# İstilacı Yabani Ot Optimizasyonu (IWO) — Denetlenebilir 2B Uygulama

**Referans:** Mehrabian, A. R., & Lucas, C. (2006). *A novel numerical optimization algorithm inspired from weed colonization*. **Ecological Informatics, 1(4)**, 355–366. https://doi.org/10.1016/j.ecoinf.2006.07.003

## Problem ve algoritma varyantı

İki boyutlu gerçek sayılı **minimizasyon** problemidir. Her bitki `(x, y)` bir çözümü temsil eder. Bu sürüm orijinal IWO'nun temel dört aşamasını kullanır: rastgele başlangıç, uygunluğa bağlı tohum sayısı, normal dağılımlı tohum saçılması ve **global rekabetçi eleme**. Sürüm sabit popülasyonlu bir sürü algoritması değildir.

Başlangıçta `N0` bitki, `[lower, upper]^2` bölgesinde uniform üretilir; her biri bir kez değerlendirilir. Her iterasyonda bir önceki hayatta kalan bitkiler üremeye katılır:

1. **Tohum sayısı:** `f_best = min(f_i)`, `f_worst = max(f_i)` ve **minimizasyonda**

   `seeds_i = floor(S_min + ((f_worst - f_i) / (f_worst - f_best)) * (S_max - S_min))`.

   Tam uygunluk eşitliği durumunda sıfıra bölünmez: her bitki `S_max` tohum üretir. Bu açık bir uygulama tercihidir. Normal tohum sayısı (aralığı kırpmadan) 0 ile 8 arasında ayarlanabilir.

2. **Yayılma standart sapması:** nesil `t=1..T` için

   `sigma(t) = sigma_final + (sigma_initial - sigma_final) * ((T-t)/T)^m`.

   `m` doğrusal olmayan azalma üssüdür. `t=T`'de sigma tam `sigma_final` olur. Başlangıç animasyon karesinde `sigma(0) = sigma_initial` gösterilir; ilk üreme adımında `sigma(1)` kullanılır.

3. **Yeni tohumlar:** her tohum için bağımsız iki boyutlu `z ~ Normal(0, sigma(t)^2 I)` çekilir. `child = clip(parent + z, lower, upper)`. **Kırpılanlar da** gerçek amaç fonksiyonu değerlendirmesidir.

4. **Global rekabet:** mevcut *ebeveynlerin tamamı* ve *yeni doğanların tamamı*, uygunluk değerine göre birleştirilip sıralanır. En iyi `P_max` bitki hayatta kalır. Eşit uygunluklar için sabit sıra (önceden mevcut bitki, sonra üretilen tohum kimliği) kullanılır. Önceki canlı bitkiler yeniden değerlendirilmez; aday tohumlar her koşulda bir kez değerlendirilir. En iyi tarihsel sonuç ayrıca arşivlenir.

## Değişken popülasyon ve gerçek değerlendirme bütçesi

`NFE(0) = N0`, `NFE(t) = NFE(t-1) + produced_seeds(t)`.

Çünkü popülasyon başta büyüyebilir, değerlendirme bütçesi `N0 * (T+1)` **değildir**. Eleme sonucu reddedilen tohumlar bile üretildiğinde değerlendirilmiştir. `P_max` sadece hayatta kalan sayısını sınırlar, *değerlendirilen* tohum sayısını azaltmaz. Üretilen tohum sıfırsa jenerasyon yine kaydedilir, NFE sabit kalır.

## Kare verileri ve çizgilerin gerçek anlamı

- Her canlı bitki, tüm deney boyunca benzersiz bir **ID** taşır. ID, popülasyon dizisinin indeksi **değildir**; sabit popülasyonlu algoritmalardan farklı olarak bir bitkinin sonraki karede bulunması garanti değildir.
- Her karede `iwo_population_before`, `iwo_population_after`, `iwo_sigma`, `iwo_seeds_generated`, `iwo_seeds_survived`, `iwo_competitive_exclusions` tutulur.
- O karede **yeni üretilmiş ve rekabette kalmış** bir tohumun `iwo_parent_id`, `iwo_parent_position`, `iwo_raw_step` ve `iwo_birth_generation` alanları vardır. Arayüzdeki çizgi gerçek **ebeveyn konumu → hayatta kalan yavru konumu** bağını gösterir. Bu bir böceğin fiziksel uçuş rotası değildir.
- Elenen tohumların tek tek konumları hafızayı şişirmemek için simülasyon karelerinde tutulmaz; sayıları ve fonksiyon değerlendirme maliyetleri korunur. Görsel sayısı `seeds_generated` değil, hayatta kalan yeni tohumlarla ilişkilidir.
- Başlangıç ve yaşayan yaşlı bitkiler için bazı tohum alanları `null` olabilir; bu beklenen bir durumdur.

## Varsayılan parametreler ve sınırlar

- `population_size=24` (5–60), `iterations=90` (1–250).
- `iwo_max_population=60` (5–100; en az başlangıç popülasyonu).
- `iwo_min_seeds=0`, `iwo_max_seeds=5` (0–8, min ≤ max).
- `iwo_sigma_initial=1.50`, `iwo_sigma_final=0.02` (0 < final ≤ initial).
- `iwo_modulation_index=3.0` (1–6).
- `seed=42`; NumPy `default_rng` ile tekrarlanabilir.

**Not:** Normal dağılımın standart sapması amaç fonksiyonunun koordinat birimi cinsindendir. Sphere/Rastrigin/Ackley/Rosenbrock farklı koordinat ölçekleri kullanır. Aynı sigma her problemi aynı biçimde etkilemez. Bu sürüm GWO, SSA vb. motorlarla yanlışlıkla eşit değerlendirme bütçesi varmış gibi kıyaslanmaz. IWO henüz FA–PSO–ABC karşılaştırma modülünde yoktur.

## Test doğrulaması

`backend/tests/test_iwo.py` sigma uç değerlerini, tohum sınırlarını, sabit tohum eşitliğini, tüm karelerin pozisyon ve NFE tutarlılığını, gaussian konumların yeniden kurulabilmesini, elit arşiv monotonluğunu, dört amaç fonksiyonunu ve API geçersiz girişlerini test eder. Genel backend testleri de çalıştırılır.
