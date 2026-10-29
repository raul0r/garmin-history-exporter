# Garmin History Exporter — experimental prototype

**Status: incomplete; not ready for public release or a lossless archive.** This prototype uses Garmin's official Python client to save responses locally, resume verified requests, and generate a preliminary schema inventory. Authentication, a snapshot and a seven-day export have been tested against a live account; complete historical coverage is not established. See limitations below before running it.

## Setup

1. Install Python 3.12+ and create a Garmin Personal API key in Garmin Connect Web settings. The key is shown once; treat it as a password. See [Garmin instructions](https://developer.garmin.com/gc-developer-program/personal/personal-api/).
2. Create `.env` locally with `GARMIN_PERSONAL_API_KEY` set to your key. Never commit or share it. Alternatively, use Garmin's key file `~/.config/garmin/connect-personal-api-key`.
3. Run `./run.sh --help` on Linux/macOS or `.\run.ps1 --help` in PowerShell. The launchers create a virtual environment, install dependencies, and forward arguments. On Windows, PowerShell execution policy may require allowing local scripts.

To install manually: `python -m venv .venv`, activate it, and run `python -m pip install .`. Then run `garmin-export auth-test`, `garmin-export snapshot --date 2026-10-27`, or `garmin-export full --start-date 2015-01-01 --end-date 2026-10-27`. `garmin-export full --resume` reuses successful requests with matching SHA-256 hashes; reuse is always enabled. `garmin-export report` and `garmin-export status` work offline. `--output` precedes the command. Examples: `garmin-export full --categories sleep,hrv` and `garmin-export --output archive report`.

## Coverage and known gaps

There is no documented earliest-record discovery implemented. The default lookback is not a guarantee; choose an earlier start date to scan more. Every day is examined for daily methods without stopping at gaps. Range methods use 30-day windows by default. Not every possible Garmin API endpoint has been investigated: the Swagger UI was not accessible during development. Respiration and other requested metrics have not been separately established as available; a field might appear within another returned payload. No claim is made that a range response is exhaustive or that empty means not recorded. Dataset details are in [docs/DATASETS.md](docs/DATASETS.md).

This prototype has important missing work: token renewal has not been validated against a real account; it does not verify real API pagination or server range limits; does not provide complete record counts, observed dates, activity statistics, or day-by-day coverage; does not implement a complete category taxonomy or full schema frequencies; and has limited live validation. A failed or unsupported endpoint is recorded as a failure, but cannot be reliably classified without live responses. Activity pagination assumes list-shaped pages and stops at an empty page; real server pagination semantics must be verified with Garmin. No production or comprehensive end-to-end validation has been done. Do not rely on it as your only backup.

## Storage and privacy

`output/raw/` contains full JSON results; `output/activities/` contains activity detail, workouts and ZIP bytes; `output/manifest/export_state.json` holds request metadata and hashes; `output/reports/` holds `inventory.json`, `inventory.md`, `data_dictionary.csv` and `errors.json`. All may contain sensitive health or GPS information. Do not upload, share, or commit them. Garmin's token cache is stored outside this directory by the official client and is also sensitive. Protect files with OS permissions and encrypted storage. To revoke a key, delete it in Garmin Connect, which invalidates associated tokens; then create a new one.

The report contains paths and data structure names but not sampled values. It is preliminary and is not a completeness certificate. Request exceptions are recorded by type and status rather than their potentially sensitive message. Contributions should use synthetic data only. Test with `PYTHONPATH=src python -m unittest discover -s tests -v` on Unix; in PowerShell set `$env:PYTHONPATH='src'` first.

Official references: [client](https://github.com/garmin/connect-personal-api-python), [FAQ](https://developer.garmin.com/gc-developer-program/personal/personal-faq), [Swagger](https://developer.garmin.com/gc-developer-program/personal/swagger-docs). This independent project is not affiliated with Garmin.


> **Full historical export readiness:** Not yet ready. CLI writers are protected by a process lock, but endpoint coverage and historical completeness are not established, and token renewal has not been verified against actual expiry. Use separate output directories and avoid multi-year runs until these gaps are resolved. Original downloads are checked as ZIP archives, but that does not establish that their contents are complete or usable.


## Recovery and report interpretation

Use one archive per account. CLI export and report commands take an exclusive OS lock; a leftover `.export.lock` file is harmless because the lock is held by the process, not by file existence. Do not delete it during a run. Completed requests are reused after checksum and format checks; pending, failed, missing and corrupt files are requested again. An interrupted request can leave a pending checkpoint and a file; the request is repeated. A 401 triggers one forced token renewal; persistent errors are recorded without response text. Garmin's client does not expose HTTP response headers on its HTTP error, so server Retry-After headers are unavailable in that case.

Reports separate requested dates from dates found in recognized record date fields. Record counts count top-level array elements or the documented daily summaries `data` array; other shapes are unknown and array elements may include duplicates. Schema occurrences count values, including array elements, and `responses_present` counts successful JSON files containing the path. ZIP checks validate archive structure and CRC, not FIT semantics. GPS availability is not established. Error reports and manifests may contain activity identifiers and must remain private.

For a small verification after installation, run `garmin-export --output output-smoke snapshot --date 2026-10-27`, then `garmin-export --output output-smoke report`. A proposed bounded historical run, once remaining validation is complete, is `garmin-export --output output-history full --start-date 2015-01-01 --end-date 2026-10-27`; resume with the identical command and `--resume`. This scans only those dates and implemented datasets, and is not an all-time completeness claim. Inspect failures and storage before extending the range.
