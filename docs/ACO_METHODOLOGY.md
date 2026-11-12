# ACO / Ant System — Matematiksel Tasarım

## Problem tanımı

Bu çalışma **simetrik Öklidyen Gezgin Satıcı Problemi** (TSP) çözer. N şehir, birim karede `(x,y)` ile tanımlanır; her karınca her şehri tam bir kere ziyaret eden bir permütasyon kurar ve son şehirden başlangıç şehrine dönerek **kapalı Hamilton turu** oluşturur. Amaç tüm kenar uzunluklarının toplamını azaltmaktır:

`L(π) = Σ_{k=0..N-1} d(π[k],π[(k+1) mod N])`.

Şehir koordinatlarının tohumu `city_seed`, algoritmadaki rastgele örneklemelerin tohumu `seed` olarak birbirinden ayrılmıştır. `circle` yerleşimi sabit yarıçaplıdır ve `city_seed` değerinden etkilenmez.

## Standart Ant System (AS)

### Tur kurma

Karınca bir başlangıç şehri seçer. Her adımda yalnızca henüz ziyaret edilmemiş komşu şehirler adaydır. `i` şehrinden `j` şehrine gitme olasılığı:

`P(i,j) = (τ[i,j]^α · η[i,j]^β) / Σ_{k in unvisited} (τ[i,k]^α · η[i,k]^β)`, `η[i,j] = 1/d(i,j)`.

Sıfıra çok yakın mesafeler için sayısal koruma kullanılır; olasılıklar log-ağırlıklardan log-sum-exp benzeri stabil bir normalizasyonla hesaplanır.

### Feromon güncellemesi

Tüm karıncalar turlarını **tamamladıktan sonra**, feromon şu şekilde güncellenir:

`τ[i,j] ← (1−ρ) τ[i,j] + Σ_{k: edge(i,j) in tour(k)} Q/L_k`.

Kenarlara her iki yönde aynı miktar yatırılır (simetrik problem). Köşegen sıfırdır. Başlangıçta diğer kenarlarda `τ=1`. `ρ` buharlaşma oranıdır, `Q` birikim katsayısıdır. 2-opt veya elitist ek bir iyileştirme yapılmaz.

### Ölçütler

Her oluşturulan tam tur **bir tur değerlendirmesi** sayılır: `tours_evaluated = ant_count × iteration`. Küresel en iyi tur/uzunluk tüm önceki turlardan bir arşivdir ve artmaz. `iteration_best` ve `mean_length` yalnızca mevcut döngünün turlarındandır. `unique_tours` rotasyon ve ters yön eşdeğerliği giderilerek sayılır. Tüm karıncaların turları ve feromon matrisi her döngü için saklanır.

### Neler yapılmıyor?

- Bu sürüm TSPLIB örnekleri, 2-opt, Ant Colony System (ACS), MAX-MIN Ant System (MMAS) veya başlangıç sıcaklığı gibi parametreler içermez.
- Gerçek zamanlı akış yerine sunucuda hesaplanan kareler istemciye topluca gönderilir.
- Sürekli optimizasyon yöntemleri FA/PSO/ABC ile performans karşılaştırması yapılmaz; TSP farklı bir problemdir.
- Haritadaki çizgiler feromon ağı, seçilen karınca turu ve global arşiv turunu gösterir; karıncanın tek tek şehir seçme **adımları** değil, her tam döngüdeki tamamlanmış turlar görselleştirilir.

## Kaynaklar

Dorigo, M., Maniezzo, V., & Colorni, A. (1996). *Ant System: Optimization by a Colony of Cooperating Agents*. IEEE Transactions on Systems, Man, and Cybernetics — Part B.

Dorigo, M., & Stützle, T. (2004). *Ant Colony Optimization*. MIT Press.
