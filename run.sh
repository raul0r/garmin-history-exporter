#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 -c 'import sys; assert sys.version_info >= (3,12), "Python 3.12 or newer required"'
[ -d .venv ] || python3 -m venv .venv
.venv/bin/python -m pip install .
exec .venv/bin/garmin-export full "$@"
