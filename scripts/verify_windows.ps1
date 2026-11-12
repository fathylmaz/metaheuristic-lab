# Validate the current checkout. No files or SQLite records are deleted.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$python = Join-Path $backend '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw "Python sanal ortamı bulunamadı: $python" }
Write-Host '[1/4] Backend testleri...' -ForegroundColor Cyan
Push-Location $backend
try { & $python -m pytest -q; if ($LASTEXITCODE -ne 0) { throw 'Backend testleri başarısız' } }
finally { Pop-Location }
Write-Host '[2/4] API sözleşmesi ve güvenlik kontrolleri...' -ForegroundColor Cyan
Push-Location $backend
try { & $python -m pytest -q tests/test_release_safety.py; if ($LASTEXITCODE -ne 0) { throw 'API smoke testleri başarısız' } }
finally { Pop-Location }
Write-Host '[3/4] Frontend üretim derlemesi...' -ForegroundColor Cyan
Push-Location $frontend
try { & npm.cmd run build; if ($LASTEXITCODE -ne 0) { throw 'Frontend derlemesi başarısız' } }
finally { Pop-Location }
Write-Host '[4/4] Tarayıcı testleri (Playwright kuruluysa)...' -ForegroundColor Cyan
$playwright = Join-Path $frontend 'node_modules\.bin\playwright.cmd'
if (Test-Path $playwright) {
    Push-Location $frontend
    try { & npm.cmd run test:e2e; if ($LASTEXITCODE -ne 0) { throw 'Tarayıcı testleri başarısız' } }
    finally { Pop-Location }
} else {
    Write-Warning 'Playwright kurulu değil; tarayıcı testleri atlandı. frontend klasöründe npm.cmd install ve npx.cmd playwright install chromium çalıştırın.'
}
Write-Host 'Uygulanabilir bütün kontroller tamamlandı.' -ForegroundColor Green
