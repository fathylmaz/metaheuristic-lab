# CS / Cuckoo Search — uygulama metodolojisi (v0.7.0)

## Problem ve araştırma temeli

Guguk Kuşu Arama (CS), Yang ve Deb'in 2009 tarihli Lévy uçuşlarına dayanan sürekli optimizasyon yaklaşımından esinlenir. Uygulamada her nokta bir **ev sahibi yuva / aday çözüm**dür; kuşları biyolojik olarak simüle ettiğimiz iddia edilmez. 2B Sphere, Rastrigin, Ackley ve Rosenbrock minimizasyonu yapılır. Boyut sayısı 2 ile sınırlıdır. Referans: X.-S. Yang, S. Deb, *Cuckoo Search via Lévy Flights*, NaBIC 2009, DOI: https://doi.org/10.1109/NABIC.2009.5393690 ; https://repository.mdx.ac.uk/item/83wv2

## Açık biçimde tanımlanan varyant

Uygulama özgün pseudocode ile uyumlu temel kuralları kullanır ancak birebir tüm CS varyantlarının aynısı değildir.

1. `N` yuvanın koordinatlarını `numpy.random.default_rng(seed)` ile uniform üret; her biri için amaç fonksiyonunu değerlendir (`N` adet NFE).
2. Her jenerasyonda `N` adet Lévy uçuşu öner. Her öneride rastgele *kaynak yuva* ve rastgele *ev sahibi yuva* seç. Aday, seçilen kaynaktan hesaplanır; amaç fonksiyonu bir kez değerlendirilir. Adayın değeri ev sahibi yuvasından daha iyiyse o ev sahibinin konumu güncellenir. Eşit/değersiz adaylar reddedilir.
3. Her jenerasyonda en kötü `k=min(N−1, floor(p_a N + 0.5))` yuva, o anki en iyi yuvayı koruyarak uniform yeni koordinatlarla değiştirilir. **Bu, olasılık yerine sabit oranlı yeniden başlatma varyantıdır**; algoritmadaki keşif parametresi `p_a` buna göre yorumlanır.
4. Nesil boyunca değerlendirilen en iyi kayıt ayrı arşivde saklanır; kök en iyi değer zamanla asla kötüleşmez. Rastgele yeniden oluşturulan bir yuva daha iyi bulunursa arşiv de güncellenir.

## Lévy uçuşu ve adım büyüklüğü

Mantegna örneklemesi ile `L = u/|v|^(1/β)`; `u ∼ N(0,σ_u²)`, `v ∼ N(0,1)` ve

`σ_u = [ Γ(1+β) sin(πβ/2) / ( Γ((1+β)/2) β 2^((β−1)/2) ) ]^(1/β)`.

Aday konumu şu **projeye özel yön ve ölçek varyantı** ile oluşturulur:

`x_new = clip(x_source + s * L ⊙ (x_source - x_best + 0.02 * (upper-lower) * ξ), bounds)`

Burada `ξ` standart normal, `s` kullanıcıya açık *Lévy adım ölçeği*, `x_best` en iyi arşiv konumu, `⊙` bileşen bazlı çarpımdır. Sınırları aşan koordinatlar kırpılır. Bu seçim, en iyi yuvada da keşif yapılabilmesi için ufak rassal terim ekler.

## NFE ve telemetri

- İlk kare NFE = `N`.
- Her jenerasyonda tam `N` Lévy yumurtası değerlendirilir (reddedilenler dahildir).
- Her jenerasyonda `k` tane yeniden başlatma değerlendirilir (iyileşmese dahi dahil).
- `NFE(T)=N+T·(N+k)`; örneğin `N=24`, `p_a=0.25`, `T=90` → `NFE=2724`.
- Her karede `accepted_levy_this_iteration`, `abandoned_this_iteration` gerçek olay sayılarını verir.
- `move_kind`, yuvanın o jenerasyondaki **son başarılı değişikliğini** veya yeniden başlatılmasını bildirir. `proposed_flight_length` ilgili yuvaya son önerilen uçuş vektörünün kırpma öncesi büyüklüğüdür; başarılı olmasa da görülebilir.
- Arayüzdeki çizgiler önceki ve yeni **kabul edilmiş yuva konumlarını** bağlar; reddedilmiş adaylar animasyona hareket olarak yansıtılmaz.
- Renkler: mor = korundu/reddedildi, turuncu = kabul edilmiş Lévy uçuşu, yeşil = yenilenen yuva.

## Karşılaştırma kısıtı

`POST /api/comparisons` yalnızca FA/PSO/ABC için eşit NFE kesme mantığına sahiptir. **CS henüz bu laboratuvarda seçilemez**; CS'yi eklemek için gerçek değerlendirme bütçesinde durdurulan bir algoritma adaptörü geliştirmek gerekir. ACO ise ayrı ayrık TSP sınıfıdır.

## Doğrulama

`backend/tests/test_cuckoo.py`: sabit tohum, ajan koordinatları, fonksiyon değerlerinin yeniden hesaplanması, gerçek NFE, terk sayısı, parametre sınırları, arşiv monotonluğu ve API doğrulamaları.
