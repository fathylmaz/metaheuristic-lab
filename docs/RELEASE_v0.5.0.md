# Metaheuristic Lab v0.5.0 — Üçlü Karşılaştırma Laboratuvarı

**Tarih:** 11 Kasım 2026

## Yeni özellikler

- Karşılaştırma ekranında FA, PSO ve ABC algoritmalarından 2 veya 3 tanesini seçme. Varsayılan üçlüdür.
- ABC için **tam NFE sınırı**: işçi, gözlemci ve keşifçi değerlendirmeleri eksiksiz sayılır. ABC döngüleri diğer algoritmalarla aynı uzunlukta kabul edilmez.
- Her algoritma için aynı NFE eşiklerinden 2B hareket kareleri, çoklu yakınsama grafiği, ortalama/medyan/örneklem sapması ve tohum bazında sonuçlar.
- Yatay ve dikey duyarlı ekranlarda 3 sonuç kartı, 3 hareket alanı, dinamik CSV/JSON.
- Eski FA+PSO arşiv kayıtları yeni ekranda tekrar açılabilir.
- Reproducible test coverage for budgeted ABC, multi-algorithm comparisons and backwards-compatible API.

## Deneyin doğru yorumlanması

NFE = `N × (T+1)`. T **referans kontrol noktalarının** sayısını belirler; ABC için gerçek çevrim sayısı T değildir. Örnek: N=24, T=90 -> **2.184 gerçek değerlendirme** algoritma ve koşu başına. ABC, 2.184'üncü değerlendirmeden hemen sonra, gerekirse çevrim ortasında kesilir. İlk başarı değerlendirmesi örneklenen kontrol noktasına göre raporlanır.

## Kurulum (mevcut klasörü koruyarak)

1. Backend ve frontend'i Ctrl+C ile durdur.
2. ZIP'i `Downloads` klasörüne indir.
3. Proje klasörü ZIP içinde `metaheuristic-lab/` olduğundan üstüne yüklemek için:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v0.5.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
```

4. `backend` içinde ` .\.venv\Scripts\python.exe -m pytest -q` çalıştır; beklenen **52 passed**.
5. `frontend` içinde `npm.cmd install`, `npm.cmd run build`, `npm.cmd run dev` çalıştır.

**Not:** Frontend üretim derlemesi paket hazırlama ortamında npm kayıt sunucusuna erişilemediği için yerel Windows ortamında doğrulanacak. TypeScript sözdizimi analizi başarılıdır.

## Korumalar

ZIP yalnızca kaynak kodu ve belgeleri içerir. `.git`, `.venv`, `node_modules`, `backend/data/` ve yerel deneyler pakette bulunmaz; `Expand-Archive -Force` bunları silmez. Aynı adlı kaynak dosyalarını değiştireceği için kullanıcı düzenlemeleri varsa önce yedek al.
