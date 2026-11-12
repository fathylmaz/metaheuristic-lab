# SSA — Salp Sürüsü Algoritması / Matematiksel yöntem

## Bilimsel dayanak

S. Mirjalili et al., *Salp Swarm Algorithm: A bio-inspired optimizer for engineering design problems*, Advances in Engineering Software 114 (2017), 163–191. DOI: **10.1016/j.advengsoft.2017.07.002**.

SSA sürü üyelerinin zincir hareketinden esinlenir. Bu proje 2B sürekli minimizasyon için denetlenebilir **lider ve sıralı takipçi** güncellemesini uygular. Bu bir biyolojik fizik simülasyonu değildir; her kare gerçek optimizasyon hesabından üretilir.

## Tanımlar ve matematik

- `x[0]` lider, `x[1:]` sıralı takipçilerdir; sıra her iterasyonda korunur.
- `F` jenerasyon başında **arşivde saklanan en iyi konum** olarak sabitlenir; jenerasyon içinde değişmez.
- `t` 1..T ve `c1(t) = c1_initial * exp(- (4t/T)^2)`; standart `c1_initial=2.0`.
- Her lider koordinatı için bağımsız `c2[j],c3[j] ~ U(0,1)` çekilir.
- `sign[j] = +1` if `c3[j] >= 0.5`, aksi halde `-1`.
- **Lider:** `x_new[0,j] = clip(F[j] + sign[j]*c1*((upper-lower)*c2[j]+lower),lower,upper)`.
- **Takipçi i>=1:** `x_new[i] = clip(0.5*(x_old[i]+x_new[i-1]),lower,upper)`; takipçiler önden arkaya sırayla hesaplanır. Öncülün **yeni** konumu kullanılır.
- Güncellemeden sonra **N** konumun her biri yalnızca bir kere değerlendirilir. Başlangıç N değerlendirmesi de dahil toplam **NFE = N*(T+1)**.

Senkron tüm takipçi güncellemesi yerine sıra-bağımlı takipçi seçimi bilinçli olarak kullanılır ve varyant metninde bildirilir. Arşiv en iyi çözümü, güncel populasyondan kaybolsa bile saklanır. Tek popülasyon dizisindeki lider sırası en iyi salp sırasıyla karıştırılmamalıdır. `ssa_target` lider için eski F, takipçi için yeni öncül konumunu gösterir. Görsel zincir bağlantıları **bu karedeki güncel salp konumları** arasındadır; denklemin bütün katkılarını ayrı seçilebilir panelde inceleyebilirsiniz.

## Denetim ölçümleri

- `ssa_c1` = o jenerasyonda kullanılan kontrol katsayısı; başlangıç karesinde seçilen parametre.
- `ssa_food_position` = güncellemenin referans aldığı F; başlangıçta ilk arşiv değeri.
- `ssa_chain_length` = ardışık salpler arasındaki 2B mesafelerin toplamı (iz/yol mesafesi değildir).
- `ssa_leader_distance` = liderden kayıtlı besin referansına Öklid uzaklığı.
- Salp üzerinde `ssa_previous`, `ssa_target`, `ssa_c2`, `ssa_c3` hareketin hesaplandığı verileri gösterir; c2/c3 takipçide boş olmalıdır.

## Tekrarlanabilirlik ve kapsam

Rastgelelik NumPy `default_rng(seed)` ile sabitlenir. 4 referans fonksiyonu: Sphere, Rastrigin, Ackley, Rosenbrock. Giriş aralığı Pydantic ile doğrulanır; `c1_initial` ∈ [0.25,3.0]. Tam 2D görselleştirme, yüksek boyutlu optimizasyon desteği değildir. Daha ileri istatistikler, yüksek boyut ve eşit NFE karşılaştırmasına dahil edilme sonraki sürümlerin kapsamındadır.
