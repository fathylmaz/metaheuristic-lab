# Metaheuristic Lab v2.5.0 — 14/14 sürekli algoritmada D-boyut desteği

## Kapsam

Yüksek Boyut Laboratuvarı'na ABC, CS, SMA, IWO ve SA eklendi. 2/5/10/30 boyutta gerçek D-bileşenli amaç fonksiyonları kullanılır. Önceki PSO/GWO/DE/WOA/MFO/SSA/FA/BA/GSA ve 15 algoritmanın bağımsız 2B modülleri korunur. ACO, ayrık TSP modeli olarak ayrı kalır.

## Adil NFE ve uyarlanmış varyantlar

- **ABC:** İşçi arı, gözlemci arı, keşifçi arı aşamaları. Her aday veya yeni besin kaynağı tek tek değerlendirilir. Tek koordinat değiştiren komşu üretimi ve limit denemesi korunur; değerlendirme bütçesi gerektiğinde bir aşamanın ortasında durur.
- **CS:** Mantegna dağılımıyla D-boyutlu Lévy adımları, rastgele ev sahibi yuvalar, açgözlü güncelleme, elit korumalı en kötü yuvaları terk etme. Atılan yumurtalar ve yeniden oluşturulan yuvaların tamamı gerçek NFE'dir.
- **SMA:** Uygunluğa göre ağırlık, en iyi arşive göre seçilme olasılığı, D-boyutlu yaklaşma, büzülme ve yeniden başlangıç. Her yeni birey bir kez değerlendirilir. Son büzülme aşamasında `v_c=0` seçimi, orijini optimum olan fonksiyonlarda sıfır hata doğurabilir; bu tüm fonksiyonlarda üstünlük değildir.
- **IWO:** D-boyutlu Gaussian saçılma ve uygunluğa bağlı tohum sayısı, büyüyen nüfusta rekabetçi seçim. Gaussian standart sapma **gerçek NFE ilerleme oranına** göre azalır; bu, bağımsız 2B IWO'nun nesil bazlı σ zamanlamasından farklı, açık bir karşılaştırma varyantıdır.
- **SA:** Bir güncel çözüm, bir Gaussian komşu, Metropolis olasılığı, her aday için tek gerçek NFE; eski en iyi çözüm ayrı arşivlenir. Soğutma, tek çözüm için 2.184 defa geometrik çarpılmak yerine aynı `Tref` ufkuna **NFE üzerinden normalize edilir**. `N=24`, SA'nın 24 eşzamanlı çözüm tuttuğu anlamına gelmez.

Tüm algoritmalarda ortak örneklem NFE değerleri `N, 2N, …, N×(Tref+1)` şeklindedir; bu örneklem adımları CS/ABC/IWO/SA için tam nesil/döngü sınırı olmayabilir. Arşivde tam D-boyutlu tarihsel en iyi vektör bulunur; ilk iki koordinat yalnız izdüşümdür. Aynı tohum etiketi aynı başlangıç konumlarını garanti etmez.

## API ve testler

`POST /api/dimensional` eski şemayla uyumludur; eksik yeni parametreler varsayılanlarla tamamlanır. `GET /api/dimensional` ve `GET /api/dimensional/{id}` eski ve yeni arşivleri yükler. Arşiv şemasında kırıcı değişiklik yoktur. Yürütme ve veri limitleri (2–4 algoritma, 2–8 tohum, 160.000 NFE üst sınırı) değişmedi.

Backend regresyon testi: **386/386 başarılı**. Yeni adaptörler 2/5/10/30 D, beş amaç fonksiyonu, gerçek NFE sayacı, sabit tohum, hatalı parametre, SQLite API ve tarihsel en iyi arşivi için test edildi. TypeScript sözdizimi kontrolü yapıldı; tam Vite/TypeScript üretim derlemesi Windows'ta kontrol edilmelidir.

## Windows güncelleme

ZIP içinde `metaheuristic-lab/` kök klasörü yer alır; çalışır `.venv`, `node_modules`, `.git` veya SQLite dosyası bulunmaz.

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\metaheuristic-lab-v2.5.0.zip" -DestinationPath "C:\VS CODE PROJE" -Force
```

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Yeni terminalde:

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd run build
npm.cmd run dev
```

## Deneme yapılandırması

`ABC + CS + SA`, `Rastrigin`, `10D`, `N=24`, `Tref=90`, `3 tohum`, `ilk tohum=42`. Her algoritma/koşu 2.184 NFE, bütün deney 19.656 NFE kullanır. Çıktılar yalnızca bu koşullara ilişkindir; az tekrarla genel üstünlük sonucu çıkarılmaz.

## Yöntem referansları

- Karaboga, *An Idea Based on Honey Bee Swarm for Numerical Optimization* (2005), Artificial Bee Colony.
- Yang & Deb, *Cuckoo Search via Lévy Flights* (2009).
- Li et al., *Slime Mould Algorithm: A New Method for Stochastic Optimization* (2020).
- Mehrabian & Lucas, *A Novel Numerical Optimization Algorithm Inspired from Weed Colonization* (2006).
- Kirkpatrick, Gelatt & Vecchi, *Optimization by Simulated Annealing* (1983).

Bunlar esin kaynağıdır; yukarıda tanımlanan değerlendirme sınırlandırması, sıcaklık ve yayılma zamanlamaları bu projenin açıkça belgelenmiş eğitim/karşılaştırma varyantlarıdır.
