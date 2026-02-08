"""
Download land parcel (地籍), bus route, sidewalk, campus boundary,
and block data from NYCU GIS WFS server.

Saves all results to data/ymmap_archive/wfs_data/ subdirectories.
"""

import json
import os
import ssl
import time
import urllib.request

# --- SSL context (skip certificate verification) ---
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# --- Base paths ---
BASE_DIR = r"C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive"
WFS_BASE = "https://ymspace.ga.nycu.edu.tw:8080/geoserver/gis/wfs"

# --- Layer definitions ---
PARCEL_LAYERS = [
    ("gis_parcel0821line", "福林段二小段_線", 5214),
    ("gis_parcel0821point", "福林段二小段_文字/點", 875),
    ("gis_parcel0886line", "振興段四小段_線", 4227),
    ("gis_parcel0886text", "振興段四小段_文字", 898),
    ("gis_parcel0893line", "立農段二小段_線", 2090),
    ("gis_parcel0893text", "立農段二小段_文字", 512),
    ("gis_parcel0981line", "崇仰段三小段_線", 3803),
    ("gis_parcel0981point", "崇仰段三小段_文字/點", 625),
]

BUS_LAYERS = [
    ("gis_busroutes_1", "559公車"),
    ("gis_busroutes_2", "綠線公車"),
    ("gis_busroutes_3", "紅線公車"),
]

SIDEWALK_LAYERS = [
    ("gss_sidewalk", "全校步道網"),
]

CAMPUS_LAYERS = [
    ("gis_campus", "校區邊界"),
    ("gis_block", "校園區塊"),
    ("gis_building_geom", "建物多邊形"),
    ("bak_gis_building_geom_v1", "舊版建物多邊形"),
]


def build_wfs_url(layer_name, max_features=10000):
    """Build a WFS GetFeature URL for the given layer."""
    params = (
        f"service=WFS&version=1.1.0&request=GetFeature"
        f"&typeName=gis:{layer_name}"
        f"&outputFormat=application/json"
        f"&maxFeatures={max_features}"
    )
    return f"{WFS_BASE}?{params}"


def download_layer(layer_name, output_path, description="", max_features=10000):
    """
    Download a single WFS layer and save as GeoJSON.

    Returns a dict with download statistics or error info.
    """
    url = build_wfs_url(layer_name, max_features)
    result = {
        "layer": layer_name,
        "description": description,
        "url": url,
        "output_path": output_path,
        "success": False,
        "feature_count": 0,
        "file_size_bytes": 0,
        "file_size_display": "",
        "error": None,
    }

    print(f"\n{'='*70}")
    print(f"Downloading: {layer_name} ({description})")
    print(f"URL: {url[:100]}...")

    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "NYCU-GIS-Downloader/1.0")

        start_time = time.time()
        with urllib.request.urlopen(req, context=ctx, timeout=120) as response:
            data = response.read()
            elapsed = time.time() - start_time

        # Parse JSON to verify and count features
        geojson = json.loads(data.decode("utf-8"))

        feature_count = 0
        if "features" in geojson:
            feature_count = len(geojson["features"])
        elif "totalFeatures" in geojson:
            feature_count = geojson["totalFeatures"]

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False)

        file_size = os.path.getsize(output_path)
        size_display = format_size(file_size)

        result["success"] = True
        result["feature_count"] = feature_count
        result["file_size_bytes"] = file_size
        result["file_size_display"] = size_display

        print(f"  Status: SUCCESS")
        print(f"  Features: {feature_count}")
        print(f"  File size: {size_display}")
        print(f"  Download time: {elapsed:.1f}s")
        print(f"  Saved to: {output_path}")

    except urllib.error.HTTPError as e:
        error_msg = f"HTTP {e.code}: {e.reason}"
        result["error"] = error_msg
        print(f"  Status: FAILED - {error_msg}")
        try:
            body = e.read().decode("utf-8", errors="replace")[:500]
            print(f"  Response body: {body}")
        except Exception:
            pass

    except urllib.error.URLError as e:
        error_msg = f"URL Error: {e.reason}"
        result["error"] = error_msg
        print(f"  Status: FAILED - {error_msg}")

    except json.JSONDecodeError as e:
        error_msg = f"JSON parse error: {e}"
        result["error"] = error_msg
        print(f"  Status: FAILED - {error_msg}")
        # Save raw data anyway for debugging
        raw_path = output_path + ".raw"
        os.makedirs(os.path.dirname(raw_path), exist_ok=True)
        with open(raw_path, "wb") as f:
            f.write(data)
        print(f"  Raw data saved to: {raw_path}")

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        result["error"] = error_msg
        print(f"  Status: FAILED - {error_msg}")

    return result


