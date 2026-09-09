"""
Automated tests for AASI backend API endpoints.
Tests run without requiring a GPU or a live Ollama service by mocking HTTP transport.
"""

import pytest
from unittest.mock import AsyncMock, patch
import httpx
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import settings

client = TestClient(app)


def test_root_endpoint():
    """Verify root index returns application metadata and tool endpoint link."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["version"] == settings.app_version
    assert data["tools_url"] == "/api/tools"


def test_tools_endpoint():
    """Verify GET /api/tools returns the registered engineering tools catalog."""
    response = client.get("/api/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    tool_names = [t["name"] for t in data["tools"]]
    assert "orbit" in tool_names
    assert "rocket" in tool_names
    assert "math" in tool_names


def test_health_endpoint_ollama_connected():
    """Verify /api/health when Ollama is running and accessible."""
    mock_tags_response = httpx.Response(
        status_code=200,
        json={"models": [{"name": settings.ollama_model}]},
        request=httpx.Request("GET", f"{settings.ollama_base_url}/api/tags"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_tags_response
        response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == settings.app_version
    assert data["ollama_connected"] is True
    assert data["configured_model"] == settings.ollama_model
    assert data["error"] is None


def test_health_endpoint_ollama_unreachable():
    """Verify /api/health reports disconnected state when Ollama is not running."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["ollama_connected"] is False
    assert "Could not connect to Ollama" in data["error"]


def test_chat_endpoint_conceptual_success():
    """Verify POST /api/chat returns structured response on successful conceptual inference."""
    mock_chat_response = httpx.Response(
        status_code=200,
        json={
            "model": settings.ollama_model,
            "message": {
                "role": "assistant",
                "content": "A Hohmann transfer is an elliptical orbital maneuver used to transfer between two circular orbits.",
            },
            "done": True,
        },
        request=httpx.Request("POST", f"{settings.ollama_base_url}/api/chat"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_chat_response
        response = client.post("/api/chat", json={"message": "What is a Hohmann transfer?"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["model"] == settings.ollama_model
    assert "Hohmann transfer" in data["response"]
    assert len(data["tool_calls"]) == 0


def test_chat_endpoint_computational_tool_execution():
    """Verify POST /api/chat executes tool and provides trace for numerical calculation."""
    mock_chat_response = httpx.Response(
        status_code=200,
        json={
            "model": settings.ollama_model,
            "message": {
                "role": "assistant",
                "content": "The circular orbital velocity at 500 km is approximately 7.61 km/s with a period of 94.6 minutes.",
            },
            "done": True,
        },
        request=httpx.Request("POST", f"{settings.ollama_base_url}/api/chat"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_chat_response
        response = client.post(
            "/api/chat",
            json={"message": "What is the circular orbital velocity at 500 km altitude around Earth?"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["tool_calls"]) == 1
    assert data["tool_calls"][0]["tool"] == "orbit"
    assert data["tool_calls"][0]["operation"] == "circular_orbit"
    assert len(data["calculations"]) == 1
    assert data["calculations"][0]["results"]["orbital_velocity_km_s"] > 7.0


def test_chat_endpoint_validation_empty():
    """Verify POST /api/chat rejects empty messages with HTTP 422."""
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422


def test_chat_endpoint_validation_missing_field():
    """Verify POST /api/chat rejects payload with missing 'message' field with HTTP 422."""
    response = client.post("/api/chat", json={})
    assert response.status_code == 422


def test_chat_endpoint_ollama_unavailable():
    """Verify POST /api/chat returns HTTP 503 when Ollama is not running."""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        response = client.post("/api/chat", json={"message": "What is specific impulse?"})

    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert "Cannot connect to Ollama" in data["detail"]


def test_chat_endpoint_ollama_model_not_found():
    """Verify POST /api/chat returns HTTP 502 with diagnostic when model is not installed."""
    mock_err_response = httpx.Response(
        status_code=404,
        text='{"error":"model not found, try pulling it first"}',
        request=httpx.Request("POST", f"{settings.ollama_base_url}/api/chat"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_err_response
        response = client.post("/api/chat", json={"message": "Explain specific impulse."})

    assert response.status_code == 502
    data = response.json()
    assert "detail" in data
    assert "was not found in Ollama" in data["detail"]


def test_chat_endpoint_ollama_timeout():
    """Verify POST /api/chat returns HTTP 502 when Ollama query times out on conceptual request."""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Timeout")
        response = client.post("/api/chat", json={"message": "What is the Oberth effect?"})

    assert response.status_code == 502
    data = response.json()
    assert "detail" in data
    assert "timed out" in data["detail"]


def test_docs_endpoint():
    """Verify GET /docs serves the OpenAPI / Swagger documentation."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


def test_chat_endpoint_clarification_response():
    """Verify POST /api/chat returns structured clarification when required parameters are missing."""
    response = client.post("/api/chat", json={"message": "How fast does a satellite move?"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "clarification_needed"
    assert "Clarification" in data["response"]
    assert len(data["tool_calls"]) == 1
    assert data["tool_calls"][0]["status"] == "clarification_needed"


def test_chat_endpoint_unicode_and_symbols():
    """Verify POST /api/chat safely handles Unicode characters and engineering symbols."""
    mock_chat_response = httpx.Response(
        status_code=200,
        json={
            "model": settings.ollama_model,
            "message": {"role": "assistant", "content": "Analysis of Δv and Keplerian orbit: θ = 45°"},
            "done": True,
        },
        request=httpx.Request("POST", f"{settings.ollama_base_url}/api/chat"),
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_chat_response
        response = client.post("/api/chat", json={"message": "Analyze orbital velocity Δv with θ = 45° and altitude = 500 km"})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data


def test_chat_endpoint_long_input():
    """Verify POST /api/chat handles large input payloads up to 8000 characters."""
    long_msg = "Explain orbital mechanics. " + ("Keplerian motion. " * 300)
    mock_chat_response = httpx.Response(
        status_code=200,
        json={
            "model": settings.ollama_model,
            "message": {"role": "assistant", "content": "Summary of Keplerian mechanics."},
            "done": True,
        },
        request=httpx.Request("POST", f"{settings.ollama_base_url}/api/chat"),
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_chat_response
        response = client.post("/api/chat", json={"message": long_msg})
    assert response.status_code == 200

