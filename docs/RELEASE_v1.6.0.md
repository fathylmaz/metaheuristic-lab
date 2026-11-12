# Metaheuristic Lab — v1.6.0 GSA Release

Bu sürümde **Gravitational Search Algorithm (GSA)** 14. çalışan algoritma olarak eklenmiştir.

## Eklendi

- `backend/app/optimizers/gravitational.py`: normalize kütle ve Kbest kuvvetleri, azalan G(t), ivme, hız ve konum entegrasyonu
- `backend/tests/test_gsa.py`: 10 bağımsız matematik/API regresyon testi
- `RunRequest`, `AgentState`, `SimulationFrame` için GSA parametre ve telemetri alanları
- GSA için özel kütle/kuvvet 2B görselleştirme, seçilen ajan paneli ve özet istatistikleri
- GSA algoritma rehberi, formüller ve varsayımlar
- `docs/GSA_METHODOLOGY.md`

## Korunanlar

FA, PSO, ABC, ACO, CS, MFO, GWO, WOA, BA, SSA, SMA, IWO, SA ve önceki üçlü FA–PSO–ABC karşılaştırma deneyleri.

## Kontrollü deney

- Objective: Sphere; N=24; T=90; seed=42; G0=100; decay=20; epsilon=0.01.
- Tam 91 kare ve NFE=2.184.
- GSA'nın aktif kuvvet kaynağı sayısı N→1; G(t) üstel azalır.
- Referans son amaç değeri motorun aynı Python/NumPy sürümündeki hesaplarıyla kontrol edilebilir; tek bir deneye dayanarak GSA'nın diğer algoritmalardan üstünlüğü iddia edilmez.

## Yerel kontroller

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Yeni terminal:

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd run build
npm.cmd run dev
```

Frontend üretim derlemesi, paketin oluşturulduğu ortamda React bağımlılıkları bulunmadığından Windows'ta doğrulanmalıdır.
