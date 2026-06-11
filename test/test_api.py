"""Smoke tests for FastAPI routers and HTTP error mapping."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app import create_app
from backend.dependencies import get_prediction_service, get_simulation_service
from backend.services.exceptions import PredictionsNotFoundError, SimulationValidationError
from backend.services.prediction_service import PredictionService
from backend.services.simulation_service import SimulationService


class _StubPredictionService(PredictionService):
    def get_status(self) -> dict:
        return {
            "has_predictions": False,
            "source": None,
            "n_simulations": 0,
            "path": "/tmp/predictions.json",
        }

    def get_predictions(self) -> dict:
        raise PredictionsNotFoundError("No predictions snapshot found.")


class _StubSimulationService(SimulationService):
    def __init__(self) -> None:
        pass

    def run_custom(self, n_simulations: int) -> dict:
        if n_simulations < 10:
            raise SimulationValidationError(
                "n_simulations must be between 10 and 5000"
            )
        return {"n_simulations": n_simulations, "champion_probs": {}}


class _StubResourceService:
    def preload(self) -> None:
        pass

    def get(self) -> dict:
        raise RuntimeError("stub resource service should not load models in API tests")


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> httpx.AsyncClient:
    monkeypatch.setattr(
        "backend.app.get_resource_service", lambda: _StubResourceService()
    )
    app = create_app()
    app.dependency_overrides[get_prediction_service] = lambda: _StubPredictionService()
    app.dependency_overrides[get_simulation_service] = lambda: _StubSimulationService()
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


def _run(coro):
    return asyncio.run(coro)


def test_health_check(client: httpx.AsyncClient):
    response = _run(client.get("/health"))
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_predictions_missing_snapshot_returns_404(client: httpx.AsyncClient):
    response = _run(client.get("/api/predictions"))
    assert response.status_code == 404
    assert "No predictions snapshot found" in response.json()["detail"]


def test_predictions_status(client: httpx.AsyncClient):
    response = _run(client.get("/api/predictions/status"))
    assert response.status_code == 200
    assert response.json()["has_predictions"] is False


def test_simulate_invalid_iterations_returns_400(client: httpx.AsyncClient):
    response = _run(client.post("/api/simulate", json={"n_simulations": 5}))
    assert response.status_code == 400
    assert "n_simulations must be between" in response.json()["detail"]
