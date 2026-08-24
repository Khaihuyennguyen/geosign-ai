import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.corridor_data import REAL_PARCELS_DATA, EXISTING_BILLBOARDS
from spatial_engine import SpatialBufferEngine
from vision_agent import GeminiVisionInspector

def test_vision_agent():
    print("=" * 75)
    print(">>> [TEST] MULTIMODAL SATELLITE VISION & PIXEL CANOPY INSPECTOR")
    print("=" * 75)
    
    spatial_engine = SpatialBufferEngine()
    spatial_results = spatial_engine.audit_corridor(REAL_PARCELS_DATA, EXISTING_BILLBOARDS)
    green_parcels = [p for p in spatial_results if p["is_qualified"]]
    
    print(f"[*] Analyzing {len(green_parcels)} spatially-qualified parcels with Vision Engine...")
    
    vision_agent = GeminiVisionInspector()
    
    for parcel in green_parcels[:5]:
        vision_result = vision_agent.analyze_aerial_imagery(parcel)
        
        assert 0 <= vision_result["visibility_score"] <= 100
        assert vision_result["driver_dwell_time_sec"] > 0
        assert vision_result["unobstructed_sightline_ft"] > 0
        assert "model_version" in vision_result
        
        print(f"[PARCEL] {vision_result['parcel_id']}")
        print(f"   * Model Engine: {vision_result['model_version']}")
        print(f"   * Visibility Score: {vision_result['visibility_score']} / 100")
        print(f"   * Canopy Density: {vision_result['canopy_density_pct']}%")
        print(f"   * Dwell Time: {vision_result['driver_dwell_time_sec']}s at {vision_result['highway_speed_mph']} mph")
        print(f"   * Rec Monopole Height: {vision_result['recommended_monopole_height_ft']} ft")
        print(f"   * AI Justification: {vision_result['ai_visual_justification']}")
        print("-" * 75)
        
    print("[SUCCESS] VISION INSPECTOR TEST PASSED 100%!")

if __name__ == "__main__":
    test_vision_agent()
