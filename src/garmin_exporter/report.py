import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from .storage import atomic_json, atomic_bytes, digest


def report(root):
    root = Path(root)
    state_path = root / "manifest/export_state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {"queries": {}}
    entries = state.get("queries", {})
    schemas = defaultdict(Counter)
    counts = Counter()
    corrupt = []
    def walk(value, path="$"):
        t = "null" if value is None else type(value).__name__
        schemas[path][t] += 1
        if isinstance(value, dict):
            for k, v in value.items(): walk(v, path + "." + k)
        elif isinstance(value, list):
            for v in value: walk(v, path + "[]")
    for key, item in entries.items():
        counts[item.get("status", "unknown")] += 1
        file = root / item.get("path", "missing")
        if item.get("status") != "success": continue
        if not file.is_file() or digest(file) != item.get("sha256"):
            corrupt.append(key); continue
        if file.suffix == ".json":
            try: walk(json.loads(file.read_text()))
            except (ValueError, UnicodeError): corrupt.append(key)
    result = {"plan": state.get("last_plan"), "query_status_counts": dict(counts), "integrity_failures": corrupt,
              "schema": {k: dict(v) for k, v in schemas.items()},
              "assessment": "Historical completeness is not established. The scan is bounded by the selected dates; failures, missing data, and unimplemented endpoints may remain."}
    out = root / "reports"
    atomic_json(out / "inventory.json", result)
    atomic_json(out / "errors.json", {k: v for k, v in entries.items() if v.get("status") != "success"})
    lines = ["# Export inventory", "", result["assessment"], "", "## Query statuses", ""]
    lines.extend(f"- {k}: {v}" for k, v in sorted(counts.items()))
    lines.extend(["", f"Integrity failures: {len(corrupt)}", "", "## Scope", "", "Unscanned dates and unsupported datasets are not checked. Empty responses do not prove a metric was not recorded.", "", "## Future integration", "", "Potential entities include account, daily summary, sleep, measurements, activity, and raw artifact."])
    atomic_bytes(out / "inventory.md", ("\n".join(lines)+"\n").encode())
    out.mkdir(parents=True, exist_ok=True)
    import io
    buf = io.StringIO(newline="")
    writer = csv.writer(buf); writer.writerow(["path", "type", "occurrences"])
    for path, types in sorted(schemas.items()):
        for typ, n in sorted(types.items()): writer.writerow([path, typ, n])
    atomic_bytes(out / "data_dictionary.csv", buf.getvalue().encode())
    return result
