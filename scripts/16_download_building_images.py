#!/usr/bin/env python3
"""
Download ALL building photos from ymspace.ga.nycu.edu.tw GIS system.

For each building ID, queries:
  1. buildinfo.htm?action=loadImage  (building photos)
  2. buildinfo.htm?action=getFloorListOfFloorPlain  (floor plan image refs)

Then downloads actual image files via:
  uploadfiles.htm?action=listImg&q={image_id}

Output:
  data/ymmap_archive/building_images/{buildId}/{image_id}.jpg
  data/ymmap_archive/building_images/loadImage_responses.json
"""

import json
import os
import sys
import time

import requests
import urllib3

# Suppress InsecureRequestWarning for verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "data", "ymmap_archive", "building_images")
API_DATA_DIR = os.path.join(BASE_DIR, "data", "ymmap_archive", "api_data")

API_BASE = "https://ymspace.ga.nycu.edu.tw/gisweb/public"
BUILDINFO_URL = f"{API_BASE}/buildinfo.htm"
UPLOAD_URL = f"{API_BASE}/uploadfiles.htm"

# Building IDs specified in the task (44 buildings)
BUILDING_IDS = [
    "A109", "A133", "A143",
    "B003", "B004", "B005", "B009", "B010", "B012", "B015",
    "B016", "B017", "B020", "B021", "B022", "B023", "B024", "B025",
    "B027", "B028", "B029", "B030", "B031", "B032", "B033", "B034",
    "G002", "G005",
    "P003", "P004", "P005", "P006",
    "Y001", "Y002", "Y003", "Y004", "Y005", "Y006", "Y007", "Y008",
    "Y009", "Y010", "Y011", "Y012",
]

SESSION = requests.Session()
SESSION.verify = False
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (NYCU-Archive-Research)",
    "Content-Type": "application/x-www-form-urlencoded",
})


