# Metaheuristic Lab v2.3.0 — D-boyutlu kapsam genişletmesi

## İçerik
- Gerçek D boyutlu **PSO + GWO + DE + WOA + MFO + SSA** (2, 5, 10, 30D)
- Deney başına 2–4 algoritma, 2–8 tohum ve tam NFE eşitliği
- WOA a₀, spiral b / olasılık; MFO spiral b; SSA başlangıç c₁ parametre alanları
- Matematiksel hareketlere özel regresyon testleri; eski 2B modüller korunur
- Örnek yeni test: WOA + MFO + SSA / Sphere / 10D / N=24 / T=90 / tohum 42,43,44

## Windows üzerinde mevcut klasörün üzerine uygulama
Önce açık sunucuları `Ctrl+C` ile durdur. ZIP'i Downloads'a indir.

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v2.3.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
```

Backend:
```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Frontend (ayrı terminal):
```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd run build
npm.cmd run dev
```

**Sınırlamalar:** Eski 15 algoritmalı 2B modüller korunur, ancak yüksek boyutlu matematiksel destek yalnızca altı algoritmadır. ACO ayrık TSP'dir. 2B izdüşüm tam yüksek boyutlu çözüm geometrisini temsil etmez. NFE eşitliği çalışma süresi eşitliği demek değildir.
