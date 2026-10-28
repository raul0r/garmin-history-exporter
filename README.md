# Garmin History Exporter — experimental prototype

**Status: incomplete; not ready for public release or a lossless archive.** This prototype uses Garmin's official Python client to save responses locally, resume verified requests, and generate a preliminary schema inventory. It has not been tested against a live Garmin account. See limitations below before running it.

## Setup

1. Install Python 3.12+ and create a Garmin Personal API key in Garmin Connect Web settings. The key is shown once; treat it as a password. See [Garmin instructions](https://developer.garmin.com/gc-developer-program/personal/personal-api/).
2. Copy `.env.example` to `.env` and set `GARMIN_PERSONAL_API_KEY` locally. Never commit or share it. Alternatively, use Garmin's key file `~/.config/garmin/connect-personal-api-key`.
3. Run `./run.sh` on Linux/macOS or `.\run.ps1` in PowerShell. The launchers create a virtual environment and install dependencies. On Windows, PowerShell execution policy may require allowing local scripts. This can take a long time and defaults to the previous 3,650 days.

To install manually: `python -m venv .venv`, activate it, and run `python -m pip install .`. Then run `garmin-export auth-test`, `garmin-export snapshot --date 2026-10-27`, or `garmin-export full --start-date 2015-01-01 --end-date 2026-10-27`. `garmin-export full --resume` reuses successful requests with matching SHA-256 hashes; reuse is always enabled. `garmin-export report` and `garmin-export status` work offline. `--output` precedes the command. Examples: `garmin-export full --categories sleep,hrv` and `garmin-export --output archive report`.

## Coverage and known gaps

There is no documented earliest-record discovery implemented. The default lookback is not a guarantee; choose an earlier start date to scan more. Every day is examined for daily methods without stopping at gaps. Range methods use 30-day windows by default. Not every possible Garmin API endpoint has been investigated: the Swagger UI was not accessible during development. Respiration and other requested metrics have not been separately established as available; a field might appear within another returned payload. No claim is made that a range response is exhaustive or that empty means not recorded. Dataset details are in [docs/DATASETS.md](docs/DATASETS.md).

This prototype has important missing work: token renewal has not been validated against a real account; it does not verify real API pagination or server range limits; does not provide complete record counts, observed dates, activity statistics, or day-by-day coverage; does not implement a complete category taxonomy or full schema frequencies; and has no verified live connection. A failed or unsupported endpoint is recorded as a failure, but cannot be reliably classified without live responses. Activity pagination assumes list-shaped pages and terminates on a short page, which must be verified with Garmin. No production or comprehensive end-to-end validation has been done. Do not rely on it as your only backup.

## Storage and privacy

`output/raw/` contains full JSON results; `output/activities/` contains activity detail, workouts and ZIP bytes; `output/manifest/export_state.json` holds request metadata and hashes; `output/reports/` holds `inventory.json`, `inventory.md`, `data_dictionary.csv` and `errors.json`. All may contain sensitive health or GPS information. Do not upload, share, or commit them. Garmin's token cache is stored outside this directory by the official client and is also sensitive. Protect files with OS permissions and encrypted storage. To revoke a key, delete it in Garmin Connect, which invalidates associated tokens; then create a new one.

The report contains paths and data structure names but not sampled values. It is preliminary and is not a completeness certificate. Request exceptions are recorded by type and status rather than their potentially sensitive message. Contributions should use synthetic data only. Test with `PYTHONPATH=src python -m unittest discover -s tests -v` on Unix; in PowerShell set `$env:PYTHONPATH='src'` first.

Official references: [client](https://github.com/garmin/connect-personal-api-python), [FAQ](https://developer.garmin.com/gc-developer-program/personal/personal-faq), [Swagger](https://developer.garmin.com/gc-developer-program/personal/swagger-docs). This independent project is not affiliated with Garmin.
