$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)"
if ($LASTEXITCODE -ne 0) { Write-Error 'Python 3.12 or newer is required.'; exit 1 }
if (!(Test-Path .venv)) { py -3 -m venv .venv; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
& .venv/Scripts/python.exe -m pip install .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ($args.Count -eq 0) { $args = @('--help') }
& .venv/Scripts/garmin-export.exe @args
exit $LASTEXITCODE
