import json
import random
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from .endpoints import ACCOUNT, DAYS, RANGES
from .storage import atomic_bytes, atomic_json, digest


def windows(start, end, size):
    if start > end or size < 1:
        raise ValueError("invalid range or window size")
    while start <= end:
        last = min(end, start + timedelta(days=size - 1))
        yield start.isoformat(), last.isoformat()
        start = last + timedelta(days=1)


class Exporter:
    def __init__(self, client, root, delay=0.25, retries=3, sleep=time.sleep):
        self.client, self.root, self.delay, self.retries, self.sleep = client, Path(root), delay, retries, sleep
        self.state_path = self.root / "manifest/export_state.json"
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {"queries": {}}

    def save(self):
        atomic_json(self.state_path, self.state)

    def request(self, key, method, args, path, kwargs=None, binary=False):
        path = Path(path)
        previous = self.state["queries"].get(key, {})
        target = self.root / path
        if previous.get("status") == "success" and target.is_file() and digest(target) == previous.get("sha256"):
            return True
        entry = {"method": method, "args": args, "kwargs": kwargs or {}, "path": path.as_posix(),
                 "timestamp": datetime.now(timezone.utc).isoformat()}
        for attempt in range(self.retries + 1):
            try:
                self.sleep(self.delay)
                value = getattr(self.client, method)(*args, **(kwargs or {}))
                checksum = atomic_bytes(target, value) if binary else atomic_json(target, value)
                entry.update(status="success", sha256=checksum, bytes=target.stat().st_size,
                             empty=(not value))
                self.state["queries"][key] = entry
                self.save()
                return True
            except Exception as exc:
                response = getattr(exc, "response", None)
                status = getattr(exc, "status_code", None) or getattr(response, "status_code", None)
                retryable = status in (429, 500, 502, 503, 504) or (status is None and exc.__class__.__name__ in ("ConnectionError", "Timeout", "ReadTimeout", "ConnectTimeout"))
                if retryable and attempt < self.retries:
                    retry_after = (getattr(response, "headers", {}) or {}).get("Retry-After", "")
                    try: wait = max(0, float(retry_after))
                    except (TypeError, ValueError): wait = min(60, 2**attempt + random.random())
                    self.sleep(wait)
                    continue
                entry.update(status="failed", http_status=status, error_type=type(exc).__name__)
                self.state["queries"][key] = entry
                self.save()
                return False
        return False

    def run(self, start, end, categories=None, batch_days=30):
        categories = set(categories or list(RANGES) + list(DAYS) + list(ACCOUNT) + ["activities", "menstrual_day"])
        known = set(RANGES) | set(DAYS) | set(ACCOUNT) | {"activities", "menstrual_day"}
        if categories - known: raise ValueError("Unknown categories: " + ", ".join(sorted(categories-known)))
        self.state["last_plan"] = {"start": start.isoformat(), "end": end.isoformat(), "categories": sorted(categories), "batch_days": batch_days}
        self.save()
        for name, method in ACCOUNT.items():
            if name in categories: self.request(name, method, [], f"raw/account/{name}.json")
        for name, method in RANGES.items():
            if name not in categories: continue
            for a, b in windows(start, end, batch_days):
                print(f"{name}: {a} to {b}", flush=True)
                self.request(f"{name}:{a}:{b}", method, [a, b], f"raw/ranges/{name}/{a}_{b}.json")
        for name, method in DAYS.items():
            if name not in categories: continue
            for a, _ in windows(start, end, 1):
                print(f"{name}: {a}", flush=True)
                self.request(f"{name}:{a}", method, [a], f"raw/daily/{a}/{name}.json")
        if "menstrual_day" in categories:
            for a, _ in windows(start, end, 1):
                self.request(f"menstrual_day:{a}:{end}", "get_menstrual_cycle_day_view", [a, end.isoformat()], f"raw/daily/{a}/menstrual_day.json")
        if "activities" in categories: self.activities(start, end)

    def activities(self, start, end):
        offset, limit = 0, 100
        seen_pages = set()
        while True:
            key = f"activities:page:{start}:{end}:{offset}"
            path = f"raw/activities/pages/{start}_{end}_{offset}.json"
            if not self.request(key, "search_activities", [], path, {"start": offset, "limit": limit, "start_date": start.isoformat(), "end_date": end.isoformat()}): return
            page = json.loads((self.root / path).read_text())
            if not isinstance(page, list):
                self.state["queries"][key]["status"] = "invalid_response"; self.save(); return
            signature = json.dumps(page, sort_keys=True)
            if page and signature in seen_pages:
                self.state["queries"][key]["status"] = "repeated_page"; self.save(); return
            seen_pages.add(signature)
            for item in page:
                if not isinstance(item, dict) or not str(item.get("activityId", "")).isdigit():
                    self.state["queries"][key]["status"] = "invalid_activity_id"; self.save(); continue
                ident = str(item["activityId"])
                for suffix, method, binary in (("details.json", "get_activity", False), ("workouts.json", "get_activity_workouts", False), ("original.zip", "download_activity", True)):
                    self.request(f"activity:{ident}:{suffix}", method, [int(ident)], f"activities/{ident}/{suffix}", binary=binary)
            if len(page) < limit: return
            offset += limit
