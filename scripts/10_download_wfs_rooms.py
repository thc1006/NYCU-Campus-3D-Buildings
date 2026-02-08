#!/usr/bin/env python3
"""
Download ALL room vector data from ymspace GeoServer via WFS.
Also downloads hidden/backup layers from the gis workspace.

Output: data/ymmap_archive/wfs_data/
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
OUT_DIR = os.path.join(BASE_DIR, "data", "ymmap_archive", "wfs_data")
ROOMS_DIR = os.path.join(OUT_DIR, "rooms")
GIS_DIR = os.path.join(OUT_DIR, "gis_layers")

os.makedirs(ROOMS_DIR, exist_ok=True)
os.makedirs(GIS_DIR, exist_ok=True)

# Disable SSL verification (self-signed cert)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

GEOSERVER_BASE = "https://ymspace.ga.nycu.edu.tw:8080/geoserver"

# Room layers from WFS GetCapabilities
ROOM_LAYERS = [
    "A009_1F","A009_2F","A011_1F","A011_2F","A015_1F","A015_2F",
    "A017_1F","A017_2F","A019_1F","A019_2F","A021_1F","A021_2F",
    "A023_1F","A023_2F","A025_1F","A025_2F","A027_1F","A027_2F",
    "A029_1F","A029_2F","A031_1F","A031_2F","A033_1F","A033_2F",
    "A101_1F","A101_2F","A103_1F","A103_2F","A105_1F","A105_2F",
    "A107_1F","A107_2F","A109_1F","A109_2F","A111_1F","A111_2F",
    "A115_1F","A115_2F","A117_1F","A117_2F","A121_1F","A121_2F",
    "A123_1F","A123_2F","A125_1F","A125_2F","A127_1F","A127_2F",
    "A129_1F","A129_2F","A131_1F","A131_2F","A133_1F","A133_2F",
    "A143_1F","A143_2F","A143_3F",
    "B003_1F","B003_2F","B003_3F","B003_4F","B003_B1",
    "B004_1F","B004_2F","B004_B1",
    "B005_1F","B005_2F","B005_3F","B005_4F","B005_4M","B005_5F","B005_6F","B005_B1","B005_RF",
    "B009_1F","B009_2F","B009_3F","B009_RF",
    "B010_1F","B010_2F","B010_B1",
    "B011_1F","B011_2F","B011_3F","B011_4F","B011_5F","B011_B1","B011_RF",
    "B012_1F","B012_2F","B012_3F","B012_4F","B012_B1","B012_RF",
    "B013_1F","B013_2F","B013_3F","B013_4F","B013_5F","B013_6F","B013_B1","B013_RF",
    "B014_1F","B014_2F","B014_3F","B014_4F","B014_5F","B014_6F","B014_7F","B014_RF",
    "B015_1F","B015_2F",
    "B016_1F","B016_2F","B016_3F","B016_4F","B016_B1","B016_RF",
    "B017_1F","B017_2F","B017_3F","B017_4F","B017_B1","B017_RF",
    "B018_1F","B018_2F","B018_3F","B018_4F","B018_5F","B018_6F","B018_7F","B018_B1","B018_R1","B018_R2","B018_R3",
    "B019_1F","B019_2F","B019_3F","B019_4F","B019_5F","B019_6F","B019_7F","B019_B1","B019_R1","B019_R2",
    "B020_1F","B020_2F","B020_3F","B020_4F","B020_5F","B020_6F","B020_7F","B020_B1","B020_R1","B020_R2",
    "B021_1F","B021_2F","B021_3F","B021_4F","B021_5F","B021_RF",
    "B022_1F","B022_2F","B022_3F","B022_4F","B022_5F","B022_RF",
    "B023_1F","B023_2F",
    "B024_1F","B024_2F",
    "B025_1F","B025_2F",
    "B026_1F","B026_B1",
    "B027_1F","B027_2F",
    "B028_1F","B028_2F","B028_3F",
    "B029_1F","B029_2F","B029_3F","B029_4F","B029_5F",
    "B030_1F","B030_2F","B030_3F","B030_4F","B030_5F","B030_6F","B030_7F","B030_R1","B030_R2","B030_R3",
    "B031_1F","B031_2F","B031_3F","B031_4F","B031_5F","B031_6F","B031_7F","B031_R1","B031_R2","B031_R3",
    "B032_1F","B032_2F","B032_3F","B032_4F","B032_5F","B032_6F","B032_7F","B032_R1","B032_R2","B032_R3",
    "B033_1F","B033_2F","B033_3F","B033_4F","B033_5F","B033_6F","B033_7F","B033_B1","B033_R1","B033_R2","B033_R3",
    "B034_1F","B034_2F","B034_3F","B034_4F","B034_B1","B034_RF",
    "G002_1F","G002_2F","G002_3F","G002_4F","G002_B1","G002_RF",
    "G005_1F","G005_2F","G005_3F","G005_4F","G005_5F","G005_6F","G005_7F","G005_B1","G005_B2","G005_RF",
    "G007_1F","G007_2F",
    "G008_1F","G008_2F",
    "G009_1F","G009_2F",
    "G010_1F","G010_2F",
    "G011_1F","G011_2F",
    "G012_1F","G012_2F",
    "G013_1F","G013_2F",
    "G014_1F","G014_2F",
    "G015_1F","G015_2F",
    "G016_1F","G016_2F",
    "G017_1F","G017_2F",
    "G018_1F","G018_2F",
    "G019_1F","G019_2F",
    "G020_1F","G020_2F","G020_3F",
    "G021_1F",
    "G022_1F",
    "P003_10F","P003_1F","P003_2F","P003_3F","P003_4F","P003_5F","P003_6F","P003_7F","P003_8F","P003_9F","P003_B1","P003_B2","P003_RF",
    "P004_1F","P004_2F","P004_3F","P004_4F","P004_5F","P004_6F","P004_7F","P004_B1","P004_RF",
    "P005_1F","P005_2F","P005_3F","P005_4F","P005_5F","P005_6F","P005_7F","P005_8F","P005_9F","P005_B1","P005_B2","P005_RF",
    "P006_1F","P006_2F","P006_3F","P006_4F","P006_5F","P006_6F","P006_7F","P006_8F","P006_B1","P006_B2","P006_RF",
    "T001_1F",
    "Y001_1F","Y001_2F","Y001_3F","Y001_4F","Y001_5F","Y001_6F","Y001_B1","Y001_R1","Y001_R2",
    "Y002_1F","Y002_2F","Y002_3F","Y002_B1",
    "Y003_1F","Y003_2F","Y003_2M","Y003_3F","Y003_4F","Y003_RF",
    "Y004_1F","Y004_2F","Y004_3F","Y004_4F","Y004_RF",
    "Y005_1F","Y005_1M","Y005_2F","Y005_3F","Y005_B1","Y005_R1","Y005_RF",
    "Y006_1F","Y006_2F","Y006_3F","Y006_4F","Y006_5F","Y006_RF",
    "Y007_1F","Y007_2F","Y007_3F","Y007_B1","Y007_RF",
    "Y008_1F","Y008_2F","Y008_2M","Y008_3F","Y008_B1",
    "Y009_10F","Y009_1F","Y009_2F","Y009_3F","Y009_4F","Y009_B1","Y009_RF",
    "Y010_1F","Y010_2F","Y010_3F","Y010_4F","Y010_5F","Y010_6F","Y010_R1","Y010_R2",
    "Y011_1F","Y011_2F","Y011_RF",
    "Y012_1F","Y012_2F","Y012_3F",
]

# Hidden/backup GIS layers not in the public config
HIDDEN_GIS_LAYERS = [
    "bak_gis_building_geom_v1",
    "bak_gis_campus_v1",
    "bak_gis_campus_v2",
    "bak_gis_sidewalk_7_v1",
    "gis_auditorium",  # old version (v2 is current)
    "gis_barrierfreetoilet",  # old version
    "gis_block",
    "gis_elevator",
    "gis_emergencycall2",
    "gis_firestation",
    "gis_handicapparking",
    "gis_healthroom",
    "gis_monthlyparking",
    "gis_parking",
    "gis_telephonebooth",
    "gis_timerecorder",
    "gis_wheelchairramp",
    "gis_test",
    "gis_test202305016",
    "point_sample",
    "AED_test11",
    "AEDtest2",
    "system_test_gis_sidewalk",
    "test_c",
]


def fetch_wfs_geojson(workspace, layer_name):
    """Fetch GeoJSON features for a layer via WFS."""
    url = (
        f"{GEOSERVER_BASE}/{workspace}/wfs?"
        f"service=WFS&version=1.1.0&request=GetFeature"
        f"&typeName={workspace}:{layer_name}"
        f"&outputFormat=application/json"
        f"&maxFeatures=10000"
    )
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "url": url}
    except Exception as e:
        return {"error": str(e), "url": url}


def main():
    # Phase 1: Download hidden/backup GIS layers
    print(f"=== Phase 1: Hidden/backup GIS layers ({len(HIDDEN_GIS_LAYERS)} layers) ===")
    gis_stats = {}
    for i, layer in enumerate(HIDDEN_GIS_LAYERS):
        out_path = os.path.join(GIS_DIR, f"{layer}.json")
        if os.path.exists(out_path):
            print(f"  [{i+1}/{len(HIDDEN_GIS_LAYERS)}] {layer} — already exists, skipping")
            with open(out_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "features" in data:
                    gis_stats[layer] = len(data["features"])
            continue

        print(f"  [{i+1}/{len(HIDDEN_GIS_LAYERS)}] {layer} ...", end=" ", flush=True)
        data = fetch_wfs_geojson("gis", layer)
        if "error" in data:
            print(f"ERROR: {data['error']}")
            gis_stats[layer] = f"ERROR: {data['error']}"
        else:
            n = len(data.get("features", []))
            print(f"{n} features")
            gis_stats[layer] = n
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        time.sleep(0.3)

    print(f"\n--- GIS layer summary ---")
    for k, v in sorted(gis_stats.items()):
        print(f"  {k}: {v}")

    # Phase 2: Download room layers
    print(f"\n=== Phase 2: Room layers ({len(ROOM_LAYERS)} layers) ===")
    room_stats = {}
    total_rooms = 0
    errors = 0

    for i, layer in enumerate(ROOM_LAYERS):
        out_path = os.path.join(ROOMS_DIR, f"{layer}.json")
        if os.path.exists(out_path):
            with open(out_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "features" in data:
                    n = len(data["features"])
                    room_stats[layer] = n
                    total_rooms += n
            if (i + 1) % 50 == 0:
                print(f"  [{i+1}/{len(ROOM_LAYERS)}] (skipping existing) cumulative: {total_rooms} rooms")
            continue

        if (i + 1) % 10 == 0 or i == 0:
            print(f"  [{i+1}/{len(ROOM_LAYERS)}] {layer} ...", end=" ", flush=True)
        else:
            print(f"  [{i+1}/{len(ROOM_LAYERS)}] {layer} ...", end=" ", flush=True)

        data = fetch_wfs_geojson("gis_room", layer)
        if "error" in data:
            print(f"ERROR: {data['error']}")
            room_stats[layer] = f"ERROR: {data['error']}"
            errors += 1
        else:
            n = len(data.get("features", []))
            print(f"{n} rooms")
            room_stats[layer] = n
            total_rooms += n
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        time.sleep(0.2)

    print(f"\n=== SUMMARY ===")
    print(f"Room layers: {len(ROOM_LAYERS)}")
    print(f"Total rooms downloaded: {total_rooms}")
    print(f"Errors: {errors}")

    # Save summary
    summary = {
        "gis_hidden_layers": gis_stats,
        "room_layers": room_stats,
        "total_room_layers": len(ROOM_LAYERS),
        "total_rooms": total_rooms,
        "total_gis_hidden": len(HIDDEN_GIS_LAYERS),
    }
    with open(os.path.join(OUT_DIR, "download_summary.json"), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\nSummary saved to {os.path.join(OUT_DIR, 'download_summary.json')}")


if __name__ == "__main__":
    main()
