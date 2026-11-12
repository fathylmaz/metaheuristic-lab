# Metaheuristic Lab v2.12.0 — Görev Geçmişi ve Dayanıklılık

## Kapsam

v2.11.0'ın 15 algoritmalı 2D simülasyonları, 14 sürekli yüksek boyutlu çözümleyicisi, bilimsel raporları, Docker Compose ortamı ve üç kuyruk deney türü korunur. Yalnızca görev yönetimine ve sürüm göstergelerine ekleme yapılır.

- Yeni SQLite `background_job_events` tablosu: olayları tarih ve ilerleme ile saklar.
- `attempts`, `restart_count`, `last_recovered_at`, `retry_of`: geçmişteki işlerin nasıl yürütüldüğünü gösterir. Eski veritabanları otomatik ve geriye uyumlu şekilde yükseltilir.
- Kesintiye uğrayan `running` iş, tamamlanmış koşuların ilerlemesi sıfırlanarak kuyrukta tekrar başlatılır. **Tamamlanan trial sonuçları ayrı kaydedilmediği için hesaplama tüm tohumlarda baştan yürür.**
- Başarısız ve iptal edilmiş işleri yeni bir kimlikle yeniden deneme, eski sonucu ve olayları koruma.
- Tamamlanan/iptal edilmiş/başarısız görevi kuyruk geçmişinden kaldırma. **Arşive yazılmış bilimsel deney sonucu silinmez.**
- Başarılı sonuç, işin terminal durumu ve son olay aynı SQLite transaction içinde yazılır.
- Deney Kuyruğu arayüzünde durum filtresi, olay akışı, kurtarma açıklaması, yeniden deneme ve onaylı silme.

## API eklemeleri

| İşlem | Rota | Yanıt |
|---|---|---|
| Olayları getir | `GET /api/jobs/{id}/events` | 200, `{ "events": [...] }` |
| İptal/başarısız işi tekrar dene | `POST /api/jobs/{id}/retry` | 202 yeni görev; 409 yanlış durum; 429 kapasite dolu |
| Yalnız görev geçmişini kaldır | `DELETE /api/jobs/{id}` | 204; 409 aktif iş; 404 eksik kayıt |

## Kurulum

ZIP'in kökünde `metaheuristic-lab/` klasörü bulunur. `.git`, `.venv`, `node_modules`, `.sqlite3`, yerel loglar veya kullanıcı deney verisi dahil değildir. Çalışan API ve web sunucularını durdurduktan sonra:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v2.12.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd run build
npm.cmd run test:e2e
```

Windows uygulama denetimi Rollup'ın yerel `.node` dosyasını engellerse, önceki v2.11.0 hotfix'i bu pakete dahildir: `frontend/ROLLUP_WASM_WINDOWS.md` ve `scripts/repair_rollup_wasm_windows.ps1`.

## Sınırlar

- Bu yerel, tek API işçili araştırma uygulamasıdır; kimlik doğrulama, uzaktan çok kullanıcılı erişim, oran sınırlandırma, dağıtık işçi havuzu veya ara deneme checkpoint'i içermez.
- İptal bir algoritma–tohum koşusunun bitiminde uygulanır, anında uygulanmaz.
- Görev geçmişini silmek deney sonucunu silmez; eski `GET /api/jobs/{id}` artık 404 döner, fakat arşiv raporu orijinal ID ile açılabilir.
- Doğrulanmış backend testleri yerel Python ortamında çalıştırıldı; frontend Vite/Playwright ve Docker'ın kullanıcı Windows sisteminde ayrıca çalıştırılması gerekir.
