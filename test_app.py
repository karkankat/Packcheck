"""Автоматические проверки PackCheck."""

import importlib
import logging

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_module(monkeypatch):
    # Начинаем каждый тест без внешней настройки лимита.
    monkeypatch.delenv("DEFAULT_WEIGHT_LIMIT_KG", raising=False)
    import app_final

    return importlib.reload(app_final)


@pytest.fixture
def client(app_module):
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version(client):
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"version": "0.3.0"}


def test_items(client):
    response = client.get("/items")
    assert response.status_code == 200
    data = response.json()
    assert data["item_count"] == 9
    assert len(data["items"]) == 9
    assert [item["id"] for item in data["items"]] == [1, 2, 3, 4, 5, 6, 7, 8, 9]


def test_items_category(client):
    response = client.get("/items", params={"category": "sleep"})
    assert response.status_code == 200
    data = response.json()
    assert data["item_count"] == 3
    assert [item["id"] for item in data["items"]] == [1, 2, 3]
    assert all(item["category"] == "sleep" for item in data["items"])


def test_unknown_category(client):
    response = client.get("/items", params={"category": "unknown"})
    assert response.status_code == 200
    assert response.json() == {"item_count": 0, "items": []}


def test_summary(client):
    response = client.get("/summary")
    assert response.status_code == 200
    assert response.json() == {
        "item_count": 9,
        "total_weight_g": 8400,
        "total_weight_kg": 8.4,
        "heaviest_item": {
            "id": 8,
            "name": "Вода",
            "category": "supplies",
            "weight_g": 2500,
        },
    }


@pytest.mark.parametrize(
    "limit_kg, fits, remaining_kg, overweight_kg",
    [
        (10, True, 1.6, 0.0),
        (8, False, 0.0, 0.4),
        (8.4, True, 0.0, 0.0),
    ],
)
def test_check_limits(client, limit_kg, fits, remaining_kg, overweight_kg):
    response = client.get("/check", params={"limit_kg": limit_kg})
    assert response.status_code == 200
    assert response.json() == {
        "total_weight_kg": 8.4,
        "limit_kg": limit_kg,
        "fits": fits,
        "remaining_kg": remaining_kg,
        "overweight_kg": overweight_kg,
    }


@pytest.mark.parametrize("limit_kg", ["0", "-1", "abc", "nan", "inf", "8.3996"])
def test_invalid_limit(client, limit_kg):
    response = client.get("/check", params={"limit_kg": limit_kg})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "limit_kg"]


def test_default_limit(client):
    response = client.get("/check")
    assert response.status_code == 200
    assert response.json() == {
        "total_weight_kg": 8.4,
        "limit_kg": 10.0,
        "fits": True,
        "remaining_kg": 1.6,
        "overweight_kg": 0.0,
    }


def test_environment_limit_and_query_override(app_module, monkeypatch):
    monkeypatch.setenv("DEFAULT_WEIGHT_LIMIT_KG", "8")
    importlib.reload(app_module)

    with TestClient(app_module.app) as env_client:
        response = env_client.get("/check")
        assert response.status_code == 200
        assert response.json() == {
            "total_weight_kg": 8.4,
            "limit_kg": 8.0,
            "fits": False,
            "remaining_kg": 0.0,
            "overweight_kg": 0.4,
        }

        response = env_client.get("/check", params={"limit_kg": 10})
        assert response.status_code == 200
        assert response.json() == {
            "total_weight_kg": 8.4,
            "limit_kg": 10.0,
            "fits": True,
            "remaining_kg": 1.6,
            "overweight_kg": 0.0,
        }


def test_check_logging(client, caplog):
    with caplog.at_level(logging.INFO, logger="packcheck"):
        response = client.get("/check", params={"limit_kg": 8})

    assert response.status_code == 200
    assert (
        "Проверка веса: total_kg=8.400 limit_kg=8.000 fits=False"
        in caplog.text
    )