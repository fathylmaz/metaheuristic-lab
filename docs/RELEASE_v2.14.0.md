# Metaheuristic Lab v2.14.0 — Bilimsel doğrulama ve performans analizi

**v2.13.0'dan veri kaybı olmadan güncelleme**: eski SQLite arşiv tabloları değişmez. Yeni API yalnızca kayıtlı deneyleri okur; performans profil betiği ise yeni deneyler koşturur fakat arşive yazmaz.

## Yeni

- **Bilimsel Doğrulama** arayüz sekmesi: kayıtlı yüksek boyut deneylerini okuyup vektör-NFE-yakınsama, grup istatistikleri ve başarı kayıtlarını denetler; sorunlu kayıtlara `attention` verir.
- Kaydedilen koşu sürelerinden medyan, p95 ve NFE/s; deney sonucundan keşifsel bootstrap %95 aralıkları, tam işaret testleri, Holm düzeltmesi ve eşleştirilmiş log10 hata oranı.
- `GET /api/science/dimensional/{id}` — geriye dönük uyumlu, salt okunur JSON API; UI'den JSON indirme.
- Yüksek boyutlu deneylerde **2–20 tekrar**; 160.000 NFE üst sınırı korunur.
- `scripts/scientific_profile.py` — 2/5/10/30D × beş fonksiyon için yerel, hücre bazlı JSON ve Markdown performans profili. Aynı hedef klasörde kayıt varsa üzerine yazmaz.
- Gerçek değerleri sorgulayan yeni otomatik testler ve bir Playwright senaryosu.

## Doğrulama kapsamı

Bu analiz, **algoritmaların matematiksel olarak doğru referans uygulamalar olduğunu ispat etmez** ve başka makinede aynı çalışma süresini vaat etmez. Amaç fonksiyonunun referans kontrolü, kayıtlı sonuçların kontrolünden ayrı matematiksel testlerde değerlendirilir. Üç veya daha az tekrarlı sonuçlar kesin istatistiksel üstünlük kanıtı olarak kullanılamaz. Geliştirme ayrıntıları: [`SCIENTIFIC_VALIDATION.md`](SCIENTIFIC_VALIDATION.md).

## Yükleme

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab"
py -3.13 .\scripts\backup_experiments.py
docker compose down
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v2.14.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
```

ZIP `.git`, `.venv`, `node_modules`, SQLite arşivlerini veya çalışma/CSV çıktılarını taşımaz. Güncelleme üstüne yazma şeklindedir; el ile düzenlediğiniz kaynaklar varsa önceden yedekleyin.

## Windows doğrulama

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd install
npm.cmd run build
npm.cmd run test:e2e
cd "C:\VS CODE PROJE\metaheuristic-lab"
powershell -ExecutionPolicy Bypass -File .\scripts\verify_docker_windows.ps1
```

**Önerilen kullanıcı deneyi:** Deney Kuyruğu > Yüksek Boyut, PSO + GWO + DE, Sphere, 5D, 16 popülasyon, 30 iterasyon, 10 tekrar, seed=42. Tamamlandıktan sonra **Bilimsel Doğrulama** sekmesinden en son kaydı aç; `status=passed`, her algoritmada 10 tekrar ve koşu başına 496 NFE beklenir. `160.000 NFE` sınırı aşılmamalı. JSON çıktısını indir.
