# Metaheuristic Lab v2.13.0 — Kalıcı bağımsız koşu checkpoint'leri

v2.12.0 üzerinde geriye dönük uyumlu yükseltme.

**Özellikler:** Üç deney türü için bağımsız koşu başına atomik SQLite checkpoint; doğrulanmış kurtarma; SHA-256, kod ve çalışma ortamı parmak izi; tamamlanan deneyi arşivleme ve ara kayıt temizliği; uygulamada disk üzerindeki checkpoint ve yeniden kullanılan koşu sayaçları.

**Sınır:** Koşu ortasında continuation yok. Değişen algoritma veya Python/NumPy ortamı ile eski checkpoint birleştirilmez. Çok worker / internete açık kullanım desteklenmez.

**Güncelleme:** Docker ve yerel API sunucularını durdurun. SQLite deney yedeğinizi alın. Downloads'a indirilen ZIP'i `C:\VS CODE PROJE` dizinine `Expand-Archive -Force` ile açın. `.git`, `.venv`, `node_modules` ve SQLite verileri paket dışında tutulur.

**Windows doğrulama:**

```powershell
cd "C:\VS CODE PROJE\metaheuristic-lab\backend"
.\.venv\Scripts\python.exe -m pytest -q
cd "C:\VS CODE PROJE\metaheuristic-lab\frontend"
npm.cmd install
npm.cmd run build
npm.cmd run test:e2e
cd "C:\VS CODE PROJE\metaheuristic-lab"
powershell -ExecutionPolicy Bypass -File .\scripts\verify_docker_windows.ps1
```

**Kritik doğrulama:** Tamamlanan bir tohum checkpoint'i bulunan `running` işin API restart sonrası `reused_units > 0` olması ve eksik tohumlar hesaplandıktan sonra sonucun Akademik Raporlar'da görüntülenebilmesi. Kesintiyi manuel tetiklemek için çalışan Docker konteynerini zorla sonlandırmak yerine otomatik backend testleri tercih edilir.

**Ayrıntı:** [`CHECKPOINT_METHODOLOGY.md`](CHECKPOINT_METHODOLOGY.md).
