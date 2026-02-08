"""
Download rendered floor plan images for ALL building floors
from NYCU Yangming campus GIS server via WMS GetMap requests.
"""

import json
import os
import re
import time
import warnings

import requests

warnings.filterwarnings("ignore")
requests.packages.urllib3.disable_warnings()

# Output directory
OUTPUT_DIR = r"C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive\wms_floor_plans"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# All buildings and their floors
BUILDINGS = {
    "Y001": ["R2", "R1", "6F", "5F", "4F", "3F", "2F", "1F", "B1"],
    "B013": ["RF", "6F", "5F", "4F", "3F", "2F", "1F", "B1"],
    "B020": ["R2", "R1", "7F", "6F", "5F", "4F", "3F", "2F", "1F", "B1"],
    "P004": ["RF", "7F", "6F", "5F", "4F", "3F", "2F", "1F", "B1"],
    "B019": ["R2", "R1", "7F", "6F", "5F", "4F", "3F", "2F", "1F", "B1"],
    "B003": ["4F", "3F", "2F", "1F", "B1"],
    "B005": ["RF", "6F", "5F", "4F", "3F", "2F", "1F", "B1", "4M"],
    "B029": ["5F", "4F", "3F", "2F", "1F"],
    "P006": ["RF", "7F", "6F", "5F", "4F", "3F", "2F", "1F", "B1", "B2"],
    "P003": ["RF", "9F", "8F", "7F", "6F", "5F", "4F", "3F", "2F", "1F", "B1", "B2"],
    "Y012": ["3F", "2F", "1F"],
    "B010": ["2F", "1F", "B1"],
    "B009": ["RF", "3F", "2F", "1F"],
    "B004": ["2F", "1F", "B1"],
    "P005": ["RF", "9F", "8F", "7F", "6F", "5F", "4F", "3F", "2F", "1F", "B1", "B2"],
    "B017": ["RF", "4F", "3F", "2F", "1F", "B1"],
    "B016": ["RF", "4F", "3F", "2F", "1F", "B1"],
    "B012": ["RF", "4F", "3F", "2F", "1F", "B1"],
    "B011": ["RF", "5F", "4F", "3F", "2F", "1F", "B1"],
    "B015": ["2F", "1F"],
    "B021": ["RF", "5F", "4F", "3F", "2F", "1F"],
    "B022": ["RF", "5F", "4F", "3F", "2F", "1F"],
    "B014": ["RF", "7F", "6F", "5F", "4F", "3F", "2F", "1F"],
    "B018": ["R3", "R2", "R1", "7F", "6F", "5F", "4F", "3F", "2F", "1F", "B1"],
    "B023": ["2F", "1F"],
    "G005": ["RF", "7F", "6F", "5F", "4F", "3F", "2F", "1F", "B1", "B2"],
    "Y002": ["3F", "2F", "1F", "B1"],
    "B033": ["R3", "R2", "R1", "7F", "6F", "5F", "4F", "3F", "2F", "1F", "B1"],
    "B028": ["3F", "2F", "1F"],
    "Y004": ["RF", "4F", "3F", "2F", "1F"],
    "Y005": ["RF", "3F", "2F", "1F", "B1", "1M"],
    "B032": ["R3", "R2", "R1", "7F", "6F", "5F", "4F", "3F", "2F", "1F"],
    "B034": ["RF", "4F", "3F", "2F", "1F", "B1"],
    "B030": ["R3", "R2", "R1", "7F", "6F", "5F", "4F", "3F", "2F", "1F"],
    "B025": ["2F", "1F"],
    "B026": ["1F", "B1"],
    "G002": ["RF", "4F", "3F", "2F", "1F", "B1"],
    "B027": ["2F", "1F"],
    "B031": ["R3", "R2", "R1", "7F", "6F", "5F", "4F", "3F", "2F", "1F"],
    "B024": ["2F", "1F"],
    "Y003": ["RF", "4F", "3F", "2F", "1F", "2M"],
    "G022": ["1F"],
    "Y011": ["RF", "2F", "1F"],
    "Y007": ["RF", "3F", "2F", "1F", "B1"],
    "Y006": ["RF", "5F", "4F", "3F", "2F"],
    "Y008": ["3F", "2F", "1F", "B1", "2M"],
    "Y010": ["R2", "R1", "6F", "5F", "4F", "3F", "2F", "1F"],
    "Y009": ["RF", "4F", "3F", "2F", "1F", "B1"],
}

# GeoServer endpoints
BBOX_URL = "https://ymspace.ga.nycu.edu.tw/gisweb/public/buildinfo.htm"
WMS_URL = "https://ymspace.ga.nycu.edu.tw:8080/geoserver/wms"

# Buffer in meters (TWD97) to add around bounding box
BUFFER_M = 10


def parse_polygon_bbox(polygon_wkt):
    """Parse POLYGON WKT and extract min/max x/y as bbox."""
    # Extract coordinate pairs from POLYGON((x1 y1, x2 y2, ...))
    coords_str = re.search(r"POLYGON\(\((.*?)\)\)", polygon_wkt)
    if not coords_str:
        return None
    pairs = coords_str.group(1).split(",")
    xs = []
    ys = []
    for pair in pairs:
        parts = pair.strip().split()
        xs.append(float(parts[0]))
        ys.append(float(parts[1]))
    return min(xs), min(ys), max(xs), max(ys)


