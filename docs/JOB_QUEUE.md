# Metaheuristic Lab — Kalıcı deney kuyruğu (v2.13.0)

## Kapsam

Tek worker'lı, SQLite kalıcılığını kullanan yerel görev kuyruğu aşağıdaki **üç** bilimsel deney türünü destekler:

| Tür | İstek | Arşiv | İlerleme birimi |
|---|---|---|---|
| `dimensional` | `DimensionalRequest` | `/api/dimensional/{id}` | algoritma × tohum |
| `benchmark` | `BenchmarkSuiteRequest` | `/api/benchmarks/{id}` | amaç fonksiyonu × algoritma × tohum |
| `sensitivity` | `SensitivityRequest` | `/api/sensitivity/{id}` | parametre değeri × tohum |

Algoritmaların matematiksel yürütmesi değişmez: senkron deney uç noktaları korunur. Kuyruk API'si bir iş için önce **202 Accepted** döndürür. Değerlendirmeler arka planda yapılır. İş sonucunun arşivlenmesi ve `completed` durumuna geçmesi **aynı SQLite işleminde** gerçekleşir.

## API sözleşmeleri

- `POST /api/jobs/dimensional` — yüksek boyutlu deney ekle
- `POST /api/jobs/benchmark` — çoklu benchmark ekle
- `POST /api/jobs/sensitivity` — OFAT duyarlılık analizi ekle
- `GET /api/jobs` — son 30 görevi listele; `kind`, `state`, `completed_units`, `total_units`, `progress_percent` içerir
- `GET /api/jobs/{id}` — tek bir görevi kontrol et
- `POST /api/jobs/{id}/cancel` — bekleyen görevi anında, çalışanı **koşular arasında** iptal et
- `GET /api/jobs/{id}/result` — yalnızca `completed` için ilgili türün sonuç modeli; aksi halde HTTP 409

Tamamlanan deneyler uygun akademik rapor uç noktalarıyla raporlanır: `/api/reports/{kind}/{id}?format=html|json|md`. Buradaki `kind`, `dimensional`, `benchmark` veya `sensitivity` değeridir.

## İlerleme ve iptal semantiği

`total_units`, deneyde planlanan **bağımsız koşu sayısıdır**; fonksiyon değerlendirmesi veya iç algoritma iterasyonu değildir. NFE hesabı her deney modelinin `total_evaluations` alanında ayrıca korunur. Yüzde, yalnızca bir koşu başarıyla hesaplandığında ilerler. Çalışan koşuyu kesintiye uğratıp ara popülasyonu kaydetmez.

Durumlar: `queued → running → completed`, `queued → cancelled`, `running → cancelling → cancelled`, `running → failed`.

Worker durdurulur veya API konteyneri yeniden başlatılırsa tamamlanmış **bağımsız koşu** checkpoint'leri doğrulanarak yeniden kullanılır; yalnızca eksik koşular hesaplanır. Koşu ortasında kesinti olursa **o koşu baştan çalıştırılır**. Arşiv sonuçları saklanır. Bozuk/uyumsuz checkpoint halinde iş `failed` olur, diğer işler devam eder. Ayrıntı: `docs/CHECKPOINT_METHODOLOGY.md`.

## Sınırlar ve güvenlik

- **Bir** API/worker süreci; aynı SQLite verisini kullanan birden çok worker veya konteyner desteklenmez.
- Aynı anda en fazla **8 aktif iş**; her deney türünün Pydantic doğrulaması ve NFE sınırları geçerlidir.
- Sadece **localhost**. Kimlik doğrulama, yetkilendirme, rate-limit ve çalışan işlere kaynak izolasyonu olmadan internete açılmamalıdır.
- Düzleştirilmiş/projeksiyon grafikleri D-boyutlu optimizasyonun tüm uzayı değildir; istatistiksel raporlar sınırlı tohum/problemler için keşifsel sonuçlardır.
- İş durumu SQLite `background_jobs`, sonuçlar `dimensional_experiments`, `benchmark_suites`, `sensitivity_studies` tablolarına kaydedilir.
- ZIP güncellemesi bu SQLite veritabanını, `.git`, `.venv` veya `node_modules` klasörlerini içermez; kaynak kodda kişisel değişiklik varsa güncellemeden önce yedek alınmalıdır.

