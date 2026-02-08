#!/usr/bin/env python3
"""
Extract room boundaries from NYCU Yangming Campus GIS data.

This script:
1. Reads existing WFS GeoJSON room layers (already downloaded from GeoServer)
2. Converts EPSG:3826 (TWD97/TM2) coordinates to EPSG:4326 (WGS84)
3. Cross-references with room data for proper Chinese/English names
4. Also queries the public API getBound endpoint for additional boundary data
5. Organizes results by building/floor
6. Creates a comprehensive summary

Data sources:
- WFS GeoJSON: data/ymmap_archive/wfs_geojson/gis_room/{BuildID}_{Floor}.json
- Room list: data/ymmap_archive/api_data/public_bypass/all_rooms_by_building.json
- Public API: roominfo.htm?action=getBound (for comparison)
"""

import json
import math
import os
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Configuration ──────────────────────────────────────────────────────────
BASE_DIR = Path(r"C:\Users\thc1006\Desktop\NQSD\新增資料夾")
WFS_GEOJSON_DIR = BASE_DIR / "data" / "ymmap_archive" / "wfs_geojson" / "gis_room"
ROOMS_DATA_PATH = (
    BASE_DIR
    / "data"
    / "ymmap_archive"
    / "api_data"
    / "public_bypass"
    / "all_rooms_by_building.json"
)
OUTPUT_DIR = BASE_DIR / "data" / "ymmap_archive" / "room_boundaries"
PUBLIC_API_URL = "https://ymspace.ga.nycu.edu.tw/gisweb/public/roominfo.htm"

# Priority buildings to process first
PRIORITY_BUILDINGS = ["Y001", "P003", "P004", "P005", "P006", "G005", "Y009", "Y010"]

SESSION = requests.Session()
SESSION.verify = False
SESSION.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    }
)


# ── Coordinate Transformation: EPSG:3826 (TWD97/TM2) -> EPSG:4326 (WGS84) ──
# TWD97 uses GRS80 ellipsoid, same as WGS84 for practical purposes
# EPSG:3826 is Transverse Mercator with:
#   Central Meridian: 121 degrees East
#   Scale Factor: 0.9999
#   False Easting: 250000
#   False Northing: 0
#   Ellipsoid: GRS80 (a=6378137, f=1/298.257222101)

GRS80_A = 6378137.0  # semi-major axis
GRS80_F = 1.0 / 298.257222101  # flattening
GRS80_B = GRS80_A * (1 - GRS80_F)  # semi-minor axis
GRS80_E2 = 2 * GRS80_F - GRS80_F ** 2  # eccentricity squared
GRS80_E_PRIME2 = GRS80_E2 / (1 - GRS80_E2)  # second eccentricity squared

TM2_CENTRAL_MERIDIAN = 121.0  # degrees
TM2_SCALE_FACTOR = 0.9999
TM2_FALSE_EASTING = 250000.0
TM2_FALSE_NORTHING = 0.0


def tm2_to_wgs84(easting, northing):
    """
    Convert TWD97/TM2 (EPSG:3826) coordinates to WGS84 (EPSG:4326).

    Args:
        easting: X coordinate in meters (TWD97/TM2)
        northing: Y coordinate in meters (TWD97/TM2)

    Returns:
        (longitude, latitude) in decimal degrees (WGS84)
    """
    # Remove false easting/northing
    x = (easting - TM2_FALSE_EASTING) / TM2_SCALE_FACTOR
    y = (northing - TM2_FALSE_NORTHING) / TM2_SCALE_FACTOR

    # Footpoint latitude
    a = GRS80_A
    e2 = GRS80_E2
    e_prime2 = GRS80_E_PRIME2

    # Meridional arc distance -> footpoint latitude (iterative)
    M = y
    mu = M / (a * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))

    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))

    phi1 = (
        mu
        + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
        + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
        + (151 * e1**3 / 96) * math.sin(6 * mu)
        + (1097 * e1**4 / 512) * math.sin(8 * mu)
    )

    # Compute latitude and longitude
    sin_phi1 = math.sin(phi1)
    cos_phi1 = math.cos(phi1)
    tan_phi1 = math.tan(phi1)

    N1 = a / math.sqrt(1 - e2 * sin_phi1**2)
    T1 = tan_phi1**2
    C1 = e_prime2 * cos_phi1**2
    R1 = a * (1 - e2) / (1 - e2 * sin_phi1**2) ** 1.5
    D = x / N1

    # Latitude
    lat = phi1 - (N1 * tan_phi1 / R1) * (
        D**2 / 2
        - (5 + 3 * T1 + 10 * C1 - 4 * C1**2 - 9 * e_prime2) * D**4 / 24
        + (61 + 90 * T1 + 298 * C1 + 45 * T1**2 - 252 * e_prime2 - 3 * C1**2)
        * D**6
        / 720
    )

    # Longitude
    lon = (
        D
        - (1 + 2 * T1 + C1) * D**3 / 6
        + (5 - 2 * C1 + 28 * T1 - 3 * C1**2 + 8 * e_prime2 + 24 * T1**2)
        * D**5
        / 120
    ) / cos_phi1

    lat_deg = math.degrees(lat)
    lon_deg = TM2_CENTRAL_MERIDIAN + math.degrees(lon)

    return (round(lon_deg, 10), round(lat_deg, 10))


