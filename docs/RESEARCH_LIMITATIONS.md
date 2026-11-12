# v3.0.0 — Bilimsel ve ürün kapsamı sınırlamaları

1. **Araştırma ve eğitim uygulaması:** Ticari optimizasyon servis garantisi, algoritma sertifikasyonu veya tüm problemlerde üstünlük iddiası yoktur.
2. **Eşit NFE ≠ eşit maliyet:** Algoritmaların iç karmaşıklıkları, aday hesaplama düzenleri, popülasyon/nesil tanımları ve gerçek süreleri farklıdır.
3. **ACO farklı problem:** ACO ayrık simetrik Öklidyen TSP üzerindedir. Sürekli amaç fonksiyonlarında çalışan diğer 14 yöntemle doğrudan kıyaslanmaz.
4. **İlk iki koordinat yalnızca izdüşüm:** 10D/30D deneylerde x1/x2 grafiği optimizasyonun D-boyutlu amaç yüzeyi değildir.
5. **İstatistikler keşifsel:** Bootstrap aralıkları ve eşleştirilmiş testler, özellikle az tekrarda genel üstünlük kanıtı değildir. Aynı tohum etiketi farklı algoritmalarda aynı rastgele örneklem akışı anlamına gelmeyebilir.
6. **Dahili denetim bağımsız değildir:** Sonuç vektörleri aynı uygulama fonksiyonuyla yeniden hesaplanır. Harici kütüphane ile algoritma denklik incelemesi kapsam dışıdır.
7. **Checkpoint sınırı:** Tamamlanmış koşular korunur; tek bir bağımsız koşunun iç iterasyonundan devam edilmez. Uyuşmayan motor/ortam parmak izleri reddedilir.
8. **Yerel servis:** Kimlik doğrulama, HTTPS, kullanıcı ayırma ve çoklu kullanıcı barındırma yoktur. İnternete açık sistem olarak dağıtılmamalıdır.
9. **Zaman ölçümleri makineye bağımlıdır:** API/disk/arayüz maliyetleri dahil olmayabilir; donanımlar arasında ham süre kıyaslanmaz.
10. **Tekil simülasyon/rapor saklama farklıdır:** Oturum içi simülasyonların hepsi SQLite'a yazılmaz; arşivlenmiş araştırma deneyleri ve görev kayıtları kalıcıdır.
11. **Gerçek ekran görselleri ve lisans:** Kullanıcı çalıştırdığı uygulamanın görüntülerini elde edip kontrol etmelidir; kodun paylaşım lisansı ayrıca seçilmelidir.
