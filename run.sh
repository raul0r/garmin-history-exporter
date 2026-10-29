#!/bin/sh
set -eu
cd "$(dirname "$0")"
command -v python3 >/dev/null 2>&1 || { echo 'Python 3.12 or newer is required.' >&2; exit 1; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)' || { echo 'Python 3.12 or newer is required.' >&2; exit 1; }
[ -d .venv ] || python3 -m venv .venv
.venv/bin/python -m pip install .
[ "$#" -gt 0 ] || set -- --help
exec .venv/bin/garmin-export "$@"
