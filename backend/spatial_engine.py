import math
from typing import Dict, Any, List
from shapely.geometry import Point, Polygon
from vision_agent import GeminiVisionInspector

vision_inspector = GeminiVisionInspector()

def haversine_distance_feet(lat1: float, lon1: float, lat2: float, lon2: float) -> Dict[str, Any]:
    R_EARTH_METERS = 6371000.0  # WGS-84 mean Earth radius in meters
    METERS_TO_FEET = 3.28084

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    distance_meters = R_EARTH_METERS * c
    distance_feet = distance_meters * METERS_TO_FEET

    return {
        "distance_feet": round(distance_feet, 1),
        "distance_meters": round(distance_meters, 2),
        "lat1": lat1,
        "lon1": lon1,
        "lat2": lat2,
        "lon2": lon2,
        "delta_lat_deg": round(lat2 - lat1, 6),
        "delta_lon_deg": round(lon2 - lon1, 6),
        "formula": "d = 2 * R * atan2(sqrt(a), sqrt(1-a)) [WGS-84 Geodesic]",
        "earth_radius_m": R_EARTH_METERS
    }

def check_polygon_intersection(point_lon: float, point_lat: float, cadastral_polygons: List[Dict[str, Any]]) -> Dict[str, Any]:
    p = Point(point_lon, point_lat)
    for poly in cadastral_polygons:
        poly_coords = poly["coordinates"][0]
        shapely_poly = Polygon(poly_coords)
        if shapely_poly.contains(p) or shapely_poly.touches(p):
            is_restricted = ("Residential" in poly.get("type", "") or "Park" in poly.get("type", "") or "Environmental" in poly.get("type", ""))
            return {
                "in_polygon": True,
                "polygon_id": poly.get("id", poly.get("name", "ZONE-01")),
                "polygon_name": poly["name"],
                "polygon_type": poly["type"],
                "polygon_zoning": poly["zoning"],
                "is_restricted": is_restricted,
                "restriction_status": poly.get("status", "RESTRICTED")
            }
    return {"in_polygon": False, "is_restricted": False}

