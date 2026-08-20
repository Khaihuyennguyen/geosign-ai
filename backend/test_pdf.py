import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.corridor_data import REAL_PARCELS_DATA, EXISTING_BILLBOARDS
from spatial_engine import SpatialBufferEngine
from vision_agent import GeminiVisionInspector
from report_generator import FeasibilityReportGenerator

def run_pdf_test():
    print("=" * 75)
    print(">>> [TEST] PIECE 4: 1-PAGE PDF FEASIBILITY REPORT GENERATOR")
    print("=" * 75)
    
    # 1. Run spatial engine
    spatial_engine = SpatialBufferEngine()
    spatial_results = spatial_engine.audit_corridor(REAL_PARCELS_DATA, EXISTING_BILLBOARDS)
    
    # 2. Pick top qualified green parcel (e.g. TCAD-0219200401)
    top_parcel = [p for p in spatial_results if p["parcel_id"] == "TCAD-0219200401"][0]
    
    # 3. Run Vision AI
    vision_agent = GeminiVisionInspector()
    vision_result = vision_agent.analyze_aerial_imagery(top_parcel)
    
    # 4. Generate PDF Report
    pdf_gen = FeasibilityReportGenerator(output_dir="generated_reports")
    pdf_path = pdf_gen.generate_pdf(top_parcel, vision_result)
    
    print(f"[*] PDF Report Successfully Generated!")
    print(f"    * File: {pdf_path}")
    print(f"    * Size: {os.path.getsize(pdf_path):,} bytes")
    print("=" * 75)
    print("[SUCCESS] PIECE 4 PDF REPORT GENERATOR TEST PASSED 100%!")

if __name__ == "__main__":
    run_pdf_test()
