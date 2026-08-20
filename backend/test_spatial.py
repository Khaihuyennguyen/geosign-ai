import sys
import os

# Set UTF-8 encoding for standard output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.corridor_data import REAL_PARCELS_DATA, EXISTING_BILLBOARDS
from spatial_engine import SpatialBufferEngine

def run_test():
    print("=" * 75)
    print(">>> [TEST] PIECE 2: SPATIAL BUFFER & ZONING FILTER ENGINE")
    print("=" * 75)
    
    engine = SpatialBufferEngine(min_spacing_feet=500.0, min_aadt_traffic=25000)
    results = engine.audit_corridor(REAL_PARCELS_DATA, EXISTING_BILLBOARDS)
    
    passed_count = 0
    failed_count = 0
    
    for r in results:
        status_tag = "[PASSED - GREEN]" if r["is_qualified"] else "[DISQUALIFIED - RED]"
        print(f"\n{status_tag} Property: {r['parcel_id']} ({r['address']})")
        print(f"   * Owner: {r['owner_name']}")
        print(f"   * Traffic: {r['aadt_traffic']:,} daily cars")
        print(f"   * Distance to Nearest Billboard: {r['min_distance_to_sign_feet']:,} ft ({r['nearest_operator']})")
        print(f"   * Zoning: {r['zoning']}")
        
        if r["is_qualified"]:
            passed_count += 1
            print("   >>> STATUS: PASSED 500-FT SPACING & ZONING AUDIT (READY FOR VISION AI)")
        else:
            failed_count += 1
            print(f"   >>> STATUS: DISQUALIFIED -> {' | '.join(r['disqualification_reasons'])}")
            
    print("\n" + "=" * 75)
    print(">>> SUMMARY AUDIT RESULT:")
    print(f"   * Total Parcels Evaluated: {len(results)}")
    print(f"   * [GREEN] Qualified Candidate Parcels: {passed_count}")
    print(f"   * [RED] Disqualified Parcels: {failed_count}")
    print("=" * 75)
    
    assert passed_count == 4, f"Expected 4 passed parcels, got {passed_count}"
    assert failed_count == 2, f"Expected 2 failed parcels, got {failed_count}"
    print("\n[SUCCESS] ALL SPATIAL BUFFER & ZONING TESTS PASSED 100%!")

if __name__ == "__main__":
    run_test()
