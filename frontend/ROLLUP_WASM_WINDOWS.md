# Metaheuristic Lab v2.11.0 - Rollup WASM Windows repair

Windows Application Control, `rollup.win32-x64-msvc.node` dosyasını engellerse bu paket native Rollup yerine resmi `@rollup/wasm-node` 4.68.2 sürümünü doğrudan `rollup` adı altında kullanır.

- `frontend/package.json`: `rollup` npm alias doğrudan devDependency olarak tanımlanır; `overrides` tüm bağımlılık ağacına aynı seçimi uygular.
- `scripts/repair_rollup_wasm_windows.ps1`: yalnızca frontend içindeki `node_modules` ve `package-lock.json` dosyasını yeniden oluşturur. Önceki lock dosyası Windows geçici dizininde yedeklenir. SQLite veritabanına, Python ortamına veya Git geçmişine dokunulmaz.
- İşlemi yürütmeden önce Vite ve Playwright sunucularını kapatın. Yeniden kurulum için internet gerekebilir.
- Gerçek WASM paket kimliği doğrulanmadan betik başarılı sayılmaz.

Kök proje klasöründe:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\repair_rollup_wasm_windows.ps1
cd .\frontend
npm.cmd run build
npm.cmd run test:e2e
```

Bu onarım Node/npm paket yüklemeleri ile ilgili olup Windows güvenlik ayarlarını değiştirmez. Tam Vite ve tarayıcı testlerinin kullanıcının ortamında doğrulanması gerekir.
