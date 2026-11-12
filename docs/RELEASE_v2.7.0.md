# Metaheuristic Lab v2.7.0 — Deney Belirsizliği ve Okunabilir Akademik Raporlar

Bu sürüm v2.6.0 kaynakları üzerinde, **kayıtlı deneyleri yeniden çalıştırmadan** rapor üretimini geliştirir.

## Yeni çıktılar

- Karşılaştırma, yüksek boyut ve parametre duyarlılığı raporlarında her varyant için **4096 sabit tohumlu bootstrap yeniden örneklemesiyle keşifsel %95 örneklem ortalaması aralığı**.
- Ortak tohum etiketleri için ikili **medyan log10(A/B) hata oranı** (negatifse A daha düşük hataya sahip), A/B kazanım sayısı, iki yönlü **tam işaret testi** ve **Holm** aile-hata düzeltmesi.
- Benchmark raporunda her fonksiyon/algoritma hücresinin kendi bağımsız tekrarlarında belirsizlik aralığı. Farklı fonksiyonların hata ölçüleri kesinlikle tek bir ham ortalamaya karıştırılmaz.
- PDF baskısında yalnızca o deneyin seçilen algoritmalarına ait parametreleri ve ortak yapılandırmayı özetleyen 2 sütunlu görünüm. Eksiksiz ham parametreler JSON/Markdown aktarımında **değişmeden korunur**.
- Vektör tablolarında geniş son sütun, okunaklı yazı tipi, yazdırmada yinelenen tablo başlığı ve sayfa kırılması iyileştirmeleri.

## Bilimsel yorum sınırları

**3 koşuda p < 0.05 beklemeyin.** Tam iki yönlü işaret testinin üç tutarlı kazanç için ulaşabildiği en küçük p = 0.25'tir; Holm çoklu düzeltmesi p değerlerini azaltmaz. Üç tekrarlı bootstrap aralıkları çok kırılgan olabilir; bunlar güvenilir sonuç ilan etmek için değil, başlangıçtaki dağılımı görünür kılmak içindir. Aynı tohum sayısını kullanmak algoritmalarda özdeş başlangıç popülasyonu garantisi değildir.

## Geriye uyumluluk ve doğrulama

Mevcut API uçları, SQLite şemaları, 15 algoritma simülasyonları ve 14 yüksek boyut motoru aynı kalır. JSON rapor sürümü 1.1 olarak işaretlenir; v1.0 alanları korunur. Rapor hesapları deney arşivini değiştirmez. **409/409 backend testi** `python -m pytest -q` ile başarıyla doğrulandı. Frontend üretim derlemesi kullanıcı Windows ortamında `npm.cmd run build` ile yapılmalıdır.