def evaluate_parcel(parcel: Dict[str, Any], existing_billboards: List[Dict[str, Any]], min_spacing_feet: float = 500.0, cadastral_polygons: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    p_lon, p_lat = parcel["coordinates"]
    cadastral_polygons = cadastral_polygons or []
    
    # 1. Geodesic Spacing calculation against all existing billboards
    min_dist = float("inf")
    nearest_bb = None
    best_proof = {}

    for bb in existing_billboards:
        bb_lon, bb_lat = bb["coordinates"]
        calc = haversine_distance_feet(p_lat, p_lon, bb_lat, bb_lon)
        dist = calc["distance_feet"]
        if dist < min_dist:
            min_dist = dist
            nearest_bb = bb
            best_proof = calc

    spacing_passed = min_dist >= min_spacing_feet
    spacing_margin = round(min_dist - min_spacing_feet, 1)

    # 2. Point-in-Polygon (PIP) Spatial Intersection Check
    pip_result = check_polygon_intersection(p_lon, p_lat, cadastral_polygons)

    # 3. Commercial Zoning Check
    zoning_code = parcel.get("zoning", "")
    is_commercial = any(code in zoning_code for code in ["CS", "CH", "LI", "C-1", "C-2", "C-3", "B-3", "W", "Commercial"])
    
    disqualifications = []
    
    # Strict Polygon Enforcement
    if pip_result.get("is_restricted", False):
        is_commercial = False
        disqualifications.append(f"Zoning Violation: Inside {pip_result['polygon_name']} ({pip_result['polygon_zoning']} Prohibits Off-Premise Advertising)")
    elif not is_commercial:
        disqualifications.append(f"Zoning Incompatible: {zoning_code} prohibits off-premise advertising")

    if not spacing_passed:
        operator_name = nearest_bb['operator'] if nearest_bb else 'Existing'
        disqualifications.append(f"Spacing Violation: Only {min_dist:,.1f} ft from {operator_name} sign (Min: {min_spacing_feet} ft)")

    is_qualified = len(disqualifications) == 0

    # 4. Multimodal Vision Sightline Ray-Casting & Physics Inspection
    vision_res = vision_inspector.analyze_aerial_imagery(parcel)

    aadt = vision_res["mainlane_traffic"]
    est_ad_revenue = int(aadt * 365 * 0.0018 * 0.70) if is_qualified else 0

    county = "Travis" if "TCAD" in parcel.get("parcel_id", "") else ("Williamson" if "WCAD" in parcel.get("parcel_id", "") else "Hays")
    county_cad_link = "https://propaccess.traviscad.org/clientdb/?cid=1" if county == "Travis" else ("https://www.wcad.org/" if county == "Williamson" else "https://hayscad.com/")
    statute_link = "https://statutes.capitol.texas.gov/Docs/TN/htm/TN.391.htm#391.031"
    station_id = parcel.get("station_id", "")
    txdot_traffic_link = f"https://services.arcgis.com/KTcxiTD9dsQw4r7Z/arcgis/rest/services/TxDOT_AADT_Annuals_(Public_View)/FeatureServer/0/query?where=ON_ROAD%3D%27IH0035%27+AND+TRFC_STATN_ID%3D%27{station_id}%27&outFields=*&f=html"

    return {
        **parcel,
        "is_qualified": is_qualified,
        "disqualification_reasons": disqualifications,
        "min_distance_to_sign_feet": min_dist,
        "nearest_billboard_permit": nearest_bb["permit_id"] if nearest_bb else "None",
        "nearest_operator": nearest_bb["operator"] if nearest_bb else "None",
        "nearest_coordinates": nearest_bb["coordinates"] if nearest_bb else [0, 0],
        "spacing_passed": spacing_passed,
        "spacing_margin_feet": spacing_margin,
        "is_commercial_zoning": is_commercial,
        "pip_intersection": pip_result,
        "tree_canopy_present": vision_res["tree_canopy_present"],
        "visibility_score": vision_res["visibility_score"],
        "obstruction_level": vision_res["obstruction_level"],
        "ai_visual_justification": vision_res["ai_visual_justification"],
        "unobstructed_sightline_ft": vision_res["unobstructed_sightline_ft"],
        "driver_dwell_time_sec": vision_res["driver_dwell_time_sec"],
        "est_annual_ad_revenue": est_ad_revenue,
        "pdf_available": is_qualified and not vision_res["tree_canopy_present"],
        "proof": {
            "mathematical": {
                "property_gps": [p_lat, p_lon],
                "nearest_sign_gps": [nearest_bb["coordinates"][1], nearest_bb["coordinates"][0]] if nearest_bb else [],
                "distance_feet": min_dist,
                "delta_lat": best_proof.get("delta_lat_deg", 0),
                "delta_lon": best_proof.get("delta_lon_deg", 0),
                "statutory_min_feet": min_spacing_feet,
                "formula_used": "Haversine Great-Circle Geodesic (WGS-84 Sphere R=6,371,000m)"
            },
            "sightline_physics": {
                "driver_speed_mph": vision_res["highway_speed_mph"],
                "unobstructed_distance_ft": vision_res["unobstructed_sightline_ft"],
                "driver_viewing_dwell_seconds": vision_res["driver_dwell_time_sec"],
                "canopy_density_pct": vision_res["canopy_density_pct"],
                "tree_height_ft": vision_res["canopy_height_est_ft"]
            },
            "legal": {
                "statute_name": "Texas Transportation Code § 391.031",
                "statute_requirement": "Minimum 500-foot distance between commercial signs on Interstate Highway corridors",
                "statute_link": statute_link,
                "zoning_classification": pip_result.get("polygon_zoning", zoning_code) if pip_result.get("in_polygon") else zoning_code,
                "zoning_status": "Non-Compliant (Inside Residential/Parkland Polygon)" if pip_result.get("is_restricted") else ("Compliant Commercial" if is_commercial else "Non-Compliant (Residential)")
            },
            "cadastral": {
                "county": county,
                "parcel_id": parcel.get("parcel_id"),
                "owner_name": parcel.get("owner_name"),
                "verification_portal": county_cad_link,
                "txdot_traffic_station": station_id,
                "txdot_live_verification": txdot_traffic_link,
                "polygon_enclosure": pip_result.get("polygon_name", "Standard Highway Frontage")
            }
        }
    }
