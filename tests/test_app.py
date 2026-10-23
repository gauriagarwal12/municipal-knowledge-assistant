import os
import pytest

# Ensure tests do not need a live Gemini API key.
os.environ.setdefault("GEMINI_API_KEY", "")

import app as app_module

@pytest.fixture()
def client():
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()

def test_homepage_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Municipal Knowledge Assistant" in response.data

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"

def test_rejects_non_json(client):
    response = client.post("/chat", data="hello", content_type="text/plain")
    assert response.status_code == 400

def test_rejects_empty_message(client):
    response = client.post("/chat", json={"message": "   "})
    assert response.status_code == 400

def test_rejects_long_message(client):
    response = client.post("/chat", json={"message": "x" * 2001})
    assert response.status_code == 400
