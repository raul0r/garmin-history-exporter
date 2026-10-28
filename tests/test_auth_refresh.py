import unittest
from types import SimpleNamespace
from garmin_exporter.auth import RefreshingClient

class TokenTests(unittest.TestCase):
    def test_expiring_token_is_replaced(self):
        class Auth:
            def obtain_token(self, key, force_refresh=False):
                self.called = (key, force_refresh)
                return SimpleNamespace(access_token='new', expires_at=10000)
        class Client:
            def update_bearer_token(self, value): self.token = value
            def get_data(self): return 'ok'
        auth = Auth(); raw = Client()
        client = RefreshingClient(raw, auth, 'secret', SimpleNamespace(expires_at=100), clock=lambda: 50)
        self.assertEqual(client.get_data(), 'ok')
        self.assertEqual(raw.token, 'new')
        self.assertEqual(auth.called, ('secret', False))
    def test_401_refreshes_once(self):
        class Error(Exception): status_code = 401
        class Auth:
            def obtain_token(self, key, force_refresh=False):
                self.force = force_refresh
                return SimpleNamespace(access_token='new', expires_at=10000)
        class Client:
            calls = 0
            def update_bearer_token(self, value): pass
            def get_data(self):
                self.calls += 1
                if self.calls == 1: raise Error()
                return 'ok'
        auth = Auth(); raw = Client()
        client = RefreshingClient(raw, auth, 'secret', SimpleNamespace(expires_at=10000), clock=lambda: 0)
        self.assertEqual(client.get_data(), 'ok')
        self.assertTrue(auth.force)
        self.assertEqual(raw.calls, 2)
