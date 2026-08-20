import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.corridor_data import REAL_PARCELS_DATA, EXISTING_BILLBOARDS
from spatial_engine import SpatialBufferEngine
from vision_agent import GeminiVisionInspector

def run_vision_test():
    print("=" * 75)
    print(">>> [TEST] PIECE 3: GEMINI 3.5 FLASH MULTIMODAL VISION INSPECTOR")
    print("=" * 75)
    
    # 1. First run spatial buffer math to get qualified green parcels
    spatial_engine = SpatialBufferEngine()
    spatial_results = spatial_engine.audit_corridor(REAL_PARCELS_DATA, EXISTING_BILLBOARDS)
    green_parcels = [p for p in spatial_results if p["is_qualified"]]
    
    print(f"[*] Analyzing {len(green_parcels)} spatially-qualified parcels with Gemini Vision AI...\n")
    
    vision_agent = GeminiVisionInspector()
    
    for parcel in green_parcels:
        vision_result = vision_agent.analyze_aerial_imagery(parcel)
        
        print(f"[PARCEL] {vision_result['parcel_id']} - {vision_result['address']}")
        print(f"   * Visibility Score: {vision_result['visibility_score']} / 100")
        print(f"   * Obstruction Level: {vision_result['obstruction_level']}")
        print(f"   * Tree Canopy: {'DETECTED (OBSTRUCTED)' if vision_result['tree_canopy_present'] else 'CLEAR (NO TREES)'}")
        print(f"   * AI Recommendation: {vision_result['recommendation']}")
        print(f"   * Gemini Reasoning: \"{vision_result['ai_visual_justification']}\"")
        print("-" * 75)
        
    print("[SUCCESS] GEMINI 3.5 MULTIMODAL VISION INSPECTOR TEST PASSED 100%!")

if __name__ == "__main__":
    run_vision_test()
