param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvRoot = Join-Path $projectRoot ".venv-build"
$pythonExe = Join-Path $venvRoot "Scripts\python.exe"
$browserRoot = Join-Path $projectRoot ".build-browsers"
$iconPng = Join-Path $projectRoot "assets\app-icon.png"
$iconIco = Join-Path $projectRoot "assets\app.ico"

if ($Clean) {
    foreach ($target in @("build", "dist")) {
        $resolved = Join-Path $projectRoot $target
        if (Test-Path -LiteralPath $resolved) {
            Remove-Item -LiteralPath $resolved -Recurse -Force
        }
    }
}

if (-not (Test-Path -LiteralPath $pythonExe)) {
    py -3 -m venv $venvRoot
}

& $pythonExe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Failed to upgrade pip (exit code $LASTEXITCODE)" }
& $pythonExe -m pip install -r (Join-Path $projectRoot "requirements.txt") -r (Join-Path $projectRoot "requirements-build.txt")
if ($LASTEXITCODE -ne 0) { throw "Failed to install build dependencies (exit code $LASTEXITCODE)" }
$env:PLAYWRIGHT_BROWSERS_PATH = $browserRoot
& $pythonExe -m playwright install chromium
if ($LASTEXITCODE -ne 0) { throw "Failed to install Chromium (exit code $LASTEXITCODE)" }

if ((Test-Path -LiteralPath $iconPng) -and -not (Test-Path -LiteralPath $iconIco)) {
    & $pythonExe (Join-Path $projectRoot "scripts\prepare_icon.py") $iconPng $iconIco
    if ($LASTEXITCODE -ne 0) { throw "Failed to prepare the application icon (exit code $LASTEXITCODE)" }
}

Push-Location $projectRoot
try {
    & $pythonExe -m PyInstaller --noconfirm "FrameAnimeDesk.spec"
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (exit code $LASTEXITCODE)" }
} finally {
    Pop-Location
}

Write-Host "Build complete: $projectRoot\dist\FrameAnimeDesk.exe"
