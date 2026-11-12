# GSA — Yerçekimsel Arama Algoritması / Matematiksel Yöntem

**Sürüm:** 1.6.0 · 2B sürekli minimizasyon · ayrık TSP algoritması ACO'dan ayrıdır.

## Referans

E. Rashedi, H. Nezamabadi-pour, S. Saryazdi, **GSA: A Gravitational Search Algorithm**, *Information Sciences* **179** (2009), 2232–2248. DOI: [10.1016/j.ins.2009.03.004](https://doi.org/10.1016/j.ins.2009.03.004).

> GSA, Newton'dan esinlenen **meta-sezgisel** bir optimizasyon modelidir; birebir fiziksel evren simülasyonu değildir. Özellikle standart GSA'daki `distance + epsilon` paydası Newton'un `distance²` biçimiyle aynı değildir. Arayüzdeki çekim çizgileri ve hareketler algoritmanın verilerini temsil eder.

## Parametreler

- `population_size` N: 5–60 ajan; başlangıç N ajanın uygunluğu birer kez değerlendirilir.
- `iterations` T: 1–250. Her iterasyonda N yeni konum bir kez değerlendirilir.
- `gsa_initial_gravity` G0: varsayılan **100.0**, >0–500.
- `gsa_decay` alpha: varsayılan **20.0**, 0–40.
- `gsa_epsilon`: varsayılan **0.01**, 1e-6–1; küçük mesafelerin sayısal stabilitesi.
- `seed`: NumPy `default_rng` için sabit tohum; tam hesap/telemetri tekrarlanabilir.

## 1. Uygunluk ve kütle

Minimizasyon için her nesilde en iyi/kötü `best=min(f)` ve `worst=max(f)`:

```
m_i(t) = (worst(t) - f_i(t)) / (worst(t) - best(t))
M_i(t) = m_i(t) / Σ_k m_k(t)
```

Tüm uygunluklar aynıysa tüm kütleler `1/N` olur. Bu özel durum rastgele sıralama veya sıfıra bölme üretmez. Kütleler [0,1] aralığında olup toplamları 1'dir. Kuvvetin ve ataletsel hareketin hesaplandığı kütleler **önceki popülasyon** üzerinden dondurulur; karedeki `gsa_mass` yeni popülasyona ait olup önceki kütle `gsa_force_mass` alanına kaydedilir.

## 2. Yerçekimi katsayısı ve elit çekim kaynakları

```
G(t) = G0 · exp(-alpha · t / T)
Kbest(t) = max(1, ceil(N - (N-1) · t/T))
```

İlk kare `t=0` N aktif kaynak, son kare `t=T` bir aktif kaynak gösterir. Bir ajanın kendisi çekim kaynağı olarak seçilmez; en büyük kütleli ajan tek elit olduğunda kuvveti sıfır olabilir. Bu GSA için normaldir. Kbest, önceki nesildeki en ağır ajanların indeksleridir.

## 3. Hareket

Ajan `i` üzerindeki ajan `j` kaynaklı kuvvet (iki eksende):

```
F_ij(t) = G(t) · M_i(t) · M_j(t) · (x_j(t) - x_i(t)) / (||x_j(t)-x_i(t)||₂ + epsilon)
F_i(t)  = Σ_{j ∈ Kbest, j ≠ i} U_ij ⊙ F_ij(t)
a_i(t)  = F_i(t) / max(M_i(t), 10^-12)
v_i(t+1) = U_i ⊙ v_i(t) + a_i(t)
x_i(t+1) = clip(x_i(t) + v_i(t+1), lower, upper)
```

`U_ij` ve `U_i` birbirinden bağımsız **iki koordinatlı** U[0,1) rastgele örnekleridir. Kütlenin sıfır olduğu durumda hem kaynak kuvvet hem net kuvvet sıfır olacağı için ivme sıfır hesaplanır. Bütün ajanlar eşzamanlı olarak eski nesildeki kuvvet/mass değerleriyle güncellenir.

Sınırı aşan koordinat için konum sınırda tutulur, ilgili hız bileşeni sıfırlanır. Bu **eğitim amaçlı açık bir sınır yönetimi tercihidir**, tüm GSA kütüphaneleriyle birebir aynı davranış olmak zorunda değildir.

## 4. Animasyonun açıklaması

- Nokta yarıçapı güncel **normalize kütle** ile artar.
- Seçilen ajanın eski konumundan çizilen kesik mavi çizgi, o adımda **en büyük rastgele ağırlıklı tek çekim katkısını** yapan kaynağın **eski** konumuna gider. Bu, bütün net kuvvetin tek kaynak tarafından uygulandığı anlamına gelmez.
- Turuncu ok, net kuvvetin **yönünü** gösterir; okun uzunluğu okunabilirlik için logaritmik olarak ölçeklenir. Ölçek, fiziksel uzaklık veya mutlak kuvvet büyüklüğü değildir.
- `gsa_force`, `gsa_acceleration`, `gsa_previous`, `gsa_previous_velocity`, `gsa_velocity_draw`, `vx/vy` alanları seçilen ajanın bütün konum güncellemesini yeniden hesaplamaya yeterlidir.
- `gsa_gravity`, `gsa_kbest`, `gsa_max_mass`, `gsa_mean_acceleration` her jenerasyonda ayrıca gösterilir.

## 5. Doğrulama ve sınırlar

- Fonksiyon değerlendirme bütçesi: `NFE = N × (T + 1)`.
- Ajanların güncel konumu ve amaç değeri, arşiv en iyi ve popülasyon ortalaması ayrı veridir.
- Aynı seed + parametre, UUID ve ölçülen süre dışında aynı kareleri üretir.
- `backend/tests/test_gsa.py`: kütle normalizasyonu, kuvvetin elle kontrolü, ivme/hız/konumun geri hesaplanması, NFE, sınırlar, katalog/API ve geçersiz parametreler.
- GSA gerçek bilimsel fizik doğrulaması olarak sunulmaz; önceki SA ve sonraki DE dahil sürekli optimizasyon metotlarıyla adil karşılaştırma için ayrıca ortak NFE bütçesi uygulanmalıdır.
