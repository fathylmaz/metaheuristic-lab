# Diferansiyel Evrim (DE) — matematiksel yöntem ve izlenebilir deneyler

## Kaynak ve varyant

Rainer Storn & Kenneth Price (1997). *Differential Evolution – A Simple and Efficient Heuristic for Global Optimization over Continuous Spaces*. Journal of Global Optimization **11**, 341–359. DOI: [10.1023/A:1008202821328](https://doi.org/10.1023/A:1008202821328).

**Uygulanan varyant:** `DE/rand/1/bin`, **iki boyutlu sürekli minimizasyon**, her nesilde **eşzamanlı** yenileme (tüm donörler aynı dondurulmuş eski popülasyondan), sınır dışına çıkan mutant koordinatlarının kırpılması, eşit uygunluktaki adayın kabulü.

Bu sürümün amacı, bütün DE stratejilerini kapsamak değil; tek bir açıkça tanımlanmış varyantı ölçülebilir ve yeniden üretilebilir biçimde öğretmektir.

## Girdi ve başlangıç

- `population_size` = N, 5–60 (DE/rand/1 için en az 4 gerekir; ortak API sınırı 5'tir).
- `iterations` = T, 1–250.
- `de_mutation_factor` = F, varsayılan **0.75**, kabul edilen 0–2.
- `de_crossover_rate` = CR, varsayılan **0.90**, kabul edilen 0–1.
- `seed` NumPy rastgele sayı üretecini sabitler.
- Amaç: Sphere, Rastrigin, Ackley veya Rosenbrock; her birinin sınırları fonksiyon kataloğundan gelir.

İlk popülasyonda N ayrı nokta sınırlar içinde uniform örneklenir ve N amaç fonksiyonu değerlendirmesi yapılır.

## 1 — Mutasyon

Her hedef `i` için `r1`, `r2`, `r3` indeksleri **birbirinden ve `i`'den farklı** olacak şekilde, aynı eski popülasyondan yerine koymadan seçilir:

```
V_raw = X[r1] + F * (X[r2] - X[r3])
V = clip(V_raw, lower_bound, upper_bound)
```

Ham mutant ile sınırlandırılmış mutant **ayrı** kaydedilir. Kırpma bir varyant tercihidir; sınır işleme tekniği DE literatüründe tek değildir.

## 2 — Binom çaprazlama

İki koordinat için bağımsız `U(0,1)` çekilişi yapılır; ayrıca zorunlu koordinat `jrand ∈ {0,1}` seçilir:

```
mask[j] = (draw[j] < CR) or (j == jrand)
trial[j] = V[j] if mask[j] else X[i,j]
```

`jrand`, CR=0 olsa bile deneme adayının **en az bir koordinatı mutanttan almasını** sağlar. CR=1 olduğunda bütün koordinatlar mutanttan gelir. `de_crossover_draws`, `de_crossover_mask` ve `de_j_rand` kayıt edilir.

## 3 — Seçim ve değerlendirme bütçesi

Her deneme vektörü amaç fonksiyonunda **bir kez** değerlendirilir:

```
new_X[i] = trial   if f(trial) <= f(old_X[i])
           old_X[i] otherwise
```

Reddedilen adaylar da hesaplama bütçesine dahildir. Bütün hedeflerin adayları eski popülasyondan üretildiğinden birbirlerinin aynı nesilde kabul edilen yeni konumlarını kullanmazlar.

Her nesilde N deneme değerlendirilir. Başlangıç N değerlendirmeyle toplam:

```
NFE(T) = N * (T + 1)
```

`best_so_far`, elde tutulan tarihsel en iyi çözüm olarak ayrıca izlenir; `current_best` mevcut neslin en iyisidir. DE'nin bu sürümünde açgözlü seçim nedeniyle mevcut neslin en iyi değeri de kötüleşmez.

## Telemetri

Her ajan `AgentState` içinde aşağıdaki alanları taşır (iterasyon 0'da hareket alanları boş):

- `de_parent`, `de_donors`, `de_donor_positions` (önceki nesilden)
- `de_mutant_raw`, `de_mutant`, `de_trial`, `de_trial_fitness`
- `de_crossover_draws`, `de_crossover_mask`, `de_j_rand`
- `de_accepted`

Her `SimulationFrame` içinde `de_accepted_count`, `de_rejected_count`, `de_forced_crossover_count` ve `function_evaluations` vardır. Jenerasyonun toplam kabul+ret sayısı N'dir.

### Görsel kodlama

Seçilen bireyde çizilen vektörler gerçek kayıtlara dayanır: `r2 → r3` fark doğrusu, `r1 → mutant`, `eski hedef → deneme adayı`. Üç donör halka ile; mutant kare ile; aday ise kabul edilirse yeşil, reddedilirse turuncu ve çarpıyla gösterilir. Çizgiler algoritmanın geometrik hesaplarını açıklar; fiziksel yol veya sürekli zamanda ajan hareketi değildir.

## Denetlenebilirlik ve testler

- Üç donör ile hedef birbirinden farklıdır.
- Mutasyon, sınır kırpma ve çaprazlama formülleri kayıtlı değerlerden tekrar hesaplanır.
- Her deneme adayı yeniden değerlendirilerek kabul/ret sonucu kontrol edilir.
- Sınırlar, deterministik tohum, monotona yakınsama, NFE ve API doğrulaması test edilir.
- CR=0 ve CR=1 uç değerleri de test edilir.

## Sınırlamalar

İki boyutlu eğitim laboratuvarıdır; DE/`best` stratejileri, SHADE/jDE, özuyarlamalı F/CR, N-boyutlu benchmark standardizasyonu ve denk bütçeli genel karşılaştırma adaptörü bu sürüme dahil değildir. Görsel simülasyon, backend hesaplamasının kaydedilmiş karelerini oynatır; WebSocket ile çevrimiçi iterasyon akışı henüz uygulanmamıştır.
