# Future DailyBase integration

A future importer could copy immutable raw files to R2, retain endpoint, query dates and SHA-256 as provenance, and write normalized account, day, measurement, sleep, and activity entities to D1. Preserve source record IDs, timestamp and timezone, raw object keys, schema version, and null values. Use content hashes and source IDs as import idempotency keys. No Cloudflare integration is implemented here.
