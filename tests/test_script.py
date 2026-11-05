import json

import pytest
import requests
from fastapi import HTTPException

import scraping.script as script


class FakeResponse:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text


def _conf_data():
    return {
        "times": ["05:10", "12:30", "15:45", "18:12", "19:40"],
        "shuruq": "06:42",
        "calendar": [{"1": ["05:10", "06:42", "12:30", "15:45", "18:12", "19:40"]}],
        "iqamaCalendar": [{"1": ["05:20", "12:40", "16:00", "18:20", "19:50"]}],
        "announcements": [],
        "womenSpace": True,
        "janazaPrayer": False,
        "aidPrayer": True,
        "childrenCourses": False,
        "adultCourses": True,
        "ramadanMeal": False,
        "handicapAccessibility": True,
        "ablutions": True,
        "parking": False,
    }


def test_fetch_mawaqit_extracts_and_caches_config(monkeypatch):
    payload = _conf_data()
    html = (
        "<html><script>var confData = "
        + json.dumps(payload)
        + ";</script></html>"
    )
    calls = []
    cache_calls = []

    class FakeRedis:
        def get(self, key):
            calls.append(("get", key))
            return None

        def set(self, key, value, ex):
            cache_calls.append((key, json.loads(value), ex))

    monkeypatch.setattr(script, "redisClient", FakeRedis())
    monkeypatch.setattr(
        script.requests,
        "get",
        lambda url: calls.append(("request", url)) or FakeResponse(text=html),
    )

    result = script.fetch_mawaqit("test-mosque")

    assert result == payload
    assert calls == [
        ("get", "test-mosque"),
        ("request", "https://mawaqit.net/fr/test-mosque"),
    ]
    assert cache_calls == [("test-mosque", payload, 604800)]


def test_fetch_mawaqit_uses_cached_config(monkeypatch):
    payload = _conf_data()

    class FakeRedis:
        def get(self, key):
            return json.dumps(payload)

    def unexpected_request(*args, **kwargs):
        pytest.fail("Should not request Mawaqit when a cache entry exists")

    monkeypatch.setattr(script, "redisClient", FakeRedis())
    monkeypatch.setattr(script.requests, "get", unexpected_request)

    assert script.fetch_mawaqit("test-mosque") == payload


@pytest.mark.parametrize(
    ("status_code", "expected_status"),
    [(404, 404), (500, 502)],
)
def test_fetch_mawaqit_maps_upstream_errors(monkeypatch, status_code, expected_status):
    monkeypatch.setattr(script, "redisClient", None)
    monkeypatch.setattr(
        script.requests,
        "get",
        lambda _: FakeResponse(status_code=status_code),
    )

    with pytest.raises(HTTPException) as error:
        script.fetch_mawaqit("missing-mosque")

    assert error.value.status_code == expected_status


def test_fetch_mawaqit_reports_missing_conf_data(monkeypatch):
    monkeypatch.setattr(script, "redisClient", None)
    monkeypatch.setattr(script.requests, "get", lambda _: FakeResponse(text="<html></html>"))

    with pytest.raises(HTTPException) as error:
        script.fetch_mawaqit("test-mosque")

    assert error.value.status_code == 500
    assert "confData" in error.value.detail


def test_fetch_mawaqit_propagates_request_errors(monkeypatch):
    monkeypatch.setattr(script, "redisClient", None)

    def raise_request_error(_):
        raise requests.ConnectionError("upstream unavailable")

    monkeypatch.setattr(script.requests, "get", raise_request_error)

    with pytest.raises(requests.ConnectionError):
        script.fetch_mawaqit("test-mosque")


def test_get_prayer_times_maps_mawaqit_payload(monkeypatch):
    monkeypatch.setattr(script, "fetch_mawaqit", lambda _: _conf_data())

    assert script.get_prayer_times_of_the_day("test-mosque") == {
        "fajr": "05:10",
        "sunrise": "06:42",
        "dohr": "12:30",
        "asr": "15:45",
        "maghreb": "18:12",
        "icha": "19:40",
    }


@pytest.mark.parametrize("month_number", [0, 13])
def test_get_month_rejects_out_of_range_month(month_number):
    with pytest.raises(HTTPException) as error:
        script.get_month("test-mosque", month_number)

    assert error.value.status_code == 400