def convert_coordinates(geometry):
    """
    Convert a GeoJSON geometry from EPSG:3826 to EPSG:4326.

    Args:
        geometry: GeoJSON geometry dict with coordinates in EPSG:3826

    Returns:
        New geometry dict with coordinates in EPSG:4326
    """
    geom_type = geometry.get("type", "")

    if geom_type == "Point":
        coords = geometry["coordinates"]
        lon, lat = tm2_to_wgs84(coords[0], coords[1])
        return {"type": "Point", "coordinates": [lon, lat]}

    elif geom_type == "MultiPolygon":
        new_coords = []
        for polygon in geometry["coordinates"]:
            new_polygon = []
            for ring in polygon:
                new_ring = []
                for point in ring:
                    lon, lat = tm2_to_wgs84(point[0], point[1])
                    new_ring.append([lon, lat])
                new_polygon.append(new_ring)
            new_coords.append(new_polygon)
        return {"type": "MultiPolygon", "coordinates": new_coords}

    elif geom_type == "Polygon":
        new_coords = []
        for ring in geometry["coordinates"]:
            new_ring = []
            for point in ring:
                lon, lat = tm2_to_wgs84(point[0], point[1])
                new_ring.append([lon, lat])
            new_coords.append(new_ring)
        return {"type": "Polygon", "coordinates": new_coords}

    else:
        # Return as-is for unknown types
        return geometry


def geometry_to_wkt(geometry):
    """Convert a GeoJSON geometry to WKT format."""
    geom_type = geometry.get("type", "")

    if geom_type == "Point":
        c = geometry["coordinates"]
        return f"POINT({c[0]} {c[1]})"

    elif geom_type == "Polygon":
        rings = []
        for ring in geometry["coordinates"]:
            pts = ", ".join(f"{p[0]} {p[1]}" for p in ring)
            rings.append(f"({pts})")
        return f"POLYGON({', '.join(rings)})"

    elif geom_type == "MultiPolygon":
        polygons = []
        for polygon in geometry["coordinates"]:
            rings = []
            for ring in polygon:
                pts = ", ".join(f"{p[0]} {p[1]}" for p in ring)
                rings.append(f"({pts})")
            polygons.append(f"({', '.join(rings)})")
        return f"MULTIPOLYGON({', '.join(polygons)})"

    return ""


def compute_centroid(geometry):
    """Compute approximate centroid of a geometry."""
    coords = []

    geom_type = geometry.get("type", "")
    if geom_type == "MultiPolygon":
        for polygon in geometry["coordinates"]:
            for ring in polygon:
                coords.extend(ring)
    elif geom_type == "Polygon":
        for ring in geometry["coordinates"]:
            coords.extend(ring)
    elif geom_type == "Point":
        return geometry["coordinates"]

    if not coords:
        return None

    avg_lon = sum(c[0] for c in coords) / len(coords)
    avg_lat = sum(c[1] for c in coords) / len(coords)
    return [round(avg_lon, 8), round(avg_lat, 8)]


# ── Main Processing ──────────────────────────────────────────────────────────


