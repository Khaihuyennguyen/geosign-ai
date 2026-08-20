from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os

from data.corridor_data import CORRIDORS_REGISTRY
from spatial_engine import evaluate_parcel
from vision_agent import GeminiVisionInspector
from report_generator import FeasibilityReportGenerator

report_gen = FeasibilityReportGenerator()
vision_inspector = GeminiVisionInspector()

app = FastAPI(
    title="GeoSignAI Autonomous Billboard Siting Agent",
    description="Production-grade AI Agent for automated highway corridor scouting, 500-ft spacing math, Gemini 3.5 visual inspection, and 1-page municipal permit PDF generation.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)



class ScoutRequest(BaseModel):
    corridor_id: str = "I35-50Mile-Regional"
    min_traffic: int = 25000
    min_spacing_feet: float = 500.0

class ScoutedParcelResponse(BaseModel):
    parcel_id: str
    name: Optional[str] = None
    address: str
    owner_name: str
    zoning: str
    aadt_traffic: int
    coordinates: List[float]
    lot_boundary: Optional[List[List[float]]] = None
    county: Optional[str] = None
    frontage_side: Optional[str] = None
    has_dense_trees: bool
    is_qualified: bool
    disqualification_reasons: List[str]
    min_distance_to_sign_feet: float
    nearest_billboard_permit: str
    nearest_operator: str
    nearest_coordinates: List[float]
    spacing_passed: bool
    spacing_margin_feet: float
    is_commercial_zoning: bool
    tree_canopy_present: bool
    visibility_score: int
    obstruction_level: str
    ai_visual_justification: str
    est_annual_ad_revenue: int
    pdf_available: bool
    proof: Optional[Dict[str, Any]] = None

class ScoutCorridorResponse(BaseModel):
    corridor_id: str
    corridor_name: str
    total_evaluated: int
    qualified_count: int
    disqualified_count: int
    parcels: List[ScoutedParcelResponse]
    highway_centerline: List[List[float]]
    existing_billboards: List[Dict[str, Any]]
    cadastral_polygons: Optional[List[Dict[str, Any]]] = None
    agent_thought_traces: List[str]

@app.get("/")
def read_root():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"status": "GeoSignAI Backend Running", "message": "Visit /static/index.html"}

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "GeoSignAI", "agent_version": "2.0.0"}

@app.get("/api/corridors")
def list_corridors():
    return [
        {
            "id": c["id"],
            "name": c["name"],
            "state": c["state"],
            "county": c["county"],
            "center": c["center"],
            "zoom": c["zoom"]
        }
        for c in CORRIDORS_REGISTRY.values()
    ]

@app.post("/api/scout/run", response_model=ScoutCorridorResponse)
def scout_corridor(req: ScoutRequest):
    if req.corridor_id not in CORRIDORS_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Corridor '{req.corridor_id}' not found.")
        
    corridor = CORRIDORS_REGISTRY[req.corridor_id]
    existing_billboards = corridor["existing_billboards"]
    raw_parcels = corridor["parcels"]
    cadastral_polygons = corridor.get("cadastral_polygons", [])
    
    thought_traces = [
        f"[INIT] Autonomous Scout Agent initialized for {corridor['name']}.",
        f"[DATA] Ingested {len(existing_billboards)} live TxDOT licensed billboard locations from State of Texas database.",
        f"[INGEST] Ingested {len(raw_parcels)} real individual parcel lots with separate cadastral boundaries.",
        f"[CADASTRAL] Evaluating Shapely Point-in-Polygon (PIP) spatial intersections against {len(cadastral_polygons)} zoning ribbons...",
        "[SPATIAL] Executing Haversine Geodesic 500-foot buffer exclusion algorithm (Texas Transportation Code § 391.031)..."
    ]
    
    evaluated_parcels = []
    qualified_count = 0
    disqualified_count = 0
    
    for p in raw_parcels:
        eval_p = evaluate_parcel(p, existing_billboards, req.min_spacing_feet, cadastral_polygons)
        
        if eval_p["is_qualified"]:
            qualified_count += 1
            if eval_p["tree_canopy_present"]:
                thought_traces.append(f"[VISION CAUTION] {eval_p['parcel_id']} ({eval_p['owner_name']}): Passed 500ft spacing ({eval_p['min_distance_to_sign_feet']:,.1f} ft) but flagged for tree canopy obstruction.")
            else:
                thought_traces.append(f"[VISION APPROVED] {eval_p['parcel_id']} ({eval_p['owner_name']}): 100% Clear sightline from I-35 lanes. Est. Revenue: ${eval_p['est_annual_ad_revenue']:,}/yr.")
        else:
            disqualified_count += 1
            reason = eval_p["disqualification_reasons"][0] if eval_p["disqualification_reasons"] else "Ineligible"
            thought_traces.append(f"[DISQUALIFIED] {eval_p['parcel_id']}: {reason}")
            
        evaluated_parcels.append(eval_p)
        
    thought_traces.append(f"[COMPLETE] Corridor analysis complete. {qualified_count} / {len(raw_parcels)} individual lots qualified for municipal permit filings.")
    
    return {
        "corridor_id": corridor["id"],
        "corridor_name": corridor["name"],
        "total_evaluated": len(evaluated_parcels),
        "qualified_count": qualified_count,
        "disqualified_count": disqualified_count,
        "parcels": evaluated_parcels,
        "highway_centerline": corridor["highway_centerline"],
        "existing_billboards": existing_billboards,
        "cadastral_polygons": cadastral_polygons,
        "agent_thought_traces": thought_traces
    }

@app.get("/api/parcels/{parcel_id}/pdf")
def get_parcel_pdf(parcel_id: str):
    found_parcel = None
    existing_bb = []
    cadastral_polygons = []
    
    for c in CORRIDORS_REGISTRY.values():
        for p in c["parcels"]:
            if p["parcel_id"] == parcel_id:
                found_parcel = p
                existing_bb = c["existing_billboards"]
                cadastral_polygons = c.get("cadastral_polygons", [])
                break
        if found_parcel:
            break
            
    if not found_parcel:
        raise HTTPException(status_code=404, detail=f"Parcel ID {parcel_id} not found.")
        
    eval_p = evaluate_parcel(found_parcel, existing_bb, 500.0, cadastral_polygons)
    vision_data = vision_inspector.analyze_aerial_imagery(eval_p)
    pdf_path = report_gen.generate_pdf(eval_p, vision_data)
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"Feasibility_Report_{parcel_id}.pdf"
    )

@app.get("/{full_path:path}")
def serve_spa_and_assets(full_path: str):
    file_path = os.path.join(static_dir, full_path)
    if full_path and os.path.isfile(file_path):
        return FileResponse(file_path)
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"status": "GeoSignAI Backend Online"}