## Yerel doğrulama

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q

cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd install
npm.cmd run build
npm.cmd run test:e2e
```

Ek regresyon testleri `backend/tests/test_job_queue_extended.py` içinde bulunur: canlı iptal, hata yalıtımı, sürüm geçişi, eski arşive yazma ve API yanıtları.


## v2.12.0 — Olay kayıtları ve geçmiş yönetimi

Yeni veri alanları: `attempts` (çalıştırılma sayısı), `restart_count` (kesinti sonrası otomatik yeniden kuyruğa alma sayısı), `last_recovered_at`, `retry_of` (yeniden denenen orijinal iş). Eski SQLite arşivleri uygulama açılışında `ALTER TABLE` ile yükseltilir.

- `GET /api/jobs/{id}/events`: son 80 olay, eski kayıtlarda boş olabilir. Bir koşu bittiğinde ilerleme olayı yazılır. Sonuç arşivi ve `completed` olayı aynı SQL transaction'da kaydedilir.
- `POST /api/jobs/{id}/retry`: yalnızca `failed`/`cancelled`, sonuç eski işten ayrı ve yeni bir kimlik taşır; yeniden deneme 8 aktif görev sınırına tabidir.
- `DELETE /api/jobs/{id}`: yalnızca `completed`/`failed`/`cancelled` görev metaverisini ve olaylarını siler. `dimensional_experiments`, `benchmark_suites` ve `sensitivity_studies` arşiv tablolarını **değiştirmez**. Sonuçlara doğrudan ilgili arşivden erişilebilir.
- v2.12.0 davranışı: sunucu kesintisi sonrasında görev bütün koşuları tekrarlardı. v2.13.0 bunu **tamamlanmış koşu checkpoint'lerinden güvenli devam** olarak değiştirdi.
- Olay kaydı yalnızca yerel kullanıcı içindir; görevleri güvenilmeyen internete açık hale getirmeyin. Çoklu Uvicorn worker kullanmayın.

## v2.13.0 — Tamamlanmış koşu checkpoint sistemi

- Yeni `background_job_checkpoints` tablosu SQLite kaydına JSON/zlib veri, SHA-256 ve sayısal motor parmak izi ile yazılır.
- `GET /api/jobs/{id}` ve liste uç noktaları `checkpoint_units` (şu anda tutulan ara koşu) ve `reused_units` (bu yürütmede yeniden kullanılan kayıt) alanlarını döndürür.
- Sunucu yeniden başladığında `recovered` olayı kaydedilir; `completed_units` disk üzerindeki **gerçek checkpoint sayısına** göre ayarlanır. Eski v2.12 ilerleme sayacı tek başına checkpoint sayılmaz.
- Yeni çalıştırılan koşu checkpoint'i öncelikle diske yazılır, ardından ilerleme olayı bildirilir. Bağlantı tam bu iki işlem arasında kapanırsa tamamlanan koşu korunur.
- Tamamlanan deneyin sonuç arşivi ile `completed` durumuna geçişi ve gereksiz checkpoint temizliği aynı SQLite transaction içindedir.
- `cancelled`/`failed` işlerde checkpoint'ler hata analizi için tutulur; geçmiş kaydı silinirse checkpoint'ler de kaldırılır, akademik arşiv ise korunur. Yeni kimlikle `retry` güvenli biçimde bütün deneyi yeniden çalıştırır.
- Ortam/algoritma değişirse checkpoint doğrulaması başarısız olur; karışık varyantlardan bilimsel sonuç oluşturulmaz.
