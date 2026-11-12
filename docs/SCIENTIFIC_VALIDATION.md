# Metaheuristic Lab — Bilimsel Doğrulama Protokolü (v2.14.0)

## Hedef

Bu sürüm mevcut **D-boyutlu** optimizasyon deneylerini daha dikkatli incelemek için iki araç sunar:

1. **Bilimsel Doğrulama ekranı:** Arşivdeki bir deneyi değiştirmeden ve yeniden çalıştırmadan sonuç/NFE tutarlılığı denetimi, kaydedilmiş koşu süreleri, keşifsel belirsizlik ve ikili karşılaştırmalar sunar.
2. **Yerel bilimsel profil betiği:** Sphere/Rastrigin/Ackley/Rosenbrock/Griewank × D=2/5/10/30 üzerinde *yeni*, kontrollü ve otomatik tekrarlı deneyler koşturur. Her hücre için NFE, hata, süre ve istatistikleri JSON/Markdown olarak kaydeder; mevcut SQLite arşivine **dokunmaz**.

Her iki araç da eğitim/araştırma amaçlıdır; bağımsız referans algoritma sertifikasyonu değildir.

## Arşiv denetiminin kapsamı

`GET /api/science/dimensional/{experiment_id}` yalnızca mevcut deneyin kayıtlarını okur. Aşağıdakileri kontrol eder:

- Deneydeki algoritmalar, tohum sayısı ve tohum dizisi belirtilen parametrelerle uyumlu mu?
- NFE/koşu tam olarak `popülasyon × (referans iterasyonu + 1)` mi? Kaydedilen toplam NFE doğru mu?
- Her tohum ve algoritma koşusunda kayıtlı NFE tam aynı kontrol noktalarında mı?
- Her yakınsama adımının kayıtlı vektörü D koordinat içeriyor mu? **Aynı amaç fonksiyonu implementasyonunda** yeniden değerlendirildiğinde kaydedilmiş hata ile uyuşuyor mu?
- Arşivdeki tarihsel en iyi hata monoton kötüleşmiyor mu? Son yörünge, nihai sonuçla tutarlı mı?
- Ortalama, örneklem std, başarı oranı, ortalama süre ve grup yakınsama ortalaması ham tekrarları yansıtıyor mu?
- Kaydedilmiş süreler pozitif/sonlu, ilk başarı NFE bilgisi geçerli aralıkta mı?

Denetimde sorun varsa `status=attention` ve açıklayıcı `issues` alanı döner; bilimsel olarak sorunlu kayıt **sessizce başarılı sayılmaz**. Bu API arşivi güncellemez veya başka tabloya veri yazmaz. **Amaç fonksiyonu uyum kontrolünün aynı kaynak implementasyonunu kullanması** bağımsız bir bilimsel doğrulama değildir; bundan ayrı olarak testlerde analitik olarak bilinen optimum ve referans noktaları kontrol edilir.

## İstatistiksel ve zaman ölçümü kuralları

- Başarı: `best_error <= success_tolerance`; optimumdan mutlak hata kullanılır.
- Aralık: Algoritma/deney hücresinin örneklem ortalaması için deterministik, 4096 tekrar örneklemeli **%95 yüzdecil bootstrap**. Küçük örneklemlerde kapsama zayıf olabilir.
- İkili karşılaştırmalar: Aynı **tohum etiketleri** üzerinden tam iki taraflı işaret testi, Holm düzeltmesi; etki ölçüsü eşleştirilmiş medyan `log10(error_A/error_B)`. Farklı algoritmalar eş başlangıç popülasyonu kullanmayabilir.
- Performans: Kaydedilmiş algoritma koşusu süresi (ms) üzerinden **medyan**, örneklem **p95** (doğrusal yüzdecil enterpolasyon), ortalama süre ve açıklayıcı `NFE/s`. Bu ölçümler API/Nginx/React, disk arşivleme, ağ ve grafik maliyetini kapsamaz.
- Çalışma süreleri CPU, diğer işlemler, Python/NumPy sürümü, donanım, ısınma ve sistem yükünden etkilenir. Makineler arası doğrudan kıyas veya kesin performans vaadi yapılmaz. Aynı donanımda dahi bir profil önce/sonra kontrolü ve tutarlı yük gerektirir.
- NFE eşitliği gerçek zaman eşitliği değildir; bazı algoritmalar (`FA`, `GSA`, `SA`, `IWO`) farklı iç karmaşıklıklara sahiptir.
- **Tek bir Sphere/Rastrigin deneyi üstünlük kanıtı değildir.** CEC/COCO gibi dış benchmark setleri, bağımsız uygulama karşılaştırmaları ve çok problemli istatistikler hâlâ kapsam dışıdır.

