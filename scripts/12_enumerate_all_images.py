#!/usr/bin/env python3
"""
Enumerate ALL image IDs from buildinfo.htm?action=loadImage for all buildings.
Discovers building photos AND floor plan images with their uploadfiles IDs.

Output: data/ymmap_archive/api_data/all_image_ids.json
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
import ssl

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "data", "ymmap_archive", "api_data")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

API_URL = "https://ymspace.ga.nycu.edu.tw/gisweb/public/buildinfo.htm"

# All 48 building IDs
BUILDINGS = [
    "B003","B004","B005","B009","B010","B011","B012","B013","B014","B015",
    "B016","B017","B018","B019","B020","B021","B022","B023","B024","B025",
    "B026","B027","B028","B029","B030","B031","B032","B033","B034",
    "G002","G005","G007","G008","G009","G010","G011","G012","G013","G014",
    "G015","G016","G017","G018","G019","G020","G021","G022",
    "P003","P004","P005","P006",
    "T001",
    "Y001","Y002","Y003","Y004","Y005","Y006","Y007","Y008","Y009","Y010",
    "Y011","Y012",
]


def fetch_images(build_id, navi_key, floor=None):
    """Fetch image URLs for a building/floor."""
    data = f"buildId={build_id}&naviKey={navi_key}"
    if floor:
        data += f"&floor={floor}"
    req = urllib.request.Request(
        f"{API_URL}?action=loadImage",
        data=data.encode('utf-8'),
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            if result and result.get('data'):
                # Extract image IDs from URLs
                ids = []
                for url in result['data']:
                    if 'q=' in url:
                        ids.append(int(url.split('q=')[1]))
                return ids
            return []
    except Exception as e:
        return []


def main():
    # Load floor plans data
    floors_path = os.path.join(BASE_DIR, "data", "ymmap_archive", "api_data", "floor_plans.json")
    with open(floors_path, 'r', encoding='utf-8') as f:
        floor_plans = json.load(f)

    results = {}
    all_image_ids = set()

    # Phase 1: Building photos
    print("=== Phase 1: Building Photos ===")
    for i, bid in enumerate(BUILDINGS):
        ids = fetch_images(bid, "buildinfo")
        if ids:
            results.setdefault(bid, {})["photos"] = ids
            all_image_ids.update(ids)
            print(f"  [{i+1}/{len(BUILDINGS)}] {bid}: {len(ids)} photos (IDs: {min(ids)}-{max(ids)})")
        else:
            print(f"  [{i+1}/{len(BUILDINGS)}] {bid}: no photos")
        time.sleep(0.2)

    # Phase 2: Floor plan images
    print(f"\n=== Phase 2: Floor Plan Images ===")
    total_fp = 0
    for bid in BUILDINGS:
        if bid not in floor_plans:
            continue
        floors = [f['floor'] for f in floor_plans[bid]]
        for floor in floors:
            ids = fetch_images(bid, "floorinfo", floor)
            if ids:
                results.setdefault(bid, {}).setdefault("floors", {})[floor] = ids
                all_image_ids.update(ids)
                total_fp += len(ids)
            time.sleep(0.15)
        if bid in results and "floors" in results[bid]:
            n_floors = len(results[bid]["floors"])
            n_imgs = sum(len(v) for v in results[bid]["floors"].values())
            print(f"  {bid}: {n_floors} floors, {n_imgs} images")

    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Buildings with photos: {sum(1 for b in results if 'photos' in results[b])}")
    print(f"Buildings with floor plans: {sum(1 for b in results if 'floors' in results[b])}")
    print(f"Total unique image IDs: {len(all_image_ids)}")
    if all_image_ids:
        print(f"ID range: {min(all_image_ids)} - {max(all_image_ids)}")
    print(f"Total floor plan images: {total_fp}")

    # Save
    output = {
        "buildings": results,
        "all_image_ids": sorted(all_image_ids),
        "total_unique_images": len(all_image_ids),
        "id_range": [min(all_image_ids), max(all_image_ids)] if all_image_ids else None,
    }
    out_path = os.path.join(OUT_DIR, "all_image_ids.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
