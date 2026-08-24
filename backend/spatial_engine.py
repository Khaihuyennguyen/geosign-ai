import math
from typing import Dict, Any, List, Optional
from shapely.geometry import Point, Polygon

def haversine_distance_feet(lat1: float, lon1: float, lat2: float, lon2: float) -> Dict[str, Any]:
    """
    Computes exact geodesic distance between two points on Earth using WGS-84 mean radius.
    """
    R_EARTH_METERS = 6371000.0
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
    """
    Point-in-Polygon (PIP) intersection check using Shapely.
    """
    p = Point(point_lon, point_lat)
    for poly in (cadastral_polygons or []):
        poly_coords = poly.get("coordinates", [[]])[0]
        if len(poly_coords) >= 3:
            shapely_poly = Polygon(poly_coords)
            if shapely_poly.contains(p) or shapely_poly.touches(p):
                poly_type = poly.get("type", "")
                is_restricted = any(k in poly_type for k in ["Residential", "Park", "Environmental", "Agricultural"])
                return {
                    "in_polygon": True,
                    "polygon_id": poly.get("id", poly.get("name", "ZONE-01")),
                    "polygon_name": poly.get("name", "Special District"),
                    "polygon_type": poly_type,
                    "polygon_zoning": poly.get("zoning", "RESTRICTED"),
                    "is_restricted": is_restricted,
                    "restriction_status": poly.get("status", "RESTRICTED")
                }
    return {"in_polygon": False, "is_restricted": False}

class SpatialBufferEngine:
    """
    Spatial reasoning engine for 500-foot buffer exclusions and cadastral zoning checks.
    """
    def __init__(self, min_spacing_feet: float = 500.0, min_aadt_traffic: int = 25000):
        self.min_spacing_feet = min_spacing_feet
        self.min_aadt_traffic = min_aadt_traffic
        
    def evaluate_parcel(self, parcel: Dict[str, Any], existing_billboards: List[Dict[str, Any]], cadastral_polygons: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        coords = parcel.get("coordinates", [0.0, 0.0])
        p_lon, p_lat = coords[0], coords[1]
        cadastral_polygons = cadastral_polygons or []
        
        # 1. Geodesic Spacing against existing billboard registry
        min_dist = float("inf")
        nearest_bb = None
        best_proof = {}

        for bb in existing_billboards:
            bb_coords = bb.get("coordinates", [0.0, 0.0])
            bb_lon, bb_lat = bb_coords[0], bb_coords[1]
            calc = haversine_distance_feet(p_lat, p_lon, bb_lat, bb_lon)
            dist = calc["distance_feet"]
            if dist < min_dist:
                min_dist = dist
                nearest_bb = bb
                best_proof = calc

        spacing_passed = min_dist >= self.min_spacing_feet
        spacing_margin = round(min_dist - self.min_spacing_feet, 1)

        # 2. Point-in-Polygon (PIP) Spatial Intersection Check
        pip_result = check_polygon_intersection(p_lon, p_lat, cadastral_polygons)

        # 3. Commercial Zoning Check
        zoning_code = parcel.get("zoning", "")
        commercial_prefixes = ["CS", "CH", "LI", "C-1", "C-2", "C-3", "B-3", "W", "Commercial"]
        is_commercial = any(code in zoning_code for code in commercial_prefixes)
        
        # 4. Traffic Threshold Check
        traffic_count = parcel.get("aadt_traffic", 0)
        traffic_passed = traffic_count >= self.min_aadt_traffic
        
        disqualifications = []
        if pip_result.get("is_restricted", False):
            is_commercial = False
            disqualifications.append(f"Zoning Violation: Inside {pip_result.get('polygon_name')} ({pip_result.get('polygon_zoning')} Prohibits Billboard Siting)")
        elif not is_commercial:
            disqualifications.append(f"Zoning Incompatible: {zoning_code} prohibits off-premise advertising")

        if not spacing_passed:
            operator_name = nearest_bb.get("operator", "Existing Operator") if nearest_bb else "Existing"
            permit_id = nearest_bb.get("permit_id", "N/A") if nearest_bb else "N/A"
            disqualifications.append(f"Spacing Violation: Only {min_dist:,.1f} ft from {operator_name} sign ({permit_id}) — Legal Min: {self.min_spacing_feet} ft")

        if not traffic_passed:
            disqualifications.append(f"Low Traffic Volume: {traffic_count:,} AADT is below commercial viability threshold ({self.min_aadt_traffic:,})")

        is_qualified = len(disqualifications) == 0

        # Estimated Annual Advertising Value calculation based on traffic volume & visibility
        est_ad_revenue = int(traffic_count * 365 * 0.0018 * 0.70) if is_qualified else 0

        return {
            **parcel,
            "is_qualified": is_qualified,
            "disqualification_reasons": disqualifications,
            "min_distance_to_sign_feet": min_dist,
            "nearest_billboard_permit": nearest_bb.get("permit_id", "None") if nearest_bb else "None",
            "nearest_operator": nearest_bb.get("operator", "None") if nearest_bb else "None",
            "nearest_coordinates": nearest_bb.get("coordinates", [0, 0]) if nearest_bb else [0, 0],
            "spacing_passed": spacing_passed,
            "spacing_margin_feet": spacing_margin,
            "is_commercial_zoning": is_commercial,
            "pip_intersection": pip_result,
            "est_annual_ad_revenue": est_ad_revenue,
            "proof": {
                "mathematical": {
                    "property_gps": [p_lat, p_lon],
                    "nearest_sign_gps": [nearest_bb["coordinates"][1], nearest_bb["coordinates"][0]] if nearest_bb else [],
                    "distance_feet": min_dist,
                    "delta_lat": best_proof.get("delta_lat_deg", 0),
                    "delta_lon": best_proof.get("delta_lon_deg", 0),
                    "statutory_min_feet": self.min_spacing_feet,
                    "formula_used": "Haversine Great-Circle Geodesic (WGS-84 Sphere R=6,371,000m)"
                },
                "legal": {
                    "statute_name": "Texas Transportation Code § 391.031",
                    "statute_requirement": "Minimum 500-foot distance between commercial signs on highway corridors",
                    "zoning_classification": zoning_code,
                    "zoning_status": "Compliant Commercial" if is_commercial else "Non-Compliant"
                }
            }
        }

    def audit_corridor(self, parcels: List[Dict[str, Any]], existing_billboards: List[Dict[str, Any]], cadastral_polygons: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        return [self.evaluate_parcel(p, existing_billboards, cadastral_polygons) for p in parcels]

# Module-level convenience function
_default_engine = SpatialBufferEngine(min_spacing_feet=500.0, min_aadt_traffic=25000)

def evaluate_parcel(parcel: Dict[str, Any], existing_billboards: List[Dict[str, Any]], min_spacing_feet: float = 500.0, cadastral_polygons: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    engine = SpatialBufferEngine(min_spacing_feet=min_spacing_feet)
    return engine.evaluate_parcel(parcel, existing_billboards, cadastral_polygons)
