param(
    [string]$AppRoot = "."
)

$ErrorActionPreference = "Stop"
$failed = $false

function Step($name, [scriptblock]$block) {
    Write-Host "[CHECK] $name"
    try {
        & $block
        Write-Host "  [OK] $name" -ForegroundColor Green
    }
    catch {
        $script:failed = $true
        Write-Host "  [FAIL] $name - $($_.Exception.Message)" -ForegroundColor Red
    }
}

Step "OS=Windows 7 SP1" {
    $os = Get-WmiObject Win32_OperatingSystem
    if ($os.Version -notlike "6.1*") { throw "OS version is $($os.Version), expected 6.1.x" }
    if (-not ($os.ServicePackMajorVersion -ge 1)) { throw "Service Pack 1 is required" }
}

Step "Architecture is x64/x86" {
    $arch = $env:PROCESSOR_ARCHITECTURE
    if ($arch -notin @("AMD64", "x86")) { throw "Unsupported architecture: $arch" }
}

Step "TLS 1.2 available" {
    $proto = [Net.ServicePointManager]::SecurityProtocol
    if (-not ($proto.ToString().Contains("Tls12"))) {
        [Net.ServicePointManager]::SecurityProtocol = $proto -bor [Net.SecurityProtocolType]::Tls12
    }
}

Step "UTF-8 codepage available" {
    $cp = & cmd /c chcp
    if ($cp -notmatch "65001") {
        Write-Host "  [INFO] Current code page is not UTF-8; recommend: chcp 65001"
    }
}

Step "Writable temp and app directories" {
    $targets = @($env:TEMP, (Resolve-Path $AppRoot).Path)
    foreach ($dir in $targets) {
        $probe = Join-Path $dir (".write-test-" + [guid]::NewGuid().ToString() + ".tmp")
        "ok" | Out-File -FilePath $probe -Encoding ascii
        Remove-Item $probe -Force
    }
}

Step "Root certificate store accessible" {
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root","LocalMachine")
    $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadOnly)
    if ($store.Certificates.Count -lt 1) { throw "Root certificate store is empty" }
    $store.Close()
}

if ($failed) {
    Write-Host "\nPreflight: FAILED" -ForegroundColor Red
    exit 1
}

Write-Host "\nPreflight: PASSED" -ForegroundColor Green
exit 0
