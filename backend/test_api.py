import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def run_api_test():
    print("=" * 75)
    print(">>> [TEST] PIECE 5: FASTAPI REST API SERVER ENDPOINTS")
    print("=" * 75)
    
    # 1. Health Check
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print(f"[GET /api/health] -> 200 OK: {res.json()}")
    
    # 2. List Corridors
    res = client.get("/api/corridors")
    assert res.status_code == 200, f"List corridors failed: {res.text}"
    corridors = res.json()
    assert len(corridors) > 0
    print(f"[GET /api/corridors] -> 200 OK: Found {len(corridors)} highway corridor ({corridors[0]['name']})")
    
    # 3. Trigger Autonomous Scout
    payload = {"corridor_id": "I35-Austin", "min_traffic": 25000, "min_spacing_feet": 500.0}
    res = client.post("/api/scout/run", json=payload)
    assert res.status_code == 200, f"Scout run failed: {res.text}"
    scout_data = res.json()
    print(f"[POST /api/scout/run] -> 200 OK: Evaluated {scout_data['total_evaluated']} parcels ({scout_data['qualified_count']} Green, {scout_data['disqualified_count']} Red)")
    print(f"   * Sample Agent Trace: {scout_data['agent_thought_traces'][0]}")
    
    # 4. Download PDF
    res = client.get("/api/parcels/TCAD-0219200401/pdf")
    assert res.status_code == 200, f"PDF download failed: {res.text}"
    assert res.headers["content-type"] == "application/pdf"
    print(f"[GET /api/parcels/TCAD-0219200401/pdf] -> 200 OK: Received PDF binary ({len(res.content):,} bytes)")
    
    print("=" * 75)
    print("[SUCCESS] PIECE 5 FASTAPI BACKEND API TEST PASSED 100%!")

if __name__ == "__main__":
    run_api_test()
