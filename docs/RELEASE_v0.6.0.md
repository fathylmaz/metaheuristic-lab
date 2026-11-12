# Metaheuristic Lab v0.6.0 — Karınca Kolonisi / TSP Laboratuvarı

**Tarih:** 11 Kasım 2026

## Yeni modül

- Ayrık optimizasyon: simetrik Öklidyen gezgin satıcı problemi, deterministik şehir yerleşimleri (uniform, circle, clusters).
- Standart **Ant System (AS)**: roulette-wheel olasılıksal rota kurma, feromon buharlaşması ve tüm karıncaların tur uzunluğuna göre çift yönlü feromon bırakması.
- Gerçek tur ve feromon kayıtları: kullanıcı şehir seçer, bağlantı feromonlarını inceler, karınca seçer, turun uzunluğunu ve yolunu görür.
- En iyi rota / seçili rota / feromon yoğunluğu katmanlarını ayrı ayrı açıp kapatma; oynatma, hız, zaman çizelgesi.
- Ayrı algoritma ve şehir tohumu, tüm yapılandırmayı içeren JSON ve yakınsama CSV'si.
- Akademik açıklama ve `docs/ACO_METHODOLOGY.md`.
- ACO için bağımsız FastAPI uç noktası: `POST /api/aco/simulations`.

## Uyum ve sınırlar

- **FA, PSO, ABC** sürekli optimizasyon motorları ve karşılaştırma laboratuvarı değiştirilmedi.
- ACO/TSP ayrık bir problem olduğundan Sphere, Ackley vb. sürekli testlere zorla dahil edilmez. ACO'nun ölçütü **inşa edilen tam tur sayısıdır**; bu değer sürekli fonksiyon değerlendirme sayısı (NFE) değildir.
- Örnek yapılandırma: 16 şehir, 24 karınca, 80 döngü = 1.920 tam tur.
- Bu sürümde ACO için 2-opt, elitist güncelleme, Ant Colony System, TSPLIB importu, kalıcı ACO deney veritabanı veya WebSocket akışı bulunmamaktadır.
- API tüm iterasyonları sunucuda hesaplar, ardından frontend oynatır.

## Kurulum (mevcut klasörün üzerine)

ZIP içinde üst dizin `metaheuristic-lab/` olduğundan proje klasörünün **üst dizinine** çıkartın:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v0.6.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
```

Backend için ` .\.venv\Scripts\python.exe -m pytest -q`; frontend için `npm.cmd install`, `npm.cmd run build`, `npm.cmd run dev`. Testlerin geçmesi gerekir.

**Paket:** Kaynak kodları ve dokümantasyon; `.git`, `.venv`, `node_modules`, `backend/data/` hariç. ZIP üzerine yazma mevcut kaynakları değiştirir, önce yedek alın.

**Derleme notu:** Bu paketleme ortamında npm paket deposuna erişim engellendi; frontend kaynakları TypeScript sözdizimi seviyesinde doğrulandı, tam frontend üretim derlemesi Windows'ta kontrol edilmeli.
