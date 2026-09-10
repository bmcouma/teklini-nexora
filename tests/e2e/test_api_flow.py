import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nexora.api.db import Base, get_db
from nexora.api.main import app
from nexora.config.settings import get_settings


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test_nexora.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_and_version(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    r = client.get("/api/version")
    assert r.status_code == 200
    assert r.json()["version"]


def test_full_incident_lifecycle_via_api(client):
    r = client.post("/api/incidents", json={"use_demo_data": True})
    assert r.status_code == 200
    body = r.json()
    incident_id = body["incident"]["incident_id"]
    assert body["incident"]["stage"] == "report_ready"

    r = client.get(f"/api/incidents/{incident_id}")
    assert r.status_code == 200
    assert r.json()["incident_id"] == incident_id

    r = client.get(f"/api/incidents/{incident_id}/status")
    assert r.status_code == 200

    r = client.get(f"/api/incidents/{incident_id}/evidence")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    r = client.get(f"/api/incidents/{incident_id}/report")
    assert r.status_code == 200
    assert r.json()["is_demo_data"] is True

    r = client.get("/api/incidents")
    assert r.status_code == 200
    assert any(item["incident_id"] == incident_id for item in r.json())


def test_creating_incident_without_title_or_demo_data_returns_422(client):
    r = client.post("/api/incidents", json={"description": "Missing a title."})
    assert r.status_code == 422


def test_report_not_found_for_unknown_incident(client):
    r = client.get("/api/incidents/INC-DOESNOTEXIST/report")
    assert r.status_code == 404


def test_sensitive_routes_require_api_key_when_enabled(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "auth_required", True)
    monkeypatch.setattr(settings, "api_key", "test-api-key")

    assert client.post("/api/incidents", json={"use_demo_data": True}).status_code == 401

    response = client.post(
        "/api/incidents",
        json={"use_demo_data": True},
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 200


def test_approval_flow_updates_recommendation_state(client):
    r = client.post(
        "/api/incidents",
        json={
            "title": "Repeated authentication failures",
            "description": "Many users are failing authentication and credentials may be compromised.",
            "logs": "authentication failed\nauthentication failed\n",
        },
    )
    incident_id = r.json()["incident"]["incident_id"]
    recommendations = r.json()["recommendations"]
    approvable = next((i for i, rec in enumerate(recommendations) if rec["requires_approval"]), None)

    if approvable is not None:
        r = client.post(
            f"/api/incidents/{incident_id}/approve",
            json={"recommendation_index": approvable, "approved": True, "approved_by": "test-user"},
        )
        assert r.status_code == 200
        assert r.json()["recommendations"][approvable]["approved"] is True
