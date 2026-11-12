# Metaheuristic Lab v0.8.0 — MFO modülü

## Kapsam

- 6. çalışan algoritma: **Güve–Alev Optimizasyonu (MFO)**.
- FastAPI `POST /api/simulations` için `algorithm="mfo"` ve `mfo_spiral_b` (0.1–3.0) desteği.
- Gerçek koordinat bazlı spiral formül, iterasyonla azalan alev sayısı ve sıralı seçkin alev belleği.
- MFO'ya özgü kaynak telemetrisi: alev koordinatları, rütbesi ve her eksendeki spiral t parametresi.
- Canvas çizimi: alev işaretleri, gerçek güve–alev hedef bağlantıları, seçilen güvenin tam değerleri.
- Aynı tasarım sisteminde parametre paneli, alev dinamiği, matematiksel açıklamalar, CSV ve JSON.
- 8 yeni MFO testi; önceki algoritma ve karşılaştırma kodları korunur.
- FA/PSO/ABC eşit-NFE karşılaştırması, ACO/TSP ve CS bağımsız modülleri değişmeden kalır. MFO karşılaştırma motoruna **henüz dahil edilmedi**.

## Kurulum / güncelleme (Windows PowerShell)

İki çalışan sunucuyu Ctrl+C ile durdur. `metaheuristic-lab-v0.8.0.zip` dosyasını İndirilenler'e kaydet:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v0.8.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
```

Üst klasöre açılır; yeni bir iç içe `metaheuristic-lab` oluşturmaz. Aynı adlı kaynakların üstüne yazar, yerel `.venv`, `node_modules`, `.git`, `backend/data` ve SQLite içeriklerine dokunmaz. Özelleştirilmiş kaynak dosyaları önce yedeklenmelidir.

Backend:

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Frontend ayrı terminalde:

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd install
npm.cmd run build
npm.cmd run dev
```

## Beklenen yerel doğrulama

- Sol menüde **Güve-Alev Optimizasyonu (MFO)** artık hazır.
- Sphere, N=24, T=90, b=1, seed=42: 91 kare, NFE=2.184, 24→1 alev; hesaplanan en iyi fitness yaklaşık **7.25749e−12** (NumPy sürümüne bağlı olabilir).
- Bir güveyi seçince ilgili alevin konumu/rütbesi ve spiral t değerleri görüntülenir.
- Ders sayfasında matematik, varyant ve referans bulunur.
- Python backend testleri bu paket için başarıyla çalıştırılmıştır. Frontend tam `npm run build` bu ortamda npm ağ erişimi olmadığı için doğrulanamadı; **kullanıcının Windows terminalinde kontrol edilecek.**

## Kaynak

Mirjalili (2015), DOI: 10.1016/j.knosys.2015.07.006. Algoritmanın uygulama kararları [`MFO_METHODOLOGY.md`](MFO_METHODOLOGY.md) içinde.
