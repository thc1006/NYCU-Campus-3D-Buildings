#!/usr/bin/env python3
"""
Download ALL layer data via dataTransmissionAPI (returns WGS84 WKT geometry).
Tests each public and hidden GIS layer as a target.

Output: data/ymmap_archive/api_data/dataTransmissionAPI_dump.json
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

API_URL = "https://ymspace.ga.nycu.edu.tw/gisweb/public/route.htm"

# All layer names from both public config and GeoServer
ALL_LAYERS = [
    # Public config layers
    "gis_aed", "gis_artwork", "gis_atm", "gis_auditorium2",
    "gis_barrierfreetoilet2", "gis_block", "gis_building",
    "gis_building_geom", "gis_busroutes_1", "gis_busroutes_2",
    "gis_busroutes_3", "gis_busstop", "gis_campus",
    "gis_campusphotos", "gis_conveniencestore", "gis_elevator2",
    "gis_emergencycall", "gis_gateway", "gis_handicapparking2",
    "gis_monthlyparking", "gis_parcel0821line", "gis_parcel0821point",
    "gis_parcel0886line", "gis_parcel0886text",
    "gis_parcel0893line", "gis_parcel0893text",
    "gis_parcel0981line", "gis_parcel0981point",
    "gis_postoffice", "gis_restaurant", "gis_securityoffice",
    "gis_sidewalk_1", "gis_sidewalk_2", "gis_sidewalk_3",
    "gis_sidewalk_4", "gis_sidewalk_5", "gis_sidewalk_6",
    "gis_sidewalk_7", "gis_sidewalk_8", "gis_sidewalk_9",
    "gis_sidewalk_10", "gis_sidewalk_11", "gis_sidewalk_12",
    "gis_sidewalk_13", "gis_sidewalk_14", "gis_sidewalk_15",
    "gis_sport", "gis_sport_p", "gss_sidewalk", "toilet",
    # Hidden/backup layers
    "gis_auditorium", "gis_barrierfreetoilet",
    "gis_elevator", "gis_emergencycall2",
    "gis_firestation", "gis_handicapparking",
    "gis_healthroom", "gis_parking",
    "gis_telephonebooth", "gis_timerecorder",
    "gis_wheelchairramp",
    "bak_gis_building_geom_v1", "bak_gis_campus_v1",
    "bak_gis_campus_v2", "bak_gis_sidewalk_7_v1",
    "test_c",
]


def fetch_data(target):
    """Fetch all records for a target via dataTransmissionAPI."""
    query = json.dumps({"target": target, "action": "find", "filter": []})
    url = f"{API_URL}?action=dataTransmissionAPI&query={urllib.request.quote(query)}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}


def main():
    results = {}
    stats = {}

    for i, layer in enumerate(ALL_LAYERS):
        print(f"  [{i+1}/{len(ALL_LAYERS)}] {layer} ...", end=" ", flush=True)
        data = fetch_data(layer)

        if "error" in data:
            print(f"ERROR: {data['error']}")
            stats[layer] = f"ERROR: {data['error']}"
        elif "message" in data:
            print(f"DENIED: {data['message'][:80]}")
            stats[layer] = "DENIED"
        elif data.get("success") and data.get("data"):
            records = data["data"]
            if isinstance(records, list):
                n = len(records)
                print(f"{n} records")
                stats[layer] = n
                results[layer] = records
            else:
                print(f"unexpected: {str(data)[:100]}")
                stats[layer] = "unexpected"
        else:
            print(f"empty or failed: {str(data)[:100]}")
            stats[layer] = 0

        time.sleep(0.3)

    # Save all results
    out_path = os.path.join(OUT_DIR, "dataTransmissionAPI_dump.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Save stats
    stats_path = os.path.join(OUT_DIR, "dataTransmissionAPI_stats.json")
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    total_records = sum(v for v in stats.values() if isinstance(v, int))
    accessible = sum(1 for v in stats.values() if isinstance(v, int) and v > 0)
    denied = sum(1 for v in stats.values() if v == "DENIED")

    print(f"\n=== SUMMARY ===")
    print(f"Layers tested: {len(ALL_LAYERS)}")
    print(f"Accessible: {accessible}")
    print(f"Denied: {denied}")
    print(f"Total records: {total_records}")
    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()
