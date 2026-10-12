from fastapi.testclient import TestClient

from web.server import app


client = TestClient(app)


def test_health_and_preset_catalog():
    health = client.get("/api/health")
    presets = client.get("/api/circuits/presets")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"
    assert presets.status_code == 200
    assert any(item["id"] == "cnot_chain_4q" for item in presets.json())


def test_compile_endpoint_returns_validated_weighted_route():
    response = client.post("/api/compile", json={
        "circuit_mode": "preset",
        "preset_circuit_id": "cnot_chain_4q",
        "layout_id": "line_4q",
        "method": "weighted",
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["primary_result"]["legality_verified"] is True
    assert payload["primary_result"]["semantic_validation"] is True
    assert len(payload["primary_result"]["initial_mapping"]) == 4


def test_compile_endpoint_rejects_invalid_circuit_preset():
    response = client.post("/api/compile", json={
        "circuit_mode": "preset",
        "preset_circuit_id": "not-a-preset",
        "layout_id": "line_4q",
        "method": "weighted",
    })
    assert response.status_code == 400