def format_size(size_bytes):
    """Format byte size into human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def main():
    all_results = []

    # ---------------------------------------------------------------
    # 1. Download parcel layers
    # ---------------------------------------------------------------
    print("\n" + "#" * 70)
    print("# SECTION 1: Land Parcel Layers (地籍圖層)")
    print("#" * 70)

    parcel_dir = os.path.join(BASE_DIR, "wfs_data", "parcel")
    os.makedirs(parcel_dir, exist_ok=True)

    for layer_name, description, expected_count in PARCEL_LAYERS:
        output_path = os.path.join(parcel_dir, f"{layer_name}.json")
        result = download_layer(layer_name, output_path, description)
        result["expected_count"] = expected_count
        all_results.append(result)
        time.sleep(0.5)  # Be polite to the server

    # ---------------------------------------------------------------
    # 2. Download bus route layers
    # ---------------------------------------------------------------
    print("\n" + "#" * 70)
    print("# SECTION 2: Bus Route Layers (公車路線圖層)")
    print("#" * 70)

    bus_dir = os.path.join(BASE_DIR, "wfs_data", "bus_routes")
    os.makedirs(bus_dir, exist_ok=True)

    for layer_name, description in BUS_LAYERS:
        output_path = os.path.join(bus_dir, f"{layer_name}.json")
        result = download_layer(layer_name, output_path, description)
        all_results.append(result)
        time.sleep(0.5)

    # ---------------------------------------------------------------
    # 3. Download sidewalk network
    # ---------------------------------------------------------------
    print("\n" + "#" * 70)
    print("# SECTION 3: Campus Sidewalk Network (全校步道網)")
    print("#" * 70)

    sidewalk_dir = os.path.join(BASE_DIR, "wfs_data", "sidewalk")
    os.makedirs(sidewalk_dir, exist_ok=True)

    for layer_name, description in SIDEWALK_LAYERS:
        output_path = os.path.join(sidewalk_dir, f"{layer_name}.json")
        result = download_layer(layer_name, output_path, description)
        all_results.append(result)
        time.sleep(0.5)

    # ---------------------------------------------------------------
    # 4. Download campus boundary and block data
    # ---------------------------------------------------------------
    print("\n" + "#" * 70)
    print("# SECTION 4: Campus Boundary & Block Data (校區邊界/區塊/建物)")
    print("#" * 70)

    campus_dir = os.path.join(BASE_DIR, "wfs_data", "campus")
    os.makedirs(campus_dir, exist_ok=True)

    for layer_name, description in CAMPUS_LAYERS:
        output_path = os.path.join(campus_dir, f"{layer_name}.json")
        result = download_layer(layer_name, output_path, description)
        all_results.append(result)
        time.sleep(0.5)

    # ---------------------------------------------------------------
    # 5. Print summary statistics
    # ---------------------------------------------------------------
    print("\n" + "#" * 70)
    print("# DOWNLOAD SUMMARY")
    print("#" * 70)

    success_count = sum(1 for r in all_results if r["success"])
    fail_count = sum(1 for r in all_results if not r["success"])
    total_features = sum(r["feature_count"] for r in all_results)
    total_bytes = sum(r["file_size_bytes"] for r in all_results)

    print(f"\nTotal layers attempted: {len(all_results)}")
    print(f"Successful downloads:   {success_count}")
    print(f"Failed downloads:       {fail_count}")
    print(f"Total features:         {total_features:,}")
    print(f"Total data size:        {format_size(total_bytes)}")

    print(f"\n{'Layer':<35} {'Status':<10} {'Features':>10} {'Size':>12} {'Description'}")
    print("-" * 100)

    for r in all_results:
        status = "OK" if r["success"] else "FAILED"
        features = str(r["feature_count"]) if r["success"] else "-"
        size = r["file_size_display"] if r["success"] else "-"
        desc = r.get("description", "")

        expected = r.get("expected_count")
        if expected and r["success"]:
            match_str = " (match)" if r["feature_count"] == expected else f" (expected {expected})"
        else:
            match_str = ""

        print(f"{r['layer']:<35} {status:<10} {features:>10} {size:>12} {desc}{match_str}")

    if fail_count > 0:
        print(f"\nFailed layers:")
        for r in all_results:
            if not r["success"]:
                print(f"  - {r['layer']}: {r['error']}")

    # Save summary JSON
    summary_path = os.path.join(BASE_DIR, "wfs_data", "parcel_bus_download_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "download_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_layers": len(all_results),
                "successful": success_count,
                "failed": fail_count,
                "total_features": total_features,
                "total_bytes": total_bytes,
                "layers": all_results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"\nSummary saved to: {summary_path}")


if __name__ == "__main__":
    main()
