# Metaheuristic Lab v0.9.0 — Grey Wolf Optimizer (GWO)

## Eklenenler
- Çalışan **yedinci algoritma**: iki boyutlu **Grey Wolf Optimizer**.
- Güncel en iyi 3 farklı kurttan alfa, beta ve delta liderlerini seçen matematiksel motor.
- Bileşen bazında bağımsız A, C rastgele katsayıları ve üç ayrı adaydan yeni konum üretimi.
- Varsayılan `a0=2` ve `T` güncellemede sonu sıfıra ulaşan lineer kontrol parametresi.
- Her kurtta güncel rol (`wolf_role`) ve ara adaylar (`gwo_x1/2/3`); karede hareketi üreten önceki lider konumları ve ID'leri.
- Canvas'ta kurt rolleri, üç gerçek lider halkası ve seçilen kurdun lider bağlantıları.
- Algoritma rehberi, özel `a0` kontrolü, yakınsama grafiği, JSON/CSV, seçim paneli, animasyon/scrub.
- **9 yeni backend testi**; önceki FA, PSO, ABC, ACO, CS, MFO modülleri ve karşılaştırma laboratuvarı korunur.
- Tüm Python testleri: **83 passed** (bu paketteki geliştirme ortamında).

## Beklenen simülasyon
`Sphere`, 24 kurt, 90 iterasyon, `a0=2.0`, `seed=42`: 91 kare ve **2.184 NFE**; 3 lider + 21 omega. En iyi değerin kesin sayısı için yerel hesaplama motoruna bakılır.

## Windows güncellemesi
Önce iki sunucuyu `Ctrl + C` ile durdur. İndirilenler'e kaydettiğin `metaheuristic-lab-v0.9.0.zip` için:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v0.9.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
```

Proje dizinini iç içe oluşturmadan, mevcut `C:\VS CODE PROJE\metaheuristic-lab` üstüne açılır. `.venv`, `node_modules`, `.git` ve yerel SQLite kayıtlarını silmez. Özelleştirilmiş aynı isimli kaynak dosyalarının üzerine yazar; önce yedeklenmelidir.

**Backend:**
```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
**Frontend (ayrı terminal):**
```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd install
npm.cmd run build
npm.cmd run dev
```

**Doğrulama:** Bu ortamda frontend TSX sözdizimi kontrolleri geçti. npm bağımlılıklarına erişim zaman aşımına uğradığından tam Vite üretim derlemesi henüz doğrulanmadı; Windows'ta `npm.cmd run build` ile kontrol edilmeli.

## Sınır
GWO tekli 2B minimizasyon modülüdür. FA/PSO/ABC ortak karşılaştırma motoruna **henüz dahil değildir**; ACO'nun TSP karşılaştırması farklı problem türüdür. Varyant ve formüller için `GWO_METHODOLOGY.md`.
