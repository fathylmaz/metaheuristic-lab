# Metaheuristic Lab v2.11.0 — Çok Türlü Bilimsel Deney Kuyruğu

## Yeni

- Yüksek boyutlu optimizasyon yanında **çoklu benchmark (2D)** ve **OFAT parametre duyarlılığı (2D)** için de kalıcı arka plan görevleri.
- Deney Kuyruğu sayfasında tür, algoritma, fonksiyon matrisi veya taranan parametre-değer aralığı seçimi.
- Gerçek bağımsız koşular tamamlandıkça güncellenen, deney türüne göre hesaplanmış ilerleme.
- Her üç türün aynı SQLite kayıtlarında sürdürülmesi, arşivlenmesi ve Akademik Raporlar üzerinden erişilebilirliği.
- `GET /api/jobs/{id}/result` için tür bazlı doğru sonuç modeli.
- Çalışan benchmark/OFAT deneylerinde tohum sınırlarında güvenli iptal; bekleyen işi anında iptal; başarı ve arşivlemenin tek veritabanı işleminde birleştirilmesi.
- Yeni Python regresyon ve Playwright E2E senaryoları.
- Önceki Windows SQLite bağlantı hotfix'i, gezinme testi düzeltmesi ve Docker sağlık sürüm kontrolü korunmuştur.

## Bilimsel kısıtlar

- Her deney `NFE` gerçek fonksiyon değerlendirmesiyle ölçülür. Kuyruk yüzdesi ise **tamamlanan algoritma-tohum koşusunu** sayar; hesaplanan yüzdeler fiziksel CPU süre oranı değildir.
- Benchmark ve OFAT optimizasyonları iki boyutlu, yüksek boyut laboratuvarı 2/5/10/30 boyutludur. Bunlar aynı deney türü değildir.
- SA tek çözümlü, IWO değişken popülasyonlu varyantları korunur. Aynı tohum etiketi ilk popülasyonun özdeş olduğunu kanıtlamaz.
- Parametre duyarlılığı OFAT, parametreler arası etkileşimi test etmez.
- Tek worker, yerel API süreci; internet erişimi için üretim kimlik doğrulaması ve ayrı iş izolasyonu gereklidir.
- Çalışan görev sunucu yeniden başladığında kısmi iterasyondan değil **orijinal tohumdan** yeniden başlar.

## Güncelleme

İki servis çalışıyorsa önce `Ctrl+C` ile durdur veya `docker compose down` uygula. ZIP'i `C:\VS CODE PROJE` içine `Expand-Archive -Force` ile aç. Proje klasörü ZIP içinde bulunur; **yerel SQLite DB, .git, .venv ve node_modules pakette bulunmaz**.

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v2.11.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q

cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd install
npm.cmd run build
npm.cmd run test:e2e
```

Docker için `powershell -ExecutionPolicy Bypass -File .\scripts\verify_docker_windows.ps1`; bu betik sürümü `frontend/package.json` dosyasından okur.

## Test ve sürüm durumu

- Kaynak paketinden **475 backend testi başarılı** (Linux çalışma ortamında).
- **15 TypeScript/TSX kaynağının sözdizimi denetimi başarılı.** Tam Vite production build ve yeni Playwright senaryoları bağımlılıklar erişilemediği için bu ortamda çalıştırılamadı; Windows üzerinde kullanıcı doğrulaması bekleniyor.
- 2 yeni Playwright senaryosu eklendi; mevcut 5 ile birlikte hedef **7/7**.

## Hâlâ yapılacaklar

- Benchmark/sensitivity sonuçları için performans ve bellek profilleri; uzun deneylerde kuyruk bekleme ve iptal sürelerinin gözlemlenmesi.
- Gelişmiş koşu-başı checkpoint/resume; çok worker/çok kullanıcılı sunucu tasarımı; uzaktan erişim güvenliği.
- Sürüm sabitleme ve dağıtımın güvenli yapılandırılması; yayın belgeleri.