def get_building_bbox(session, build_id):
    """Get bounding box for a building in EPSG:3826."""
    params = {
        "action": "getBoundingBoxByBuildId",
        "buildId": build_id,
        "proj": "EPSG:3826",
    }
    try:
        resp = session.get(BBOX_URL, params=params, verify=False, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("data") and len(data["data"]) > 0:
            bound = data["data"][0].get("bound", "")
            bbox = parse_polygon_bbox(bound)
            if bbox:
                # Add buffer
                return (
                    bbox[0] - BUFFER_M,
                    bbox[1] - BUFFER_M,
                    bbox[2] + BUFFER_M,
                    bbox[3] + BUFFER_M,
                )
    except Exception as e:
        print(f"  [ERROR] Failed to get bbox for {build_id}: {e}")
    return None


def download_floor_plan(session, build_id, floor, bbox):
    """Download a single floor plan image via WMS GetMap."""
    layer_name = f"gis_room:{build_id}_{floor}"

    # Calculate proportional width/height based on bbox aspect ratio
    dx = bbox[2] - bbox[0]
    dy = bbox[3] - bbox[1]
    if dx <= 0 or dy <= 0:
        return False, "Invalid bbox dimensions"

    max_dim = 1024
    if dx >= dy:
        width = max_dim
        height = max(1, int(max_dim * dy / dx))
    else:
        height = max_dim
        width = max(1, int(max_dim * dx / dy))

    bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"

    params = {
        "service": "WMS",
        "version": "1.1.0",
        "request": "GetMap",
        "layers": layer_name,
        "styles": "",
        "bbox": bbox_str,
        "width": width,
        "height": height,
        "srs": "EPSG:3826",
        "format": "image/png",
        "transparent": "true",
    }

    try:
        resp = session.get(WMS_URL, params=params, verify=False, timeout=60)

        # Check if we got an error XML response instead of an image
        content_type = resp.headers.get("Content-Type", "")
        if "xml" in content_type or "text" in content_type:
            # GeoServer returned an error
            error_text = resp.text[:200]
            return False, f"WMS error: {error_text}"

        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}"

        # Check if the image has meaningful content (not just transparent)
        # A fully transparent 1024x1024 PNG is typically very small (~1-5 KB)
        content_length = len(resp.content)
        if content_length < 500:
            return False, f"Image too small ({content_length} bytes), likely empty"

        # Save the image
        output_path = os.path.join(OUTPUT_DIR, f"{build_id}_{floor}.png")
        with open(output_path, "wb") as f:
            f.write(resp.content)

        return True, f"OK ({content_length:,} bytes, {width}x{height})"

    except requests.exceptions.Timeout:
        return False, "Request timed out"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    # Count total floors
    total_floors = sum(len(floors) for floors in BUILDINGS.values())
    print(f"Total buildings: {len(BUILDINGS)}")
    print(f"Total floor plans to download: {total_floors}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 70)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (NYCU GIS Floor Plan Downloader)",
        }
    )

    success_count = 0
    fail_count = 0
    skip_count = 0
    failed_items = []
    current = 0

    for build_id, floors in BUILDINGS.items():
        print(f"\n--- Building {build_id} ({len(floors)} floors) ---")

        # Get bounding box for the building
        bbox = get_building_bbox(session, build_id)
        if bbox is None:
            print(f"  [SKIP] Could not get bounding box for {build_id}")
            skip_count += len(floors)
            current += len(floors)
            for floor in floors:
                failed_items.append((build_id, floor, "No bbox"))
            continue

        print(f"  BBOX: {bbox[0]:.2f}, {bbox[1]:.2f}, {bbox[2]:.2f}, {bbox[3]:.2f}")

        for floor in floors:
            current += 1
            layer_label = f"{build_id}_{floor}"

            # Check if already downloaded
            output_path = os.path.join(OUTPUT_DIR, f"{layer_label}.png")
            if os.path.exists(output_path) and os.path.getsize(output_path) > 500:
                print(
                    f"  [{current}/{total_floors}] {layer_label} - ALREADY EXISTS, skipping"
                )
                success_count += 1
                continue

            ok, msg = download_floor_plan(session, build_id, floor, bbox)
            if ok:
                print(f"  [{current}/{total_floors}] {layer_label} - {msg}")
                success_count += 1
            else:
                print(f"  [{current}/{total_floors}] {layer_label} - FAILED: {msg}")
                fail_count += 1
                failed_items.append((build_id, floor, msg))

            # Small delay to be polite to the server
            time.sleep(0.3)

    print("\n" + "=" * 70)
    print(f"DONE!")
    print(f"  Success: {success_count}")
    print(f"  Failed:  {fail_count}")
    print(f"  Skipped: {skip_count}")
    print(f"  Total:   {current}")

    if failed_items:
        print(f"\nFailed items ({len(failed_items)}):")
        for build_id, floor, reason in failed_items:
            print(f"  {build_id}_{floor}: {reason}")


if __name__ == "__main__":
    main()
