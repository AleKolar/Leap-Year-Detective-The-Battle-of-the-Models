import pytest
from fastapi.testclient import TestClient
from main import app
from src.services.leap_year_service import is_leap_year
from unittest.mock import patch

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.mark.parametrize("year,expected", [
    (2024, True), (2000, True), (0, True), (-400, True),
    (1900, False), (1800, False), (2100, False), (2023, False), (1, False)
])
def test_is_leap_year(year, expected):
    assert is_leap_year(year) == expected

def test_check_year(client):
    resp = client.get("/api/check/2000")
    data = resp.json()
    assert data["is_leap"] == True
    assert data["days"] == 366

def test_check_1900(client):
    resp = client.get("/api/check/1900")
    data = resp.json()
    assert data["is_leap"] == False
    assert data["rule_check"]["divisible_by_100"] == True

def test_stats(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    assert "total_checks" in resp.json()

def test_main_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Leap Year Detective" in resp.text

@pytest.mark.asyncio
async def test_compare_models(client):
    with patch("src.services.ai_service.fetch_from_model") as mock_fetch:
        mock_fetch.side_effect = [
            {"model": "openai/gpt-4o-mini", "content": "def is_leap(y): return y%4==0 and (y%100!=0 or y%400==0)", "status": "success"},
            {"model": "deepseek/deepseek-chat", "content": "def is_leap(y): return y%4==0", "status": "success"},
        ]
        resp = client.post("/api/llm-arena/compare", json={"models": ["gpt-4o-mini", "deepseek-chat"]})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) == 2
        assert data["elapsed"] >= 0

def test_winner_endpoint(client):
    good = {"model": "A", "content": "def f(): return year % 400 == 0"}
    bad = {"model": "B", "content": "def f(): return True"}
    resp = client.post("/api/llm-arena/winner", json=[good, bad])
    data = resp.json()
    assert data["winners"] == ["A"]
    assert "B" in data["losers"]

def test_list_models(client):
    resp = client.get("/api/llm-arena/models")
    assert "deepseek-chat" in resp.json()