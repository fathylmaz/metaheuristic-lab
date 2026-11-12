# v3.0.0 — Bilimsel Tekrarlanabilirlik Protokolü

## 1. Deney amacını ve kapsamını önceden belirle

- Karşılaştırılacak algoritmaları ve **aynı amaç fonksiyonunu** seç.
- Yüksek boyut için D = 2/5/10/30; Sphere, Rastrigin, Ackley, Rosenbrock veya Griewank seç.
- Eşit NFE bütçesi, tekrar sayısı, başlangıç tohumu ve başarı eşiğini kaydet.
- ACO'yu sürekli D-boyutlu sorunlarla aynı sıralama tablosuna koyma; ACO ayrık TSP çözer.

## 2. Kontrol edilen bütçe

D-boyutlu deneylerde kullanıcı tanımlı referans bütçe `NFE/koşu = population_size × (iterations + 1)` şeklindedir. **ABC/CS/IWO/SA** gibi yöntemlerde bu bütçe ortak kayıt noktasıdır; bir algoritmanın gerçek nesil sayısı değildir. Eşit NFE, eşit çalışma süresi veya karşılaştırılabilir algoritmik iç karmaşıklık garantisi değildir.

## 3. Deneyin yeniden üretilebilir verilerini sakla

Asgari arşiv bilgileri: algoritma kimliği, amaç fonksiyonu, D, popülasyon, referans iterasyonu, tüm etkin parametreler, `seed_start`, tekrarlar, başarı eşiği, uygulama sürümü ve ortam bilgisi. Her tekrardan nihai hata, tam D-boyutlu en iyi vektör, gerçek NFE, yakınsama izi ve (varsa) ölçülmüş koşu süresi saklanır.

**Tohum etiketleri:** 42, 43, ... yalnızca algoritma içi tekrarlanabilirliği kontrol eder; farklı algoritmalarda bit düzeyinde aynı RNG akışı veya aynı ilk popülasyon anlamına gelmez.

## 4. Kaydı denetle

`Bilimsel Doğrulama` ekranında kaydı seç; NFE, amaç fonksiyonu, vektör boyutu, yakınsama monotoniği ve özet istatistiklerin tutarlılığını incele. `status=attention` durumunu raporda açıkça belirt; bozuk kaydı geçerli sonuç gibi kullanma.

**Bağımsız referans doğrulaması değildir:** uygulama kaydı aynı amaç fonksiyonu implementasyonuyla yeniden değerlendirir; bu yalnızca iç tutarlılık sınamasıdır.

## 5. İstatistiksel raporlama

- Ortalama ve medyan mutlak hata, örneklem standart sapması, başarı oranı ve yakınsama eğrisi ayrı yorumlanır.
- %95 keşifsel yüzdecil bootstrap örneklem aralığı ve eşleştirilmiş tam işaret testi/uygun karşılaştırma testleriyle Holm düzeltmesi kullanılır.
- Küçük örneklemde (özellikle 2–3 tekrar) p değerlerini kesin üstünlük kanıtı sayma. Tohum eşleşmesi aynı ilk durum anlamına gelmez.
- Başarı eşiğini değiştirmek sonuçları ve başarı oranını etkiler; eşiği raporda belirt.

## 6. Performans

Algoritma başına medyan/p95 süre, NFE/s ve hata **ayrı ölçülerdir**. Süreler çalışılan makineye bağımlıdır ve HTTP, disk kaydı, Nginx, tarayıcı ve çizim süresini içermeyebilir. Donanım, Python/NumPy sürümü ve eş zamanlı sistem yükünü not et. Bir makinedeki değerleri başka makineyle doğrudan kıyaslama.

## 7. Örnek profil komutu

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab"
py -3.13 .\scripts\scientific_profile.py --algorithms pso gwo de --objectives sphere rastrigin --dimensions 2 5 10 --population 16 --iterations 30 --trials 10 --seed 42 --output-dir .\outputs\profile-v300
```

Bu komut **2 fonksiyon × 3 boyut × 3 algoritma × 10 tekrar × 16 × 31 = 89.280 NFE** değerlendirir. Profil, çıktıları `outputs/` altına JSON/Markdown olarak yazar; var olan SQLite arşivine dokunmaz. Benzersiz `--output-dir` kullan.

## 8. Yayınlanabilir kanıt

- `backend/tests` ve Playwright logları, CI işlerinin sonucunu gösteren gerçek ekran görüntüsü veya iş bağlantısı.
- Gerçek deney kimliği, parametreler, tohumlar, NFE, ortam ve bilinmeyenleri açıkça belirten JSON/Markdown raporu.
- Gerçek uygulama ekran görüntüleri, kişisel yerel arşivlerin ayıklanması sonrası.

**Ek araştırma gerektiğinde:** CEC/COCO veya bağımsız referans kütüphaneler ile model eşdeğerliğini sınamak, daha çok fonksiyonda çoklu problem istatistikleri ve çok çekirdekli/dağıtık deneyler bu finalin kapsamı dışındadır.
