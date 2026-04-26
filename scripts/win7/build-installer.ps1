param(
    [string]$Version = "0.1.0",
    [string]$InputDir = "dist/app",
    [string]$ISCC = "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $InputDir)) {
    throw "InputDir '$InputDir' not found. Please place Win7-compatible binaries under this directory first."
}

if (-not (Test-Path $ISCC)) {
    throw "ISCC not found at '$ISCC'. Install Inno Setup 6 first."
}

$iss = Join-Path $PSScriptRoot "build-installer.iss"
& $ISCC "/DAppVersion=$Version" $iss

Write-Host "Installer package created under dist/win7"
