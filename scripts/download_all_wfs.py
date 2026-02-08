"""
Download ALL WFS layers from NYCU Yangming campus GeoServer as GeoJSON.

This script:
1. Fetches WFS GetCapabilities to enumerate all layers
2. Downloads each layer as GeoJSON with maxFeatures=100000
3. Saves to organized directory structure: wfs_geojson/{workspace}/{layername}.json
4. Produces a summary JSON with layer stats
"""

import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
import urllib3

# Suppress SSL warnings (self-signed cert on GeoServer)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://ymspace.ga.nycu.edu.tw:8080/geoserver"
WFS_URL = f"{BASE_URL}/wfs"
OUTPUT_DIR = Path(r"C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive\wfs_geojson")
SUMMARY_PATH = OUTPUT_DIR / "download_summary.json"

# Request timeout in seconds
TIMEOUT = 120

# Priority keywords for non-room infrastructure layers
PRIORITY_KEYWORDS = [
    "building", "campus", "block", "sidewalk", "road", "parking",
    "tree", "utility", "pipe", "electric", "water", "drainage",
    "fire", "hydrant", "landscape", "fence", "gate", "elevator",
    "stair", "toilet", "entrance", "door", "wall", "column",
    "floor", "roof", "bridge", "tunnel", "cable", "manhole",
    "lamp", "light", "sign", "bench", "garden", "pond",
]

# Priority exact layer names (known important layers)
PRIORITY_LAYERS = [
    "gis:gis_building_geom",
    "gis:gis_campus",
    "gis:gis_block",
    "gss:gss_sidewalk",
]


def get_capabilities():
    """Fetch and parse WFS GetCapabilities to extract all layer names."""
    url = f"{WFS_URL}?service=WFS&version=1.1.0&request=GetCapabilities"
    print(f"Fetching GetCapabilities from: {url}")
    resp = requests.get(url, verify=False, timeout=TIMEOUT)
    resp.raise_for_status()

    # Save raw capabilities XML for reference
    caps_path = OUTPUT_DIR / "_capabilities.xml"
    caps_path.parent.mkdir(parents=True, exist_ok=True)
    caps_path.write_bytes(resp.content)
    print(f"Saved capabilities XML to: {caps_path} ({len(resp.content)} bytes)")

    # Parse XML - handle namespaces
    root = ET.fromstring(resp.content)

    # Extract all namespaces
    namespaces = {}
    for event, elem in ET.iterparse(
        caps_path, events=["start-ns"]
    ):
        ns_prefix, ns_uri = elem
        if ns_prefix:
            namespaces[ns_prefix] = ns_uri

    # Common WFS namespaces
    ns = {
        "wfs": "http://www.opengis.net/wfs",
        "ows": "http://www.opengis.net/ows",
    }
    # Try to find the actual namespaces from the document
    for prefix, uri in namespaces.items():
        ns[prefix] = uri

    # Find all FeatureType elements
    layers = []

    # Try multiple namespace patterns
    feature_types = root.findall(".//{http://www.opengis.net/wfs}FeatureType")
    if not feature_types:
        feature_types = root.findall(".//{http://www.opengis.net/wfs/2.0}FeatureType")
    if not feature_types:
        # Try without namespace
        feature_types = root.findall(".//FeatureType")

    for ft in feature_types:
        # Try to get Name element with various namespaces
        name_elem = ft.find("{http://www.opengis.net/wfs}Name")
        if name_elem is None:
            name_elem = ft.find("{http://www.opengis.net/wfs/2.0}Name")
        if name_elem is None:
            name_elem = ft.find("Name")

        if name_elem is not None and name_elem.text:
            layers.append(name_elem.text.strip())

    print(f"Found {len(layers)} layers in GetCapabilities")
    return layers


def parse_layer_name(full_name):
    """Parse 'workspace:layername' into (workspace, layername)."""
    if ":" in full_name:
        parts = full_name.split(":", 1)
        return parts[0], parts[1]
    return "default", full_name


