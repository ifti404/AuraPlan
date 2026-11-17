param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $ProjectRoot
try {
    $Version = & $Python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ($LASTEXITCODE -ne 0) { throw "Could not run Python at '$Python'." }
    if ($Version -ne "3.12") {
        throw "Build with 64-bit Python 3.12 for the Vosk/PyAudio Windows wheels. Selected interpreter is Python $Version. Pass -Python with the full path to python.exe."
    }

    $BuildVenv = Join-Path $ProjectRoot ".venv-build"
    if (-not (Test-Path (Join-Path $BuildVenv "Scripts\python.exe"))) {
        & $Python -m venv $BuildVenv
        if ($LASTEXITCODE -ne 0) { throw "Could not create the packaging environment." }
    }
    $BuildPython = Join-Path $BuildVenv "Scripts\python.exe"
    & $BuildPython -m pip install -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) { throw "Could not install the app and packaging dependencies." }

    Remove-Item -LiteralPath (Join-Path $ProjectRoot "build") -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath (Join-Path $ProjectRoot "dist\AuraPlan") -Recurse -Force -ErrorAction SilentlyContinue
    & $BuildPython -m PyInstaller --noconfirm --clean AuraPlan.spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed." }

    $Bundle = Join-Path $ProjectRoot "dist\AuraPlan"
    New-Item -ItemType Directory -Path (Join-Path $Bundle "model") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $Bundle "data") -Force | Out-Null
    Copy-Item -Path (Join-Path $ProjectRoot "model\*") -Destination (Join-Path $Bundle "model") -Recurse -Force
    Set-Content -LiteralPath (Join-Path $Bundle "portable.mode") -Value "AuraPlan portable data mode" -Encoding ascii
    Copy-Item -LiteralPath (Join-Path $ProjectRoot "portable-model-README.txt") -Destination (Join-Path $Bundle "model\README.txt")
    & $BuildPython (Join-Path $ProjectRoot "make_portable_zip.py") $Bundle (Join-Path $ProjectRoot "dist\AuraPlan-portable.zip")
    if ($LASTEXITCODE -ne 0) { throw "Could not create the portable ZIP." }

    Write-Host "Created: $Bundle\AuraPlan.exe"
    Write-Host "Created: $ProjectRoot\dist\AuraPlan-portable.zip"
    Write-Host "Place extracted Vosk model files under: $Bundle\model\"
}
finally {
    Pop-Location
}
