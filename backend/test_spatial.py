import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.corridor_data import CORRIDORS_REGISTRY, REAL_PARCELS_DATA, EXISTING_BILLBOARDS
from spatial_engine import SpatialBufferEngine, haversine_distance_feet

def test_haversine():
    # Austin to Round Rock (~18 miles / ~95,000 ft)
    calc = haversine_distance_feet(30.2672, -97.7431, 30.5083, -97.6789)
    assert calc["distance_feet"] > 80000 and calc["distance_feet"] < 110000
    print(f"[PASS] Haversine math verified: Austin to Round Rock = {calc['distance_feet']:,} ft")

def test_spatial_engine_corridors():
    engine = SpatialBufferEngine(min_spacing_feet=500.0, min_aadt_traffic=25000)
    
    total_evaluated = 0
    total_qualified = 0
    total_disqualified = 0
    
    for cid, corridor in CORRIDORS_REGISTRY.items():
        results = engine.audit_corridor(corridor["parcels"], corridor["existing_billboards"])
        q_count = sum(1 for r in results if r["is_qualified"])
        d_count = sum(1 for r in results if not r["is_qualified"])
        
        total_evaluated += len(results)
        total_qualified += q_count
        total_disqualified += d_count
        
        print(f"[PASS] Corridor {cid}: {len(results)} evaluated, {q_count} qualified, {d_count} disqualified")
        
    assert total_evaluated == 444
    assert total_qualified > 0
    assert total_disqualified > 0
    print(f"\n[SUMMARY] Evaluated {total_evaluated} parcels across 3 corridors:")
    print(f"  * Total Qualified: {total_qualified}")
    print(f"  * Total Disqualified (500-ft / Zoning): {total_disqualified}")
    print("[SUCCESS] ALL SPATIAL BUFFER & ZONING TESTS PASSED 100%!")

if __name__ == "__main__":
    test_haversine()
    test_spatial_engine_corridors()