def is_priority_layer(full_name):
    """Check if a layer is a priority (non-room infrastructure) layer."""
    if full_name in PRIORITY_LAYERS:
        return True
    lower = full_name.lower()
    for kw in PRIORITY_KEYWORDS:
        if kw in lower:
            return True
    return False


def download_layer(layer_name, output_path):
    """Download a single WFS layer as GeoJSON.

    Returns:
        dict with layer stats, or None if failed.
    """
    url = (
        f"{WFS_URL}?service=WFS&version=1.1.0&request=GetFeature"
        f"&typeName={layer_name}&outputFormat=application/json&maxFeatures=100000"
    )

    try:
        resp = requests.get(url, verify=False, timeout=TIMEOUT)
        resp.raise_for_status()

        data = resp.json()
        features = data.get("features", [])
        feature_count = len(features)

        # Determine geometry type from first feature
        geometry_type = None
        if features:
            geom = features[0].get("geometry")
            if geom:
                geometry_type = geom.get("type")

        # Save GeoJSON
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

        file_size = output_path.stat().st_size

        return {
            "layer_name": layer_name,
            "feature_count": feature_count,
            "file_size_bytes": file_size,
            "geometry_type": geometry_type,
            "status": "success",
        }

    except requests.exceptions.Timeout:
        print(f"  TIMEOUT for {layer_name}")
        return {
            "layer_name": layer_name,
            "feature_count": 0,
            "file_size_bytes": 0,
            "geometry_type": None,
            "status": "timeout",
        }
    except requests.exceptions.RequestException as e:
        print(f"  HTTP ERROR for {layer_name}: {e}")
        return {
            "layer_name": layer_name,
            "feature_count": 0,
            "file_size_bytes": 0,
            "geometry_type": None,
            "status": f"http_error: {e}",
        }
    except json.JSONDecodeError as e:
        # Might be XML error response - save raw content
        error_path = output_path.with_suffix(".error.txt")
        error_path.parent.mkdir(parents=True, exist_ok=True)
        error_path.write_text(resp.text[:2000], encoding="utf-8")
        print(f"  JSON PARSE ERROR for {layer_name}: {e}")
        return {
            "layer_name": layer_name,
            "feature_count": 0,
            "file_size_bytes": 0,
            "geometry_type": None,
            "status": f"json_error: {e}",
        }
    except Exception as e:
        print(f"  UNEXPECTED ERROR for {layer_name}: {e}")
        return {
            "layer_name": layer_name,
            "feature_count": 0,
            "file_size_bytes": 0,
            "geometry_type": None,
            "status": f"error: {e}",
        }


