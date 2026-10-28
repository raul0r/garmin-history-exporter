$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
py -3 -c "import sys; assert sys.version_info >= (3,12), 'Python 3.12 or newer required'"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (!(Test-Path .venv)) { py -3 -m venv .venv }
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& .venv/Scripts/python.exe -m pip install .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& .venv/Scripts/garmin-export.exe full @args
exit $LASTEXITCODE
