#!/usr/bin/env python3
"""
Download ALL POI (Point of Interest) photos from ymspace.ga.nycu.edu.tw.
Uses route.htm?action=loadImageByApKey to find photos for each POI layer,
then downloads actual images via uploadfiles.htm?action=listImg.

Output: data/ymmap_archive/poi_photos/{layer}/{apkey}_{index}.jpg
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
OUT_DIR = os.path.join(BASE_DIR, "data", "ymmap_archive", "poi_photos")
API_DATA_DIR = os.path.join(BASE_DIR, "data", "ymmap_archive", "api_data")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

API_BASE = "https://ymspace.ga.nycu.edu.tw/gisweb/public"
UPLOAD_URL = "https://ymspace.ga.nycu.edu.tw/gisweb/public/uploadfiles.htm"

# POI layers that might have photos (from dataTransmissionAPI dump)
POI_LAYERS = [
    "gis_aed", "gis_artwork", "gis_atm", "gis_auditorium2",
    "gis_barrierfreetoilet2", "gis_busstop", "gis_campusphotos",
    "gis_conveniencestore", "gis_elevator2", "gis_emergencycall",
    "gis_gateway", "gis_handicapparking2", "gis_postoffice",
    "gis_restaurant", "gis_securityoffice", "gis_sport", "gis_sport_p",
]


def fetch_json(url, timeout=15):
    """Fetch JSON from URL."""
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}


def fetch_image(image_id):
    """Fetch actual image bytes via uploadfiles."""
    url = f"{UPLOAD_URL}?action=listImg&q={image_id}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            ct = resp.headers.get('Content-Type', '')
            if 'image' in ct or 'octet' in ct:
                return resp.read()
            else:
                data = resp.read()
                if len(data) > 100 and data[:3] == b'\xff\xd8\xff':
                    return data
                return None
    except Exception:
        return None


def get_poi_image_urls(navi_key, ap_key):
    """Get image URLs for a POI via loadImageByApKey."""
    url = f"{API_BASE}/route.htm?action=loadImageByApKey&naviKey={navi_key}&apKey={ap_key}"
    result = fetch_json(url)
    if result and result.get('data'):
        ids = []
        for img_url in result['data']:
            if 'q=' in img_url:
                ids.append(int(img_url.split('q=')[1]))
        return ids
    return []


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Load dataTransmissionAPI dump to get ap_key values for each layer
    dump_path = os.path.join(API_DATA_DIR, "dataTransmissionAPI_dump.json")
    with open(dump_path, 'r', encoding='utf-8') as f:
        dump_data = json.load(f)

    all_results = {}
    total_photos = 0
    total_downloaded = 0
    total_bytes = 0

    for layer in POI_LAYERS:
        if layer not in dump_data:
            print(f"\n--- {layer}: not in dump data, skipping ---")
            continue

        records = dump_data[layer]
        if not records:
            continue

        # Find ap_key field
        ap_keys = []
        for rec in records:
            ak = rec.get('ap_key')
            if ak is not None and ak != -1 and ak != '':
                ap_keys.append(ak)

        if not ap_keys:
            # Some layers don't use ap_key but have gid
            for rec in records:
                gid = rec.get('gid')
                if gid is not None:
                    ap_keys.append(gid)

        if not ap_keys:
            print(f"\n--- {layer}: no ap_keys found, skipping ---")
            continue

        layer_dir = os.path.join(OUT_DIR, layer)
        os.makedirs(layer_dir, exist_ok=True)

        layer_results = {}
        layer_photos = 0

        print(f"\n=== {layer} ({len(ap_keys)} POIs) ===")

        for i, ak in enumerate(ap_keys):
            image_ids = get_poi_image_urls(layer, ak)
            if not image_ids:
                continue

            layer_results[str(ak)] = image_ids
            print(f"  [{i+1}/{len(ap_keys)}] ap_key={ak}: {len(image_ids)} photos (IDs: {min(image_ids)}-{max(image_ids)})")

            # Download each photo
            for j, img_id in enumerate(image_ids):
                out_path = os.path.join(layer_dir, f"{ak}_{j}.jpg")
                if os.path.exists(out_path):
                    layer_photos += 1
                    continue

                img_data = fetch_image(img_id)
                if img_data:
                    with open(out_path, 'wb') as f:
                        f.write(img_data)
                    layer_photos += 1
                    total_downloaded += 1
                    total_bytes += len(img_data)
                    time.sleep(0.1)
                else:
                    print(f"    WARN: failed to download image {img_id}")

            time.sleep(0.2)

        total_photos += layer_photos
        all_results[layer] = layer_results
        print(f"  => {layer}: {layer_photos} photos downloaded")

    # Save results
    results_path = os.path.join(OUT_DIR, "poi_photo_index.json")
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n=== SUMMARY ===")
    print(f"Layers checked: {len(POI_LAYERS)}")
    print(f"Total POI photos found: {total_photos}")
    print(f"Newly downloaded: {total_downloaded}")
    print(f"Total bytes: {total_bytes / 1024 / 1024:.1f} MB")
    print(f"Index saved to: {results_path}")


if __name__ == "__main__":
    main()
