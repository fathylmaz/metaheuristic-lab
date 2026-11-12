# Parametre Duyarlılığı Laboratuvarı — v2.1.0

## Bilimsel amaç ve sınırlamalar

Bu bölüm, tek değişkenli (OFAT — One Factor At a Time) kontrollü parametre deneyidir. Bir optimizasyon algoritması ve 2B test fonksiyonu seçilir; tek parametrenin 2–5 değeri değiştirilirken diğer bütün algoritma parametreleri varsayılan karşılaştırma ayarlarında kalır. Böylece **hangi değişkenin etkisinin** incelendiği açıkça tanımlanır. Bu yöntem parametreler arasındaki etkileşimleri ölçmez, otomatik hiperparametre optimizasyonu veya genel üstünlük testi olarak yorumlanmamalıdır.

Her koşu `N × (T + 1)` gerçek amaç fonksiyonu değerlendirmesi (NFE) kullanır. Ajan/yuva/çözüm sayısı `N`, referans adım sayısı `T` ile tanımlanır. **SA, CS, IWO ve ABC** karşılaştırma adaptörleri, iç jenerasyonların farklı olabileceğini göz önünde tutar; veri kareleri ortak gerçek NFE kontrol noktalarında kaydedilir. Tüm koşularda NFE tam eşit olmalıdır. Koşu süresi karşılaştırmalı bir başarım ölçüsü olarak kullanılabilir, ancak donanım/ortam bağımlıdır.

Aynı rastgele tohum *etiketleri* kullanılır (örn. 42,43,44). Parametre değişimi rastgele sayı tüketimini değiştirebileceğinden bit düzeyinde ortak arama yolu garanti edilmez. İstatistikler tekrar sayısına ve test fonksiyonuna bağlıdır; özellikle yalnızca 2–5 tekrardan gelen farklar anlamlılık kanıtı değildir.

## Matematiksel kayıtlar

- Her koşunun `best_so_far` değeri ve NFE kontrol noktaları saklanır.
- Her problemde bilinen teorik en iyi amaç değeri `f*`, `OBJECTIVES` kataloğundan alınır.
- `absolute_error = max(0, f(x_best) - f*)` tanımlanır; farklı problemlerin ham amaç değerleri birbirleriyle ortalanmaz.
- Ortalama, medyan, minimum, maksimum ve örneklem standart sapması (`n-1`) hesaplanır.
- Başarı oranı, `absolute_error <= success_tolerance` koşulunu karşılayan tekrarlara göre hesaplanır.
- Yakınsama eğrisi her NFE noktasındaki tekrar ortalama mutlak hatasıdır. Yalnızca **çizim** için logaritmik minimum taban `1e-16` kullanılır; kayıttaki sıfırlar sıfır olarak kalır.
- Sıralama ve öneri olarak en düşük **gözlenen** ortalama hata gösterilir. Bu değer yalnızca bu deneyin tanımlayıcı sonucudur.

## Kaydetme ve tekrarlanabilirlik

`POST /api/sensitivity` girişini Pydantic doğrular: algoritmaya uygun parametre, farklı ve izin verilen aralıktaki 2–5 değer, 2–5 ortak tohum ve sınırlı hesaplama bütçesi. `GET /api/sensitivity/parameters` katalog sunar; kalıcı arşivde `sensitivity_studies` isimli yeni SQLite tablosu kullanılır. Arşiv açma `GET /api/sensitivity/{id}` üzerinden yapılır. Eski `comparison` ve `benchmark` tablolarına dokunulmaz.

## İleri araştırma

Güçlü bir akademik çalışma için tekrarlanan bağımsız koşu sayısını artırmak, problem sınıflarını çeşitlendirmek, sonuçları ayrı bir holdout deneyinde doğrulamak, etkileşimleri faktöriyel tasarımla incelemek ve maliyet/başarı eğrileri raporlamak gereklidir. Bu modül bu işin **denetlenebilir başlangıcıdır**, tamamı değildir.
