"""Refresh Garmin bearer tokens without exposing credentials in logs."""

import time


class RefreshingClient:
    def __init__(self, client, authenticator, key, token, clock=time.time):
        self.client = client
        self.authenticator = authenticator
        self.key = key
        self.token = token
        self.clock = clock

    def refresh(self, force=False):
        self.token = self.authenticator.obtain_token(self.key, force_refresh=force)
        self.client.update_bearer_token(self.token.access_token)

    def __getattr__(self, name):
        method = getattr(self.client, name)
        if not callable(method):
            return method

        def call(*args, **kwargs):
            if self.clock() >= self.token.expires_at - 3600:
                self.refresh()
            try:
                return method(*args, **kwargs)
            except Exception as exc:
                if getattr(exc, "status_code", None) != 401:
                    raise
                self.refresh(force=True)
                return method(*args, **kwargs)

        return call
