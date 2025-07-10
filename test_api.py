from __future__ import annotations

import pytest
from app_flask import app as flask_app

# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """Flask test client with TESTING flag enabled."""
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client

# ---------------------------------------------------------------------------
# Tests – /api/weather (daily) ------------------------------------------------
# ---------------------------------------------------------------------------

def test_weather_basic(client):
    """Endpoint returns 200 and expected JSON skeleton."""
    rv = client.get("/api/weather?page=1&page_size=1")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == {"meta", "data"}
    assert isinstance(body["data"], list)


def test_weather_filter_station(client):
    """Filtering by station_id returns only that station."""
    # grab one station_id from first row
    first = client.get("/api/weather?page=1&page_size=1").get_json()
    assert first["data"], "Database appears empty—run ingest.py first."  # guard
    station_id = first["data"][0]["station_id"]

    rv = client.get(f"/api/weather?station_id={station_id}&page=1&page_size=5")
    assert rv.status_code == 200
    rows = rv.get_json()["data"]
    assert rows, "Station filter returned zero rows (unexpected for test)."
    assert all(r["station_id"] == station_id for r in rows)


def test_weather_page_out_of_range(client):
    """Requesting a page far beyond total_pages yields 404."""
    rv = client.get("/api/weather?page=99999&page_size=50")
    assert rv.status_code == 404

def test_weather_pagination_meta(client):
    rv = client.get("/api/weather?page=1&page_size=2")
    assert rv.status_code == 200
    meta = rv.get_json()["meta"]
    assert "total_pages" in meta
    assert "page" in meta
    assert meta["page"] == 1

def test_weather_bad_query(client):
    rv = client.get("/api/weather?station_id=INVALID123&page=abc&page_size=xyx")
    assert rv.status_code == 400

def test_weather_invalid_station(client):
    """Requesting a non-existent station_id returns empty data."""
    rv = client.get("/api/weather?station_id=INVALID123&page=1&page_size=5")
    assert rv.status_code == 200
    assert rv.get_json()["data"] == []

def test_weather_negative_page(client):
    """Negative page numbers should return 400."""
    rv = client.get("/api/weather?station_id=INVALID123&page=-1&page_size=5")
    assert rv.status_code == 400
# ---------------------------------------------------------------------------
# Tests – /api/weather/stats (yearly) ----------------------------------------
# ---------------------------------------------------------------------------

def test_stats_basic(client):
    rv = client.get("/api/weather/stats?page=1&page_size=1")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == {"meta", "data"}
    assert isinstance(body["data"], list)


def test_stats_filter_station_year(client):
    """Filter yearly stats by station + year returns 0 or 1 row."""
    first = client.get("/api/weather/stats?page=1&page_size=1").get_json()
    assert first["data"], "Yearly table empty—run calc_yearly_stats.py first."  # guard
    row = first["data"][0]
    station_id = row["station_id"]
    year       = row["year"]

    rv = client.get(f"/api/weather/stats?station_id={station_id}&year={year}")
    assert rv.status_code == 200
    rows = rv.get_json()["data"]
    # at most one row per (station, year)
    assert len(rows) <= 1
    if rows:
        r = rows[0]
        assert r["station_id"] == station_id and r["year"] == year
    
    def test_stats_invalid_year(client):
        """Requesting a non-existent year returns empty data."""
        rv = client.get("/api/weather/stats?year=3000&page=1&page_size=5")
        assert rv.status_code == 200
        assert rv.get_json()["data"] == []

def test_stats_missing_params(client):
    """Missing required params should still return valid response."""
    rv = client.get("/api/weather/stats")
    assert rv.status_code == 200
    assert "data" in rv.get_json()

def test_swagger_docs(client):
    rv = client.get("/docs")
    assert rv.status_code == 200
    assert b"Swagger" in rv.data or b"OpenAPI" in rv.data