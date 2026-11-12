# Metaheuristic Lab 3.0.0 — Yayın kontrol listesi

Bu liste kasıtlı olarak **yerel testler başarılı** ile **GitHub yayını tamamlandı** durumlarını ayırır.

## A — Teknik doğrulama

- [ ] `backend` → `.\.venv\Scripts\python.exe -m pytest -q` (yeni v3.0.0 toplamını kayıt altına al).
- [ ] `frontend` → `npm.cmd install`, `npm.cmd run build`, `npm.cmd run report:bundle`, `npm.cmd run test:e2e`.
- [ ] Proje kökünde `powershell -ExecutionPolicy Bypass -File .\scripts\verify_windows.ps1`.
- [ ] `powershell -ExecutionPolicy Bypass -File .\scripts\verify_docker_windows.ps1` ve `3.0.0` health yanıtı.
- [ ] Gerçek deney kuyruğu: oluştur, tamamla, arşive aç, API konteynerini yeniden başlat, kaydın kaldığını kontrol et.
- [ ] Bağımsız deneyin checkpoint yeniden kullanımını veya buna ait otomatik test kanıtını sakla.
- [ ] Bilimsel denetimde `status=passed`; ilgisiz bozuk kayıtları silmeden ayrı belirt.
- [ ] `py -3.13 .\scripts\release_audit.py` ile sürüm, dosya güvenliği ve belgeleri kontrol et.

## B — Veri ve izinler

- [ ] `py -3.13 .\scripts\backup_experiments.py` ile SQLite yedeği al, manifest SHA doğrula.
- [ ] `.gitignore` kontrolü: `backend/data`, `backups`, `.env`, `outputs`, `node_modules`, `dist`, `test-results`.
- [ ] Projeyi Git'e eklemeden önce `git status` ve `git diff --cached --stat` incele; kişisel veriler, `.sqlite3`, yedek ZIP veya token yükleme.
- [x] **Lisans kararı:** Proje sahibi MIT lisansını onayladı; kök dizinde `LICENSE` eklendi. Telif ve üçüncü taraf katkı izinleri yayın öncesi yine kontrol edilmeli.
- [ ] Varsa katkıda bulunanların isim, kod ve görüntü kullanım izinlerini doğrula.

## C — GitHub / görseller

- [ ] Gerçek v3 ekran görüntülerini `npm.cmd run capture:screenshots` ile oluştur; görüntülerde yerel özel veri var mı denetle.
- [ ] `README.md`, `README_TR.md`, `README_EN.md` metnini gerçek repo bağlantılarıyla son kez gözden geçir.
- [ ] Kodun ve dokümanların tarihli final commit'ini oluştur; GitHub Actions işlerini repo üzerinde çalıştır.
- [ ] CI backend, frontend, tarayıcı ve Docker işlerinin **gerçek GitHub bağlantısı veya ekran görüntüsü**.
- [ ] Repo `public` yapılacaksa bundan önce saklı dosyalar, izinler ve lisansı yeniden kontrol et.
- [ ] İsteğe bağlı: etiket `v3.0.0` ve Release sayfası; notlarda 'local research/portfolio' kapsamını açıkça belirt.

## D — Profesyonel yayın

- [ ] `docs/PORTFOLIO_KIT_TR.md` metnini LinkedIn profil alanı/karakter sınırına göre düzenle.
- [ ] Örnek raporda kullanılan 3 tekrarlı sonuçları **pilot deney** olarak etiketle; genel başarı iddiası üretme.
- [ ] Gerçek v3 ekran görüntüleri, sunum ve README bağlantılarını LinkedIn proje kaydına ekle.
- [ ] CV maddelerinden doğrulanabilir tek/iki cümle seç; gerçek GitHub repo URL'sini koy.

**Yayın durumu:** GitHub deposu herkese açık, MIT lisansı eklendi ve dört CI görevi başarılı. Resmî v3.0.0 Release ve LinkedIn yayını bekliyor.
