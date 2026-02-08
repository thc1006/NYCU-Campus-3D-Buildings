"""
WMS GetFeatureInfo Extraction Script for ymspace.ga.nycu.edu.tw GeoServer
Extracts attribute data from all GIS layers using WMS GetFeatureInfo requests.
Also attempts alternative export formats (PDF, SVG) for key layers.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Fix encoding for Windows
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Configuration
WMS_URL = "https://ymspace.ga.nycu.edu.tw:8080/geoserver/wms"
WFS_URL = "https://ymspace.ga.nycu.edu.tw:8080/geoserver/wfs"
OUTPUT_DIR = Path(
    r"C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive\wms_featureinfo"
)
WFS_DIR = Path(
    r"C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive\wfs_all_gis_layers"
)
DELAY = 0.2
TIMEOUT = 30

# Campus BBOX in EPSG:3826 (TWD97/TM2 zone 121)
# Covers entire Yangming campus area
CAMPUS_BBOX = {
    "minx": 301286,
    "miny": 2776527,
    "maxx": 303865,
    "maxy": 2780020,
}

# All 74 known GIS layers to query
ALL_LAYERS = [
    # Core campus layers
    "gis:gis_building_geom",
    "gis:gis_building",
    "gis:gis_campus",
    "gis:gis_block",
    # POI layers
    "gis:gis_aed",
    "gis:gis_atm",
    "gis:gis_artwork",
    "gis:gis_busstop",
    "gis:gis_parking",
    "gis:gis_restaurant",
    "gis:gis_sport",
    "gis:gis_sport_p",
    "gis:gis_campusphotos",
    "gis:gis_conveniencestore",
    "gis:gis_firestation",
    "gis:gis_gateway",
    "gis:gis_healthroom",
    "gis:gis_postoffice",
    "gis:gis_securityoffice",
    "gis:gis_telephonebooth",
    "gis:gis_timerecorder",
    # Accessibility layers (campus 1 and campus 2)
    "gis:gis_elevator",
    "gis:gis_elevator2",
    "gis:gis_auditorium",
    "gis:gis_auditorium2",
    "gis:gis_barrierfreetoilet",
    "gis:gis_barrierfreetoilet2",
    "gis:gis_emergencycall",
    "gis:gis_emergencycall2",
    "gis:gis_handicapparking",
    "gis:gis_handicapparking2",
    "gis:gis_wheelchairramp",
    "gis:gis_wheelchairramp2",
    # Parking
    "gis:gis_monthlyparking",
    # Bus routes
    "gis:gis_busroutes_1",
    "gis:gis_busroutes_2",
    "gis:gis_busroutes_3",
    # Parcel layers
    "gis:gis_parcel0821line",
    "gis:gis_parcel0821point",
    "gis:gis_parcel0886line",
    "gis:gis_parcel0886text",
    "gis:gis_parcel0893line",
    "gis:gis_parcel0893text",
    "gis:gis_parcel0981line",
    "gis:gis_parcel0981point",
    # Sidewalk layers
    "gis:gis_sidewalk_1",
    "gis:gis_sidewalk_2",
    "gis:gis_sidewalk_3",
    "gis:gis_sidewalk_4",
    "gis:gis_sidewalk_5",
    "gis:gis_sidewalk_6",
    "gis:gis_sidewalk_7",
    "gis:gis_sidewalk_8",
    "gis:gis_sidewalk_9",
    "gis:gis_sidewalk_10",
    "gis:gis_sidewalk_11",
    "gis:gis_sidewalk_12",
    "gis:gis_sidewalk_13",
    "gis:gis_sidewalk_14",
    "gis:gis_sidewalk_15",
    "gis:gss_sidewalk",
    # Toilet
    "gis:toilet",
    # Backup layers
    "gis:bak_gis_building_geom_v1",
    "gis:bak_gis_campus_v1",
    "gis:bak_gis_campus_v2",
    "gis:bak_gis_sidewalk_7_v1",
    "gis:bak_gss_sidewalk_v1",
    # Test layers
    "gis:AED_test11",
    "gis:gis_test202305016",
    "gis:point_sample",
    "gis:system_test_gis_sidewalk",
    "gis:test_c",
]

# Key layers for alternative format exports
KEY_LAYERS = [
    "gis:gis_building_geom",
    "gis:gis_campus",
    "gis:gis_parking",
    "gis:gis_building",
    "gis:gis_block",
    "gis:gis_aed",
]

# Grid of query points (X, Y pixel positions in 256x256 image)
# Spread across the image to maximize feature hits
QUERY_GRID = [
    (128, 128),  # center
    (64, 64),    # top-left quadrant
    (192, 64),   # top-right quadrant
    (64, 192),   # bottom-left quadrant
    (192, 192),  # bottom-right quadrant
    (32, 32),
    (224, 32),
    (32, 224),
    (224, 224),
    (128, 32),   # top center
    (128, 224),  # bottom center
    (32, 128),   # left center
    (224, 128),  # right center
    (96, 96),
    (160, 96),
    (96, 160),
    (160, 160),
]


def get_session():
    """Create a requests session with retry logic."""
    session = requests.Session()
    session.verify = False
    adapter = requests.adapters.HTTPAdapter(max_retries=3)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_featureinfo_single(session, layer, x, y, bbox_str, srs="EPSG:3826",
                           width=256, height=256, feature_count=100):
    """Make a single GetFeatureInfo request."""
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetFeatureInfo",
        "LAYERS": layer,
        "QUERY_LAYERS": layer,
        "INFO_FORMAT": "application/json",
        "FEATURE_COUNT": str(feature_count),
        "SRS": srs,
        "BBOX": bbox_str,
        "WIDTH": str(width),
        "HEIGHT": str(height),
        "X": str(x),
        "Y": str(y),
    }
    try:
        resp = session.get(WMS_URL, params=params, timeout=TIMEOUT)
        if resp.status_code == 200:
            content_type = resp.headers.get("Content-Type", "")
            if "json" in content_type:
                return resp.json()
            else:
                return {"error": f"Non-JSON response: {content_type}", "text": resp.text[:500]}
        else:
            return {"error": f"HTTP {resp.status_code}", "text": resp.text[:500]}
    except Exception as e:
        return {"error": str(e)}


def get_featureinfo_grid(session, layer, feature_count=100):
    """Query a layer with multiple grid points to maximize feature coverage."""
    bbox_str = f"{CAMPUS_BBOX['minx']},{CAMPUS_BBOX['miny']},{CAMPUS_BBOX['maxx']},{CAMPUS_BBOX['maxy']}"

    all_features = {}
    feature_ids_seen = set()
    total_queries = 0
    successful_queries = 0

    for x, y in QUERY_GRID:
        result = get_featureinfo_single(session, layer, x, y, bbox_str,
                                         feature_count=feature_count)
        total_queries += 1
        time.sleep(DELAY)

        if isinstance(result, dict) and "features" in result:
            for feat in result["features"]:
                # Deduplicate by feature ID or properties hash
                feat_id = feat.get("id", "")
                props = feat.get("properties", {})
                # Create a unique key from gid or properties
                gid = props.get("gid", "")
                unique_key = feat_id or f"gid_{gid}" or json.dumps(props, sort_keys=True)

                if unique_key not in feature_ids_seen:
                    feature_ids_seen.add(unique_key)
                    all_features[unique_key] = feat
            if result["features"]:
                successful_queries += 1

    # Also try sub-regions (split BBOX into 4 quadrants)
    dx = (CAMPUS_BBOX["maxx"] - CAMPUS_BBOX["minx"]) / 2
    dy = (CAMPUS_BBOX["maxy"] - CAMPUS_BBOX["miny"]) / 2

    quadrants = [
        (CAMPUS_BBOX["minx"], CAMPUS_BBOX["miny"],
         CAMPUS_BBOX["minx"] + dx, CAMPUS_BBOX["miny"] + dy),
        (CAMPUS_BBOX["minx"] + dx, CAMPUS_BBOX["miny"],
         CAMPUS_BBOX["maxx"], CAMPUS_BBOX["miny"] + dy),
        (CAMPUS_BBOX["minx"], CAMPUS_BBOX["miny"] + dy,
         CAMPUS_BBOX["minx"] + dx, CAMPUS_BBOX["maxy"]),
        (CAMPUS_BBOX["minx"] + dx, CAMPUS_BBOX["miny"] + dy,
         CAMPUS_BBOX["maxx"], CAMPUS_BBOX["maxy"]),
    ]

    for qminx, qminy, qmaxx, qmaxy in quadrants:
        qbbox = f"{qminx},{qminy},{qmaxx},{qmaxy}"
        for x, y in [(64, 64), (128, 128), (192, 192), (64, 192), (192, 64)]:
            result = get_featureinfo_single(session, layer, x, y, qbbox,
                                             feature_count=feature_count)
            total_queries += 1
            time.sleep(DELAY)

            if isinstance(result, dict) and "features" in result:
                for feat in result["features"]:
                    feat_id = feat.get("id", "")
                    props = feat.get("properties", {})
                    gid = props.get("gid", "")
                    unique_key = feat_id or f"gid_{gid}" or json.dumps(props, sort_keys=True)

                    if unique_key not in feature_ids_seen:
                        feature_ids_seen.add(unique_key)
                        all_features[unique_key] = feat
                if result["features"]:
                    successful_queries += 1

    return {
        "type": "FeatureCollection",
        "features": list(all_features.values()),
        "query_stats": {
            "total_queries": total_queries,
            "queries_with_hits": successful_queries,
            "unique_features": len(all_features),
        },
    }


def get_featureinfo_text_format(session, layer):
    """Also try text/plain and text/html formats for additional info."""
    bbox_str = f"{CAMPUS_BBOX['minx']},{CAMPUS_BBOX['miny']},{CAMPUS_BBOX['maxx']},{CAMPUS_BBOX['maxy']}"
    results = {}

    for fmt_name, fmt_value in [("text_plain", "text/plain"), ("text_html", "text/html"),
                                 ("gml", "application/vnd.ogc.gml")]:
        params = {
            "SERVICE": "WMS",
            "VERSION": "1.1.1",
            "REQUEST": "GetFeatureInfo",
            "LAYERS": layer,
            "QUERY_LAYERS": layer,
            "INFO_FORMAT": fmt_value,
            "FEATURE_COUNT": "100",
            "SRS": "EPSG:3826",
            "BBOX": bbox_str,
            "WIDTH": "256",
            "HEIGHT": "256",
            "X": "128",
            "Y": "128",
        }
        try:
            resp = session.get(WMS_URL, params=params, timeout=TIMEOUT)
            results[fmt_name] = {
                "status": resp.status_code,
                "content_type": resp.headers.get("Content-Type", ""),
                "content": resp.text[:2000] if resp.status_code == 200 else resp.text[:500],
            }
        except Exception as e:
            results[fmt_name] = {"error": str(e)}
        time.sleep(DELAY)

    return results


def download_alternative_format(session, layer, fmt, ext, output_dir):
    """Download a map in an alternative format (PDF, SVG)."""
    bbox_str = f"{CAMPUS_BBOX['minx']},{CAMPUS_BBOX['miny']},{CAMPUS_BBOX['maxx']},{CAMPUS_BBOX['maxy']}"
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetMap",
        "LAYERS": layer,
        "SRS": "EPSG:3826",
        "BBOX": bbox_str,
        "WIDTH": "1024",
        "HEIGHT": "1024",
        "FORMAT": fmt,
    }

    layer_safe = layer.replace(":", "_")
    outfile = output_dir / f"{layer_safe}.{ext}"

    try:
        resp = session.get(WMS_URL, params=params, timeout=60)
        if resp.status_code == 200:
            content_type = resp.headers.get("Content-Type", "")
            # Check if it's an error response
            if "xml" in content_type and "ServiceException" in resp.text:
                return {
                    "status": "error",
                    "message": f"ServiceException: {resp.text[:300]}",
                }

            with open(outfile, "wb") as f:
                f.write(resp.content)
            return {
                "status": "success",
                "file": str(outfile),
                "size": len(resp.content),
                "content_type": content_type,
            }
        else:
            return {
                "status": "error",
                "http_status": resp.status_code,
                "message": resp.text[:300],
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def load_wfs_data(layer_name):
    """Load existing WFS data for comparison."""
    safe_name = layer_name.replace(":", "_")
    wfs_file = WFS_DIR / f"{safe_name}.json"
    if wfs_file.exists():
        try:
            with open(wfs_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            features = data.get("features", [])
            if features:
                props_keys = set()
                for feat in features:
                    props_keys.update(feat.get("properties", {}).keys())
                return {
                    "feature_count": len(features),
                    "attribute_keys": sorted(list(props_keys)),
                }
        except Exception:
            pass
    return None


def compare_with_wfs(layer_name, wms_result):
    """Compare WMS FeatureInfo results with existing WFS data."""
    wfs_info = load_wfs_data(layer_name)
    if not wfs_info:
        return {"wfs_available": False}

    wms_features = wms_result.get("features", [])
    wms_props_keys = set()
    for feat in wms_features:
        wms_props_keys.update(feat.get("properties", {}).keys())

    wfs_keys = set(wfs_info["attribute_keys"])
    wms_keys = wms_props_keys

    return {
        "wfs_available": True,
        "wfs_feature_count": wfs_info["feature_count"],
        "wms_feature_count": len(wms_features),
        "wfs_attributes": sorted(list(wfs_keys)),
        "wms_attributes": sorted(list(wms_keys)),
        "wms_only_attributes": sorted(list(wms_keys - wfs_keys)),
        "wfs_only_attributes": sorted(list(wfs_keys - wms_keys)),
        "common_attributes": sorted(list(wfs_keys & wms_keys)),
    }


def main():
    """Main extraction function."""
    print(f"=" * 70)
    print(f"WMS GetFeatureInfo Extraction - ymspace.ga.nycu.edu.tw")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    alt_format_dir = OUTPUT_DIR / "alternative_formats"
    alt_format_dir.mkdir(exist_ok=True)
    text_format_dir = OUTPUT_DIR / "text_formats"
    text_format_dir.mkdir(exist_ok=True)

    session = get_session()

    # Phase 1: GetFeatureInfo for all layers (JSON format with grid queries)
    print(f"\n{'='*70}")
    print(f"Phase 1: GetFeatureInfo (JSON) for {len(ALL_LAYERS)} layers")
    print(f"{'='*70}")

    layer_results = {}
    comparison_results = {}
    total_features = 0

    for i, layer in enumerate(ALL_LAYERS, 1):
        layer_safe = layer.replace(":", "_")
        print(f"\n[{i}/{len(ALL_LAYERS)}] Querying: {layer}")

        result = get_featureinfo_grid(session, layer)
        feat_count = len(result.get("features", []))
        stats = result.get("query_stats", {})
        total_features += feat_count

        print(f"  -> {feat_count} unique features found "
              f"(queries: {stats.get('total_queries', 0)}, "
              f"with hits: {stats.get('queries_with_hits', 0)})")

        # Save individual layer result
        outfile = OUTPUT_DIR / f"{layer_safe}_featureinfo.json"
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # Print sample attributes
        if result.get("features"):
            props = result["features"][0].get("properties", {})
            print(f"  -> Attributes: {list(props.keys())}")
            # Print first feature properties (truncated)
            for key, val in list(props.items())[:5]:
                val_str = str(val)[:80]
                print(f"     {key}: {val_str}")

        # Compare with WFS data
        comparison = compare_with_wfs(layer, result)
        comparison_results[layer] = comparison
        if comparison.get("wfs_available"):
            wms_only = comparison.get("wms_only_attributes", [])
            wfs_only = comparison.get("wfs_only_attributes", [])
            if wms_only:
                print(f"  -> NEW attributes (WMS only): {wms_only}")
            if wfs_only:
                print(f"  -> Missing in WMS (WFS only): {wfs_only}")

        layer_results[layer] = {
            "feature_count": feat_count,
            "query_stats": stats,
            "attributes": list(
                set().union(
                    *(feat.get("properties", {}).keys()
                      for feat in result.get("features", []))
                )
            ) if result.get("features") else [],
        }

    # Phase 2: Alternative text formats for key layers
    print(f"\n{'='*70}")
    print(f"Phase 2: Alternative text formats for key layers")
    print(f"{'='*70}")

    text_results = {}
    for layer in KEY_LAYERS:
        layer_safe = layer.replace(":", "_")
        print(f"\nQuerying text formats: {layer}")
        text_result = get_featureinfo_text_format(session, layer)
        text_results[layer] = text_result

        # Save text format results
        outfile = text_format_dir / f"{layer_safe}_text_formats.json"
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(text_result, f, ensure_ascii=False, indent=2)

        for fmt_name, fmt_result in text_result.items():
            status = fmt_result.get("status", fmt_result.get("error", "?"))
            ct = fmt_result.get("content_type", "")
            content_len = len(fmt_result.get("content", ""))
            print(f"  {fmt_name}: status={status}, type={ct}, len={content_len}")

    # Phase 3: Alternative export formats (PDF, SVG) for key layers
    print(f"\n{'='*70}")
    print(f"Phase 3: Alternative export formats (PDF, SVG)")
    print(f"{'='*70}")

    alt_results = {}
    for layer in KEY_LAYERS:
        print(f"\nExporting: {layer}")
        alt_results[layer] = {}

        for fmt, ext in [("application/pdf", "pdf"), ("image/svg+xml", "svg")]:
            result = download_alternative_format(session, layer, fmt, ext, alt_format_dir)
            alt_results[layer][ext] = result
            status = result.get("status", "unknown")
            size = result.get("size", 0)
            print(f"  {ext}: {status} (size={size})")
            time.sleep(DELAY)

    # Phase 4: Try EPSG:4326 BBOX as well (some layers might be in WGS84)
    print(f"\n{'='*70}")
    print(f"Phase 4: EPSG:4326 queries for layers with 0 features in EPSG:3826")
    print(f"{'='*70}")

    # Approximate EPSG:4326 BBOX for the Yangming campus area
    bbox_4326 = "121.505,25.015,121.540,25.135"

    zero_feature_layers = [
        layer for layer, info in layer_results.items()
        if info["feature_count"] == 0
    ]

    epsg4326_results = {}
    for layer in zero_feature_layers:
        layer_safe = layer.replace(":", "_")
        print(f"\nRetrying with EPSG:4326: {layer}")

        all_features_4326 = {}
        for x, y in QUERY_GRID[:9]:  # Use fewer points for retry
            result = get_featureinfo_single(
                session, layer, x, y, bbox_4326, srs="EPSG:4326"
            )
            time.sleep(DELAY)
            if isinstance(result, dict) and "features" in result:
                for feat in result["features"]:
                    feat_id = feat.get("id", "")
                    props = feat.get("properties", {})
                    gid = props.get("gid", "")
                    unique_key = feat_id or f"gid_{gid}" or json.dumps(props, sort_keys=True)
                    if unique_key not in all_features_4326:
                        all_features_4326[unique_key] = feat

        feat_count = len(all_features_4326)
        print(f"  -> {feat_count} features with EPSG:4326")

        if all_features_4326:
            result_4326 = {
                "type": "FeatureCollection",
                "features": list(all_features_4326.values()),
                "query_stats": {"srs": "EPSG:4326", "unique_features": feat_count},
            }
            outfile = OUTPUT_DIR / f"{layer_safe}_featureinfo_4326.json"
            with open(outfile, "w", encoding="utf-8") as f:
                json.dump(result_4326, f, ensure_ascii=False, indent=2)
            epsg4326_results[layer] = feat_count
            layer_results[layer]["feature_count_4326"] = feat_count

    # Phase 5: DescribeLayer for metadata about styling and data
    print(f"\n{'='*70}")
    print(f"Phase 5: DescribeLayer for key layers")
    print(f"{'='*70}")

    describe_results = {}
    for layer in KEY_LAYERS:
        params = {
            "SERVICE": "WMS",
            "VERSION": "1.1.1",
            "REQUEST": "DescribeLayer",
            "LAYERS": layer,
            "OUTPUT_FORMAT": "application/json",
        }
        try:
            resp = session.get(WMS_URL, params=params, timeout=TIMEOUT)
            if resp.status_code == 200:
                content_type = resp.headers.get("Content-Type", "")
                if "json" in content_type:
                    describe_results[layer] = resp.json()
                else:
                    describe_results[layer] = {"content_type": content_type, "text": resp.text[:1000]}
            else:
                describe_results[layer] = {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            describe_results[layer] = {"error": str(e)}
        time.sleep(DELAY)

    describe_file = OUTPUT_DIR / "describe_layer_results.json"
    with open(describe_file, "w", encoding="utf-8") as f:
        json.dump(describe_results, f, ensure_ascii=False, indent=2)

    print(f"\nDescribeLayer results saved.")
    for layer, result in describe_results.items():
        print(f"  {layer}: {json.dumps(result, ensure_ascii=False)[:200]}")

    # Phase 6: GetLegendGraphic for all layers (extract styling info)
    print(f"\n{'='*70}")
    print(f"Phase 6: GetLegendGraphic for key layers")
    print(f"{'='*70}")

    legend_dir = OUTPUT_DIR / "legends"
    legend_dir.mkdir(exist_ok=True)
    legend_results = {}

    for layer in KEY_LAYERS:
        layer_safe = layer.replace(":", "_")
        params = {
            "SERVICE": "WMS",
            "VERSION": "1.1.1",
            "REQUEST": "GetLegendGraphic",
            "LAYER": layer,
            "FORMAT": "image/png",
            "WIDTH": "200",
            "HEIGHT": "200",
        }
        try:
            resp = session.get(WMS_URL, params=params, timeout=TIMEOUT)
            if resp.status_code == 200:
                content_type = resp.headers.get("Content-Type", "")
                outfile = legend_dir / f"{layer_safe}_legend.png"
                with open(outfile, "wb") as f:
                    f.write(resp.content)
                legend_results[layer] = {
                    "status": "success",
                    "size": len(resp.content),
                    "file": str(outfile),
                }
                print(f"  {layer}: legend saved ({len(resp.content)} bytes)")
            else:
                legend_results[layer] = {"status": "error", "http_status": resp.status_code}
                print(f"  {layer}: HTTP {resp.status_code}")
        except Exception as e:
            legend_results[layer] = {"status": "error", "message": str(e)}
            print(f"  {layer}: Error - {e}")
        time.sleep(DELAY)

    # Generate comprehensive summary
    print(f"\n{'='*70}")
    print(f"Generating Summary Report")
    print(f"{'='*70}")

    summary = {
        "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
        "wms_endpoint": WMS_URL,
        "total_layers_queried": len(ALL_LAYERS),
        "total_unique_features_extracted": total_features,
        "campus_bbox_epsg3826": CAMPUS_BBOX,
        "layer_results": {},
        "comparison_summary": {
            "layers_with_new_wms_attributes": [],
            "layers_with_more_wms_features": [],
            "layers_with_fewer_wms_features": [],
            "layers_only_in_wms": [],
            "layers_with_zero_features": [],
        },
        "alternative_formats": alt_results,
        "describe_layer": describe_results,
        "legend_results": legend_results,
    }

    for layer, info in layer_results.items():
        comp = comparison_results.get(layer, {})
        layer_entry = {
            "wms_feature_count": info["feature_count"],
            "attributes": info["attributes"],
            "query_stats": info["query_stats"],
        }

        if comp.get("wfs_available"):
            layer_entry["wfs_feature_count"] = comp["wfs_feature_count"]
            layer_entry["wms_only_attributes"] = comp.get("wms_only_attributes", [])
            layer_entry["wfs_only_attributes"] = comp.get("wfs_only_attributes", [])
            layer_entry["common_attributes"] = comp.get("common_attributes", [])

            if comp.get("wms_only_attributes"):
                summary["comparison_summary"]["layers_with_new_wms_attributes"].append({
                    "layer": layer,
                    "new_attributes": comp["wms_only_attributes"],
                })
            if info["feature_count"] > comp["wfs_feature_count"]:
                summary["comparison_summary"]["layers_with_more_wms_features"].append({
                    "layer": layer,
                    "wms": info["feature_count"],
                    "wfs": comp["wfs_feature_count"],
                })
            elif info["feature_count"] < comp["wfs_feature_count"]:
                summary["comparison_summary"]["layers_with_fewer_wms_features"].append({
                    "layer": layer,
                    "wms": info["feature_count"],
                    "wfs": comp["wfs_feature_count"],
                })
        else:
            layer_entry["wfs_available"] = False

        if info.get("feature_count_4326"):
            layer_entry["feature_count_epsg4326"] = info["feature_count_4326"]

        if info["feature_count"] == 0 and not info.get("feature_count_4326"):
            summary["comparison_summary"]["layers_with_zero_features"].append(layer)

        summary["layer_results"][layer] = layer_entry

    # Save summary
    summary_file = OUTPUT_DIR / "WMS_FEATUREINFO_SUMMARY.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # Generate markdown report
    report_lines = [
        "# WMS GetFeatureInfo Extraction Report",
        f"",
        f"**Date:** {datetime.now(timezone.utc).isoformat()}",
        f"**Endpoint:** {WMS_URL}",
        f"**Total Layers Queried:** {len(ALL_LAYERS)}",
        f"**Total Unique Features Extracted:** {total_features}",
        f"",
        "## Layer Results Summary",
        "",
        "| Layer | WMS Features | WFS Features | WMS-Only Attrs | Status |",
        "|-------|-------------|-------------|----------------|--------|",
    ]

    for layer in ALL_LAYERS:
        info = layer_results.get(layer, {})
        comp = comparison_results.get(layer, {})
        wms_count = info.get("feature_count", 0)
        wfs_count = comp.get("wfs_feature_count", "-")
        new_attrs = len(comp.get("wms_only_attributes", []))
        status = "OK" if wms_count > 0 else "No features"
        if info.get("feature_count_4326"):
            status = f"OK (4326: {info['feature_count_4326']})"
        report_lines.append(
            f"| {layer} | {wms_count} | {wfs_count} | {new_attrs} | {status} |"
        )

    report_lines.extend([
        "",
        "## Layers with NEW WMS-Only Attributes",
        "",
    ])

    new_attr_layers = summary["comparison_summary"]["layers_with_new_wms_attributes"]
    if new_attr_layers:
        for item in new_attr_layers:
            report_lines.append(f"### {item['layer']}")
            report_lines.append(f"New attributes: {', '.join(item['new_attributes'])}")
            report_lines.append("")
    else:
        report_lines.append("No layers found with WMS-only attributes.")
        report_lines.append("")

    report_lines.extend([
        "## Feature Count Comparison",
        "",
        "### Layers with MORE features in WMS than WFS",
        "",
    ])
    for item in summary["comparison_summary"]["layers_with_more_wms_features"]:
        report_lines.append(f"- {item['layer']}: WMS={item['wms']}, WFS={item['wfs']}")

    report_lines.extend([
        "",
        "### Layers with FEWER features in WMS than WFS",
        "",
    ])
    for item in summary["comparison_summary"]["layers_with_fewer_wms_features"]:
        report_lines.append(f"- {item['layer']}: WMS={item['wms']}, WFS={item['wfs']}")

    report_lines.extend([
        "",
        "### Layers with ZERO features (neither EPSG:3826 nor EPSG:4326)",
        "",
    ])
    for layer in summary["comparison_summary"]["layers_with_zero_features"]:
        report_lines.append(f"- {layer}")

    report_lines.extend([
        "",
        "## Alternative Format Results",
        "",
    ])
    for layer, fmts in alt_results.items():
        report_lines.append(f"### {layer}")
        for ext, result in fmts.items():
            status = result.get("status", "unknown")
            size = result.get("size", 0)
            report_lines.append(f"- {ext.upper()}: {status} ({size} bytes)")
        report_lines.append("")

    report_lines.extend([
        "## Notes",
        "",
        "- WMS GetFeatureInfo returns features intersecting the query point pixel.",
        "- Multiple grid points and quadrant sub-regions were used to maximize coverage.",
        "- EPSG:3826 (TWD97/TM2) was used as the primary CRS; EPSG:4326 was tried as fallback.",
        "- Feature count differences between WMS and WFS are expected due to query method.",
        f"- WMS queries used BBOX: {CAMPUS_BBOX}",
        "",
    ])

    report_file = OUTPUT_DIR / "WMS_FEATUREINFO_REPORT.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    # Final stats
    print(f"\n{'='*70}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"Total layers queried: {len(ALL_LAYERS)}")
    print(f"Total unique features: {total_features}")
    print(f"Layers with features: {sum(1 for v in layer_results.values() if v['feature_count'] > 0)}")
    print(f"Layers with zero features: {len(summary['comparison_summary']['layers_with_zero_features'])}")
    print(f"Layers with new WMS-only attrs: {len(new_attr_layers)}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Summary JSON: {summary_file}")
    print(f"Report MD: {report_file}")


if __name__ == "__main__":
    main()
