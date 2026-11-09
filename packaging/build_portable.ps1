# Builds a single-file portable GeneratorPassword.exe for Windows 10/11.
# Usage (from the repo root):  powershell -ExecutionPolicy Bypass -File packaging\build_portable.ps1
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$version = (python -c "import passgen; print(passgen.__version__)").Trim()

python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed - build aborted" }

python -m flet.cli pack main.py `
    --name GeneratorPassword `
    --icon packaging\icon.ico `
    --add-data "passgen/assets:passgen/assets" `
    --product-name "GeneratorPassword" `
    --file-description "GeneratorPassword - secure password generator (portable)" `
    --product-version $version `
    --file-version "$version.0" `
    --copyright "zakr1, MIT License" `
    --distpath dist `
    -y
if ($LASTEXITCODE -ne 0) { throw "flet pack failed" }

$exe = Get-Item dist\GeneratorPassword.exe
"Built $($exe.FullName)  ($([math]::Round($exe.Length / 1MB, 1)) MB)"
(Get-FileHash $exe -Algorithm SHA256).Hash | Out-File -Encoding ascii dist\GeneratorPassword.exe.sha256
"SHA256: $(Get-Content dist\GeneratorPassword.exe.sha256)"
