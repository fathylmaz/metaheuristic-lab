# Metaheuristic Lab v1.8.0 — Scientific Comparison Expansion

- 15 bağımsız simülasyonun tamamı korunur.
- 11 sürekli optimizasyon algoritmasından eşit gerçek NFE bütçesinde 2–6'sı karşılaştırılabilir: FA, PSO, ABC, MFO, GWO, WOA, BA, SSA, SMA, GSA, DE.
- Algoritmaya özgü parametreler karşılaştırma isteği ve deney arşivi içinde kaydedilir.
- Ortak NFE grafiği ve senkron hareket alanları, otomatik olarak seçilen algoritma sayısına göre genişler.
- Eşleştirilmiş tohumlar üzerinden tanımlayıcı kazanç sayıları, log10 medyan fark, tam iki taraflı işaret-değiştirme testi ve Holm düzeltmesi eklenmiştir. **Bunlar küçük örneklemde keşifsel verilerdir.**
- Önceki karşılaştırma SQLite kayıtları geriye uyumludur. Eski kayıtların `pairwise` verisi olmayabilir, bu beklenen davranıştır.
- **Kısıt:** CS, IWO, SA eşit-NFE algoritma adaptörleri hazır olmadığından karşılaştırma seçiminde bulunmaz. ACO hâlâ ayrı ayrık TSP problemi çözer.
- Backend testleri ve bilimsel metodoloji `docs/SCIENTIFIC_COMPARISON.md` içinde belgelenmiştir.

## Windows güncelleme

Önce iki sunucuyu durdur, ZIP'i Downloads'a indir ve proje klasörünün üst dizinine çıkar:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v1.8.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
```

Backend:

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Frontend:

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd run build
npm.cmd run dev
```

Bağımlılıklar değişmedi. Windows'ta `npm.cmd run build` başarılı çıktısı ayrıca doğrulanmalıdır.
