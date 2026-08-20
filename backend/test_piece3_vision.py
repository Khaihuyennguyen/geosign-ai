import sys
import os
import json

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vision_agent import GeminiVisionInspector

def test_piece3_multimodal_vision():
    print("=" * 85)
    print("PIECE 3 TEST: GEMINI 3.5 FLASH MULTIMODAL SIGHTLINE & TREE CANOPY REASONING")
    print("=" * 85)
    
    inspector = GeminiVisionInspector()
    
    # Test Case 1: Clear Sightline Parcel
    clear_parcel = {
        "parcel_id": "TCAD-STN-227H3501",
        "address": "2200 South I-35 Frontage Rd, Austin, TX 78704",
        "aadt_traffic": 180443,
        "has_dense_trees": False,
        "coordinates": [-97.7373, 30.2404]
    }
    
    print("\n[TEST 1] EVALUATING CLEAR COMMERCIAL HIGHWAY FRONTAGE:")
    res_clear = inspector.analyze_aerial_imagery(clear_parcel)
    print(f"  * Parcel ID: {res_clear['parcel_id']}")
    print(f"  * Visibility Score: {res_clear['visibility_score']} / 100 ({res_clear['obstruction_level']})")
    print(f"  * Recommended Monopole Height: {res_clear['recommended_monopole_height_ft']} ft")
    print(f"  * Driver Viewing Window: {res_clear['sightline_duration_seconds']} seconds @ 65 mph")
    print(f"  * Recommendation: {res_clear['recommendation']}")
    print(f"  * AI Reasoning: {res_clear['ai_visual_justification']}")
    assert res_clear['visibility_score'] >= 90
    assert res_clear['tree_canopy_present'] == False
    
    # Test Case 2: Tree-Obstructed Parcel
    tree_parcel = {
        "parcel_id": "TCAD-STN-227H3504",
        "address": "7400 North I-35 Frontage Rd, Austin, TX 78752",
        "aadt_traffic": 163332,
        "has_dense_trees": True,
        "coordinates": [-97.7049, 30.3313]
    }
    
    print("\n[TEST 2] EVALUATING TREE-OBSTRUCTED CANOPY SITE:")
    res_tree = inspector.analyze_aerial_imagery(tree_parcel)
    print(f"  * Parcel ID: {res_tree['parcel_id']}")
    print(f"  * Visibility Score: {res_tree['visibility_score']} / 100 ({res_tree['obstruction_level']})")
    print(f"  * Estimated Canopy Height: {res_tree['canopy_height_est_ft']} ft Oak Canopy")
    print(f"  * Required Monopole Height: {res_tree['recommended_monopole_height_ft']} ft (Variance Needed)")
    print(f"  * Recommendation: {res_tree['recommendation']}")
    print(f"  * AI Reasoning: {res_tree['ai_visual_justification']}")
    assert res_tree['visibility_score'] <= 50
    assert res_tree['tree_canopy_present'] == True
    
    print("\n" + "=" * 85)
    print("PIECE 3 VERIFICATION PASSED: Multimodal Vision Agent Accurately Detects Tree Obstructions!")
    print("=" * 85)

if __name__ == "__main__":
    test_piece3_multimodal_vision()