def fetch_load_image(build_id):
    """Fetch image URLs for a building via loadImage POST endpoint.

    Returns the raw API response dict and a list of extracted image IDs.
    """
    url = f"{BUILDINFO_URL}?action=loadImage"
    data = f"buildId={build_id}&naviKey=buildinfo"
    try:
        resp = SESSION.post(url, data=data, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        image_ids = []
        if result and result.get("data"):
            for img_url in result["data"]:
                if "q=" in str(img_url):
                    try:
                        image_ids.append(int(str(img_url).split("q=")[1]))
                    except (ValueError, IndexError):
                        pass
        return result, image_ids
    except Exception as e:
        return {"error": str(e)}, []


def fetch_floor_list(build_id):
    """Fetch floor plan list via getFloorListOfFloorPlain.

    Returns the raw API response dict.
    """
    url = f"{BUILDINFO_URL}?action=getFloorListOfFloorPlain&buildId={build_id}"
    try:
        resp = SESSION.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def fetch_floor_images(build_id, floor):
    """Fetch image URLs for a specific floor via loadImage POST.

    Returns a list of image IDs.
    """
    url = f"{BUILDINFO_URL}?action=loadImage"
    data = f"buildId={build_id}&naviKey=floorinfo&floor={floor}"
    try:
        resp = SESSION.post(url, data=data, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        image_ids = []
        if result and result.get("data"):
            for img_url in result["data"]:
                if "q=" in str(img_url):
                    try:
                        image_ids.append(int(str(img_url).split("q=")[1]))
                    except (ValueError, IndexError):
                        pass
        return image_ids
    except Exception:
        return []


def download_image(image_id, out_path):
    """Download an actual image file via uploadfiles.htm.

    Returns the number of bytes written, or 0 on failure.
    """
    if os.path.exists(out_path):
        return os.path.getsize(out_path)

    url = f"{UPLOAD_URL}?action=listImg&q={image_id}"
    try:
        resp = SESSION.get(url, timeout=30)
        content = resp.content
        ct = resp.headers.get("Content-Type", "")

        # Validate that response is actually an image
        is_image = False
        if "image" in ct or "octet" in ct:
            is_image = True
        elif len(content) > 100 and content[:3] == b"\xff\xd8\xff":
            # JPEG magic bytes
            is_image = True
        elif len(content) > 100 and content[:8] == b"\x89PNG\r\n\x1a\n":
            # PNG magic bytes
            is_image = True

        if is_image and len(content) > 0:
            with open(out_path, "wb") as f:
                f.write(content)
            return len(content)
        else:
            return 0
    except Exception as e:
        print(f"    ERROR downloading image {image_id}: {e}")
        return 0


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Try to load existing building_images.json for supplemental data
    existing_images_path = os.path.join(API_DATA_DIR, "building_images.json")
    existing_images = {}
    if os.path.exists(existing_images_path):
        with open(existing_images_path, "r", encoding="utf-8") as f:
            existing_images = json.load(f)
        print(f"Loaded existing building_images.json with {len(existing_images)} buildings")

    all_responses = {}
    all_image_ids = set()
    stats = {
        "buildings_queried": 0,
        "buildings_with_photos": 0,
        "total_image_ids": 0,
        "images_downloaded": 0,
        "images_skipped_existing": 0,
        "images_failed": 0,
        "total_bytes": 0,
    }

    # ====================================================================
    # Phase 1: Query loadImage for each building and collect image IDs
    # ====================================================================
    print("=" * 60)
    print("Phase 1: Querying loadImage for all buildings")
    print("=" * 60)

    for i, bid in enumerate(BUILDING_IDS):
        stats["buildings_queried"] += 1
        raw_response, image_ids = fetch_load_image(bid)
        all_responses[bid] = {
            "loadImage": raw_response,
            "image_ids": image_ids,
        }

        if image_ids:
            stats["buildings_with_photos"] += 1
            all_image_ids.update(image_ids)
            print(
                f"  [{i+1}/{len(BUILDING_IDS)}] {bid}: "
                f"{len(image_ids)} photos (IDs: {min(image_ids)}-{max(image_ids)})"
            )
        else:
            print(f"  [{i+1}/{len(BUILDING_IDS)}] {bid}: no photos")

        time.sleep(0.5)

    # Also pull in image IDs from existing data for buildings in our list
    for bid in BUILDING_IDS:
        if bid in existing_images and existing_images[bid]:
            for url_str in existing_images[bid]:
                if "q=" in str(url_str):
                    try:
                        img_id = int(str(url_str).split("q=")[1])
                        all_image_ids.add(img_id)
                        # Merge into responses if not already there
                        if bid in all_responses and img_id not in all_responses[bid].get("image_ids", []):
                            all_responses[bid].setdefault("image_ids", []).append(img_id)
                    except (ValueError, IndexError):
                        pass

    # ====================================================================
    # Phase 2: Query floor plan info
    # ====================================================================
    print()
    print("=" * 60)
    print("Phase 2: Querying floor plan image references")
    print("=" * 60)

    for i, bid in enumerate(BUILDING_IDS):
        floor_response = fetch_floor_list(bid)
        all_responses[bid]["floorList"] = floor_response

        if floor_response and floor_response.get("data"):
            floors = floor_response["data"]
            floor_names = []
            for fl in floors:
                if isinstance(fl, dict):
                    floor_names.append(fl.get("floor", str(fl)))
                else:
                    floor_names.append(str(fl))

            if floor_names:
                # Get floor-specific images
                floor_image_data = {}
                for floor_name in floor_names:
                    floor_ids = fetch_floor_images(bid, floor_name)
                    if floor_ids:
                        floor_image_data[floor_name] = floor_ids
                        all_image_ids.update(floor_ids)
                    time.sleep(0.15)

                if floor_image_data:
                    all_responses[bid]["floor_images"] = floor_image_data
                    total_floor_imgs = sum(len(v) for v in floor_image_data.values())
                    print(
                        f"  [{i+1}/{len(BUILDING_IDS)}] {bid}: "
                        f"{len(floor_names)} floors, {total_floor_imgs} floor image refs"
                    )
                else:
                    print(f"  [{i+1}/{len(BUILDING_IDS)}] {bid}: {len(floor_names)} floors, no floor images")
            else:
                print(f"  [{i+1}/{len(BUILDING_IDS)}] {bid}: no floor data")
        else:
            print(f"  [{i+1}/{len(BUILDING_IDS)}] {bid}: no floor plan data")

        time.sleep(0.5)

    # Deduplicate all image IDs
    unique_ids = sorted(all_image_ids)
    stats["total_image_ids"] = len(unique_ids)

    print()
    print(f"Total unique image IDs to download: {len(unique_ids)}")
    if unique_ids:
        print(f"ID range: {unique_ids[0]} - {unique_ids[-1]}")

    # ====================================================================
    # Phase 3: Download actual images, organized by building
    # ====================================================================
    print()
    print("=" * 60)
    print("Phase 3: Downloading image files")
    print("=" * 60)

    # Build a mapping: image_id -> list of building IDs that reference it
    image_to_buildings = {}
    for bid in BUILDING_IDS:
        bid_data = all_responses.get(bid, {})
        bid_image_ids = set(bid_data.get("image_ids", []))
        # Also include floor images
        for floor_ids in bid_data.get("floor_images", {}).values():
            bid_image_ids.update(floor_ids)
        for img_id in bid_image_ids:
            image_to_buildings.setdefault(img_id, []).append(bid)

    # Download images, saving into the first building's directory
    downloaded_ids = set()
    for i, img_id in enumerate(unique_ids):
        buildings_for_img = image_to_buildings.get(img_id, ["unknown"])
        primary_bid = buildings_for_img[0]

        bid_dir = os.path.join(OUT_DIR, primary_bid)
        os.makedirs(bid_dir, exist_ok=True)

        out_path = os.path.join(bid_dir, f"{img_id}.jpg")

        if os.path.exists(out_path):
            stats["images_skipped_existing"] += 1
            downloaded_ids.add(img_id)
            if (i + 1) % 50 == 0:
                print(f"  [{i+1}/{len(unique_ids)}] Skipping existing...")
            continue

        nbytes = download_image(img_id, out_path)
        if nbytes > 0:
            stats["images_downloaded"] += 1
            stats["total_bytes"] += nbytes
            downloaded_ids.add(img_id)
            if (i + 1) % 10 == 0 or (i + 1) == len(unique_ids):
                print(
                    f"  [{i+1}/{len(unique_ids)}] Downloaded {img_id} "
                    f"({nbytes / 1024:.1f} KB) -> {primary_bid}/"
                )
        else:
            stats["images_failed"] += 1
            print(f"  [{i+1}/{len(unique_ids)}] FAILED: {img_id} (building: {primary_bid})")

        time.sleep(0.5)

    # For images referenced by multiple buildings, create symlinks or copies
    # in other building directories for easy browsing
    print()
    print("Creating cross-references for shared images...")
    cross_refs = 0
    for img_id, bids in image_to_buildings.items():
        if len(bids) <= 1:
            continue
        primary_bid = bids[0]
        src_path = os.path.join(OUT_DIR, primary_bid, f"{img_id}.jpg")
        if not os.path.exists(src_path):
            continue
        for other_bid in bids[1:]:
            other_dir = os.path.join(OUT_DIR, other_bid)
            os.makedirs(other_dir, exist_ok=True)
            dst_path = os.path.join(other_dir, f"{img_id}.jpg")
            if not os.path.exists(dst_path):
                try:
                    # Copy instead of symlink for Windows compatibility
                    import shutil
                    shutil.copy2(src_path, dst_path)
                    cross_refs += 1
                except Exception:
                    pass

    if cross_refs > 0:
        print(f"  Created {cross_refs} cross-reference copies")

    # ====================================================================
    # Save metadata
    # ====================================================================
    responses_path = os.path.join(OUT_DIR, "loadImage_responses.json")
    with open(responses_path, "w", encoding="utf-8") as f:
        json.dump(all_responses, f, ensure_ascii=False, indent=2)
    print(f"\nSaved API responses to: {responses_path}")

    # Save a summary index
    index = {
        "building_ids": BUILDING_IDS,
        "image_to_buildings": {str(k): v for k, v in image_to_buildings.items()},
        "all_image_ids": unique_ids,
        "total_unique_images": len(unique_ids),
        "id_range": [unique_ids[0], unique_ids[-1]] if unique_ids else None,
        "stats": stats,
    }
    index_path = os.path.join(OUT_DIR, "download_index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"Saved download index to: {index_path}")

    # ====================================================================
    # Final statistics
    # ====================================================================
    print()
    print("=" * 60)
    print("FINAL STATISTICS")
    print("=" * 60)
    print(f"  Buildings queried:        {stats['buildings_queried']}")
    print(f"  Buildings with photos:    {stats['buildings_with_photos']}")
    print(f"  Total unique image IDs:   {stats['total_image_ids']}")
    print(f"  Images downloaded:        {stats['images_downloaded']}")
    print(f"  Images skipped (existing):{stats['images_skipped_existing']}")
    print(f"  Images failed:            {stats['images_failed']}")
    print(f"  Total bytes downloaded:   {stats['total_bytes'] / 1024 / 1024:.2f} MB")
    print(f"  Cross-reference copies:   {cross_refs}")
    print()

    # Per-building breakdown
    print("Per-building breakdown:")
    for bid in BUILDING_IDS:
        bid_dir = os.path.join(OUT_DIR, bid)
        if os.path.isdir(bid_dir):
            files = [f for f in os.listdir(bid_dir) if f.endswith(".jpg")]
            total_size = sum(
                os.path.getsize(os.path.join(bid_dir, f)) for f in files
            )
            print(f"  {bid}: {len(files)} images ({total_size / 1024:.1f} KB)")
        else:
            print(f"  {bid}: no images")


if __name__ == "__main__":
    main()
