# Metaheuristic Lab v1.0.0 — Whale Optimization Algorithm (WOA)

## Eklenenler

- Sekizinci çalışan optimizasyon algoritması: **WOA / Balina Optimizasyon Algoritması**.
- Gerçek iki boyutlu kuşatma, rastgele başka balina ile keşif ve baloncuk-ağı spiral matematiği.
- Ayrı `a0`, spiral şekli `b` ve spiral hareket olasılığı kontrolleri.
- Eşzamanlı popülasyon güncellemesi, tekli NFE hesabı, tarihsel en iyi arşivi.
- Birey bazında hareket türü, hareket öncesi pozisyon, önceki nesilden hedef, A/C, p ve ℓ telemetrisi.
- Her karede keşif/kuşatma/spiral sayıları, gerçek arama hareketi bağlantıları, seçilebilir balina incelemesi.
- WOA açıklama ekranı ve `docs/WOA_METHODOLOGY.md` kaynak/denklem dokümantasyonu.
- Önceki yedi algoritma (FA, PSO, ABC, ACO, CS, MFO, GWO) ve FA/PSO/ABC karşılaştırma laboratuvarı korunuyor.

## Doğrulama

- **92/92 backend testi başarılı**; bunların 9'u WOA için yenidir.
- TypeScript/TSX kaynak dosyalarının sözdizimi kontrol edildi; npm kayıt sunucusu bu ortamdan erişilemediğinden tam üretim derlemesi kullanıcı Windows ortamında doğrulanmalıdır.
- `Sphere`, N=24, T=90, a0=2, b=1, spiral probability=0.5, seed=42: 91 kare; 2.184 NFE; en iyi tarihsel değer **7.368812980278884 × 10⁻³²**. Bu **tek koşuya** aittir, genel üstünlük iddiası değildir.

## Tek komutla mevcut klasöre uygulama

Çalışan iki terminali durdur, ZIP'i Windows `Downloads` dizinine indir. Sonra:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v1.0.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
```

ZIP dosyasında birinci klasör `metaheuristic-lab/` olduğundan iç içe proje açılmaz. Aynı adlı kaynak dosyalarının üzerine yazar; `.venv`, `node_modules`, `.git` ve `backend/data` (SQLite) gibi klasörler ZIP'de bulunmaz ve var olan kayıtları silinmez. Kullanıcı değişiklikleri varsa önce yedeklenmelidir.

Backend:

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Frontend (ikinci terminal):

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd install
npm.cmd run build
npm.cmd run dev
```

## Sınırlar

WOA bu sürümde kendi tekli simülasyon ekranında çalışır; 3 algoritmalı eşit-NFE karşılaştırma laboratuvarına dahil edilmedi. Karşılaştırma eklemesi ayrı bilimsel uyarlama ve testlerle yapılmalıdır.
