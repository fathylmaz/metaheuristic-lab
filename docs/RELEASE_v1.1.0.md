# Metaheuristic Lab v1.1.0 — Bat Algorithm (BA)

## Yeni yetenekler

- **Dokuzuncu çalışan algoritma:** Ekolokasyon ilhamlı Bat Algorithm (BA).
- 2B Yang-tarzı gerçek sayısal motor: frekans seçimi, hız güncellemesi, yerel arama, ses şiddeti ve darbe oranı uyarlanması.
- **Ajan bazında denetlenebilirlik:** bir yarasanın önceki konumu, hesaplanan adayı, frekansı, hızı, örneklenen rastgele değerleri, kabul/ret sonucu ve işlem sonrası ses/darbe değerleri.
- Aday reddedilse bile fonksiyon değerlendirmesinin bütçeye yazılması, geçmiş en iyi arşivinin korunması.
- BA'ya özgü 6 parametre kontrolü, kabul/güncelleme metrikleri, aday/başlangıç/hedef gösterimi, matematiksel rehber.
- Diğer sekiz algoritma (FA, PSO, ABC, ACO, CS, MFO, GWO, WOA), üçlü karşılaştırma ve SQLite arşivi korunur.

## Doğrulama

- **101/101 backend testi başarılı** (9 yeni BA testi).
- TS/TSX sözdizimi parser ile 8 kaynak dosyasında kontrol edildi; tam React bağımlılıkları bu ortamda mevcut olmadığından **Vite üretim derlemesi henüz doğrulanmadı**. Windows'ta `npm.cmd run build` uygulanmalı.
- `Sphere`, N=24, T=90, fmin=0, fmax=2, A0=0.9, α=0.9, r0=0.5, γ=0.9, seed=42 → 91 kare, NFE=2184, en iyi amaç = **0.0001917783398792746**.
- BA'nin bu parametrelerdeki sonucu diğer algoritmalar için bilimsel üstünlük karşılaştırması değildir.

## ZIP güncelleme

Önce backend ve frontend terminallerini Ctrl+C ile durdur. `metaheuristic-lab-v1.1.0.zip` dosyasını Windows Downloads klasörüne indirip PowerShell'de:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v1.1.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
```

ZIP kökü `metaheuristic-lab/` olduğu için projeyi iç içe kopyalamaz. Var olan `.venv`, `node_modules`, `.git`, `.sqlite` ve `backend/data/` dosyaları ZIP'e dahil değildir; güncelleme sırasında normalde korunurlar. **Aynı adlı kaynak dosyaları üzerine yazılır**; kullanıcıya ait özel kod düzenlemeleri varsa önceden yedek alınmalıdır.

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

İkinci terminal:

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd install
npm.cmd run build
npm.cmd run dev
```

Yeni testlerin sonucunu ve BA ekranını kontrol edin. Ayrıntılı matematiksel tanım `docs/BA_METHODOLOGY.md` içindedir.
