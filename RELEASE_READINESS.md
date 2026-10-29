# Monitored export release evidence

Scope is the endpoint wrappers listed in [docs/DATASETS.md](docs/DATASETS.md), not the entire Garmin Personal API. Two additional routes are unimplemented pending Garmin's OpenAPI specification: `/usersummary-service/usersummary/daily` needs its query parameters and response contract; `/weight-service/weight/all/{startDate}/{endDate}` needs its query options, range limits and response contract. The Swagger page rendered only a shell through the available reader, and direct DNS resolution failed during inspection. Garmin's specification or equivalent authoritative documentation is needed.

A prior live snapshot and seven-day export succeeded. Offline analysis of a temporary copy of the week archive found 78 successful queries, three listed activities, three structurally valid ZIPs and zero integrity failures. This establishes neither exhaustive response content nor all-time coverage. Token expiry, live pagination and Garmin's maximum range size are not verified. Start and end dates are explicit scan boundaries; earlier and later dates remain unchecked, and empty responses are not evidence that data was never recorded.

The previous PR CI matrix passed on Windows, macOS and Linux with Python 3.12, 3.13 and 3.14. Local Python 3.15 synthetic tests and a clean Python 3.12 installation were exercised. Consult current PR checks for the latest revision. The exporter records failures and pending queries, and a nonzero exit indicates unresolved requests or integrity failures. Review reports during the run. ZIP validation checks structure and CRC, not FIT semantics or GPS completeness.

From the repository, install using `python3 -m venv .venv` and `.venv/bin/python -m pip install .` on macOS/Linux. On Windows use `py -3 -m venv .venv` and `.venv\Scripts\python.exe -m pip install .`. Configure `GARMIN_PERSONAL_API_KEY` in a private `.env` file or use Garmin's key file. Never share that file or the token cache.

```sh
.venv/bin/garmin-export auth-test
.venv/bin/garmin-export --output output-smoke snapshot --date 2026-10-27
.venv/bin/garmin-export --output output-smoke report
.venv/bin/garmin-export --output output-history full --start-date 2015-01-01 --end-date 2026-10-27
```

Choose your own date boundaries. Interrupt with Ctrl-C. Resume by repeating the same command and options, optionally adding `--resume`; completed verified files are reused. Afterward run `.venv/bin/garmin-export --output output-history report` and inspect `reports/` privately. On Windows replace `.venv/bin/garmin-export` with `.venv\Scripts\garmin-export.exe`. Never run two processes against the same archive outside the CLI lock.
