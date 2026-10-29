# Release checklist

## Required for implemented datasets

- [x] Inclusive day and range iteration, capped-page traversal until empty, duplicate suppression and repeated-page detection. Synthetic pagination and failure tests; range limits remain a Garmin-side unknown.
- [x] Exclusive process lock, pending checkpoints and checksum/format checks on resume. Synthetic lock and interruption tests; Windows lock test passed in PR CI on Python 3.12–3.14.
- [x] Record failures and stop after a persistent 401; one forced renewal on 401. Synthetic tests cover renewal, persistent 401 and retry limits; actual token expiry has not been exercised.
- [x] Preserve returned ZIP bytes and JSON values (JSON is reserialized). Failed and pending requests remain visible.
- [x] Python 3.12 clean install and offline CLI tested; credential-free OS/Python matrix and launcher forwarding checks configured.

## Truthful reporting

- [x] Distinguish query status, recognized date fields, countable array elements and unknown record counts; count unchecked planned daily/range requests and integrity failures. Synthetic tests and offline week-archive verification.
- [x] Dataset-specific schema types, occurrence counts and response denominators; activity and ZIP aggregates. These are structural observations, not completeness proofs.

## Deferred within this bounded release

- GPS interpretation and FIT semantic validation: original ZIP bytes are preserved and ZIP CRC checked; these enhancements require format-specific parsing and are not required to retrieve the supported endpoint responses.
- Automatic earliest-history discovery and exhaustive per-measurement classifications: no verified contract establishes them; users choose boundaries and review unresolved coverage.

## External documentation

- [ ] Verify the parameters and response contracts of `/usersummary-service/usersummary/daily` and `/weight-service/weight/all/{startDate}/{endDate}` from Garmin's OpenAPI specification. They remain unimplemented until that specification or equivalent authoritative evidence is accessible.
