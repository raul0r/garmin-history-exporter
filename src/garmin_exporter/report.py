"""Privacy-conscious structural inventory of a local archive."""

import csv
import io
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from .exporter import valid_original
from .storage import atomic_bytes, atomic_json, digest


def report(root):
    root = Path(root)
    state_path = root / "manifest/export_state.json"
    state = (
        json.loads(state_path.read_text(encoding="utf-8"))
        if state_path.exists()
        else {"queries": {}}
    )
    entries = state.get("queries", {})
    statuses = Counter()
    categories = defaultdict(
        lambda: {
            "statuses": Counter(),
            "empty": 0,
            "bytes": 0,
            "query_start": None,
            "query_end": None,
            "observed_start": None,
            "observed_end": None,
            "records": 0,
            "record_count_unknown_responses": 0,
        }
    )
    schemas = defaultdict(Counter)
    schema_responses = defaultdict(set)
    corrupt = []
    activity_ids = set()
    activity_years = Counter()
    activity_types = Counter()
    originals = Counter()

    def walk(value, dataset, path, query):
        typ = "null" if value is None else type(value).__name__
        schemas[(dataset, path)][typ] += 1
        schema_responses[(dataset, path)].add(query)
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, dataset, path + "." + k, query)
        elif isinstance(value, list):
            for v in value:
                walk(v, dataset, path + "[]", query)

    def observed(category, value):
        if isinstance(value, dict):
            for field in ("calendarDate", "startTimeLocal", "startTimeGMT"):
                raw = value.get(field)
                if isinstance(raw, str):
                    try:
                        day = date.fromisoformat(raw[:10]).isoformat()
                    except ValueError:
                        continue
                    category["observed_start"] = min(
                        filter(None, [category["observed_start"], day])
                    )
                    category["observed_end"] = max(
                        filter(None, [category["observed_end"], day])
                    )
            for v in value.values():
                observed(category, v)
        elif isinstance(value, list):
            for v in value:
                observed(category, v)

    for key, item in entries.items():
        status = item.get("status", "unknown")
        statuses[status] += 1
        name = key.split(":", 1)[0]
        cat = categories[name]
        cat["statuses"][status] += 1
        dates = [
            x
            for x in list(item.get("args", [])) + list(item.get("kwargs", {}).values())
            if isinstance(x, str) and len(x) == 10 and x[4:5] == "-" and x[7:8] == "-"
        ]
        if dates:
            cat["query_start"] = min(filter(None, [cat["query_start"], *dates]))
            cat["query_end"] = max(filter(None, [cat["query_end"], *dates]))
        is_original = name == "activity" and item.get("path", "").endswith(
            "/original.zip"
        )
        if is_original:
            originals[status] += 1
        if status != "success":
            continue
        file = root / item.get("path", "missing")
        if not file.is_file() or digest(file) != item.get("sha256"):
            corrupt.append(key)
            if is_original:
                originals["integrity_failure"] += 1
            continue
        cat["bytes"] += file.stat().st_size
        if is_original:
            if not valid_original(file.read_bytes()):
                corrupt.append(key)
                originals["invalid_zip"] += 1
            else:
                originals["valid_zip"] += 1
            continue
        if file.suffix != ".json":
            continue
        try:
            value = json.loads(file.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError):
            corrupt.append(key)
            continue
        cat["empty"] += int(value is None or value == [] or value == {})
        walk(value, name, "$", key)
        observed(cat, value)
        # A top-level array is countable; a daily summaries data array is documented.
        records = (
            value
            if isinstance(value, list)
            else (
                value.get("data")
                if name == "daily_summaries" and isinstance(value, dict)
                else None
            )
        )
        if isinstance(records, list):
            cat["records"] += len(records)
        elif value is not None:
            cat["record_count_unknown_responses"] += 1
        if name == "activities" and isinstance(value, list):
            for activity in value:
                if not isinstance(activity, dict):
                    continue
                ident = activity.get("activityId")
                if ident is None or str(ident) in activity_ids:
                    continue
                activity_ids.add(str(ident))
                start = activity.get("startTimeLocal")
                if isinstance(start, str):
                    try:
                        activity_years[str(date.fromisoformat(start[:10]).year)] += 1
                    except ValueError:
                        pass
                kind = activity.get("activityType")
                if isinstance(kind, dict):
                    kind = kind.get("typeKey")
                activity_types[kind if isinstance(kind, str) else "unknown"] += 1
    schema = {}
    for (dataset, path), types in sorted(schemas.items()):
        schema.setdefault(dataset, {})[path] = {
            "types": dict(types),
            "null": types.get("null", 0),
            "non_null": sum(types.values()) - types.get("null", 0),
            "responses_present": len(schema_responses[(dataset, path)]),
        }
    assessment = (
        "Historical completeness is not established. The scan is bounded by the selected dates; "
        "failures, missing data, unexamined dates and unimplemented endpoints may remain."
    )
    result = {
        "plan": state.get("last_plan"),
        "query_status_counts": dict(statuses),
        "integrity_failures": corrupt,
        "categories": dict(categories),
        "schema": schema,
        "activities": {
            "unique_listed": len(activity_ids),
            "by_year": dict(activity_years),
            "by_type": dict(activity_types),
            "originals": dict(originals),
            "gps_availability": "not established",
        },
        "assessment": assessment,
        "counting_rules": "Records count top-level array elements or the daily_summaries data array; other response shapes are unknown. Arrays may contain duplicates. Schema occurrences count values, including array elements; responses_present counts distinct successful files containing the path.",
    }
    out = root / "reports"
    atomic_json(out / "inventory.json", result)
    atomic_json(
        out / "errors.json",
        {k: v for k, v in entries.items() if v.get("status") != "success"},
    )
    atomic_json(
        out / "summary.json",
        {
            "assessment": assessment,
            "query_status_counts": dict(statuses),
            "integrity_failures": len(corrupt),
            "activities": result["activities"],
        },
    )
    lines = [
        "# Export inventory",
        "",
        assessment,
        "",
        result["counting_rules"],
        "",
        "## Query statuses",
        "",
    ]
    lines.extend(f"- {k}: {v}" for k, v in sorted(statuses.items()))
    lines.extend(
        [
            "",
            "## Categories",
            "",
            "| Category | Successful | Failed or pending | Empty | Countable records | Observed dates | Bytes |",
            "|---|---:|---:|---:|---:|---|---:|",
        ]
    )
    for name, cat in sorted(categories.items()):
        lines.append(
            f"| {name} | {cat['statuses']['success']} | {sum(v for k, v in cat['statuses'].items() if k != 'success')} | {cat['empty']} | {cat['records']} | {cat['observed_start'] or '?'} to {cat['observed_end'] or '?'} | {cat['bytes']} |"
        )
    lines.extend(
        [
            "",
            f"Integrity failures: {len(corrupt)}",
            "",
            "Unselected categories and dates outside the plan are unchecked. Empty responses and null fields do not prove data was never recorded.",
        ]
    )
    atomic_bytes(out / "inventory.md", ("\n".join(lines) + "\n").encode())
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(["dataset", "path", "type", "occurrences", "responses_present"])
    for (dataset, path), types in sorted(schemas.items()):
        for typ, count in sorted(types.items()):
            writer.writerow(
                [dataset, path, typ, count, len(schema_responses[(dataset, path)])]
            )
    atomic_bytes(out / "data_dictionary.csv", buf.getvalue().encode())
    return result
