import json
import io
import zipfile
import tempfile
import unittest
from datetime import date
from pathlib import Path
from garmin_exporter.exporter import Exporter, windows
from garmin_exporter.report import report
from garmin_exporter.storage import atomic_json
from garmin_exporter.locking import archive_lock

class Client:
    def __init__(self): self.calls = 0
    def get_daily_sleep(self, day):
        self.calls += 1
        return {"calendarDate": day, "sleep": {"duration": 42, "stages": [{"kind": "deep"}]}, "missing": None}
    def search_activities(self, **kw):
        return [{"activityId": n} for n in range(1, 101)] if kw["start"] == 0 else []
    def get_activity(self, activity_id): return {"activityId": activity_id}
    def get_activity_workouts(self, activity_id): return []
    def download_activity(self, activity_id):
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as archive:
            archive.writestr("activity.fit", b"synthetic")
        return out.getvalue()

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
    def test_windows(self):
        self.assertEqual(list(windows(date(2026,1,1), date(2026,1,5), 2)), [("2026-01-01","2026-01-02"),("2026-01-03","2026-01-04"),("2026-01-05","2026-01-05")])
    def test_resume_and_integrity(self):
        c = Client(); e = Exporter(c, self.root, delay=0)
        d = date(2026,1,1); e.run(d,d,["sleep"]); e.run(d,d,["sleep"])
        self.assertEqual(c.calls,1)
        (self.root / 'raw/daily/2026-01-01/sleep.json').write_text('broken')
        e.run(d,d,["sleep"]); self.assertEqual(c.calls,2)
    def test_pagination_and_files(self):
        e = Exporter(Client(),self.root,delay=0); d=date(2026,1,1)
        e.run(d,d,["activities"])
        self.assertEqual(len(list((self.root/'activities').iterdir())),100)
        self.assertTrue((self.root/'raw/activities/pages/2026-01-01_2026-01-01_100.json').exists())
    def test_server_capped_activity_pages(self):
        class Capped(Client):
            def search_activities(self, **kw):
                return [{"activityId": kw["start"] + 1}] if kw["start"] < 2 else []
        e = Exporter(Capped(), self.root, delay=0)
        d = date(2026, 1, 1)
        e.run(d, d, ["activities"])
        self.assertEqual(len(list((self.root / "activities").iterdir())), 2)
        self.assertIn("activities:page:2026-01-01:2026-01-01:2", e.state["queries"])

    def test_lock_excludes_other_writer_and_releases(self):
        with archive_lock(self.root):
            with self.assertRaises(RuntimeError):
                with archive_lock(self.root):
                    pass
        with archive_lock(self.root):
            pass

    def test_report_no_values_and_schema(self):
        e=Exporter(Client(),self.root,delay=0); d=date(2026,1,1); e.run(d,d,["sleep"])
        data=report(self.root)
        self.assertIn('$.sleep.stages[].kind',data['schema'])
        self.assertIn('null',data['schema']['$.missing'])
        self.assertNotIn('deep',(self.root/'reports/inventory.json').read_text())
    def test_failure_is_recorded_without_exception_text(self):
        class Bad:
            def get_daily_sleep(self, day): raise RuntimeError('secret-example')
        e=Exporter(Bad(),self.root,delay=0); e.run(date(2026,1,1),date(2026,1,1),['sleep'])
        self.assertNotIn('secret-example',e.state_path.read_text())
        self.assertEqual(e.state['queries']['sleep:2026-01-01']['status'],'failed')
    def test_invalid_original_is_failed(self):
        class BadOriginal(Client):
            def download_activity(self, activity_id): return b"not a zip"
        e = Exporter(BadOriginal(), self.root, delay=0)
        self.assertFalse(e.request("original", "download_activity", [1], "original.zip", binary=True))
        self.assertEqual(e.state["queries"]["original"]["status"], "failed")
        self.assertFalse((self.root / "original.zip").exists())

    def test_atomic_json(self):
        p=self.root/'x/a.json'; atomic_json(p,{'nested':[1,None]})
        self.assertEqual(json.loads(p.read_text()),{'nested':[1,None]})
    def test_retry_429(self):
        class Response: status_code=429; headers={'Retry-After':'2'}
        class Error(Exception): response=Response()
        class Flaky:
            calls=0
            def get_daily_sleep(self, day):
                self.calls += 1
                if self.calls==1: raise Error()
                return []
        waits=[]; e=Exporter(Flaky(),self.root,delay=0,sleep=waits.append)
        e.run(date(2026,1,1),date(2026,1,1),['sleep'])
        self.assertIn(2,waits)
        self.assertEqual(e.state['queries']['sleep:2026-01-01']['status'],'success')

if __name__ == '__main__': unittest.main()
