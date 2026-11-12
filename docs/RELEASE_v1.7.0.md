# Metaheuristic Lab — v1.7.0 / DE release

15. algoritma **Diferansiyel Evrim (DE/rand/1/bin)** hazır. Önceki 14 algoritma ve FA/PSO/ABC karşılaştırma laboratuvarı korunur.

## Eklenen

- `backend/app/optimizers/differential.py`: synchronously frozen donor generation, three distinct donor indices, mutant F, binomial CR / mandatory jrand, candidate acceptance and global best archive.
- `backend/tests/test_de.py`: matematiksel denklemleri kaydedilen telemetriden yeniden üreten testler.
- `RunRequest` için `de_mutation_factor`, `de_crossover_rate` alanları.
- `AgentState` için eski hedef, üç donör, ham/kırpılmış mutant, çaprazlama maskesi, deneme ve kabul bilgisi.
- `SimulationFrame` için kabul, ret ve zorunlu koordinat metrikleri.
- React/Canvas içinde donör bağlantıları, mutant/deneme işaretleri, seçilebilir detay popover'ı, DE'ye özel parametreler, yöntem açıklaması ve regresyon testleri.
- Kaynak ve varyant: `docs/DE_METHODOLOGY.md`.

## Yerel test senaryosu

`Sphere`, `population_size=24`, `iterations=90`, `de_mutation_factor=.75`, `de_crossover_rate=.90`, `seed=42`.

- 91 kare ve **2.184** fonksiyon değerlendirmesi olmalı.
- 24 ajan mevcut olmalı; her hareket karesinde **kabul+ret=24**.
- Donörler hedefe ve birbirlerine eşit olmamalı.
- Sabit seed ile aynı konum/uygunluk/telemetri kayıtları (yalnızca UUID ve süre farklı olabilir) oluşmalı.

## Çalıştırma

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Ayrı terminal:

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd run build
npm.cmd run dev
```

### Bilinçli sınırlar

Karşılaştırma laboratuvarı halen FA/PSO/ABC içindir. 15 algoritmanın hepsinin eşit NFE ile karşılaştırılması daha sonraki geliştirmedir; ACO'nun ayrık TSP alanı ayrı kalır. Frontend'in tam Vite üretim derlemesi, paket oluşturma ortamında npm kayıt sunucusuna ulaşılamadığından yerel Windows'ta doğrulanmalıdır.
