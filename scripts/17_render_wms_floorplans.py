"""
17_render_wms_floorplans.py
===========================
Download WMS floor plan images for ALL building floors from the NYCU campus
GIS system (ymspace.ga.nycu.edu.tw) via GeoServer WMS GetMap requests.

Room layers are named  gis_room:{BuildID}_{Floor}  (e.g. gis_room:B005_1F).
The bounding box for each request is derived from building polygon WKT stored
in all_building_bounds.json, with 10% padding applied.

Output directory: data/ymmap_archive/wms_floorplans/{BuildID}_{Floor}.png

Usage:
    python scripts/17_render_wms_floorplans.py
    python scripts/17_render_wms_floorplans.py --force   # re-download existing
"""

import json
import os
import re
import sys
import time

import requests
import requests.packages.urllib3

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "ymmap_archive")

FLOORS_JSON = os.path.join(
    DATA_DIR, "api_data", "public_bypass", "all_building_floors.json"
)
BOUNDS_JSON = os.path.join(
    DATA_DIR, "api_data", "public_bypass", "all_building_bounds.json"
)
OUTPUT_DIR = os.path.join(DATA_DIR, "wms_floorplans")

WMS_BASE_URL = (
    "https://ymspace.ga.nycu.edu.tw:8080/geoserver/gis_room/wms"
)

IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024
SRS = "EPSG:4326"
IMAGE_FORMAT = "image/png"
BBOX_PADDING = 0.10  # 10% padding around building polygon
REQUEST_DELAY = 0.3  # seconds between requests
REQUEST_TIMEOUT = 30  # seconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_wkt_bbox(wkt_text: str) -> tuple[float, float, float, float]:
    """Extract bounding box (minx, miny, maxx, maxy) from a WKT MULTIPOLYGON.

    Parses all numeric coordinate pairs from the WKT string and returns
    the overall min/max extents.
    """
    # Extract all numbers that look like coordinate values
    numbers = re.findall(r"[-+]?\d+\.\d+", wkt_text)
    if len(numbers) < 4:
        raise ValueError(f"Could not parse coordinates from WKT (found {len(numbers)} numbers)")

    # Coordinates alternate: x y x y ...
    xs = [float(numbers[i]) for i in range(0, len(numbers), 2)]
    ys = [float(numbers[i]) for i in range(1, len(numbers), 2)]

    return min(xs), min(ys), max(xs), max(ys)


def pad_bbox(
    minx: float, miny: float, maxx: float, maxy: float, padding: float
) -> tuple[float, float, float, float]:
    """Add percentage-based padding to a bounding box."""
    dx = (maxx - minx) * padding
    dy = (maxy - miny) * padding
    # Ensure minimum padding for very small buildings
    min_pad = 0.0001  # ~11 meters at equator
    dx = max(dx, min_pad)
    dy = max(dy, min_pad)
    return minx - dx, miny - dy, maxx + dx, maxy + dy


def is_valid_png(data: bytes) -> bool:
    """Check if the response data starts with PNG magic bytes."""
    return data[:4] == b"\x89PNG"


def is_xml_error(data: bytes) -> bool:
    """Check if the response is an XML error from GeoServer."""
    return data[:5] == b"<?xml" or data[:1] == b"<"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Windows console encoding fix
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    # Suppress SSL warnings (self-signed cert)
    requests.packages.urllib3.disable_warnings()

    force = "--force" in sys.argv

    print("=" * 70)
    print("WMS Floor Plan Downloader")
    print("=" * 70)

    # Load data files
    print(f"\nLoading floor list from: {FLOORS_JSON}")
    with open(FLOORS_JSON, "r", encoding="utf-8") as f:
        all_floors = json.load(f)

    print(f"Loading building bounds from: {BOUNDS_JSON}")
    with open(BOUNDS_JSON, "r", encoding="utf-8") as f:
        all_bounds = json.load(f)

    # Count totals
    total_floors = sum(len(floors) for floors in all_floors.values())
    print(f"\nBuildings: {len(all_floors)}")
    print(f"Total floor plans to download: {total_floors}")
    print(f"Output directory: {OUTPUT_DIR}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Track statistics
    downloaded = 0
    skipped_existing = 0
    skipped_no_bounds = 0
    errors_xml = 0
    errors_not_png = 0
    errors_http = 0
    errors_other = 0

    session = requests.Session()
    session.verify = False

    processed = 0
    for build_id, floors in sorted(all_floors.items()):
        # Get building bounding box
        if build_id not in all_bounds:
            print(f"\n  WARNING: No bounds for building {build_id}, skipping {len(floors)} floors")
            skipped_no_bounds += len(floors)
            processed += len(floors)
            continue

        wkt = all_bounds[build_id]
        try:
            raw_bbox = parse_wkt_bbox(wkt)
            bbox = pad_bbox(*raw_bbox, BBOX_PADDING)
        except ValueError as e:
            print(f"\n  ERROR: Could not parse bbox for {build_id}: {e}")
            skipped_no_bounds += len(floors)
            processed += len(floors)
            continue

        bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"

        for floor in floors:
            processed += 1
            layer_name = f"gis_room:{build_id}_{floor}"
            filename = f"{build_id}_{floor}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)

            # Skip existing (unless --force)
            if not force and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                skipped_existing += 1
                continue

            # Build WMS GetMap URL
            params = {
                "service": "WMS",
                "version": "1.1.0",
                "request": "GetMap",
                "layers": layer_name,
                "styles": "",
                "bbox": bbox_str,
                "width": IMAGE_WIDTH,
                "height": IMAGE_HEIGHT,
                "srs": SRS,
                "format": IMAGE_FORMAT,
            }

            progress = f"[{processed}/{total_floors}]"
            print(f"  {progress} Downloading {filename} ...", end=" ", flush=True)

            try:
                resp = session.get(
                    WMS_BASE_URL, params=params, timeout=REQUEST_TIMEOUT
                )
                resp.raise_for_status()

                data = resp.content

                if is_xml_error(data):
                    print("SKIP (XML error response)")
                    errors_xml += 1
                elif is_valid_png(data):
                    with open(filepath, "wb") as out:
                        out.write(data)
                    size_kb = len(data) / 1024
                    print(f"OK ({size_kb:.1f} KB)")
                    downloaded += 1
                else:
                    print(f"SKIP (not PNG, header: {data[:8]})")
                    errors_not_png += 1

            except requests.exceptions.HTTPError as e:
                print(f"HTTP ERROR ({e})")
                errors_http += 1
            except requests.exceptions.RequestException as e:
                print(f"ERROR ({e})")
                errors_other += 1

            time.sleep(REQUEST_DELAY)

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total floor plans:      {total_floors}")
    print(f"  Downloaded (new):       {downloaded}")
    print(f"  Skipped (existing):     {skipped_existing}")
    print(f"  Skipped (no bounds):    {skipped_no_bounds}")
    print(f"  Errors (XML response):  {errors_xml}")
    print(f"  Errors (not PNG):       {errors_not_png}")
    print(f"  Errors (HTTP):          {errors_http}")
    print(f"  Errors (other):         {errors_other}")
    print("=" * 70)

    # Verify final state
    existing_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".png")]
    total_size = sum(
        os.path.getsize(os.path.join(OUTPUT_DIR, f)) for f in existing_files
    )
    print(f"\n  Files in output dir:    {len(existing_files)}")
    print(f"  Total size:             {total_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
