import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["total_registered_parcels"] == 444
    print(f"[PASS] /api/health -> Total Registered Parcels: {data['total_registered_parcels']}")

def test_corridors_endpoint():
    res = client.get("/api/corridors")
    assert res.status_code == 200
    corridors = res.json()
    assert len(corridors) == 3
    print(f"[PASS] /api/corridors -> Found {len(corridors)} Corridors: {[c['id'] for c in corridors]}")

def test_scout_run_all_corridors():
    for cid in ["I35-50Mile-Regional", "US183-Airport-Expwy", "SH71-Bastrop-Corridor"]:
        res = client.post("/api/scout/run", json={"corridor_id": cid, "min_spacing_feet": 500.0})
        assert res.status_code == 200
        data = res.json()
        assert data["total_evaluated"] > 0
        assert len(data["agent_thought_traces"]) > 0
        print(f"[PASS] /api/scout/run ({cid}) -> {data['total_evaluated']} parcels evaluated in {data['execution_time_seconds']}s")

def test_pdf_endpoint():
    res = client.get("/api/parcels/TCAD-002001/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) > 1000
    print(f"[PASS] /api/parcels/TCAD-002001/pdf -> 200 OK ({len(res.content):,} bytes)")

if __name__ == "__main__":
    print("=" * 75)
    print(">>> [TEST] FASTAPI REST API SERVER ENDPOINTS")
    print("=" * 75)
    test_health_endpoint()
    test_corridors_endpoint()
    test_scout_run_all_corridors()
    test_pdf_endpoint()
    print("[SUCCESS] ALL FASTAPI ENDPOINTS VERIFIED 100%!")
