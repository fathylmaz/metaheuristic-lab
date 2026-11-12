# Metaheuristic Lab — v2.15.0 Arayüz ve Kullanılabilirlik

## Kapsam

Bu sürüm final öncesi UI/UX ve performans cilasıdır. **Optimizer matematiği, NFE hesapları, checkpoint mekanizması veya SQLite veri modeli değişmedi.**

### Üretim paketi

- React.lazy ve Suspense ile dokuz bağımsız laboratuvar/görsel modül **sayfa seçimine göre** yükleniyor.
- Kod bölme üretim paketinde Vite/Rollup tarafından yapılır. `npm.cmd run report:bundle` gerçek JS dosya boyutlarını yazdırır. Bazı parçalar tekrar kullanılabilecek ortak bağımlılıklar içerir; rapordaki **toplam JS** ilk sayfa aktarım yükü ile aynı değildir.
- Başarısız dinamik içe aktarmada hata paneli, tekrar yükleme düğmesi ve klavye erişimi sunulur.
- Arayüz sürümü `frontend/package.json` üzerinden okunur. API sürümü 2.15.0.

### Erişilebilirlik ve küçük ekran

- 390 px mobil menü açma/kapama; `aria-expanded` ve `aria-controls`.
- `Escape` ile kapatma ve menü düğmesine odak dönüşü; görünür kapatma düğmesi.
- Ana içeriğe atla bağlantısı, belirgin `:focus-visible`, `aria-live` yükleme metni.
- Dar ekranlarda başlık, stat kartı ve sayfa içeriklerinde taşmanın azaltılması.
- `prefers-reduced-motion` tercihi korunur.

### Doğrulama

- Backend pytest: önceki 536 + 4 yeni sürüm/UI sözleşmesi testi = **540** test.
- Windows Playwright hedefi: önceki 10 + 2 yeni mobil/lazy modül testi = **12**.
- Windows TypeScript/Vite derlemesi ve Docker sağlık kontrolleri ayrıca doğrulanmalıdır.
- Sürüm **yerel/akademik kullanıma** yöneliktir; çok kullanıcılı internet yayını için kimlik doğrulama ve yetkilendirme yoktur.

### Kurulum

1. SQLite arşivini yedekle, Docker konteynerlerini durdur.
2. ZIP'i `C:\VS CODE PROJE` klasörüne `Expand-Archive ... -Force` ile aç.
3. Backend `pytest -q`, frontend `npm.cmd run build`, `npm.cmd run report:bundle`, `npm.cmd run test:e2e`.
4. `powershell -ExecutionPolicy Bypass -File .\scripts\verify_docker_windows.ps1`.

Sonraki hedef: v3.0.0 profesyonel final, GitHub/LinkedIn/CV ve akademik sunum.
