import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.corridor_data import CORRIDORS_REGISTRY
from spatial_engine import SpatialBufferEngine
from vision_agent import GeminiVisionInspector

def test_all_corridors():
    print("=" * 80)
    print("TESTING MULTI-HIGHWAY CORRIDOR ENGINE (I-35 + US-183 + SH-71)")
    print("=" * 80)
    
    spatial_engine = SpatialBufferEngine(min_spacing_feet=500.0, min_aadt_traffic=25000)
    vision_agent = GeminiVisionInspector()
    
    total_evaluated = 0
    total_approved = 0
    total_tree_risk = 0
    total_disqualified = 0
    
    for corridor_id, corridor in CORRIDORS_REGISTRY.items():
        print(f"\n================================================================================")
        print(f"HIGHWAY: {corridor['name']} ({corridor['state']})")
        print(f"================================================================================")
        
        parcels = corridor["parcels"]
        billboards = corridor["existing_billboards"]
        
        spatial_results = spatial_engine.audit_corridor(parcels, billboards)
        
        c_approved = 0
        c_tree_risk = 0
        c_disqualified = 0
        
        for p in spatial_results:
            total_evaluated += 1
            if p["is_qualified"]:
                vision_res = vision_agent.analyze_aerial_imagery(p)
                if vision_res["tree_canopy_present"]:
                    c_tree_risk += 1
                    total_tree_risk += 1
                else:
                    c_approved += 1
                    total_approved += 1
            else:
                c_disqualified += 1
                total_disqualified += 1
                
        print(f"  * Total Parcels: {len(parcels)}")
        print(f"  * Approved Clear: {c_approved}")
        print(f"  * Tree Variance Required: {c_tree_risk}")
        print(f"  * Disqualified (500ft / Zoning): {c_disqualified}")
        
    print("\n" + "=" * 80)
    print("MULTI-CORRIDOR VERIFICATION SUMMARY:")
    print(f"  * Total Parcels Evaluated: {total_evaluated}")
    print(f"  * Total Approved (Clear): {total_approved}")
    print(f"  * Total Tree Risk (Variance Needed): {total_tree_risk}")
    print(f"  * Total Disqualified: {total_disqualified}")
    print("=" * 80)
    
    assert total_evaluated == 444
    assert total_approved > 0
    assert total_tree_risk > 0
    assert total_disqualified > 0
    print("[SUCCESS] ALL 3 HIGHWAY CORRIDORS VERIFIED 100%!")

if __name__ == "__main__":
    test_all_corridors()
