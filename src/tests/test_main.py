import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from main import app
from src.services.leap_year_service import is_leap_year
from src.database.database import get_async_db

@pytest.fixture
def client():
    """Фикстура TestClient с заменой зависимости БД на мок."""
    async def override_get_async_db():
        session = AsyncMock()
        # Настраиваем стандартное поведение методов, чтобы они были awaitable
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock() # синхронный, чтобы не было незавершённой корутины
        yield session

    app.dependency_overrides[get_async_db] = override_get_async_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

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

def test_list_models(client):
    resp = client.get("/api/llm-arena/models")
    assert "deepseek-chat" in resp.json()

import asyncio

def test_winner_endpoint(client):
    # Готовим замоканную битву, которую вернёт scalar()
    mock_battle = MagicMock()
    mock_battle.evidence = [
        {"model": "A", "content": "def f(): return year % 400 == 0", "status": "success"},
        {"model": "B", "content": "def f(): return True", "status": "success"}
    ]
    mock_battle.winner = None
    mock_battle.message = ""

    mock_result = MagicMock()
    mock_result.scalar.return_value = mock_battle

    # Создаём специальную зависимость для этого теста
    async def override_for_winner():
        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()
        yield session

    # Подменяем зависимость перед вызовом эндпоинта
    app.dependency_overrides[get_async_db] = override_for_winner

    resp = client.post("/api/llm-arena/winner")
    data = resp.json()

    assert data["winners"] == ["A"]
    assert "B" in data["losers"]
    assert "Победитель" in data["message"]

# !!! ВАЖНО: Определить, что мокать !!!
# В production эндпоинт через Depends(get_async_db) получает настоящий AsyncSession,
# созданный фабрикой AsyncSessionLocal. В тестах мы подменяем саму функцию-зависимость get_async_db,
# но при каждом запросе FastAPI заново вызывает её и получает новый генератор, а значит,
# и новый мок-объект — поэтому настройки, сделанные на одном экземпляре, не применялись к тому,
# который приходит в эндпоинт. Решение: заменить зависимость на генератор, который всегда возвращает
# один и тот же объект сессии с уже настроенным поведением (execute → scalar → нужный результат).
# Так эндпоинт гарантированно получает подготовленный мок.
# Коротко: мы не мокаем весь AsyncSessionLocal, а подменяем генератор сессии,
# чтобы он выдавал конкретный экземпляр с нужным ответом — сам эндпоинт declare_winner остаётся
# без изменений и просто получает этот мок через Depends(get_async_db).

# pytest src/tests/test_main.py -v