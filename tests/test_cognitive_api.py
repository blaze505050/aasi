"""
AASI Cognitive Engine: API Endpoint Integration Tests.
Validates /api/cognitive/investigate, /session/{id}, /graph, /tools, and /skills.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_api_cognitive_tools():
    res = client.get("/api/cognitive/tools")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3
    tool_ids = [t["tool_id"] for t in data]
    assert "discrete_vortex_panel" in tool_ids
    assert "openfoam_simplefoam" in tool_ids


def test_api_cognitive_skills():
    res = client.get("/api/cognitive/skills")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert "NACA Airfoil" in data[0]["name"]


def test_api_cognitive_investigate_and_graph():
    payload = {
        "question": "Investigate lift and drag for NACA 0012 cruise at alpha=4 deg",
        "geometry_name": "NACA 0012",
        "alpha_deg": 4.0,
        "reynolds": 3.0e6,
        "mach": 0.15,
        "autonomy_level": "LEVEL_4",
        "max_cycles": 2,
    }
    res = client.post("/api/cognitive/investigate", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "SUCCESS"
    session_id = body["session"]["session_id"]
    assert session_id.startswith("INV-COG-")
    assert body["session"]["current_state"] == "COMPLETED"

    # Test session get
    res_session = client.get(f"/api/cognitive/session/{session_id}")
    assert res_session.status_code == 200
    session_data = res_session.json()
    assert session_data["world_model"]["geometry"]["name"] == "NACA 0012"

    # Test graph get
    res_graph = client.get(f"/api/cognitive/session/{session_id}/graph")
    assert res_graph.status_code == 200
    graph = res_graph.json()
    assert len(graph["nodes"]) >= 4
    assert len(graph["links"]) >= 3
    node_types = [n["type"] for n in graph["nodes"]]
    assert "QUESTION" in node_types
    assert "HYPOTHESIS" in node_types
    assert "EXPERIMENT" in node_types
    assert "DECISION" in node_types
