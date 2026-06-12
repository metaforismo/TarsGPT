"""Remote Python client for a running TARS (the distributed-architecture
idea from the latishab fork, on plain HTTP):

    from tars.client import TarsClient
    tars = TarsClient("http://tars.local:8000", password="...")
    print(tars.chat("status report, please"))
    tars.move("step_forward")

Runs anywhere - your AI experiments live on a PC while the robot stays a
thin appliance.
"""
import requests


class TarsClient:
    def __init__(self, base_url: str, password: str | None = None,
                 timeout: float = 60):
        self.base = base_url.rstrip("/")
        self.timeout = timeout
        self.http = requests.Session()
        if password:
            self.login(password)

    def _post(self, path: str, **payload):
        response = self.http.post(self.base + path, json=payload or None,
                                  timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _get(self, path: str):
        response = self.http.get(self.base + path, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def login(self, password: str):
        self._post("/api/login", password=password)

    def chat(self, message: str) -> str:
        return self._post("/api/chat", message=message)["reply"]

    def move(self, action: str):
        """step_forward | turn_left | turn_right | strafe_left |
        strafe_right | pose | neutral"""
        return self._post("/api/move", action=action)

    def status(self) -> dict:
        return self._get("/api/status")

    def settings(self, **changes) -> dict:
        if changes:
            return self._post("/api/settings", **changes)
        return self._get("/api/settings")

    def calibrate(self, channel: int, value: int, save_as: str | None = None):
        payload = {"channel": channel, "value": value}
        if save_as:
            payload["save_as"] = save_as
        return self._post("/api/calibrate", **payload)

    def memory(self) -> dict:
        return self._get("/api/memory")

    def knowledge(self) -> dict:
        return self._get("/api/knowledge")
