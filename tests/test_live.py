import os
import re
from functools import partial

import pytest
from fastapi.testclient import TestClient

from config.settings import settings
from main import app
import scraping.script as script


pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.environ.get("RUN_LIVE_TESTS") != "1",
        reason="Set RUN_LIVE_TESTS=1 to fetch real data from mawaqit.net",
    ),
]


def test_prayer_times_from_live_mawaqit(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_AUTH", False)
    monkeypatch.setattr(script, "redisClient", None)
    monkeypatch.setattr(
        script.requests, "get", partial(script.requests.get, timeout=20)
    )

    with TestClient(app) as client:
        response = client.get("/api/v1/assalam-argenteuil/prayer-times")

    assert response.status_code == 200, response.text
    prayer_times = response.json()
    assert set(prayer_times) == {
        "fajr", "sunrise", "dohr", "asr", "maghreb", "icha",
    }
    for prayer, value in prayer_times.items():
        assert re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value), (prayer, value)
