param(
    [switch]$Integration
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")
Set-Location $root

$python = Join-Path $root "venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

$pytestArgs = @("-m", "pytest")
if ($Integration) {
    $env:RUN_INTEGRATION = "1"
} else {
    $pytestArgs += @("-m", "not integration")
}

& $python @pytestArgs
exit $LASTEXITCODE
