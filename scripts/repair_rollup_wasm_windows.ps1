# Rollup native module blocked by Windows Application Control.
# Reinstalls ONLY frontend npm dependencies using official Rollup WASM package.
# This script does not change system security settings or application databases.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $projectRoot 'frontend'
$manifest = Join-Path $frontendRoot 'package.json'
$lock = Join-Path $frontendRoot 'package-lock.json'
$modules = Join-Path $frontendRoot 'node_modules'

if (-not (Test-Path -LiteralPath $manifest)) {
    throw 'frontend/package.json bulunamadi. Hotfix dosyalarini proje kokune cikardiginizdan emin olun.'
}
$p = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
if ($p.devDependencies.rollup -ne 'npm:@rollup/wasm-node@4.68.2') {
    throw 'WASM Rollup bagimliligi package.json icinde bulunamadi. Hotfix ZIP dosyasini tekrar acin.'
}
if ($p.overrides.rollup -ne '$rollup') {
    throw 'Rollup bagimlilik gecersiz kilmasi eksik.'
}

$backupDir = Join-Path ([System.IO.Path]::GetTempPath()) ('metaheuristic-rollup-before-wasm-' + (Get-Date -Format 'yyyyMMdd-HHmmssfff'))
New-Item -Path $backupDir -ItemType Directory -Force | Out-Null
if (Test-Path -LiteralPath $lock) {
    Copy-Item -LiteralPath $lock -Destination (Join-Path $backupDir 'package-lock.json')
    Write-Host "Onceki package-lock.json yedeklendi: $backupDir"
}

Push-Location $frontendRoot
try {
    Write-Host '[1/4] Eski frontend npm bagimliliklari kaldiriliyor...'
    if (Test-Path -LiteralPath $modules) {
        Remove-Item -LiteralPath $modules -Recurse -Force
    }
    if (Test-Path -LiteralPath $lock) {
        Remove-Item -LiteralPath $lock -Force
    }

    Write-Host '[2/4] Resmi Rollup WASM bagimliligi ve frontend paketleri kuruluyor...'
    & npm.cmd install --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw "npm install basarisiz (kod: $LASTEXITCODE). Internet baglantisini ve npm hatasini kontrol edin." }

    Write-Host '[3/4] Gercekten WASM Rollup yuklendigini kontrol ediyoruz...'
    & node.exe .\scripts\check_rollup_wasm.cjs
    if ($LASTEXITCODE -ne 0) { throw 'WASM Rollup dogrulanamadi. npm ls rollup ciktisini paylasin.' }

    Write-Host '[4/4] Bagimlilik agaci...'
    & npm.cmd ls rollup
    if ($LASTEXITCODE -ne 0) { throw 'npm bagimlilik agacinda hata bulundu.' }

    Write-Host 'WASM Rollup hazir. Siradaki komutlar: npm.cmd run build ; npm.cmd run test:e2e'
}
finally {
    Pop-Location
}
