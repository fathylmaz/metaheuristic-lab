# Metaheuristic Lab v2.1.0 — Parametre Duyarlılığı Laboratuvarı

## Özellikler

- 15 önceki simülasyon algoritması ve mevcut karşılaştırma/benchmark modülleri korunur.
- 14 sürekli optimizasyon algoritması için seçilebilir, algoritmaya özgü parametre kataloğu.
- Parametre başına 2–5 değer, 2–5 ortak tohum etiketi ve tam eşit gerçek fonksiyon değerlendirme sayısı.
- 8 adet 2B referans fonksiyon, örneklem std, medyan, başarı oranı ve NFE karşısında log görselleştirme.
- SQLite'da kalıcı arşiv; CSV/JSON dışa aktarma.
- `docs/PARAMETER_SENSITIVITY_METHODOLOGY.md` detaylı sınırlar.
- Backend **215/215** otomatik test başarılı. Frontend üretim derlemesi bu paketleme ortamında npm registry DNS erişimi olmadığından Windows'ta test edilmelidir.

## Windows kurulum

ZIP dosyasını Downloads klasörüne indir; iki yerel sunucuyu `Ctrl+C` ile durdur. Kaynaklarda kişisel değişiklikler varsa yedekle.

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v2.1.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
```

### Backend

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### Frontend (ayrı terminal)

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd run build
npm.cmd run dev
```

Test: **Parametre Duyarlılığı** menüsü → PSO / Rastrigin / Atalet (w) / `0.4, 0.72, 1.0` / 24 ajan / 60 adım / 3 tohum / 42 başlangıç tohumu. Beklenen bütçe: koşu başına 1464 NFE, toplam 13176 NFE. Farklı eğriler, parametre istatistikleri, tohum tablosu ve kalıcı arşiv görünmeli.

## Notlar

`Expand-Archive -Force` kaynak dosyaları üzerine yazabilir; ZIP `.git`, `node_modules`, `.venv` ve yerel SQLite verilerini içermez. Bu dizinler korunur; yine de elle düzenlenen kaynakları yedeklemek önerilir.