def load_rooms_data():
    """Load room names/IDs from the all_rooms_by_building.json file."""
    with open(ROOMS_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def process_wfs_geojson(filepath, building_id, floor, rooms_lookup):
    """
    Process a single WFS GeoJSON file and extract room boundaries.

    Args:
        filepath: Path to the GeoJSON file
        building_id: Building ID (e.g., 'Y001')
        floor: Floor code (e.g., '1F')
        rooms_lookup: Dict of room data from all_rooms_by_building.json

    Returns:
        List of room dicts with boundaries
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    rooms = []

    for feature in features:
        props = feature.get("properties", {})
        geometry = feature.get("geometry")

        room_id = props.get("ID", props.get("RoomID", ""))
        class_num = props.get("ClassNum", "")
        room_name_raw = props.get("RoomName", "")
        room_name_en = props.get("RoomNameEn", "")
        floor_val = props.get("Floor", floor)
        area = props.get("AREA")
        build_id = props.get("BuildID") or building_id

        # Try to get proper Chinese name from rooms_lookup
        proper_name = room_name_raw
        if rooms_lookup and building_id in rooms_lookup and floor in rooms_lookup[building_id]:
            for r in rooms_lookup[building_id][floor]:
                if r.get("id") == room_id:
                    proper_name = r.get("name", room_name_raw)
                    if not class_num:
                        class_num = r.get("classnum", "")
                    break

        # Convert geometry to WGS84
        boundary_wgs84 = None
        boundary_wkt = ""
        centroid = None
        if geometry:
            boundary_wgs84 = convert_coordinates(geometry)
            boundary_wkt = geometry_to_wkt(boundary_wgs84)
            centroid = compute_centroid(boundary_wgs84)

        room_entry = {
            "classNum": class_num,
            "roomId": room_id,
            "name": proper_name,
            "nameEn": room_name_en,
            "floor": floor_val if floor_val else floor,
            "buildingId": build_id,
            "area_sqm": area,
            "boundary": boundary_wgs84,
            "boundary_wkt": boundary_wkt,
            "centroid": centroid,
            "properties": {
                "type": props.get("Type", ""),
                "purpose": props.get("Purpose", ""),
                "capacity": props.get("Capacity", ""),
                "propertyUnit": props.get("PropertyUnit", ""),
                "usingUnit": props.get("UsingUnit", ""),
                "category1": props.get("Category1", ""),
                "category2": props.get("Category2", ""),
                "keyword": props.get("keyword", ""),
            },
        }
        rooms.append(room_entry)

    return rooms


def query_api_getbound(building_id, floor, class_num):
    """Query the public API getBound endpoint for a room."""
    try:
        params = {
            "action": "getBound",
            "buildId": building_id,
            "floor": floor,
            "classNum": class_num,
            "proj": "EPSG:4326",
        }
        resp = SESSION.get(PUBLIC_API_URL, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("data")
    except Exception:
        pass
    return None


def query_api_room_exists(class_num):
    """Query queryRoomExists for a room."""
    try:
        resp = SESSION.get(
            PUBLIC_API_URL,
            params={"action": "queryRoomExists", "classNum": class_num},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("data")
    except Exception:
        pass
    return None


def main():
    print("=" * 80)
    print("Room Boundary Extraction - NYCU Yangming Campus GIS")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Load room names data
    print("\n[1/5] Loading room data...")
    rooms_data = load_rooms_data()
    total_rooms_expected = sum(
        len(rooms)
        for floors in rooms_data.values()
        for rooms in floors.values()
    )
    print(f"  Buildings: {len(rooms_data)}")
    print(f"  Total rooms in catalog: {total_rooms_expected}")

    # Get list of available WFS GeoJSON files
    print("\n[2/5] Scanning WFS GeoJSON files...")
    wfs_files = {}
    if WFS_GEOJSON_DIR.exists():
        for f in sorted(WFS_GEOJSON_DIR.iterdir()):
            if f.suffix == ".json":
                parts = f.stem.split("_", 1)
                if len(parts) == 2:
                    bid, floor = parts
                    if bid not in wfs_files:
                        wfs_files[bid] = {}
                    wfs_files[bid][floor] = f
    print(f"  WFS GeoJSON files: {sum(len(v) for v in wfs_files.values())}")
    print(f"  Buildings with WFS data: {len(wfs_files)}")

    # Determine processing order: priority buildings first
    all_buildings = list(rooms_data.keys())
    ordered_buildings = []
    for pb in PRIORITY_BUILDINGS:
        if pb in all_buildings:
            ordered_buildings.append(pb)
    for b in sorted(all_buildings):
        if b not in ordered_buildings:
            ordered_buildings.append(b)

    # Process all buildings
    print("\n[3/5] Processing WFS GeoJSON room boundaries...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary_stats = {
        "extraction_timestamp": datetime.now().isoformat(),
        "total_buildings": len(all_buildings),
        "total_rooms_in_catalog": total_rooms_expected,
        "total_rooms_with_boundaries": 0,
        "total_rooms_without_boundaries": 0,
        "total_coordinate_points": 0,
        "crs_source": "EPSG:3826 (TWD97/TM2)",
        "crs_output": "EPSG:4326 (WGS84)",
        "buildings": {},
    }

    total_processed = 0
    total_with_boundary = 0
    total_without_boundary = 0

    for idx, bid in enumerate(ordered_buildings):
        floors_data = rooms_data[bid]
        floor_list = list(floors_data.keys())

        building_dir = OUTPUT_DIR / bid
        building_dir.mkdir(parents=True, exist_ok=True)

        building_rooms_total = 0
        building_rooms_with_boundary = 0
        building_rooms_without_boundary = 0
        building_floors_processed = {}

        for floor in floor_list:
            rooms_on_floor = floors_data[floor]
            floor_rooms = []

            # Check if we have WFS data for this floor
            wfs_file = None
            if bid in wfs_files and floor in wfs_files[bid]:
                wfs_file = wfs_files[bid][floor]

            if wfs_file and wfs_file.exists():
                # Process from WFS GeoJSON
                floor_rooms = process_wfs_geojson(wfs_file, bid, floor, rooms_data)
            else:
                # No WFS data - create entries without boundaries
                for room in rooms_on_floor:
                    floor_rooms.append(
                        {
                            "classNum": room.get("classnum", ""),
                            "roomId": room.get("id", ""),
                            "name": room.get("name", ""),
                            "nameEn": "",
                            "floor": floor,
                            "buildingId": bid,
                            "area_sqm": None,
                            "boundary": None,
                            "boundary_wkt": "",
                            "centroid": None,
                            "properties": {},
                        }
                    )

            # Count stats
            with_boundary = sum(1 for r in floor_rooms if r.get("boundary"))
            without_boundary = len(floor_rooms) - with_boundary
            coord_points = 0
            for r in floor_rooms:
                geom = r.get("boundary")
                if geom:
                    gtype = geom.get("type", "")
                    if gtype == "MultiPolygon":
                        for poly in geom.get("coordinates", []):
                            for ring in poly:
                                coord_points += len(ring)
                    elif gtype == "Polygon":
                        for ring in geom.get("coordinates", []):
                            coord_points += len(ring)

            building_rooms_total += len(floor_rooms)
            building_rooms_with_boundary += with_boundary
            building_rooms_without_boundary += without_boundary
            total_processed += len(floor_rooms)
            total_with_boundary += with_boundary
            total_without_boundary += without_boundary
            summary_stats["total_coordinate_points"] += coord_points

            building_floors_processed[floor] = {
                "rooms_total": len(floor_rooms),
                "rooms_with_boundary": with_boundary,
                "rooms_without_boundary": without_boundary,
                "coordinate_points": coord_points,
                "source": "WFS_GeoJSON" if wfs_file else "catalog_only",
            }

            # Save floor file
            floor_output = building_dir / f"{bid}_{floor}_rooms.json"
            with open(floor_output, "w", encoding="utf-8") as f:
                json.dump(floor_rooms, f, ensure_ascii=False, indent=2)

        # Building stats
        summary_stats["buildings"][bid] = {
            "floors": len(floor_list),
            "rooms_total": building_rooms_total,
            "rooms_with_boundary": building_rooms_with_boundary,
            "rooms_without_boundary": building_rooms_without_boundary,
            "floor_details": building_floors_processed,
        }

        # Progress
        pct = (idx + 1) / len(ordered_buildings) * 100
        marker = " [PRIORITY]" if bid in PRIORITY_BUILDINGS else ""
        print(
            f"  [{idx + 1}/{len(ordered_buildings)}] {bid}{marker}: "
            f"{building_rooms_total} rooms, "
            f"{building_rooms_with_boundary} with boundaries, "
            f"{len(floor_list)} floors "
            f"({pct:.0f}%)"
        )

    summary_stats["total_rooms_with_boundaries"] = total_with_boundary
    summary_stats["total_rooms_without_boundaries"] = total_without_boundary

    # ── Phase 4: Sample API getBound queries for comparison ──
    print("\n[4/5] Sampling API getBound endpoint for comparison...")
    api_bound_results = {"tested": 0, "returned_data": 0, "returned_null": 0}

    sample_rooms = []
    for bid in PRIORITY_BUILDINGS[:3]:
        if bid in rooms_data:
            for floor in list(rooms_data[bid].keys())[:2]:
                for room in rooms_data[bid][floor][:3]:
                    cn = room.get("classnum", "")
                    if cn and cn != "000":
                        sample_rooms.append((bid, floor, cn, room.get("name", "")))

    for bid, floor, cn, name in sample_rooms[:15]:
        result = query_api_getbound(bid, floor, cn)
        api_bound_results["tested"] += 1
        if result is not None:
            api_bound_results["returned_data"] += 1
            print(f"    {bid}/{floor}/{cn} ({name}): GOT DATA -> {str(result)[:100]}")
        else:
            api_bound_results["returned_null"] += 1
        time.sleep(0.1)

    print(
        f"  API getBound results: {api_bound_results['tested']} tested, "
        f"{api_bound_results['returned_data']} with data, "
        f"{api_bound_results['returned_null']} null"
    )
    summary_stats["api_getbound_sample"] = api_bound_results

    # ── Phase 5: Save summary ──
    print("\n[5/5] Saving summary...")
    summary_stats["completion_timestamp"] = datetime.now().isoformat()

    summary_path = OUTPUT_DIR / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_stats, f, ensure_ascii=False, indent=2)

    # Also create a combined GeoJSON for all rooms with boundaries
    print("\n  Creating combined GeoJSON...")
    all_features = []
    for bid in ordered_buildings:
        if bid in rooms_data:
            for floor in rooms_data[bid]:
                floor_file = OUTPUT_DIR / bid / f"{bid}_{floor}_rooms.json"
                if floor_file.exists():
                    with open(floor_file, "r", encoding="utf-8") as f:
                        floor_rooms = json.load(f)
                    for room in floor_rooms:
                        if room.get("boundary"):
                            feature = {
                                "type": "Feature",
                                "geometry": room["boundary"],
                                "properties": {
                                    "classNum": room.get("classNum", ""),
                                    "roomId": room.get("roomId", ""),
                                    "name": room.get("name", ""),
                                    "nameEn": room.get("nameEn", ""),
                                    "floor": room.get("floor", ""),
                                    "buildingId": room.get("buildingId", ""),
                                    "area_sqm": room.get("area_sqm"),
                                },
                            }
                            all_features.append(feature)

    combined_geojson = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:EPSG::4326"},
        },
        "features": all_features,
    }

    combined_path = OUTPUT_DIR / "all_rooms_boundaries.geojson"
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(combined_geojson, f, ensure_ascii=False)

    # ── Final Report ──
    print("\n" + "=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"Total buildings processed:    {len(ordered_buildings)}")
    print(f"Total rooms processed:        {total_processed}")
    print(f"Rooms WITH boundaries:        {total_with_boundary}")
    print(f"Rooms WITHOUT boundaries:     {total_without_boundary}")
    print(f"Coordinate points total:      {summary_stats['total_coordinate_points']:,}")
    print(f"Combined GeoJSON features:    {len(all_features)}")
    print(f"Combined GeoJSON size:        {combined_path.stat().st_size:,} bytes")
    print(f"\nOutput directory:  {OUTPUT_DIR}")
    print(f"Summary file:      {summary_path}")
    print(f"Combined GeoJSON:  {combined_path}")
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
