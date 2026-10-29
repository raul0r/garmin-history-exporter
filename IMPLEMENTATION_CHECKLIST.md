# Implementation checklist

- [ ] API contract: document every accessible official read operation with parameters, response and constraints; implement verified missing operations and identify inaccessible specifications.
- [ ] Recovery: lock each archive, record pending and failed requests, verify cached files, and test retries, authentication and pagination including malformed and repeated pages.
- [ ] Reporting: distinguish query coverage from observed dates and record counts, report activity and original-file aggregates, and document schema denominators without sample values.
- [ ] Installation: verify clean installation and entry points, exercise supported launchers, and add credential-free cross-platform CI for supported stable Python versions.
- [ ] Delivery: document boundaries, recovery, security, troubleshooting and verification; commit reviewed files and publish a draft PR if possible.
