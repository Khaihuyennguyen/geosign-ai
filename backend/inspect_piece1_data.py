import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.corridor_data import CORRIDORS_REGISTRY

def inspect_dataset():
    corridor = CORRIDORS_REGISTRY["I35-50Mile-Regional"]
    
    print("=" * 85)
    print(f"🛣️  PIECE 1 AUDIT: {corridor['name']}")
    print(f"📍 Jurisdiction: {corridor['county']}, {corridor['state']}")
    print("=" * 85)
    
    centerline = corridor["highway_centerline"]
    print(f"\n[1] HIGHWAY CENTERLINE SPAN (50 MILES / 13 WAYPOINTS):")
    print(f"   * North Starting Point: Mile 260 (Georgetown/Round Rock) -> {centerline[0]}")
    print(f"   * Midpoint: Mile 230 (Central Austin / Downtown) -> {centerline[6]}")
    print(f"   * South Ending Point: Mile 200 (San Marcos / Outlets) -> {centerline[-1]}")
    
    billboards = corridor["existing_billboards"]
    print(f"\n[2] LICENSED BILLBOARD CLUSTERS ({len(billboards)} REAL PERMITS):")
    for i, bb in enumerate(billboards, 1):
        print(f"   {i:2d}. {bb['operator']:<26} | Permit: {bb['permit_id']:<24} | Height: {bb['height_ft']} ft | GPS: {bb['coordinates']}")
        
    parcels = corridor["parcels"]
    print(f"\n[3] COMMERCIAL PARCELS ALONG CORRIDOR ({len(parcels)} PROPERTIES):")
    for i, p in enumerate(parcels, 1):
        trees_flag = "[DENSE TREES]" if p["has_dense_trees"] else "[CLEAR]"
        print(f"   {i:2d}. {p['parcel_id']:<15} | {p['address']:<48} | Traffic: {p['aadt_traffic']:,} AADT | Zoning: {p['zoning']:<22} | {trees_flag}")
        
    print("\n" + "=" * 85)
    print(f"✅ PIECE 1 DATASET AUDIT COMPLETE: 50 Miles, {len(billboards)} Billboard Permits, {len(parcels)} Parcels Loaded!")
    print("=" * 85)

if __name__ == "__main__":
    inspect_dataset()