## Daha fazla tekrar: 2–20

Yüksek Boyut Laboratuvarı ve **Deney Kuyruğu > Yüksek boyut** deneyleri en fazla **20 bağımsız tekrarı** kabul eder. Önceki 8 tekrarlı deneyler aynen açılır. **Toplam 160.000 NFE** güvenlik sınırı değişmez. Örneğin 3 algoritma × 10 tekrar × 24 popülasyon × (90+1) = **65.520 NFE**. Parametre limiti aşıldığında API `422` yanıt verir.

> Bu değişiklik yalnızca yüksek boyutlu deneyler için geçerlidir. 2B benchmark ve OFAT gibi diğer laboratuvarların eski sınırları korunur.

## Yerel tekrarlı profil

Proje kökünden Windows PowerShell'de:

```powershell
py -3.13 .\scripts\scientific_profile.py --algorithms pso gwo de --objectives sphere rastrigin --dimensions 2 5 10 --population 16 --iterations 30 --trials 10 --seed 42 --output-dir .\outputs\profile-v214
```

Bu plan toplam `2 fonksiyon × 3 boyut × 3 algoritma × 10 tohum × 16 × 31 = 89.280 NFE` yürütür (hücre başına 14.880 NFE). Betik algoritma bazında hataları fonksiyonlar arasında **birleştirmez**. Çıktılar:

- `outputs/profile-v214/scientific-profile.json` — yöntem, motor SHA-256, Python/NumPy/platform sürümü, hücre bazlı istatistikler
- `outputs/profile-v214/scientific-profile.md` — GitHub/akademik rapora eklenebilen tablo

Çıktı yolunda aynı isimli dosyalar varsa betik bunların üzerine yazmaz. Bir sonraki deneyde farklı `--output-dir` kullanın. Profil betiği **backend/data içindeki SQLite arşivini okumaz veya değiştirmez**; karşılaştırma yapmak istediğiniz çıktıları ayrıca saklayın. Saat ve NFE değerleri her seferinde gerçek çalıştırmadan elde edilir.

## Tekrarlanabilirlik ve tasarım sınırlamaları

- Motor kodunun SHA-256 özeti saklanır; ancak tüm bağımlılıkların kilitli sürümlerini veya makine koşullarını tek başına kanıtlamaz.
- Aynı tohum kullanımı aynı uygulama/sayısal ortamda deterministik tekrar için kullanılır; platformlar arası bit düzeyinde eşitlik garanti edilmez.
- Checkpoint'ten yeniden kullanılan koşuların `duration_ms` alanı ilk çalıştırıldığı ortamın ölçümüdür; toparlanma süresini göstermez.
- Bu sürüm düşük hata ile düşük süreyi tek bir özet puana **indirgemez**: amaç değeri ve hesaplama maliyeti iki farklı ölçüdür.
- ACO simetrik ayrık TSP çözer ve bu sürekli D-boyutlu doğrulamaya dahil edilmez.

## Otomatik doğrulama ve CI

Backend: `python -m pytest -q`. `test_scientific_v214.py` 14 optimizasyon yöntemi için arşiv denetimlerini; beş amaç fonksiyonunun analitik optimum/referans değerlerini; bozuk kayıt, NFE, vektör, yakınsama, süre ve 20-tekrar sınırlarını; API okuma güvenliğini; profil JSON/Markdown üretimini içerir.

Frontend: `npm.cmd run build` ve `npm.cmd run test:e2e`. Playwright yeni bilimsel doğrulama ekranından gerçek kayıt açıp endpoint sonucunu kontrol eder. Windows Rollup WASM çözümü `frontend/ROLLUP_WASM_WINDOWS.md` dosyasındadır.

Docker: `powershell -ExecutionPolicy Bypass -File .\scripts\verify_docker_windows.ps1`. Bu yerel doğrulamadan önce port çakışmalarını önlemek için çalışan Vite ve Uvicorn sunucularını kapatın.
