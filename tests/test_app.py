import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_towns_uses_client(monkeypatch):
    class FakeClient:
        def __init__(self, app=None):
            self.app = app

        def fetch_towns(self, town):
            return {"towns": [{"name": town, "district": "X", "id": "1"}]}

    monkeypatch.setattr(main, "EcoharmonogramClient", FakeClient)

    response = client.post("/towns", json={"town": "Gdansk"})

    assert response.status_code == 200
    assert response.json()["towns"][0]["name"] == "Gdansk"


def test_schedule_returns_sorted_entries(monkeypatch):
    class FakeService:
        def __init__(self, **kwargs):
            pass

        def fetch(self):
            return [
                SimpleNamespace(date=datetime.date(2026, 1, 3), waste_type="Paper"),
                SimpleNamespace(date=datetime.date(2026, 1, 1), waste_type="Bio"),
            ]

    monkeypatch.setattr(main, "EcoharmonogramScheduleService", FakeService)

    payload = {
        "town": "Gdansk",
        "house_number": "1",
        "street": "Main",
    }
    response = client.post("/schedule", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert body["entries"][0] == {"date": "2026-01-01", "type": "Bio"}
