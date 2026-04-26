param(
    [string]$Version = "0.1.0",
    [string]$InputDir = "dist/app",
    [string]$OutputDir = "dist/win7",
    [string]$AppName = "GenericaAgent"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $InputDir)) {
    throw "InputDir '$InputDir' not found. Please place Win7-compatible binaries under this directory first."
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$portableRoot = Join-Path $OutputDir "$AppName-$Version-win7-portable"
if (Test-Path $portableRoot) {
    Remove-Item $portableRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $portableRoot -Force | Out-Null

Copy-Item "$InputDir/*" $portableRoot -Recurse -Force

# Keep user data local for portable mode
$runtimeDirs = @("data", "logs", "cache")
foreach ($dir in $runtimeDirs) {
    New-Item -ItemType Directory -Path (Join-Path $portableRoot $dir) -Force | Out-Null
}

$portableConfig = @"
[app]
mode = portable
log_dir = ./logs
data_dir = ./data
cache_dir = ./cache
"@

$portableConfig | Set-Content -Encoding UTF8 (Join-Path $portableRoot "portable.ini")

$zipName = "$AppName-$Version-win7-portable.zip"
$zipPath = Join-Path $OutputDir $zipName
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path "$portableRoot/*" -DestinationPath $zipPath -CompressionLevel Optimal

Write-Host "Portable package created: $zipPath"
