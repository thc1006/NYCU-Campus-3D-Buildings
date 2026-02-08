"""
21_scan_image_ids.py

Scan for valid image IDs on ymspace.ga.nycu.edu.tw uploadfiles API
outside the known range (approx 37588-39056).

Probes multiple ID ranges to discover any additional images stored
in the system, downloads found images, and saves a summary report.
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
OUTPUT_DIR = Path(
    r"C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive\building_images\unknown"
)
RESULTS_FILE = OUTPUT_DIR / "_scan_results.json"
DELAY = 0.15  # seconds between requests
TIMEOUT = 15  # seconds per request

# ID ranges to scan
SCAN_RANGES = [
    (1, 100, "very early IDs"),
    (500, 600, "early range 500-600"),
    (1000, 1100, "range 1000-1100"),
    (5000, 5100, "range 5000-5100"),
    (10000, 10100, "range 10000-10100"),
    (20000, 20100, "range 20000-20100"),
    (30000, 30100, "range 30000-30100"),
    (35000, 35100, "range 35000-35100"),
    (37000, 37600, "just before known range"),
    (39050, 39200, "just after known range"),
    (40000, 40100, "range 40000-40100"),
    (50000, 50100, "range 50000-50100"),
]

SESSION = requests.Session()
SESSION.verify = False
SESSION.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    }
)


def check_image_id(image_id: int) -> dict | None:
    """Check if an image ID returns a valid image.

    Tries HEAD first, falls back to GET with stream=True.

    Returns:
        dict with image info if valid, None otherwise.
    """
    url = f"{BASE_URL}?action=listImg&q={image_id}"

    content_type = None
    content_length = 0

    # Try HEAD first
    try:
        resp = SESSION.head(url, timeout=TIMEOUT)
        content_type = resp.headers.get("Content-Type", "")
        length_str = resp.headers.get("Content-Length", "0")
        content_length = int(length_str) if length_str.isdigit() else 0
    except Exception:
        # HEAD failed, try GET with stream
        try:
            resp = SESSION.get(url, timeout=TIMEOUT, stream=True)
            content_type = resp.headers.get("Content-Type", "")
            length_str = resp.headers.get("Content-Length", "0")
            content_length = int(length_str) if length_str.isdigit() else 0
            resp.close()
        except Exception as e:
            print(f"  [ERROR] ID {image_id}: {e}")
            return None

    if content_type and "image" in content_type.lower() and content_length > 1000:
        return {
            "id": image_id,
            "content_type": content_type,
            "content_length": content_length,
        }

    return None


def download_image(image_id: int) -> bool:
    """Download an image by its ID and save to the unknown directory.

    Returns:
        True if download succeeded, False otherwise.
    """
    url = f"{BASE_URL}?action=listImg&q={image_id}"
    output_path = OUTPUT_DIR / f"{image_id}.jpg"

    try:
        resp = SESSION.get(url, timeout=TIMEOUT)
        if resp.status_code == 200 and len(resp.content) > 1000:
            output_path.write_bytes(resp.content)
            return True
    except Exception as e:
        print(f"  [DOWNLOAD ERROR] ID {image_id}: {e}")

    return False


def main():
    print("=" * 70)
    print("ymspace.ga.nycu.edu.tw - Image ID Scanner")
    print(f"Known range: ~37588 to ~39056")
    print(f"Scanning {len(SCAN_RANGES)} ranges outside known area")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_scanned = 0
    found_images = []
    range_results = {}

    start_time = time.time()

    for range_start, range_end, description in SCAN_RANGES:
        range_count = range_end - range_start + 1
        range_found = 0

        print(f"\n--- Scanning {description}: IDs {range_start}-{range_end} "
              f"({range_count} IDs) ---")

        for image_id in range(range_start, range_end + 1):
            total_scanned += 1

            result = check_image_id(image_id)

            if result:
                range_found += 1
                print(
                    f"  [FOUND] ID {image_id}: "
                    f"{result['content_type']} "
                    f"({result['content_length']} bytes)"
                )

                # Download the image
                if download_image(image_id):
                    result["downloaded"] = True
                    result["path"] = str(OUTPUT_DIR / f"{image_id}.jpg")
                    print(f"          -> Downloaded to {result['path']}")
                else:
                    result["downloaded"] = False

                found_images.append(result)

            # Progress indicator every 50 IDs
            if (image_id - range_start + 1) % 50 == 0:
                print(
                    f"  ... scanned {image_id - range_start + 1}/{range_count} "
                    f"(found {range_found} so far)"
                )

            time.sleep(DELAY)

        range_results[description] = {
            "start": range_start,
            "end": range_end,
            "scanned": range_count,
            "found": range_found,
        }

        print(f"  Range complete: {range_found} images found in {range_count} IDs")

    elapsed = time.time() - start_time

    # --- Summary ---
    print("\n" + "=" * 70)
    print("SCAN SUMMARY")
    print("=" * 70)
    print(f"Total IDs scanned:  {total_scanned}")
    print(f"Images found:       {len(found_images)}")
    print(f"Time elapsed:       {elapsed:.1f}s")
    print(f"Avg time per ID:    {elapsed / total_scanned * 1000:.0f}ms")

    if found_images:
        found_ids = [img["id"] for img in found_images]
        print(f"\nFound image IDs: {found_ids}")
        print(f"ID range of finds: {min(found_ids)} - {max(found_ids)}")

        print("\nPer-range breakdown:")
        for desc, info in range_results.items():
            if info["found"] > 0:
                print(
                    f"  {desc}: {info['found']} images "
                    f"(IDs {info['start']}-{info['end']})"
                )
    else:
        print("\nNo images found outside known range.")

    # --- Save results ---
    results_data = {
        "scan_date": datetime.now().isoformat(),
        "total_scanned": total_scanned,
        "total_found": len(found_images),
        "elapsed_seconds": round(elapsed, 1),
        "known_range": {"start": 37588, "end": 39056},
        "scan_ranges": range_results,
        "found_images": found_images,
    }

    RESULTS_FILE.write_text(
        json.dumps(results_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nResults saved to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
