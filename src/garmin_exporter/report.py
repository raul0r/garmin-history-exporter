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
    categories = defaultdict(lambda: {"queries": 0, "successful": 0, "empty": 0, "failed": 0, "bytes": 0, "query_start": None, "query_end": None})
    corrupt = []
    def walk(value, path="$"):
        t = "null" if value is None else type(value).__name__
        schemas[path][t] += 1
        if isinstance(value, dict):
            for k, v in value.items(): walk(v, path + "." + k)
        elif isinstance(value, list):
            for v in value: walk(v, path + "[]")
    for key, item in entries.items():
        status = item.get("status", "unknown")
        counts[status] += 1
        name = key.split(":", 1)[0]
        category = categories[name]
        category["queries"] += 1
        category["successful" if status == "success" else "failed"] += 1
        category["empty"] += int(bool(item.get("empty")))
        category["bytes"] += item.get("bytes", 0) if status == "success" else 0
        dates = [x for x in item.get("args", []) if isinstance(x, str) and len(x) == 10 and x[4:5] == "-" and x[7:8] == "-"]
        if dates:
            category["query_start"] = min([category["query_start"]] + dates) if category["query_start"] else min(dates)
            category["query_end"] = max([category["query_end"]] + dates) if category["query_end"] else max(dates)
        file = root / item.get("path", "missing")
        if item.get("status") != "success": continue
        if not file.is_file() or digest(file) != item.get("sha256"):
            corrupt.append(key); continue
        if file.suffix == ".json":
            try: walk(json.loads(file.read_text()))
            except (ValueError, UnicodeError): corrupt.append(key)
    result = {"plan": state.get("last_plan"), "query_status_counts": dict(counts), "integrity_failures": corrupt,
              "categories": dict(categories), "schema": {k: dict(v) for k, v in schemas.items()},
              "assessment": "Historical completeness is not established. The scan is bounded by the selected dates; failures, missing data, and unimplemented endpoints may remain."}
    out = root / "reports"
    atomic_json(out / "inventory.json", result)
    atomic_json(out / "errors.json", {k: v for k, v in entries.items() if v.get("status") != "success"})
    lines = ["# Export inventory", "", result["assessment"], "", "## Query statuses", ""]
    lines.extend(f"- {k}: {v}" for k, v in sorted(counts.items()))
    lines.extend(["", "## Categories (request coverage, not record dates)", "", "| Category | Successful | Failed | Empty responses | Bytes |", "|---|---:|---:|---:|---:|"])
    lines.extend(f"| {name} | {x['successful']} | {x['failed']} | {x['empty']} | {x['bytes']} |" for name, x in sorted(categories.items()))
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
