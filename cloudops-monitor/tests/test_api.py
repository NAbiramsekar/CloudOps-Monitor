from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_incident_lifecycle() -> None:
    create_response = client.post(
        "/incidents",
        json={
            "title": "API latency spike",
            "description": "P95 latency is above threshold.",
            "severity": "high",
            "status": "open",
        },
    )
    assert create_response.status_code == 201
    incident = create_response.json()
    incident_id = incident["incident_id"]

    list_response = client.get("/incidents")
    assert list_response.status_code == 200
    assert any(item["incident_id"] == incident_id for item in list_response.json())

    update_response = client.put(f"/incidents/{incident_id}", json={"status": "resolved"})
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "resolved"

    delete_response = client.delete(f"/incidents/{incident_id}")
    assert delete_response.status_code == 204


def test_metrics_endpoint_exposes_prometheus_metrics() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "cloudops_http_requests_total" in response.text
    assert "cloudops_application_uptime_seconds" in response.text
