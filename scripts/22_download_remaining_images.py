"""
22_download_remaining_images.py

Download remaining images in the gap range (37600-39050) that were not
covered by previous scans.

Previous scan coverage:
  - 37000-37600: 570 images downloaded to building_images/unknown/
  - 37588-39056: 356 images downloaded to building_images/{buildId}/
  - 39050-39200: 121 images downloaded to building_images/unknown/

This script fills the gap by checking IDs 37600-39050 inclusive,
skipping any that already exist locally (in unknown/ or any building
subdirectory).
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
import requests.packages.urllib3

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")

# Suppress InsecureRequestWarning for verify=False
requests.packages.urllib3.disable_warnings()

# --- Configuration ---
BASE_URL = "https://ymspace.ga.nycu.edu.tw/gisweb/public/uploadfiles.htm"
BUILDING_IMAGES_DIR = Path(
    r"C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive\building_images"
)
OUTPUT_DIR = BUILDING_IMAGES_DIR / "unknown"
RESULTS_FILE = OUTPUT_DIR / "_gap_scan_results.json"
DELAY = 0.15  # seconds between requests
TIMEOUT = 15  # seconds per request

# Gap range to scan
SCAN_START = 37600
SCAN_END = 39050

SESSION = requests.Session()
SESSION.verify = False
SESSION.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    }
)


def build_existing_id_set() -> set[int]:
    """Scan all subdirectories of building_images/ to find already-downloaded IDs.

    Returns:
        Set of image IDs that already exist locally.
    """
    existing = set()

    for subdir in BUILDING_IMAGES_DIR.iterdir():
        if not subdir.is_dir():
            continue
        for file in subdir.iterdir():
            if file.suffix.lower() == ".jpg" and file.stem.isdigit():
                existing.add(int(file.stem))

    return existing


def download_image(image_id: int) -> dict | None:
    """Download an image by its ID if the response is a valid image.

    Args:
        image_id: The image ID to download.

    Returns:
        dict with image info if successful, None otherwise.
    """
    url = f"{BASE_URL}?action=listImg&q={image_id}"

    try:
        resp = SESSION.get(url, timeout=TIMEOUT)
    except Exception as e:
        print(f"  [ERROR] ID {image_id}: {e}")
        return None

    content_type = resp.headers.get("Content-Type", "")
    content_length = len(resp.content)

    if "image" in content_type.lower() and content_length > 1000:
        output_path = OUTPUT_DIR / f"{image_id}.jpg"
        output_path.write_bytes(resp.content)
        return {
            "id": image_id,
            "content_type": content_type,
            "content_length": content_length,
            "path": str(output_path),
        }

    return None


def main():
    total_ids = SCAN_END - SCAN_START + 1

    print("=" * 70)
    print("ymspace.ga.nycu.edu.tw - Gap Range Image Downloader")
    print(f"Scanning IDs {SCAN_START} to {SCAN_END} ({total_ids} IDs)")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build set of all existing image IDs across all subdirectories
    print("\nBuilding index of existing images...")
    existing_ids = build_existing_id_set()
    print(f"Found {len(existing_ids)} existing images across all directories")

    total_scanned = 0
    already_existed = 0
    new_downloads = 0
    not_found = 0
    downloaded_images = []

    start_time = time.time()

    print(f"\nStarting scan of {total_ids} IDs...\n")

    for image_id in range(SCAN_START, SCAN_END + 1):
        total_scanned += 1

        # Check if already exists locally
        if image_id in existing_ids:
            already_existed += 1
            # Progress still counts
            if total_scanned % 50 == 0:
                elapsed = time.time() - start_time
                print(
                    f"  Progress: {total_scanned}/{total_ids} scanned | "
                    f"existed: {already_existed}, new: {new_downloads}, "
                    f"not found: {not_found} | {elapsed:.1f}s elapsed"
                )
            continue

        # Not found locally, try to download
        result = download_image(image_id)

        if result:
            new_downloads += 1
            existing_ids.add(image_id)
            downloaded_images.append(result)
            print(
                f"  [NEW] ID {image_id}: {result['content_type']} "
                f"({result['content_length']} bytes)"
            )
        else:
            not_found += 1

        # Progress every 50 IDs
        if total_scanned % 50 == 0:
            elapsed = time.time() - start_time
            print(
                f"  Progress: {total_scanned}/{total_ids} scanned | "
                f"existed: {already_existed}, new: {new_downloads}, "
                f"not found: {not_found} | {elapsed:.1f}s elapsed"
            )

        time.sleep(DELAY)

    elapsed = time.time() - start_time

    # --- Summary ---
    print("\n" + "=" * 70)
    print("GAP SCAN SUMMARY")
    print("=" * 70)
    print(f"Range scanned:      {SCAN_START} - {SCAN_END}")
    print(f"Total IDs scanned:  {total_scanned}")
    print(f"Already existed:    {already_existed}")
    print(f"New downloads:      {new_downloads}")
    print(f"Not found / empty:  {not_found}")
    print(f"Time elapsed:       {elapsed:.1f}s")
    if total_scanned > 0:
        print(f"Avg time per ID:    {elapsed / total_scanned * 1000:.0f}ms")

    if downloaded_images:
        new_ids = [img["id"] for img in downloaded_images]
        print(f"\nNewly downloaded IDs: {new_ids}")

    # --- Save results ---
    results_data = {
        "scan_date": datetime.now().isoformat(),
        "range_start": SCAN_START,
        "range_end": SCAN_END,
        "total_scanned": total_scanned,
        "already_existed": already_existed,
        "new_downloads": new_downloads,
        "not_found": not_found,
        "elapsed_seconds": round(elapsed, 1),
        "downloaded_images": downloaded_images,
    }

    RESULTS_FILE.write_text(
        json.dumps(results_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nResults saved to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
