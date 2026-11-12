# Metaheuristic Lab v0.7.0 — Cuckoo Search (CS)

**Eklenen:** Beşinci algoritma olan Cuckoo Search (CS), bağımsız 2B sürekli optimizasyon laboratuvarına entegre edildi. Önceki FA, PSO, ABC, ACO modülleri ve üçlü FA/PSO/ABC karşılaştırması korunur.

- Mantegna yöntemiyle Lévy aday uçuşları ve rastgele ev sahibi seçimi.
- `p_a` oranı kadar en kötü yuvanın yeniden kurulması, en iyi kaydın korunması.
- Parametreler: yuva sayısı, iterasyon, amaç fonksiyonu, seed, `p_a`, Lévy adım ölçeği ve β kararlılık üssü.
- Her yuvaya tıklayarak son işlem, deneme uzunluğu, konum ve uygunluğu inceleme.
- Hareket izleri, gerçek konumları ve kabul edilmiş uçuş/yeniden başlatma yönlerini gösterir.
- Gerçek fonksiyon değerlendirmesi, kabul ve terk etme metrikleri ve yakınsama grafiği.
- Akademik model sınırları `docs/CS_METHODOLOGY.md` dosyasında belgelidir.

**Kontroller:** Backend tüm testler dahil 66 başarılı (kaynak geliştirme ortamı). Frontend TypeScript/TSX sözdizimi denetiminden geçti; npm kayıt sunucusuna erişilemediği için tam `npm.cmd run build` Windows bilgisayarında doğrulanmalıdır.

**Not:** CS algoritması henüz üçlü karşılaştırma laboratuvarına eklenmedi. CS'nin tam değerlendirme bütçesi, FA/PSO'nun sabit NFE hesabından farklıdır. ACO ayrı TSP çalışma alanıdır.
