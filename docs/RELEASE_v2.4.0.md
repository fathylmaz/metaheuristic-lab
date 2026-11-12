# Metaheuristic Lab v2.4.0 — FA + BA + GSA gerçek D-boyut desteği

## Eklenenler
- Yüksek Boyut Laboratuvarı: toplam **9/14** sürekli algoritma (PSO, GWO, DE, WOA, MFO, SSA, FA, BA, GSA).
- Gerçek 2, 5, 10, 30 koordinatlı optimizasyon; her aday için bir gerçek değerlendirme, aynı `N × (T+1)` NFE.
- FA: donmuş başlangıç parlaklığı, ardışık çekim, her çekimde rassal adım.
- BA: hız/frekans, yerel öneri, ses–darbe takvimi, reddedilen adaylar dahil değerlendirme.
- GSA: uygunluk tabanlı normalize kütle, Kbest, G(t), kuvvet/ivme güncellemesi.
- Kullanıcı arayüzünde üç algoritma seçeneği ve 12 yeni özel parametre.
- 315 backend testi geçti (35 yeni test dahil). Tam frontend derlemesi Windows'ta doğrulanmalıdır.

## Bilimsel sınırlamalar
- Eşit NFE eşit süre veya eşit başlangıç popülasyonu anlamına gelmez.
- 2B izdüşüm yalnızca en iyi vektörün `x1,x2` bileşenlerini gösterir; gerçek D-boyutlu arama alanını göstermez.
- FA çekim sayısı NFE değildir; BA'da reddedilen adaylar da NFE'ye dahildir.
- GSA kütle–çekim modeli fiziksel Newton simülasyonu değildir.
- 2B simülasyonlar değişmedi. ACO ayrı bir ayrık TSP problemidir.
- Eski yüksek boyutlu deneyler varsayılan yeni parametrelerle arşivden yeniden açılır.

## Windows: tek komutla üzerine yaz
Önce backend/frontend sunucularını Ctrl+C ile durdur. ZIP'i `Downloads` klasörüne indir.

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v2.4.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
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

**ZIP, SQLite veritabanını ve kullanıcının `.venv`, `.git`, `node_modules` klasörlerini içermez; mevcut deneyleri ve proje geçmişini korumak içindir.** Aynı isimli kaynak dosyalarındaki kişisel düzenlemeleri yine de önceden yedekleyin.
