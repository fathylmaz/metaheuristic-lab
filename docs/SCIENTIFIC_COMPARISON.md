# Bilimsel Karşılaştırma — v2.0.0

## Karşılaştırılabilir algoritmalar

Aynı sürekli, iki boyutlu amaç fonksiyonuna ve **gerçek amaç fonksiyonu değerlendirme sayısına (NFE)** göre FA, PSO, ABC, CS, MFO, GWO, WOA, BA, SSA, SMA, IWO, SA, GSA ve DE karşılaştırılır. Bir deney en az 2 en çok 6 algoritma seçer. Her algoritma 2–8 sabit tohum etiketiyle çalıştırılır; varsayılan 3 tekrardır.

- Fonksiyonlar: Sphere, Rastrigin, Ackley, Rosenbrock, Griewank, Himmelblau, Beale ve Booth (birbirlerinden ayrı koşular). Amaç değeri küçüldükçe iyidir.
- Referans NFE bütçesi `N*(T+1)`; örneğin `N=24,T=90 => 2184`.
- FA/PSO/MFO/GWO/WOA/BA/SSA/SMA/GSA/DE jenerasyon başına tam `N` değerlendirme kullanır. Karşılaştırmalar 2B olarak yapılır.
- ABC'nin işçi/gözlemci/keşifçi adayları NFE olarak tek tek sayılır. Durdurma bir ABC aşamasının ortasında olabilir. Kaynak durumu NFE sınırında örneklenir. **Eşit iterasyon sayısı iddia edilmez.**
- **CS:** her Lévy adayının ve yuva yenilemesinin tek tek NFE sayılmasıyla ortak kontrol noktalarına kaydedilir; yuva-yenileme aşaması yarım kalabilir.
- **IWO:** her yeni tohum tek gerçek değerlendirmedir. Ebeveynler nesil başında sabittir; elit seçim her tohum sonrası uygulanır ve her an popülasyon üst sınırı korunur. Yayılım sigma çizelgesi bağımsız tekil sürümdeki nesil sayısına göre değil, NFE ufkuna göre normalleştirilir.
- **SA:** bir başlangıç çözümü ve her yeni komşu için tek değerlendirme vardır. İlk NFE kontrol noktası N değerlendirmeyi (1 başlangıç + N−1 teklif) içerir. Daha sonra her NFE kontrol noktasında N yeni teklif örneklenir; soğuma çizelgesi karşılaştırma NFE ufku boyunca referans adım sayısı kadar soğuma üretir. SA popülasyonlu değildir.
- **Kısıt:** CS/IWO/SA karşılaştırma varyantları, tekil simülasyonun aynı sayıda nesille çalıştırılmasına matematiksel olarak özdeş değildir. Eşit NFE, eşit işlem süresi, başlangıç popülasyonu veya yineleme sayısı demek değildir. ACO ise ayrı simetrik TSP problemidir.

## Toplanan metrikler

- Her koşunun son arşivlenen en iyi amaç değeri, toplam NFE, süre, ilk başarı NFE noktası.
- Tohumlar üzerinde ortalama, medyan, örneklem standart sapması (n-1), minimum, maksimum, başarı oranı.
- Her ortak NFE noktasındaki ortalama `best_so_far` ve örneklem sapması.
- Temsili oynatım medyan son amaç değerine sahip koşudan seçilir. Aynı tohum farklı algoritmalar için aynı başlangıç adaylarını **garanti etmez**.

## İkili eşleştirilmiş testler

Her algoritma A ve B çifti için `d_i = log10(max(best_A_i, 1e-60)) - log10(max(best_B_i, 1e-60))` hesaplanır. Sıfır tabanı yalnızca log dönüşümündedir; ham sonuçlar değiştirilmez. `median(d_i)` negatife düşerse A'nın daha küçük amaç değerlerine eğilimi olduğu söylenebilir. Aynı tohum etiketindeki her sonuç eşleştirilir.

Çok küçük sayılı koşular için `2^k` olası işaret ataması enumerate edilerek iki taraflı **tam işaret-değiştirme** p değeri hesaplanır (`k` sıfır olmayan fark sayısı). Değişmezlerin tüm ikili testleri üzerine **Holm-Bonferroni** düzeltmesi uygulanır; ham p ve düzeltilmiş p ikisi de saklanır. Bu test farklı algoritmaların farklı rastgele akışlarını aynı ilk popülasyona zorlamaz; eşleştirme güç kazandırabilir ama değiş-tokuş edilebilirlik varsayımı her problemde garanti değildir.

**Sınırlama:** 2–8 koşu ve tek bir amaç fonksiyonuyla genellenebilir algoritma üstünlüğü kanıtlanmaz. Özellikle `n=3` için tam testin p çözünürlüğü düşüktür. Yorumlar keşifsel olmalı; ileri sürümde COCO/BBOB ve çok daha fazla bağımsız tohum, güven aralıkları, etki büyüklükleri ve doğrulanmış test protokolleri gereklidir.

## Geri uyumluluk ve kayıt

Karşılaştırmalar SQLite `backend/data/comparisons.sqlite3` içine sıkıştırılmış JSON olarak saklanır. `pairwise` alanı yeni sürümde gelir, eski arşivler boş `pairwise` ile açılabilir. Bilinen eski kayıtlardaki algoritmalar değişmeden korunur. JSON dışa aktarımında `parameters`, `methodology`, `groups`, `pairwise` yer alır; CSV'de tohum bazlı ham son metrikler vardır.

## Kullanıcı doğrulaması

1. `FA + PSO + ABC` seçimiyle önceki karşılaştırmanın eşit NFE sonuçlarını doğrula.
2. `PSO + GWO + DE`, Sphere, 24 ajan, T=90, 3 tohum, 42 başlangıç tohumu ile dene.
3. Ortak NFE, her grubun `representative_run.frames` NFE değerleri, grafiği ve ikili istatistik tablosunu kontrol et.
4. Aynı girdiyi yeniden gönderip yalnızca UUID, süre ve kayıt zamanının değiştiğini doğrula.
5. Sonucu arşivden aç ve CSV/JSON olarak dışa aktar.
