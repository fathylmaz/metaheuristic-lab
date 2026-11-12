# Checkpoint ve kurtarma metodolojisi (v2.13.0)

## Kesin sınır

Checkpoint bir algoritmanın **tamamlanmış bağımsız koşusunu** temsil eder; jenerasyon içi durum değil. Bu nedenle bir koşunun ortasında elektrik/sunucu kesintisi yaşanırsa yalnızca **o eksik koşu** ilk tohumdan yeniden yürütülür. Çalışan işin kullanıcı iptali de koşular arasında uygulanır.

## Kapsam ve anahtarlar

- `dimensional`: algoritma × tohum (`DimensionalTrial`).
- `benchmark`: fonksiyon × algoritma × tohum (`RunResponse`; tüm 2D çerçeveler dahil).
- `sensitivity`: parametre değerinin `float.hex()` karşılığı × tohum (`RunResponse`).

Veri `background_job_checkpoints` tablosunda `job_id`, benzersiz `unit_key`, sıkıştırılmış Pydantic JSON, SHA-256 ve `engine_fingerprint` olarak tutulur. Her işin isteği değişmez; böylece anahtar yalnızca o işe ait parametreleri ifade eder.

## Crash-safe işlem sırası

1. Tohum koşusu tamamlanır; tam sonuç zlib ile sıkıştırılır.
2. Checkpoint satırı ve `checkpoint_units` sayısı aynı SQLite transaction'ında commit edilir.
3. Kullanıcıya ilerleme olayı gönderilir. Eğer 2 ile 3 arasında kesinti oluşursa sonuç zaten disktedir.
4. Sonuç tamamlanınca akademik arşiv girdisi, `completed` durumu, son olay ve redundant checkpoint temizliği **tek transaction'da** commit edilir.
5. API yeniden başlatılırsa `running` işler `queued` olur. Tamamlanan koşular diskten yüklenir; eksikler hesaplanır.

Hash, accidental corruption tespitidir; veritabanına yazma yetkisi olan saldırgana karşı kimlik doğrulama değildir. Checkpoint **sayısal motor parmak izi** Python/NumPy sürümünü ve sayısal kodun kaynak SHA-256'sını içerir. Değişen motor, yarım kalan işin önceki sonuçlarıyla karıştırılmaz; güvenli yeni iş oluşturulmalıdır.

## Geriye dönük uyumluluk ve başarısızlık

- v2.12'den kalan satırlara yeni sayaç sütunları eklenir; eski arşiv tabloları değiştirilmez.
- Eski `completed_units` sayısı checkpoint olmadan hesaplamanın korunduğunu **kanıtlamaz** ve sıfırlanır.
- Bozuk kayıt / kimlik uyuşmazlığı / motor sürüm farklılığı: iş `failed`, akademik arşive kısmi sonuç yazılmaz. Diğer işler sıradaki göreve devam eder.
- Başarısız veya iptal edilen işin yeni kimlikle `retry` işlemi eski sonuçları değiştirmez; yeni iş tam olarak hesaplanır.
- Silinen terminal işin geçici checkpoint kayıtları kaldırılır; akademik arşiv tabloları kalır.
- Yedekleme araçları SQLite online backup API'sini kullanır; checkpoint'ler de aynı veritabanında tutulduğundan yedeğe dahil olur.

## Sınırlamalar

- Tek worker / tek API süreci; çoklu Uvicorn worker ya da dağıtık görev havuzu desteklenmez.
- İstatistiksel tekrarların tohumları ve değerlendirme bütçesi değişmez; saklanan `duration_ms` ilgili koşunun gerçek hesaplama süresidir, kurtarma sonrası duvar-saat süresini göstermez.
- Kişisel yerel araştırma uygulamasıdır. Kimlik doğrulama ve production-level rate limiting olmadan açık internete sunulmaz.

## Regresyon testleri

`backend/tests/test_job_checkpoints_v213.py` dosyasında üç deney türüyle kısmi kurtarma, tüm matrisin yeniden hesaplanmadan arşivlenmesi, checksum/model/kimlik bozulması, motor parmak izi farkı, iptal-silme ve v2.12 şema yükseltmesi test edilir.
