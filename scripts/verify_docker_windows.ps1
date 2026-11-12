#requires -Version 5.1
# Local container smoke test. Leaves services running and never deletes SQLite data.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw 'Docker CLI bulunamadı. Docker Desktop kurulu ve açık olmalı.'
    }
    Write-Host '[1/4] Docker Compose yapılandırması...' -ForegroundColor Cyan
    & docker compose config --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Compose yapılandırması geçersiz.' }
    Write-Host '[2/4] Servislerin derlenmesi ve başlatılması...' -ForegroundColor Cyan
    & docker compose up --build -d --wait --wait-timeout 300
    if ($LASTEXITCODE -ne 0) { throw 'Docker servisleri sağlıklı başlamadı.' }
    Write-Host '[3/4] Yerel Nginx ve API sağlık kontrolü...' -ForegroundColor Cyan
    $web = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5173/' -TimeoutSec 15
    if ($web.StatusCode -ne 200 -or $web.Content -notmatch '<html') { throw 'Web sayfası beklenen HTML içeriğini döndürmedi.' }
    # Read the expected application version from the checkout, not a fixed release literal.
    $packageJsonPath = Join-Path $root 'frontend\package.json'
    if (-not (Test-Path -LiteralPath $packageJsonPath)) { throw 'Frontend package.json bulunamadı.' }
    $packageJson = Get-Content -LiteralPath $packageJsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $expectedVersion = [string] $packageJson.version
    if ([string]::IsNullOrWhiteSpace($expectedVersion)) { throw 'Frontend sürüm bilgisi boş.' }
    $health = Invoke-RestMethod -Uri 'http://127.0.0.1:5173/api/health' -TimeoutSec 15
    if ($health.status -ne 'ok' -or [string] $health.version -ne $expectedVersion) {
        throw ("API sağlık yanıtı beklenen sürümle eşleşmiyor. Beklenen: {0}; gelen: {1}; durum: {2}" -f $expectedVersion, $health.version, $health.status)
    }
    Write-Host ("API sürümü doğrulandı: {0}" -f $expectedVersion) -ForegroundColor Green
    $catalog = Invoke-RestMethod -Uri 'http://127.0.0.1:5173/api/catalog' -TimeoutSec 15
    # Do not assume a particular catalog response array structure; health endpoint already validates proxy.
    Write-Host '[4/4] Çalışan servis durumu...' -ForegroundColor Cyan
    & docker compose ps
    if ($LASTEXITCODE -ne 0) { throw 'Servis durumu görüntülenemedi.' }
    Write-Host 'Yerel Docker web ve API bağlantısı başarıyla doğrulandı.' -ForegroundColor Green
    Write-Host 'Uygulama: http://127.0.0.1:5173 (Docker servisleri çalışmaya devam ediyor)'
} finally {
    Pop-Location
}
