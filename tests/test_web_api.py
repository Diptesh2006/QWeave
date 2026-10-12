from fastapi.testclient import TestClient
from qiskit import qasm2

from web.server import app, create_hardware_graph


client = TestClient(app)


def test_health_and_preset_catalog():
    health = client.get("/api/health")
    presets = client.get("/api/circuits/presets")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"
    assert presets.status_code == 200
    assert any(item["id"] == "cnot_chain_4q" for item in presets.json())


def test_layout_catalog_and_studio_are_served():
    layouts = client.get("/api/layouts/presets")
    studio = client.get("/")
    assert layouts.status_code == 200
    assert {item["id"] for item in layouts.json()} >= {"line_4q", "grid_2x2", "ibm_manila_5q"}
    assert studio.status_code == 200
    assert "QWeave" in studio.text


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
    downloaded = qasm2.loads(payload["primary_result"]["routed_qasm"])
    assert all(item.operation.name in {"u3", "cx"} for item in downloaded.data)


def test_all_baseline_exports_are_parseable_qasm2():
    response = client.post("/api/compile", json={
        "circuit_mode": "preset",
        "preset_circuit_id": "cnot_chain_4q",
        "layout_id": "line_4q",
        "method": "all",
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    for result in payload["all_results"].values():
        downloaded = qasm2.loads(result["routed_qasm"])
        assert all(item.operation.name in {"u3", "cx"} for item in downloaded.data)


def test_compile_endpoint_rejects_invalid_circuit_preset():
    response = client.post("/api/compile", json={
        "circuit_mode": "preset",
        "preset_circuit_id": "not-a-preset",
        "layout_id": "line_4q",
        "method": "weighted",
    })
    assert response.status_code == 400


def test_compile_endpoint_marks_unsupported_operation_as_failure():
    response = client.post("/api/compile", json={
        "circuit_mode": "custom",
        "custom_qasm": "qreg q[3]; ccx q[0],q[1],q[2];",
        "layout_id": "line_4q",
        "method": "weighted",
        "auto_decompose": False,
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert "unsupported source operation" in payload["primary_result"]["error"]


def test_compile_endpoint_rejects_unknown_method():
    response = client.post("/api/compile", json={"method": "mystery"})
    assert response.status_code == 422


def test_custom_topology_rejects_out_of_range_and_self_edges():
    import pytest

    with pytest.raises(ValueError, match="exceeds"):
        create_hardware_graph("custom", [[0, 2]], custom_nodes=2)
    with pytest.raises(ValueError, match="self-loops"):
        create_hardware_graph("custom", [[1, 1]], custom_nodes=2)


def test_compile_endpoint_reports_invalid_custom_topology():
    response = client.post("/api/compile", json={
        "circuit_mode": "preset",
        "preset_circuit_id": "cnot_chain_4q",
        "layout_id": "custom",
        "custom_nodes": 3,
        "custom_edges": [[0, 3]],
        "method": "weighted",
    })
    assert response.status_code == 400
    assert "declared node count" in response.json()["detail"]
