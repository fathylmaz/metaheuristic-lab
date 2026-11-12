# FA kullanıcı deneyleri — doğrulama kaydı (11 Kasım 2026)

## Deney kurulumu

Kullanıcı tarafından dışa aktarılan üç `sphere`/`fa` JSON kaydı analiz edildi.
Kayıtlarda 24 ajan, 90 iterasyon (başlangıçla birlikte 91 kare), `seed=42`
ve [-5.12,5.12] sınırları bulunuyor. Kullanıcı açıklamasına göre ilk iki
koşuda `alpha=0.18`, üçüncü koşuda `alpha=0.60` kullanıldı.

**Sınır:** v0.1.0 dışa aktarılan JSON'lar `alpha`, `beta0` ve `gamma`
parametrelerini kayıt altında tutmadığı için bunlar JSON içeriğinden
bağımsız doğrulanamıyor. v0.2.0'da `parameters` alanı eklendi.

## Sonuçlar

| Metrik | İlk koşu | Aynı ayar tekrarı | Yüksek alpha |
|---|---:|---:|---:|
| `best_so_far` | 0.0002632528329408253 | 0.0002632528329408253 | 0.0029052086271127 |
| `current_best` (son kare) | 0.013675343782717956 | 0.013675343782717956 | 1.0523200953392304 |
| `mean_fitness` (son kare) | 0.8021074263043513 | 0.8021074263043513 | 16.39743712946058 |
| `diversity` (son kare) | 0.7302937794893434 | 0.7302937794893434 | 3.733509507068876 |
| `function_evaluations` | 2184 | 2184 | 2184 |

- İlk iki koşunun `frames` dizileri **tam olarak eşit**; UUID ve çalışma süreleri farklı.
- Üçüncü koşunun ilk popülasyonu ilk ikisiyle eşit. Fark 1. iterasyondan başlıyor.
- Üç koşudaki tüm ajan `fitness` değerleri `x²+y²` hesabıyla sayısal tolerans
  içinde uyumlu, konumlar sınırlar içinde, `best_so_far` monoton azalmayan değil,
  **monoton artmayan**, değerlendirme sayıları beklenen `24*(iteration+1)` değeriyle eşit.
- Yüksek alpha koşusundaki son çeşitlilik yaklaşık **5.11 kat** büyüdü; bu koşuda
  arşivde bulunan en iyi amaç değeri yaklaşık **11.04 kat** daha yüksek (daha kötü).

## Yorum

Bu gözlem aynı tohum üzerindeki parametre duyarlılığını gösterir, ancak genel
algoritma üstünlüğü veya parametre optimalliği iddiası değildir. Çoklu tohumla
tekrarlanan benchmarklar sonraki bir kilometre taşına bırakılmıştır.
