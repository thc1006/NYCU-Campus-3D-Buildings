"""
20_render_extra_wms_floorplans.py
=================================
Render WMS floor plan PNGs for the A-series, G-series, and T-series building
room layers discovered in GeoServer WFS but NOT already downloaded.

Each GeoJSON file in wfs_extra_rooms/ contains a top-level ``bbox`` field with
[minx, miny, maxx, maxy] in EPSG:3826.  The script computes a padded bounding
box and requests a WMS GetMap PNG for the corresponding gis_room layer.

Output directory: data/ymmap_archive/wms_floorplans/{BuildID}_{Floor}.png

Usage:
    python scripts/20_render_extra_wms_floorplans.py
    python scripts/20_render_extra_wms_floorplans.py --force   # re-download existing
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

EXTRA_ROOMS_DIR = os.path.join(DATA_DIR, "wfs_extra_rooms")
OUTPUT_DIR = os.path.join(DATA_DIR, "wms_floorplans")

WMS_BASE_URL = "https://ymspace.ga.nycu.edu.tw:8080/geoserver/wms"

IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024
CRS = "EPSG:3826"
IMAGE_FORMAT = "image/png"
BBOX_PADDING = 0.10  # 10% padding around room extent
REQUEST_DELAY = 0.3  # seconds between requests
REQUEST_TIMEOUT = 30  # seconds

# Only process A-series, G-series, and T-series buildings
TARGET_PREFIXES = ("A", "G", "T")

# Filename pattern: gis_room_{BuildID}_{Floor}.json
FILENAME_PATTERN = re.compile(r"^gis_room_([A-Z]\w+?)_(\w+)\.json$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pad_bbox(
    minx: float, miny: float, maxx: float, maxy: float, padding: float
) -> tuple:
    """Add percentage-based padding to a bounding box in EPSG:3826 (meters)."""
    dx = (maxx - minx) * padding
    dy = (maxy - miny) * padding
    # Ensure minimum padding for very small buildings (~1 meter)
    min_pad = 1.0
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
    print("WMS Extra Floor Plan Renderer (A / G / T series)")
    print("=" * 70)

    # --- Step 1: Scan wfs_extra_rooms for matching GeoJSON files -----------
    if not os.path.isdir(EXTRA_ROOMS_DIR):
        print(f"\nERROR: Extra rooms directory not found: {EXTRA_ROOMS_DIR}")
        sys.exit(1)

    all_json_files = sorted(os.listdir(EXTRA_ROOMS_DIR))
    candidates = []

    for fname in all_json_files:
        m = FILENAME_PATTERN.match(fname)
        if not m:
            continue
        build_id = m.group(1)
        floor = m.group(2)
        if not build_id.startswith(TARGET_PREFIXES):
            continue
        candidates.append((build_id, floor, fname))

    print(f"\nScanned {len(all_json_files)} files in wfs_extra_rooms/")
    print(f"Found {len(candidates)} A/G/T-series room layers")

    # --- Step 2: Filter out layers that already have PNGs -----------------
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    to_download = []
    skipped_existing = 0

    for build_id, floor, fname in candidates:
        png_name = f"{build_id}_{floor}.png"
        png_path = os.path.join(OUTPUT_DIR, png_name)
        if not force and os.path.exists(png_path) and os.path.getsize(png_path) > 0:
            skipped_existing += 1
        else:
            to_download.append((build_id, floor, fname))

    print(f"Already have PNG (skipped): {skipped_existing}")
    print(f"To download: {len(to_download)}")
    print(f"Output directory: {OUTPUT_DIR}")

    if not to_download:
        print("\nNothing to download. All floor plans already exist.")
        return

    # --- Step 3: Download WMS GetMap PNGs ----------------------------------
    print(f"\nStarting downloads ({len(to_download)} layers)...\n")

    downloaded = 0
    errors_no_bbox = 0
    errors_xml = 0
    errors_not_png = 0
    errors_http = 0
    errors_other = 0

    session = requests.Session()
    session.verify = False

    for idx, (build_id, floor, fname) in enumerate(to_download, start=1):
        layer_name = f"gis_room:{build_id}_{floor}"
        png_name = f"{build_id}_{floor}.png"
        png_path = os.path.join(OUTPUT_DIR, png_name)

        # Load GeoJSON and extract bbox
        geojson_path = os.path.join(EXTRA_ROOMS_DIR, fname)
        try:
            with open(geojson_path, "r", encoding="utf-8") as f:
                geojson = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  [{idx}/{len(to_download)}] {png_name} ... ERROR reading JSON ({e})")
            errors_other += 1
            continue

        bbox_raw = geojson.get("bbox")
        if not bbox_raw or len(bbox_raw) < 4:
            print(f"  [{idx}/{len(to_download)}] {png_name} ... SKIP (no valid bbox)")
            errors_no_bbox += 1
            continue

        minx, miny, maxx, maxy = bbox_raw[0], bbox_raw[1], bbox_raw[2], bbox_raw[3]
        padded = pad_bbox(minx, miny, maxx, maxy, BBOX_PADDING)
        bbox_str = f"{padded[0]},{padded[1]},{padded[2]},{padded[3]}"

        # Build WMS GetMap request
        params = {
            "SERVICE": "WMS",
            "VERSION": "1.1.1",
            "REQUEST": "GetMap",
            "LAYERS": layer_name,
            "STYLES": "",
            "CRS": CRS,
            "BBOX": bbox_str,
            "WIDTH": IMAGE_WIDTH,
            "HEIGHT": IMAGE_HEIGHT,
            "FORMAT": IMAGE_FORMAT,
            "TRANSPARENT": "true",
        }

        print(f"  [{idx}/{len(to_download)}] {png_name} ...", end=" ", flush=True)

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
                with open(png_path, "wb") as out:
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

    # --- Step 4: Print summary ---------------------------------------------
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Target layers (A/G/T):  {len(candidates)}")
    print(f"  Skipped (existing):     {skipped_existing}")
    print(f"  Attempted downloads:    {len(to_download)}")
    print(f"  Downloaded (new):       {downloaded}")
    print(f"  Skipped (no bbox):      {errors_no_bbox}")
    print(f"  Errors (XML response):  {errors_xml}")
    print(f"  Errors (not PNG):       {errors_not_png}")
    print(f"  Errors (HTTP):          {errors_http}")
    print(f"  Errors (other):         {errors_other}")
    print("=" * 70)

    # Verify final state
    existing_pngs = [
        f for f in os.listdir(OUTPUT_DIR)
        if f.endswith(".png") and f[0] in TARGET_PREFIXES
    ]
    total_size = sum(
        os.path.getsize(os.path.join(OUTPUT_DIR, f)) for f in existing_pngs
    )
    print(f"\n  A/G/T PNGs in output:   {len(existing_pngs)}")
    print(f"  Total size (A/G/T):     {total_size / 1024 / 1024:.1f} MB")
    print("=" * 70)


if __name__ == "__main__":
    main()
