import json
from datetime import date

import pytest

from garmin_exporter.exporter import Exporter
from garmin_exporter.locking import archive_lock


class Client:
    def __init__(self):
        self.calls = 0

    def get_daily_sleep(self, day):
        self.calls += 1
        return {"calendarDate": day}


def test_pending_and_failed_are_retried(tmp_path):
    client = Client()
    e = Exporter(client, tmp_path, delay=0)
    for status in ("pending", "failed"):
        e.state["queries"]["x"] = {"status": status}
        assert e.request("x", "get_daily_sleep", ["2020-01-01"], "data.json")
    assert client.calls == 2


def test_invalid_cached_json_even_with_matching_hash(tmp_path):
    from garmin_exporter.storage import digest

    p = tmp_path / "data.json"
    p.write_text("invalid")
    e = Exporter(Client(), tmp_path, delay=0)
    e.state["queries"]["x"] = {"status": "success", "sha256": digest(p)}
    assert e.request("x", "get_daily_sleep", ["2020-01-01"], "data.json")
    assert json.loads(p.read_text()) == {"calendarDate": "2020-01-01"}


def test_interrupted_after_write_retries_pending(tmp_path, monkeypatch):
    e = Exporter(Client(), tmp_path, delay=0)
    original = e.save
    calls = 0

    def save():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise KeyboardInterrupt()
        original()

    monkeypatch.setattr(e, "save", save)
    with pytest.raises(KeyboardInterrupt):
        e.request("x", "get_daily_sleep", ["2020-01-01"], "data.json")
    assert json.loads(e.state_path.read_text())["queries"]["x"]["status"] == "pending"
    resumed = Exporter(Client(), tmp_path, delay=0)
    assert resumed.request("x", "get_daily_sleep", ["2020-01-01"], "data.json")
    assert resumed.client.calls == 1


def test_lock_released_after_interrupt_and_stale_file(tmp_path):
    with pytest.raises(KeyboardInterrupt):
        with archive_lock(tmp_path):
            raise KeyboardInterrupt()
    assert (tmp_path / ".export.lock").exists()
    with archive_lock(tmp_path):
        with pytest.raises(RuntimeError):
            with archive_lock(tmp_path):
                pass


def test_repeated_and_malformed_pages_are_visible(tmp_path):
    class Pages:
        def search_activities(self, **kwargs):
            return [{"activityId": 1}]

        def get_activity(self, ident):
            return {}

        def get_activity_workouts(self, ident):
            return []

        def download_activity(self, ident):
            return b"invalid"

    e = Exporter(Pages(), tmp_path, delay=0)
    d = date(2020, 1, 1)
    e.run(d, d, ["activities"])
    assert "repeated_page" in [v["status"] for v in e.state["queries"].values()]
    assert "failed" in [v["status"] for v in e.state["queries"].values()]
