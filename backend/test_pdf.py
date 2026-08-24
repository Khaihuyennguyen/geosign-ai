import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.corridor_data import REAL_PARCELS_DATA, EXISTING_BILLBOARDS
from spatial_engine import SpatialBufferEngine
from vision_agent import GeminiVisionInspector
from report_generator import FeasibilityReportGenerator

def test_pdf_generation():
    print("=" * 75)
    print(">>> [TEST] DYNAMIC PDF FEASIBILITY REPORT COMPILER")
    print("=" * 75)
    
    spatial_engine = SpatialBufferEngine()
    spatial_results = spatial_engine.audit_corridor(REAL_PARCELS_DATA, EXISTING_BILLBOARDS)
    green_parcels = [p for p in spatial_results if p["is_qualified"]]
    
    assert len(green_parcels) > 0, "No green parcels found!"
    target_parcel = green_parcels[0]
    
    vision_agent = GeminiVisionInspector()
    vision_result = vision_agent.analyze_aerial_imagery(target_parcel)
    
    pdf_gen = FeasibilityReportGenerator(output_dir="generated_reports")
    pdf_path = pdf_gen.generate_pdf(target_parcel, vision_result)
    
    assert os.path.exists(pdf_path), f"PDF file not found at {pdf_path}"
    file_size = os.path.getsize(pdf_path)
    assert file_size > 1000, f"PDF file size is suspiciously small: {file_size} bytes"
    
    print(f"[PASS] Successfully generated PDF for {target_parcel['parcel_id']}")
    print(f"   * Path: {pdf_path}")
    print(f"   * File Size: {file_size:,} bytes")
    print("[SUCCESS] PDF REPORT GENERATOR TEST PASSED 100%!")

if __name__ == "__main__":
    test_pdf_generation()
