# Metaheuristic Lab v3.0.0 — Yerel Docker dağıtım kılavuzu

> **Yerel/tek kullanıcı araştırma sistemi.** Docker Compose `127.0.0.1:5173` üzerinde web sunar. Kimlik doğrulama, HTTPS, ağ üzerinden paylaşımlı çok kullanıcılı yalıtım ve herkese açık SaaS güvenliği yoktur. Bu yapılandırmayla internete açmayın.

## Gereksinimler

- Docker Desktop / Docker Engine + Compose v2 veya üzeri.
- İlk imaj kurulumu sırasında internet bağlantısı.
- Geliştirme Vite ve Uvicorn terminallerini önceden durdurun (5173 port çakışmasını önlemek için).
- SQLite arşivleri varsa proje kökünde `py -3.13 .\scripts\backup_experiments.py` çalıştırın.

## Başlatma

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab"
docker compose config --quiet
docker compose up --build -d --wait
docker compose ps
powershell -ExecutionPolicy Bypass -File .\scripts\verify_docker_windows.ps1
```

- React + Nginx: http://127.0.0.1:5173
- API sağlık: http://127.0.0.1:5173/api/health
- API kataloğu: http://127.0.0.1:5173/api/catalog
- OpenAPI: http://127.0.0.1:5173/docs
- API'nin 8000 portu hosta açılmaz; Nginx üzerinden `/api` proxy kullanılır. Hem API hem web için Docker healthcheck tanımlıdır.

## Kalıcı arşiv ve görev kuyruğu

`docker-compose.yml` `./backend/data:/app/data` bind mount'u kullanır. Bu klasör host'ta korunur ve kaydedilmiş deneyler, kuyruk olayları ve tamamlanan koşu checkpoint'leri için SQLite kaynağıdır.

- Kuyruk **üç deney tipini** destekler: yüksek boyut, çoklu benchmark ve OFAT duyarlılık.
- Tamamlanmış bağımsız koşuların checkpoint'leri SHA-256 ve ortam/motor uyumluluk denetimleriyle yeniden kullanılabilir.
- Sunucu kesilirse yarım kalmış **tek bir koşu** yeniden çalıştırılır; yalnızca tamamlanan koşular saklanır.
- Görev geçmişinden terminal iş silmek, deney arşivindeki bilimsel kaydı silmez.
- Uygulama yerel tek-işçi/tek-kullanıcı kullanımını hedefler. Birden fazla worker ya da çok kullanıcılı dağıtım için destek iddia edilmez.

## Yedek

```powershell
py -3.13 .\scripts\backup_experiments.py
# Üretilen yedek adını kullan:
py -3.13 .\scripts\backup_experiments.py --verify .\backups\metaheuristic-experiments-YYYYMMDDTHHMMSSZ.zip
```

SQLite yedeği bağlantı açıkken SQLite online backup API ile alınır; ZIP manifest bütünlüğü doğrulanır. Kaynak arşiv yedekleme sırasında değiştirilmez. `backend/data/` veya `backups/` klasörlerini GitHub'a yükleme.

## Durdurma ve güncelleme

```powershell
docker compose down
```

Bu komut bind mount'taki veriyi silmez. Docker imajı veya ZIP kaynak güncellemesi öncesi yedek al. `docker compose down -v`, `docker system prune --volumes` gibi işlemleri yerel veri etkisini anlamadan çalıştırma.

## Sınırlar

- HTTP/localhost: HTTPS yoktur; kimlik doğrulama veya yetki sistemi yoktur.
- Uzun deneyler arka plan kuyruğuna eklenebilir; **her algoritma iç adımında canlı checkpoint** yoktur.
- API güvenlik başlıkları ve istek sınırı, internete açma izni veya güvenlik sertifikası değildir.
- Windows'ta `.node` modüllerinin engellendiği ortamlarda proje Rollup WASM alias kullanır: `frontend/ROLLUP_WASM_WINDOWS.md`.
- CI'daki Docker sürüm denetimi artık `frontend/package.json` sürümünü okur; gelecekteki sürüm etiketlerini elle değiştirmek gerekmez.
