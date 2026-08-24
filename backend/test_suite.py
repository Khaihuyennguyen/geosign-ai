import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app
from spatial_engine import haversine_distance_feet, SpatialBufferEngine
from data.corridor_data import CORRIDORS_REGISTRY

client = TestClient(app)

def test_01_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["total_registered_parcels"] == 444

def test_02_corridor_listing():
    response = client.get("/api/corridors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["id"] == "I35-50Mile-Regional"

def test_03_scout_run_full_corridor():
    req_payload = {
        "corridor_id": "I35-50Mile-Regional",
        "min_spacing_feet": 500.0
    }
    response = client.post("/api/scout/run", json=req_payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_evaluated"] == 172
    assert data["approved_clear"] > 0
    assert len(data["existing_billboards"]) == 15
    assert len(data["agent_thought_traces"]) > 0

def test_04_haversine_distance_calculation():
    calc = haversine_distance_feet(30.2672, -97.7431, 30.5083, -97.6789)
    assert 85000 < calc["distance_feet"] < 105000
    assert calc["formula"] is not None

def test_05_pdf_report_generation():
    corridor = CORRIDORS_REGISTRY["I35-50Mile-Regional"]
    first_parcel = corridor["parcels"][0]
    parcel_id = first_parcel["parcel_id"]
    
    response = client.get(f"/api/parcels/{parcel_id}/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 1000

if __name__ == "__main__":
    print("Running Master Automated Test Suite...")
    test_01_health_check()
    print("Test 1: Health Check Passed!")
    test_02_corridor_listing()
    print("Test 2: Corridor Listing Passed (3 Corridors)!")
    test_03_scout_run_full_corridor()
    print("Test 3: Full Scout Run Passed (172 Parcels on I-35)!")
    test_04_haversine_distance_calculation()
    print("Test 4: Haversine Geodesic Math Passed!")
    test_05_pdf_report_generation()
    print("Test 5: Dynamic 1-Page Permit PDF Generator Passed!")
    print("\n========================================================")
    print("ALL MASTER BACKEND TESTS PASSED (100% SUCCESS)!")
    print("========================================================")
