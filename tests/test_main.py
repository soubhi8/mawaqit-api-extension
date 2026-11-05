from fastapi.testclient import TestClient

from config.settings import settings
from main import app
import scraping.script as script


client = TestClient(app)
API_ROOT = "/api/v1"


def _apply_settings(monkeypatch, enable_auth=False, bearer_token=None):
    monkeypatch.setattr(settings, "ENABLE_AUTH", enable_auth, raising=False)
    monkeypatch.setattr(settings, "BEARER_TOKEN", bearer_token, raising=False)


def test_read_root():
    response = client.get(API_ROOT)

    assert response.status_code == 200
    assert response.json() == {
        "Greetings": (
            "Hello and Welcome to this Api, this api use the mawaqit.net as data source "
            "of prayers time in more than 8000 masjid, this api can be used to fetch "
            "data in json, you can find our docs on /docs. "
        )
    }


def test_prayer_times_endpoint_returns_scraped_data(monkeypatch):
    expected = {
        "fajr": "05:10",
        "sunrise": "06:42",
        "dohr": "12:30",
        "asr": "15:45",
        "maghreb": "18:12",
        "icha": "19:40",
    }
    calls = []

    def fake_get_prayer_times(masjid_id):
        calls.append(masjid_id)
        return expected

    _apply_settings(monkeypatch)
    monkeypatch.setattr(script, "get_prayer_times_of_the_day", fake_get_prayer_times)

    response = client.get(f"{API_ROOT}/test-mosque/prayer-times")

    assert response.status_code == 200
    assert response.json() == expected
    assert calls == ["test-mosque"]


def test_authentication_protects_api_endpoint(monkeypatch):
    _apply_settings(monkeypatch, enable_auth=True, bearer_token="test-secret")
    monkeypatch.setattr(
        script,
        "get_prayer_times_of_the_day",
        lambda _: {
            "fajr": "05:10",
            "sunrise": "06:42",
            "dohr": "12:30",
            "asr": "15:45",
            "maghreb": "18:12",
            "icha": "19:40",
        },
    )

    missing = client.get(f"{API_ROOT}/test-mosque/prayer-times")
    invalid = client.get(
        f"{API_ROOT}/test-mosque/prayer-times",
        headers={"Authorization": "Bearer wrong-secret"},
    )
    valid = client.get(
        f"{API_ROOT}/test-mosque/prayer-times",
        headers={"Authorization": "Bearer test-secret"},
    )

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert valid.status_code == 200


def test_month_calendar_rejects_invalid_month(monkeypatch):
    _apply_settings(monkeypatch)

    response = client.get(f"{API_ROOT}/test-mosque/calendar/13")

    assert response.status_code == 400
    assert response.json()["detail"] == "Month number should be between 1 and 12"


def test_month_calendar_endpoint_serializes_prayer_times(monkeypatch):
    _apply_settings(monkeypatch)
    monkeypatch.setattr(
        script,
        "get_month",
        lambda masjid_id, month_number: [
            {
                "fajr": "05:10",
                "sunrise": "06:42",
                "dohr": "12:30",
                "asr": "15:45",
                "maghreb": "18:12",
                "icha": "19:40",
            }
        ],
    )

    response = client.get(f"{API_ROOT}/test-mosque/calendar/1")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["fajr"] == "05:10"
