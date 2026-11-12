# Gri Kurt Optimizasyonu (GWO) — Matematiksel yöntem ve sınırlar

## Referans
S. Mirjalili, S. M. Mirjalili, A. Lewis, **Grey Wolf Optimizer**, *Advances in Engineering Software* 69 (2014) 46–61. DOI: **10.1016/j.advengsoft.2013.12.007**.

## Problem ve temsili
GWO, bu uygulamada **iki-boyutlu, kutu sınırları içinde minimizasyon** için kullanılır. Popülasyonun her üyesi, bir aday çözümü olan `(x, y)` konumundaki **kurt**tur. ACO gibi ayrık TSP modülünden ayrı tutulur.

## Sürünün liderleri
Her güncelleme öncesinde mevcut popülasyon, amaç değeri küçükten büyüğe (eşitlikte sabit ajan ID'si) sıralanır. En iyi üç **farklı kurt** alfa (α), beta (β) ve delta (δ), gerisi omega (ω) kabul edilir. `gwo_leader_positions` bu güncellemeye **giren önceki neslin** liderlerini gösterir. `wolf_role` ise karenin **yeni** popülasyonundaki rolüdür; birbirine karıştırılmamalıdır.

## Konum güncelleme
Her kurt `X` ve her lider `L_k` için (`k ∈ {α, β, δ}`), her koordinatta bağımsız uniform rastgele vektörler `r1_k,r2_k ∈ [0,1]^2` örneklenir:

```
A_k = 2*a*r1_k - a
C_k = 2*r2_k
D_k = |C_k ⊙ L_k - X|
X_k = L_k - A_k ⊙ D_k
X_new = clip((X_alpha + X_beta + X_delta)/3, lb, ub)
```

`⊙`: bileşen bazında çarpım. `clip` alt/üst kutu sınırıdır. Üç ara aday konum her kurt için API'de `gwo_x1`, `gwo_x2`, `gwo_x3` olarak raporlanır; böylece matematiksel hareket yeniden hesaplanabilir.

### `a` zamanlaması
Varsayılan ilk değer `a0=2.0` olup standardın keşif/kullanım aralığına uyar. `T` güncelleme için 1 tabanlı `l`:

```
T > 1: a(l) = a0 * (1 - (l-1)/(T-1)), 1 <= l <= T
T = 1: a(1) = 0
```

Bu seçim ilk güncellemede `a0`, sonuncusunda tam 0 kullanır. Farklı `a0` değerleri **parametre varyantı** oluşturur. Varsayılan a0=2 temel modeldir.

## Hesaplama ve en iyi arşiv
Başlangıçta N konum bir kez değerlendirilir. Her güncellemede bütün N kurdun yeni konumu birer kez değerlendirilir. Dolayısıyla **NFE = N × (T+1)**, diğer yöntemlerdeki gibi göstermelik bir bütçe değildir. Her nesilde mevcut en iyi çözüm değişebilir; `best_so_far` ve `best_position` bağımsız global en iyi arşivini tutar ve asla kötüleşmez.

## Görselleştirme doğruluğu
Haritada güncel alfa, beta, delta ve omega kurtları farklı renklerdedir. Üç renkli lider halkası **son hareketin hesaplanmasında kullanılan kaynak lider konumlarıdır**; dolayısıyla güncel popülasyondaki lider kurtların konumlarıyla aynı olmak zorunda değildir. Bir kurt seçilirse o kurttan gerçek önceki lider konumlarına bağlantılar çizilir ve üç aday pozisyonu gösterilir. Kullanıcı tek adım, geri sarma, izler ve lider bağlantılarını kullanabilir.

## Sınırlamalar
- 2B görsel optimizasyon, yüksek boyutlu GWO değerlendirmelerinin yerine geçmez.
- Bu sürümde lokal iyileştirme, restart, fonksiyon-dışı çözüm değerlendirmesi veya karşılaştırmaya dahil edilme bulunmaz.
- FA/PSO/ABC karşılaştırma ekranı şu an yalnızca bu üç algoritmayı kapsar; GWO tekli simülasyonda çalışır.
- Rastgelelik `numpy.random.default_rng(seed)` ile üretilir. Aynı kurulum ve tohum tekrarlanabilir.
