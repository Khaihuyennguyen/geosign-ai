import os
import json
import time
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from data.corridor_data import CORRIDORS_REGISTRY, REAL_PARCELS_DATA, EXISTING_BILLBOARDS
from spatial_engine import SpatialBufferEngine
from vision_agent import GeminiVisionInspector
from report_generator import FeasibilityReportGenerator

app = FastAPI(
    title="GeoSignAI Autonomous Siting Fleet API",
    description="Multimodal Geospatial AI Agent Platform for Autonomous Billboard Siting",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

spatial_engine = SpatialBufferEngine(min_spacing_feet=500.0, min_aadt_traffic=25000)
vision_agent = GeminiVisionInspector()
pdf_generator = FeasibilityReportGenerator()

class ScoutRunRequest(BaseModel):
    corridor_id: Optional[str] = "I35-50Mile-Regional"
    min_spacing_feet: Optional[float] = 500.0
    min_aadt_traffic: Optional[int] = 25000

@app.get("/api/health")
def get_health():
    has_gemini = bool(vision_agent.client)
    return {
        "status": "online",
        "backend": "FastAPI Python 3.12",
        "spatial_engine": "Shapely + Geodesic WGS-84",
        "vision_engine": "Google Gemini 2.5 Flash (Live)" if has_gemini else "Local Geospatial Computer Vision (Spectral Analysis)",
        "gemini_api_key_configured": has_gemini,
        "available_corridors": list(CORRIDORS_REGISTRY.keys()),
        "total_registered_parcels": sum(len(c["parcels"]) for c in CORRIDORS_REGISTRY.values())
    }

@app.get("/api/corridors")
def get_corridors():
    return [
        {
            "id": c["id"],
            "name": c["name"],
            "state": c["state"],
            "parcel_count": len(c["parcels"]),
            "billboard_count": len(c["existing_billboards"]),
            "centerline": c["highway_centerline"]
        }
        for c in CORRIDORS_REGISTRY.values()
    ]

@app.post("/api/scout/run")
def run_autonomous_scout(req: ScoutRunRequest):
    corridor_id = req.corridor_id or "I35-50Mile-Regional"
    if corridor_id not in CORRIDORS_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Corridor '{corridor_id}' not found in registry.")
        
    corridor = CORRIDORS_REGISTRY[corridor_id]
    parcels = corridor["parcels"]
    billboards = corridor["existing_billboards"]
    
    start_time = time.time()
    
    # 1. Execute Spatial Buffer Engine
    spatial_results = spatial_engine.audit_corridor(parcels, billboards)
    
    # 2. Dynamic Agent Tool Execution & Thought Trace Generation
    evaluated_parcels = []
    thought_traces = []
    
    thought_traces.append(f"[INIT] Autonomous Scout Agent initialized for {corridor['name']}.")
    thought_traces.append(f"[INGEST] Ingested {len(parcels)} cadastral lots and {len(billboards)} active state-registered signs.")
    
    passed_count = 0
    tree_risk_count = 0
    disqualified_count = 0
    
    for p in spatial_results:
        p_id = p["parcel_id"]
        
        if p["is_qualified"]:
            # Tool Call: Vision Sightline & Canopy Inspection
            vis = vision_agent.analyze_aerial_imagery(p)
            
            p_evaluated = {
                **p,
                "tree_canopy_present": vis["tree_canopy_present"],
                "visibility_score": vis["visibility_score"],
                "obstruction_level": vis["obstruction_level"],
                "ai_visual_justification": vis["ai_visual_justification"],
                "unobstructed_sightline_ft": vis["unobstructed_sightline_ft"],
                "driver_dwell_time_sec": vis["driver_dwell_time_sec"],
                "recommended_monopole_height_ft": vis["recommended_monopole_height_ft"],
                "model_version": vis["model_version"],
                "pdf_available": True
            }
            
            if vis["tree_canopy_present"]:
                tree_risk_count += 1
                if len(thought_traces) < 25:
                    thought_traces.append(f"[VISION CAUTION] Parcel {p_id}: Spacing OK ({p['min_distance_to_sign_feet']:,.0f} ft), but canopy density is {vis['canopy_density_pct']}%. Tree trimming variance required.")
            else:
                passed_count += 1
                if len(thought_traces) < 25:
                    thought_traces.append(f"[VISION APPROVED] Parcel {p_id}: Clear {vis['unobstructed_sightline_ft']:.0f}ft sightline ({vis['driver_dwell_time_sec']}s dwell time). Standard {vis['recommended_monopole_height_ft']}ft monopole approved.")
                    
            evaluated_parcels.append(p_evaluated)
        else:
            disqualified_count += 1
            evaluated_parcels.append({
                **p,
                "tree_canopy_present": False,
                "visibility_score": 0,
                "obstruction_level": "Disqualified",
                "ai_visual_justification": "Disqualified prior to vision analysis.",
                "unobstructed_sightline_ft": 0,
                "driver_dwell_time_sec": 0,
                "recommended_monopole_height_ft": 42.5,
                "model_version": "N/A",
                "pdf_available": False
            })
            if len(thought_traces) < 25:
                thought_traces.append(f"[DISQUALIFIED] Parcel {p_id}: {p['disqualification_reasons'][0]}")
                
    elapsed = round(time.time() - start_time, 2)
    thought_traces.append(f"[COMPLETE] Siting scan finished in {elapsed}s: {passed_count} Approved, {tree_risk_count} Tree Risk, {disqualified_count} Disqualified.")
    
    return {
        "corridor_id": corridor_id,
        "corridor_name": corridor["name"],
        "total_evaluated": len(parcels),
        "approved_clear": passed_count,
        "tree_risk": tree_risk_count,
        "disqualified": disqualified_count,
        "execution_time_seconds": elapsed,
        "agent_thought_traces": thought_traces,
        "existing_billboards": billboards,
        "highway_centerline": corridor["highway_centerline"],
        "parcels": evaluated_parcels
    }

@app.get("/api/parcels/{parcel_id}/pdf")
def download_feasibility_pdf(parcel_id: str):
    target_parcel = None
    target_corridor = None
    
    for corridor in CORRIDORS_REGISTRY.values():
        for p in corridor["parcels"]:
            if p["parcel_id"] == parcel_id:
                target_parcel = p
                target_corridor = corridor
                break
        if target_parcel:
            break
            
    if not target_parcel:
        raise HTTPException(status_code=404, detail=f"Parcel ID '{parcel_id}' not found.")
        
    # Evaluate spacing and vision
    eval_res = spatial_engine.evaluate_parcel(target_parcel, target_corridor["existing_billboards"])
    vision_res = vision_agent.analyze_aerial_imagery(eval_res)
    
    pdf_path = pdf_generator.generate_pdf(eval_res, vision_res)
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"Feasibility_Report_{parcel_id}.pdf"
    )

# HTTP 206 Byte-Range Video Streaming for Canvas Scroll Scrubbing
@app.get("/hero.mp4")
async def stream_hero_video(request: Request):
    video_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "hero.mp4")
    if not os.path.exists(video_path):
        video_path = os.path.join(os.path.dirname(__file__), "hero.mp4")
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video asset not found.")
        
    file_size = os.path.getsize(video_path)
    range_header = request.headers.get("range")
    
    if range_header:
        parts = range_header.replace("bytes=", "").split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
        length = end - start + 1
        
        def iterfile():
            with open(video_path, "rb") as f:
                f.seek(start)
                bytes_left = length
                while bytes_left > 0:
                    chunk = f.read(min(bytes_left, 1024 * 64))
                    if not chunk:
                        break
                    bytes_left -= len(chunk)
                    yield chunk
                    
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
            "Content-Type": "video/mp4",
        }
        return StreamingResponse(iterfile(), status_code=status.HTTP_206_PARTIAL_CONTENT, headers=headers)
    else:
        return FileResponse(video_path, media_type="video/mp4")

# Serve production frontend if built
dist_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(dist_dir):
    from fastapi.staticfiles import StaticFiles
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(dist_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))
