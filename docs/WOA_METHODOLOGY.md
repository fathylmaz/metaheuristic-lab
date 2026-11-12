# WOA / Balina Optimizasyon Algoritması — Matematiksel Yöntem

**Sürüm:** Metaheuristic Lab 1.0.0 · **Problem:** iki boyutlu, sınırlandırılmış sürekli minimizasyon.

## Akademik kaynak

S. Mirjalili ve A. Lewis (2016), *The Whale Optimization Algorithm*, Advances in Engineering Software, 95, 51–67. DOI: [10.1016/j.advengsoft.2016.01.008](https://doi.org/10.1016/j.advengsoft.2016.01.008).

### Kuşatma ve rastgele hedef arama

Her birey için iki boyutlu `r1,r2` bağımsız U(0,1) vektörleri örneklenir:

- `A = 2 a r1 − a`
- `C = 2 r2`
- `D = |C ⊙ X_target − X_old|`
- `X_new = X_target − A ⊙ D`

`⊙` bileşen bazında çarpmayı, `| · |` bileşen bazında mutlak değeri ifade eder.

`p ∼ U(0,1)` ve `p < (1 − spiral_probability)` iken yukarıdaki model uygulanır. **Geniş arama** dalı için `max(|A_x|, |A_y|) ≥ 1` koşulunda **aynı neslin hareket-öncesi** popülasyonundan, kendisi dışındaki rastgele bir balina hedef olur. Diğer durumda hedef, bu neslin başında dondurulmuş **tarihsel en iyi konumdur**. Literatürde `|A|` eşiğinin vektör boyutunda uygulanması çeşitli şekillerde yorumlanır; burada **en büyük mutlak bileşen** kuralını açıkça seçiyoruz. Bu bir uygulama kararıdır.

### Spiral bubble-net hareketi

`p ≥ (1 − spiral_probability)` ise `ℓ ∼ U(-1,1)` ve `D' = |X_best − X_old|` ile

`X_new = X_best + D' exp(b ℓ) cos(2π ℓ)`

kullanılır. Burada `ℓ` iki eksen için **aynı skaler değerdir**. `b` spiral şekil katsayısıdır. Kullanıcı `spiral_probability=0.5`, `b=1.0` ve başlangıç `a0=2.0` seçtiğinde standart WOA seçeneklerini elde eder; farklı değerler parametrik varyant olarak değerlendirilir.

### Azalan kontrol katsayısı

`T > 1` için 1 tabanlı güncelleme indeksinde `a(t)=a0 (1 − (t−1)/(T−1))`, `t=1..T`. `T=1` ise `a=0`. Dolayısıyla ilk güncellemede `a=a0`, son güncellemede `a=0`. Bazı WOA makalelerindeki `a=2(1-t/T)` indeksleme şemasından farklı uç noktaya sahiptir; arayüzde açıkça gösterilir.

### Sınır, hesaplama bütçesi, elit arşivi

- Her aday `[low, high]^2` içine kırpılır (clipping). Yalnızca **bir kez** değerlendirilir.
- N balinalı başlangıçta N değerlendirme, her güncelleme adımında da N değerlendirme vardır. **NFE = N × (T+1)**.
- Tüm balinalar eşzamanlı olarak hareket-öncesi popülasyondan hesaplanır. Tarihsel en iyi çözüm her jenerasyonda korunur ama popülasyona elit birey olarak zorla kopyalanmaz.
- `current_best` güncel popülasyondaki minimum, `best_so_far` ise tarihsel en iyi arşivdir. İkisi farklı olabilir.
- `woa_previous`, `woa_target`, `woa_A`, `woa_C`, `woa_l`, `woa_p` kayıtları kullanılarak gösterilen **her** balina güncellemesi sınır uygulamasıyla yeniden hesaplanabilir.
- Canvas üzerindeki hedef/yer değiştirme çizgileri iterasyon örnekleridir; kesintisiz fiziksel yüzme rotasını temsil etmez.

### Geliştirme sınırları

Bu sürüm WOA'yı Sphere, Rastrigin, Ackley ve Rosenbrock üzerinde 2B gösterir. FA/PSO/ABC eşit-NFE laboratuvarı henüz WOA'yı içermez. Uzun dönem istatistiksel üstünlük veya tüm problem sınıflarında en iyi algoritma iddiası bulunmaz.
