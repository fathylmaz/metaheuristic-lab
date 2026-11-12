# Moth-Flame Optimization (MFO) — v0.8.0

## Bilimsel temel ve seçilen varyant

Temel kaynak: Seyedali Mirjalili, *Moth-Flame Optimization Algorithm: A Novel Nature-inspired Heuristic Paradigm*, **Knowledge-Based Systems 89 (2015), 228–249**, DOI: [10.1016/j.knosys.2015.07.006](https://doi.org/10.1016/j.knosys.2015.07.006).

Bu modül sürekli iki boyutlu **minimizasyon** için MFO'nun alev belleği ve koordinat bazlı spiral güncellemesini uygular. Bağımsız çalışma modu, FA/PSO/ABC karşılaştırma motoruna dahil değildir. Aşağıdaki arşiv ve sıralama politikası bu yazılıma özgü açık bir varyanttır.

## Denklem ve parametreler

Her güve `M_i=(x_i,y_i)` bir çözüm; alev `F_j` sıralı seçkin çözüm belleğidir. Her eksen için bağımsız `t ~ Uniform(r, 1)` seçilir:

```text
r(l) = -1 - l/T
D_i = |F_j - M_i|
S(M_i,F_j) = F_j + D_i * exp(b*t) * cos(2*pi*t)
flame_count(l) = max(1, round_half_up(N - l*(N-1)/T))
```

- `N`: 5..60 güve; `T`: 1..250 jenerasyon; `b`: 0,1..3,0 spiral şekil katsayısı.
- `l`: 1..T (başlangıç karesi l=0); `r` değerleri −1'den −2'ye iner.
- Sınır dışındaki her koordinat doğrudan arama uzayına kırpılır (`clip`).
- Güveler **jenerasyon başındaki mevcut fitness** sırasına göre alevlere atanır. `j=min(rank,flame_count−1)`; azalan alev sayısı nedeniyle birden fazla güve tek alevi izleyebilir.
- Alev belleği, önceki en iyi N farklı *değerlendirilmiş* konum ile yeni jenerasyondaki N konumun birleşiminden en iyi N **eşsiz** koordinatı tutar. Bu tekrar giderme uygulamanın açıkça belirtilen varyantıdır; her referans uygulamasının tam eşleniği olduğu iddia edilmez.
- Her güve için jenerasyon sonunda bir fitness değeri hesaplanır. **Gerçek NFE = N*(T+1)**. Reddedilen pozisyon yoktur; tüm yeni güveler bir sonraki jenerasyonu oluşturur.

## Telemetri, gösterim ve yeniden üretilebilirlik

Her ajan karesi `flame_x`, `flame_y`, `flame_rank`, `spiral_t_x`, `spiral_t_y` alanlarını içerir. Bunlar o jenerasyonda fiilen kullanılan hedef ve rastgele katsayılardır; dolayısıyla iki ardışık kareden denklem yeniden hesaplanabilir. `flame_count`, `function_evaluations`, `best_so_far`, `current_best` ve çeşitlilik ayrıca saklanır.

Alevler çizgede dörtgen (baklava) işaretiyle, güveler nokta olarak gösterilir. İnce kesikli bağ, güve ile **o jenerasyonda kullandığı alev** arasındadır. Bunun gerçek ve sürekli zamanlı geometrik spiral yörünge olduğu iddia edilmez: görüntülenen motor **ayrık koordinat güncellemelerini** kaydeder; her eksenin kendi t'si vardır.

Rastgele sayı üretici NumPy `default_rng(seed)`; aynı Python/NumPy ortamı ve ayarlarla tüm kareler aynıdır, ancak `run_id` ve `duration_ms` farklıdır. Farklı ortamların aynı bit düzeyinde sonuç garantisi yoktur.

## Kontroller

`backend/tests/test_mfo.py`: aynı tohumdan özdeş kareler, tüm dört fonksiyonda gerçek uygunluk/koordinat eşitliği, monoton en iyi arşivi, 24→1 alev sayısı, birebir yeniden hesaplanan spiral güncellemesi, NFE ve HTTP 422 giriş doğrulaması.

Sınırlar: Yalnızca 2D; fonksiyon bazlı 3D yüzey, N-boyutlu karşılaştırma, maliyet dağılımları ve canlı WebSocket hesaplama şu an mevcut değildir.