def main():
    """Main download orchestrator."""
    print("=" * 80)
    print("NYCU Yangming Campus GeoServer - WFS Full Layer Download")
    print("=" * 80)

    # Step 1: Get all layer names
    layers = get_capabilities()
    if not layers:
        print("ERROR: No layers found. Check the GetCapabilities response.")
        sys.exit(1)

    # Step 2: Sort layers - priority layers first, then alphabetical
    priority = [l for l in layers if is_priority_layer(l)]
    non_priority = [l for l in layers if not is_priority_layer(l)]

    # Put exact priority layers at the very top
    exact_priority = [l for l in layers if l in PRIORITY_LAYERS]
    keyword_priority = [l for l in priority if l not in PRIORITY_LAYERS]

    sorted_layers = exact_priority + sorted(keyword_priority) + sorted(non_priority)
    # Remove duplicates while preserving order
    seen = set()
    ordered_layers = []
    for l in sorted_layers:
        if l not in seen:
            seen.add(l)
            ordered_layers.append(l)

    print(f"\nTotal layers: {len(ordered_layers)}")
    print(f"Priority layers: {len(priority)}")
    print(f"Non-priority layers: {len(non_priority)}")
    print()

    # Step 3: Check for already-downloaded layers (resume support)
    already_downloaded = set()
    if SUMMARY_PATH.exists():
        try:
            existing_summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
            for entry in existing_summary:
                if entry.get("status") == "success":
                    already_downloaded.add(entry["layer_name"])
            print(f"Found {len(already_downloaded)} already-downloaded layers (resume mode)")
        except Exception:
            pass

    # Step 4: Download each layer
    results = []
    # Load existing results for resume
    if SUMMARY_PATH.exists():
        try:
            results = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
        except Exception:
            results = []

    existing_layer_names = {r["layer_name"] for r in results}

    total = len(ordered_layers)
    success_count = len(already_downloaded)
    fail_count = 0
    skip_count = 0
    total_bytes = sum(r.get("file_size_bytes", 0) for r in results)
    total_features = sum(r.get("feature_count", 0) for r in results)

    start_time = time.time()

    for i, layer_name in enumerate(ordered_layers, 1):
        workspace, name = parse_layer_name(layer_name)
        output_path = OUTPUT_DIR / workspace / f"{name}.json"

        # Skip if already downloaded successfully
        if layer_name in already_downloaded and output_path.exists():
            skip_count += 1
            if skip_count <= 5 or skip_count % 50 == 0:
                print(f"[{i}/{total}] SKIP (already downloaded): {layer_name}")
            continue

        elapsed = time.time() - start_time
        rate = (i - skip_count) / max(elapsed, 1) if (i - skip_count) > 0 else 0
        remaining = (total - i) / max(rate, 0.01)

        is_prio = "PRIORITY" if is_priority_layer(layer_name) else ""
        print(
            f"[{i}/{total}] {is_prio} Downloading: {layer_name} "
            f"(elapsed: {elapsed:.0f}s, est remaining: {remaining:.0f}s)"
        )

        result = download_layer(layer_name, output_path)

        if result:
            if result["status"] == "success":
                success_count += 1
                total_bytes += result["file_size_bytes"]
                total_features += result["feature_count"]
                print(
                    f"         -> {result['feature_count']} features, "
                    f"{result['file_size_bytes']:,} bytes, "
                    f"geometry: {result['geometry_type']}"
                )
            else:
                fail_count += 1
                print(f"         -> FAILED: {result['status']}")

            # Update or append result
            if layer_name in existing_layer_names:
                for idx, r in enumerate(results):
                    if r["layer_name"] == layer_name:
                        results[idx] = result
                        break
            else:
                results.append(result)
                existing_layer_names.add(layer_name)

        # Save summary periodically (every 25 layers)
        if i % 25 == 0:
            SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

        # Small delay to be polite to the server
        time.sleep(0.1)

    # Step 5: Save final summary
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Step 6: Print final stats
    elapsed = time.time() - start_time
    print()
    print("=" * 80)
    print("DOWNLOAD COMPLETE")
    print("=" * 80)
    print(f"Total layers found:    {total}")
    print(f"Successfully downloaded: {success_count}")
    print(f"Failed:                {fail_count}")
    print(f"Skipped (cached):      {skip_count}")
    print(f"Total features:        {total_features:,}")
    print(f"Total data size:       {total_bytes:,} bytes ({total_bytes / 1024 / 1024:.1f} MB)")
    print(f"Time elapsed:          {elapsed:.1f}s")
    print(f"Summary saved to:      {SUMMARY_PATH}")

    # Print workspace breakdown
    workspace_stats = {}
    for r in results:
        ws, _ = parse_layer_name(r["layer_name"])
        if ws not in workspace_stats:
            workspace_stats[ws] = {"count": 0, "features": 0, "bytes": 0}
        workspace_stats[ws]["count"] += 1
        workspace_stats[ws]["features"] += r.get("feature_count", 0)
        workspace_stats[ws]["bytes"] += r.get("file_size_bytes", 0)

    print("\nWorkspace breakdown:")
    for ws in sorted(workspace_stats.keys()):
        s = workspace_stats[ws]
        print(
            f"  {ws}: {s['count']} layers, "
            f"{s['features']:,} features, "
            f"{s['bytes']:,} bytes"
        )


if __name__ == "__main__":
    main()
