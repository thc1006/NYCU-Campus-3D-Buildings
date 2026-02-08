#!/usr/bin/env python3
"""
Deep Probe V2: Comprehensive data extraction from NYCU Yangming Campus GIS Server
Systematically probes ALL unexplored endpoints and saves results.
"""

import json
import os
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlencode

import requests
import requests.packages.urllib3

# Suppress SSL warnings
warnings.filterwarnings("ignore")
requests.packages.urllib3.disable_warnings()

# ── Configuration ──────────────────────────────────────────────────────────
BASE_URL = "https://ymspace.ga.nycu.edu.tw"
PUBLIC_URL = f"{BASE_URL}/gisweb/public"
GEOSERVER_URL = f"{BASE_URL}:8080/geoserver"
OUTPUT_DIR = Path(r"C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive\deep_probe_v2")
EXISTING_DATA = Path(r"C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive")

SESSION = requests.Session()
SESSION.verify = False
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "Accept": "*/*",
})

# Global results tracker
RESULTS = []
FINDINGS = {"new_data": [], "errors": [], "interesting": []}


def ensure_dir(path):
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def safe_get(url, params=None, timeout=30, stream=False):
    """Safe HTTP GET with error handling."""
    try:
        resp = SESSION.get(url, params=params, timeout=timeout, stream=stream)
        return resp
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.ConnectionError:
        return None
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None


def probe_endpoint(name, url, params=None, save_subdir=None, save_filename=None,
                   expect_json=True, save_if_useful=True, binary=False):
    """
    Probe a single endpoint and record results.
    Returns the response object if successful.
    """
    full_url = url
    if params:
        full_url = f"{url}?{urlencode(params)}"
    print(f"  [{name}] {full_url[:120]}...")

    resp = safe_get(url, params=params, timeout=30)
    if resp is None:
        result = {
            "name": name, "url": full_url, "status": "TIMEOUT/ERROR",
            "size": 0, "content_type": "", "preview": ""
        }
        RESULTS.append(result)
        return None

    ct = resp.headers.get("Content-Type", "")
    size = len(resp.content)
    preview = ""
    if not binary and size < 100000:
        try:
            preview = resp.text[:500]
        except Exception:
            preview = f"<binary {size} bytes>"
    else:
        preview = f"<binary/large {size} bytes, CT: {ct}>"

    result = {
        "name": name, "url": full_url, "status": resp.status_code,
        "size": size, "content_type": ct, "preview": preview
    }
    RESULTS.append(result)

    is_useful = (resp.status_code == 200 and size > 10
                 and "404" not in preview[:50]
                 and "error" not in preview[:50].lower()
                 and preview.strip() != "null"
                 and preview.strip() != "{}")

    if is_useful and save_if_useful and save_subdir and save_filename:
        outdir = OUTPUT_DIR / save_subdir
        ensure_dir(outdir)
        outpath = outdir / save_filename
        if binary:
            with open(outpath, "wb") as f:
                f.write(resp.content)
        else:
            with open(outpath, "w", encoding="utf-8") as f:
                f.write(resp.text)
        FINDINGS["new_data"].append({
            "name": name, "file": str(outpath), "size": size
        })
        print(f"    -> SAVED ({size} bytes) -> {save_filename}")
    elif is_useful:
        FINDINGS["interesting"].append({
            "name": name, "url": full_url, "size": size,
            "preview": preview[:200]
        })
        print(f"    -> USEFUL ({size} bytes)")
    elif resp.status_code != 200:
        print(f"    -> HTTP {resp.status_code} ({size} bytes)")
    else:
        print(f"    -> Empty/null ({size} bytes)")

    return resp


def load_building_ids():
    """Load all known building IDs from existing data."""
    fpath = EXISTING_DATA / "api_data" / "public_bypass" / "all_building_floors.json"
    if fpath.exists():
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data  # dict: {buildId: [floors]}
    return {}


def load_all_layers():
    """Load all known GIS layer names."""
    fpath = EXISTING_DATA / "api_data" / "findAllLayers_full.json"
    if fpath.exists():
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "rows" in data:
            return data["rows"]
    return []


def load_rooms_data():
    """Load rooms data if available."""
    fpath = EXISTING_DATA / "api_data" / "public_bypass" / "all_rooms_by_building.json"
    if fpath.exists():
        with open(fpath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# ════════════════════════════════════════════════════════════════════════════
# PHASE 1: Public Application API Deep Probe
# ════════════════════════════════════════════════════════════════════════════

def phase1_public_api_deep_probe():
    """Exhaustively probe all public API endpoints."""
    print("\n" + "=" * 80)
    print("PHASE 1: Public Application API Deep Probe")
    print("=" * 80)

    buildings = load_building_ids()
    building_ids = list(buildings.keys())
    rooms = load_rooms_data()

    # ── 1a. buildinfo.htm comprehensive probe ──
    print("\n--- 1a. buildinfo.htm comprehensive ---")

    # Known valid actions from error messages:
    # getBoundingBoxByBuildId, search, getFloorListOfFloorPlain,
    # getCentroidByBuildId, getBoundByBuildId, findByCampus,
    # getPublicBuildInfo, getFloorList, loadPublicData
    valid_buildinfo_actions = [
        "getBoundingBoxByBuildId", "search", "getFloorListOfFloorPlain",
        "getCentroidByBuildId", "getBoundByBuildId", "findByCampus",
        "getPublicBuildInfo", "getFloorList", "loadPublicData"
    ]

    # Try search with various locales
    for locale in ["zh-tw", "en", "ja", "ko"]:
        probe_endpoint(
            f"buildinfo_search_locale_{locale}",
            f"{PUBLIC_URL}/buildinfo.htm",
            params={"action": "search", "q": "%", "locale": locale},
            save_subdir="public_api", save_filename=f"buildinfo_search_{locale}.json"
        )

    # Try search with various query strings
    for q in ["圖書", "實驗", "宿舍", "Lab", "Library", "教室", "辦公", "會議"]:
        probe_endpoint(
            f"buildinfo_search_{q}",
            f"{PUBLIC_URL}/buildinfo.htm",
            params={"action": "search", "q": q},
            save_subdir="public_api", save_filename=f"buildinfo_search_q_{q}.json"
        )

    # findByCampus - try all campus IDs
    for cid in ["1", "2", "3", "all", ""]:
        probe_endpoint(
            f"buildinfo_findByCampus_{cid}",
            f"{PUBLIC_URL}/buildinfo.htm",
            params={"action": "findByCampus", "campusId": cid},
            save_subdir="public_api", save_filename=f"buildinfo_findByCampus_{cid}.json"
        )

    # getPublicBuildInfo - try various params
    probe_endpoint(
        "buildinfo_getPublicBuildInfo_noParam",
        f"{PUBLIC_URL}/buildinfo.htm",
        params={"action": "getPublicBuildInfo"},
        save_subdir="public_api", save_filename="buildinfo_getPublicBuildInfo_noParam.json"
    )
    probe_endpoint(
        "buildinfo_getPublicBuildInfo_all",
        f"{PUBLIC_URL}/buildinfo.htm",
        params={"action": "getPublicBuildInfo", "buildId": ""},
        save_subdir="public_api", save_filename="buildinfo_getPublicBuildInfo_all.json"
    )

    # ── 1b. roominfo.htm comprehensive probe ──
    print("\n--- 1b. roominfo.htm comprehensive ---")

    # Known valid actions: search, findByFloor, getBound,
    # loadImage, loadPublicDataByClassNum, queryRoomExists

    # Room search with various queries
    for q in ["教室", "辦公室", "實驗", "Lab", "Office", "會議", "廁所", "%", "101"]:
        probe_endpoint(
            f"roominfo_search_{q}",
            f"{PUBLIC_URL}/roominfo.htm",
            params={"action": "search", "q": q},
            save_subdir="public_api/room_search", save_filename=f"room_search_{q}.json"
        )

    # getBound for rooms (room geometry!) - try several buildings and floors
    sample_buildings = ["B005", "P004", "P003", "Y001", "P006", "B019", "B010"]
    for bid in sample_buildings:
        if bid in buildings:
            floors = buildings[bid]
            for floor in floors[:3]:  # First 3 floors per building
                # First get rooms on this floor
                resp = safe_get(f"{PUBLIC_URL}/roominfo.htm",
                                params={"action": "findByFloor", "buildId": bid, "floor": floor})
                if resp and resp.status_code == 200:
                    try:
                        room_data = resp.json()
                        if "data" in room_data and room_data["data"]:
                            for room in room_data["data"][:3]:  # First 3 rooms
                                classnum = room.get("classnum", room.get("classNum", ""))
                                room_name = room.get("name", "unknown")
                                if classnum:
                                    probe_endpoint(
                                        f"roominfo_getBound_{bid}_{floor}_{classnum}",
                                        f"{PUBLIC_URL}/roominfo.htm",
                                        params={
                                            "action": "getBound",
                                            "buildId": bid,
                                            "floor": floor,
                                            "classNum": classnum
                                        },
                                        save_subdir="public_api/room_bounds",
                                        save_filename=f"bound_{bid}_{floor}_{classnum}.json"
                                    )
                    except Exception as e:
                        print(f"    [WARN] Error parsing rooms for {bid}/{floor}: {e}")

    # queryRoomExists - check various buildings
    for bid in building_ids[:10]:
        probe_endpoint(
            f"roominfo_queryRoomExists_{bid}",
            f"{PUBLIC_URL}/roominfo.htm",
            params={"action": "queryRoomExists", "buildId": bid},
            save_subdir="public_api", save_filename=f"roomExists_{bid}.json"
        )

    # loadPublicDataByClassNum - comprehensive room details
    # Try to get detailed info for rooms we know about
    for bid in sample_buildings:
        if bid in buildings:
            floors = buildings[bid]
            for floor in floors[:2]:
                resp = safe_get(f"{PUBLIC_URL}/roominfo.htm",
                                params={"action": "findByFloor", "buildId": bid, "floor": floor})
                if resp and resp.status_code == 200:
                    try:
                        room_data = resp.json()
                        if "data" in room_data:
                            for room in room_data["data"]:
                                classnum = room.get("classnum", room.get("classNum", ""))
                                room_id = room.get("id", "")
                                if classnum and room_id:
                                    probe_endpoint(
                                        f"roominfo_publicData_{room_id}",
                                        f"{PUBLIC_URL}/roominfo.htm",
                                        params={
                                            "action": "loadPublicDataByClassNum",
                                            "buildId": bid,
                                            "floor": floor,
                                            "classNum": classnum
                                        },
                                        save_subdir="public_api/room_details",
                                        save_filename=f"detail_{room_id}.json"
                                    )
                    except Exception:
                        pass

    # ── 1c. route.htm comprehensive probe ──
    print("\n--- 1c. route.htm comprehensive ---")

    # Known valid actions from error: searchByDistance, getCentroid,
    # loadImageByApKey, findAll, getHeaders, search, getLayerInfo,
    # dataTransmissionAPI, findGeom
    route_actions = [
        "searchByDistance", "getCentroid", "loadImageByApKey",
        "findAll", "getHeaders", "search", "getLayerInfo",
        "dataTransmissionAPI", "findGeom"
    ]

    # getLayerInfo for all known layers
    layers = load_all_layers()
    layer_keys = set()
    for layer in layers:
        nk = layer.get("navi_key", "")
        if nk:
            layer_keys.add(nk)

    for lk in sorted(layer_keys):
        probe_endpoint(
            f"route_getLayerInfo_{lk}",
            f"{PUBLIC_URL}/route.htm",
            params={"action": "getLayerInfo", "layerKey": lk},
            save_subdir="public_api/layer_info", save_filename=f"layerinfo_{lk}.json"
        )

    # getCentroid for various layers
    for lk in sorted(layer_keys)[:10]:
        probe_endpoint(
            f"route_getCentroid_{lk}",
            f"{PUBLIC_URL}/route.htm",
            params={"action": "getCentroid", "layerKey": lk},
            save_subdir="public_api/centroids", save_filename=f"centroid_{lk}.json"
        )

    # getHeaders for various layers
    for lk in sorted(layer_keys)[:10]:
        probe_endpoint(
            f"route_getHeaders_{lk}",
            f"{PUBLIC_URL}/route.htm",
            params={"action": "getHeaders", "layerKey": lk},
            save_subdir="public_api/headers", save_filename=f"headers_{lk}.json"
        )

    # findAll for various layers
    for lk in sorted(layer_keys)[:10]:
        probe_endpoint(
            f"route_findAll_{lk}",
            f"{PUBLIC_URL}/route.htm",
            params={"action": "findAll", "layerKey": lk},
            save_subdir="public_api/findAll", save_filename=f"findAll_{lk}.json"
        )

    # search with various queries
    for q in ["AED", "ATM", "停車", "餐廳", "圖書", "電梯", "廁所", "%"]:
        probe_endpoint(
            f"route_search_{q}",
            f"{PUBLIC_URL}/route.htm",
            params={"action": "search", "q": q},
            save_subdir="public_api/route_search", save_filename=f"search_{q}.json"
        )

    # searchByDistance
    # Use known building centroid coordinates (EPSG:3826)
    probe_endpoint(
        "route_searchByDistance_center",
        f"{PUBLIC_URL}/route.htm",
        params={
            "action": "searchByDistance",
            "x": "301800", "y": "2779500",
            "distance": "500", "layerKey": "gis_building"
        },
        save_subdir="public_api", save_filename="searchByDistance_center.json"
    )

    # findGeom for buildings
    for bid in building_ids[:5]:
        probe_endpoint(
            f"route_findGeom_{bid}",
            f"{PUBLIC_URL}/route.htm",
            params={"action": "findGeom", "buildId": bid},
            save_subdir="public_api/geom", save_filename=f"geom_{bid}.json"
        )

    # loadImageByApKey - try various keys
    for key in ["B005", "P004", "gis_building", "gis_aed"]:
        probe_endpoint(
            f"route_loadImageByApKey_{key}",
            f"{PUBLIC_URL}/route.htm",
            params={"action": "loadImageByApKey", "apKey": key},
            save_subdir="public_api", save_filename=f"imageByApKey_{key}.json"
        )

    # dataTransmissionAPI with query parameter
    for layer in ["gis_building", "gis_aed", "gis_parking", "gis_restaurant",
                   "gis_busstop", "gis_atm", "gis_elevator"]:
        probe_endpoint(
            f"route_dataTransAPI_{layer}",
            f"{PUBLIC_URL}/route.htm",
            params={"action": "dataTransmissionAPI", "tableName": layer, "query": "SELECT * FROM " + layer},
            save_subdir="public_api/dataTransAPI", save_filename=f"dta_{layer}.json"
        )

    # ── 1d. report.htm probe ──
    print("\n--- 1d. report.htm ---")
    # Known actions: findAllType, addReport
    probe_endpoint(
        "report_findAllType",
        f"{PUBLIC_URL}/report.htm",
        params={"action": "findAllType"},
        save_subdir="public_api", save_filename="report_findAllType.json"
    )

    # ── 1e. uploadfiles.htm comprehensive ──
    print("\n--- 1e. uploadfiles.htm ---")
    # Known actions: findBySourceType, listImg, listAll
    for stype in ["build", "floor", "room", "poi", "photo", "image",
                   "campus", "layer", "floorplan", "attachment"]:
        probe_endpoint(
            f"uploadfiles_findBySourceType_{stype}",
            f"{PUBLIC_URL}/uploadfiles.htm",
            params={"action": "findBySourceType", "sourceType": stype},
            save_subdir="public_api/upload_sources",
            save_filename=f"uploadfiles_source_{stype}.json"
        )

    # listImg with various IDs - try a range around known IDs
    # Known valid: 38675 returned an image
    for img_id in range(38600, 38700):
        resp = safe_get(f"{PUBLIC_URL}/uploadfiles.htm",
                        params={"action": "listImg", "q": str(img_id)}, timeout=10)
        if resp and resp.status_code == 200 and len(resp.content) > 100:
            outdir = OUTPUT_DIR / "public_api" / "upload_images"
            ensure_dir(outdir)
            ct = resp.headers.get("Content-Type", "")
            ext = "jpg" if "jpeg" in ct else "png" if "png" in ct else "bin"
            outpath = outdir / f"img_{img_id}.{ext}"
            with open(outpath, "wb") as f:
                f.write(resp.content)
            print(f"    -> Image {img_id}: {len(resp.content)} bytes ({ct})")
            FINDINGS["new_data"].append({
                "name": f"upload_image_{img_id}",
                "file": str(outpath),
                "size": len(resp.content)
            })

    # Try broader ID range with larger steps
    for img_id in list(range(1, 100)) + list(range(100, 1000, 50)) + \
                  list(range(1000, 10000, 200)) + list(range(10000, 40000, 500)):
        resp = safe_get(f"{PUBLIC_URL}/uploadfiles.htm",
                        params={"action": "listImg", "q": str(img_id)}, timeout=5)
        if resp and resp.status_code == 200 and len(resp.content) > 100:
            outdir = OUTPUT_DIR / "public_api" / "upload_images_scan"
            ensure_dir(outdir)
            ct = resp.headers.get("Content-Type", "")
            ext = "jpg" if "jpeg" in ct else "png" if "png" in ct else "bin"
            outpath = outdir / f"img_{img_id}.{ext}"
            with open(outpath, "wb") as f:
                f.write(resp.content)
            print(f"    -> Image {img_id}: {len(resp.content)} bytes")
            FINDINGS["new_data"].append({
                "name": f"upload_image_scan_{img_id}",
                "file": str(outpath),
                "size": len(resp.content)
            })

    # ── 1f. loadImage for ALL buildings ──
    print("\n--- 1f. loadImage for all buildings ---")
    all_building_images = {}
    for bid in building_ids:
        resp = safe_get(f"{PUBLIC_URL}/roominfo.htm",
                        params={"action": "loadImage", "buildId": bid, "type": "buildinfo"})
        if resp and resp.status_code == 200:
            try:
                data = resp.json()
                if data and "data" in data and data["data"]:
                    all_building_images[bid] = data["data"]
                    print(f"    {bid}: {len(data['data'])} images")
            except Exception:
                pass

    outdir = OUTPUT_DIR / "public_api"
    ensure_dir(outdir)
    with open(outdir / "all_building_image_urls.json", "w", encoding="utf-8") as f:
        json.dump(all_building_images, f, ensure_ascii=False, indent=2)

    # Also try loadImage with type=roominfo and type=floorplan
    for img_type in ["roominfo", "floorplan", "poi", "campus"]:
        for bid in building_ids[:5]:
            probe_endpoint(
                f"loadImage_{img_type}_{bid}",
                f"{PUBLIC_URL}/roominfo.htm",
                params={"action": "loadImage", "buildId": bid, "type": img_type},
                save_subdir="public_api/loadImage",
                save_filename=f"loadImage_{img_type}_{bid}.json"
            )


# ════════════════════════════════════════════════════════════════════════════
# PHASE 2: GeoServer Deep Probe
# ════════════════════════════════════════════════════════════════════════════

def phase2_geoserver_deep_probe():
    """Deep probe of GeoServer endpoints."""
    print("\n" + "=" * 80)
    print("PHASE 2: GeoServer Deep Probe")
    print("=" * 80)

    buildings = load_building_ids()
    building_ids = list(buildings.keys())

    # ── 2a. WMS GetCapabilities (full parse) ──
    print("\n--- 2a. WMS GetCapabilities ---")
    probe_endpoint(
        "wms_capabilities",
        f"{GEOSERVER_URL}/wms",
        params={"service": "WMS", "request": "GetCapabilities"},
        save_subdir="geoserver", save_filename="wms_capabilities.xml"
    )

    # ── 2b. WFS GetCapabilities (all workspaces) ──
    print("\n--- 2b. WFS GetCapabilities (all workspaces) ---")
    for workspace in ["gis", "gis_room", "gss", ""]:
        ws_path = f"/{workspace}" if workspace else ""
        probe_endpoint(
            f"wfs_capabilities_{workspace or 'global'}",
            f"{GEOSERVER_URL}{ws_path}/wfs",
            params={"service": "WFS", "version": "1.1.0", "request": "GetCapabilities"},
            save_subdir="geoserver", save_filename=f"wfs_capabilities_{workspace or 'global'}.xml"
        )

    # ── 2c. OWS GetCapabilities ──
    print("\n--- 2c. OWS GetCapabilities ---")
    probe_endpoint(
        "ows_capabilities",
        f"{GEOSERVER_URL}/ows",
        params={"service": "wfs", "version": "1.1.0", "request": "GetCapabilities"},
        save_subdir="geoserver", save_filename="ows_wfs_capabilities.xml"
    )
    probe_endpoint(
        "ows_wms_capabilities",
        f"{GEOSERVER_URL}/ows",
        params={"service": "wms", "version": "1.1.1", "request": "GetCapabilities"},
        save_subdir="geoserver", save_filename="ows_wms_capabilities.xml"
    )
    probe_endpoint(
        "ows_wcs_capabilities",
        f"{GEOSERVER_URL}/ows",
        params={"service": "wcs", "version": "1.1.1", "request": "GetCapabilities"},
        save_subdir="geoserver", save_filename="ows_wcs_capabilities.xml"
    )

    # ── 2d. WFS DescribeFeatureType for ALL workspaces/layers ──
    print("\n--- 2d. WFS DescribeFeatureType for all workspaces ---")

    # Try all known GIS layers
    gis_layers = [
        "gis_aed", "gis_artwork", "gis_atm", "gis_auditorium",
        "gis_barrierfreetoilet", "gis_block", "gis_building", "gis_building_geom",
        "gis_busroutes_1", "gis_busroutes_2", "gis_busroutes_3", "gis_busstop",
        "gis_campus", "gis_campusphotos", "gis_conveniencestore", "gis_elevator",
        "gis_emergencycall", "gis_firestation", "gis_gateway",
        "gis_handicapparking", "gis_healthroom", "gis_parking",
        "gis_postoffice", "gis_restaurant", "gis_securityoffice",
        "gis_sport", "gis_telephonebooth", "gis_timerecorder",
        "gis_wheelchairramp", "gis_toilet",
        # Parcel layers
        "gis_parcel0821line", "gis_parcel0981line",
        # Sidewalk layers
        "gis_sidewalk_1", "gis_sidewalk_2", "gis_sidewalk_3",
        "gis_sidewalk_4", "gis_sidewalk_5", "gis_sidewalk_6",
        "gis_sidewalk_7", "gis_sidewalk_8", "gis_sidewalk_9",
        "gis_sidewalk_10", "gis_sidewalk_11", "gis_sidewalk_12",
        "gis_sidewalk_13", "gis_sidewalk_14", "gis_sidewalk_15",
    ]

    # Also try in gss workspace
    for ws in ["gis", "gss"]:
        for layer in gis_layers:
            probe_endpoint(
                f"wfs_descFT_{ws}_{layer}",
                f"{GEOSERVER_URL}/wfs",
                params={
                    "service": "WFS", "version": "1.1.0",
                    "request": "DescribeFeatureType",
                    "typeName": f"{ws}:{layer}"
                },
                save_subdir=f"geoserver/describe_feature/{ws}",
                save_filename=f"{layer}.xsd"
            )

    # ── 2e. GetLegendGraphic for ALL layers ──
    print("\n--- 2e. GetLegendGraphic for all layers ---")

    # GIS layers
    for layer in gis_layers:
        for ws in ["gis"]:
            probe_endpoint(
                f"legend_{ws}_{layer}",
                f"{GEOSERVER_URL}/wms",
                params={
                    "service": "WMS",
                    "request": "GetLegendGraphic",
                    "layer": f"{ws}:{layer}",
                    "format": "image/png",
                    "width": 200, "height": 200
                },
                save_subdir="geoserver/legends",
                save_filename=f"legend_{ws}_{layer}.png",
                binary=True
            )

    # Room layers - sample some
    for bid in building_ids[:10]:
        if bid in buildings:
            for floor in buildings[bid][:2]:
                layer_name = f"{bid}_{floor}"
                probe_endpoint(
                    f"legend_room_{layer_name}",
                    f"{GEOSERVER_URL}/wms",
                    params={
                        "service": "WMS",
                        "request": "GetLegendGraphic",
                        "layer": f"gis_room:{layer_name}",
                        "format": "image/png",
                        "width": 200, "height": 200
                    },
                    save_subdir="geoserver/legends/rooms",
                    save_filename=f"legend_room_{layer_name}.png",
                    binary=True
                )

    # ── 2f. SLD styles for ALL layers ──
    print("\n--- 2f. SLD styles for all layers ---")
    for layer in gis_layers:
        for ws in ["gis"]:
            probe_endpoint(
                f"sld_{ws}_{layer}",
                f"{GEOSERVER_URL}/wms",
                params={
                    "service": "WMS", "version": "1.1.1",
                    "request": "GetStyles",
                    "layers": f"{ws}:{layer}"
                },
                save_subdir="geoserver/sld_styles",
                save_filename=f"sld_{ws}_{layer}.xml"
            )

    # ── 2g. GetFeatureInfo for room layers ──
    print("\n--- 2g. GetFeatureInfo for room layers ---")
    # We need bbox for each building to do proper GetFeatureInfo
    bboxes_file = EXISTING_DATA / "api_data" / "public_bypass" / "all_building_bounds.json"
    bboxes = {}
    if bboxes_file.exists():
        with open(bboxes_file, "r", encoding="utf-8") as f:
            bboxes = json.load(f)

    for bid in building_ids[:8]:
        if bid in buildings and bid in bboxes:
            bbox_data = bboxes[bid]
            # Parse bbox - it should have minx,miny,maxx,maxy
            if isinstance(bbox_data, dict):
                minx = bbox_data.get("minx", bbox_data.get("left", 0))
                miny = bbox_data.get("miny", bbox_data.get("bottom", 0))
                maxx = bbox_data.get("maxx", bbox_data.get("right", 0))
                maxy = bbox_data.get("maxy", bbox_data.get("top", 0))
            elif isinstance(bbox_data, list) and len(bbox_data) >= 4:
                minx, miny, maxx, maxy = bbox_data[:4]
            elif isinstance(bbox_data, str):
                # Try to parse POLYGON or bbox string
                try:
                    coords = [float(x) for x in bbox_data.replace(",", " ").split() if x.replace(".", "").replace("-", "").isdigit()]
                    if len(coords) >= 4:
                        minx, miny, maxx, maxy = coords[0], coords[1], coords[2], coords[3]
                    else:
                        continue
                except Exception:
                    continue
            else:
                continue

            bbox_str = f"{minx},{miny},{maxx},{maxy}"

            for floor in buildings[bid][:3]:
                layer_name = f"gis_room:{bid}_{floor}"
                probe_endpoint(
                    f"getFeatureInfo_{bid}_{floor}",
                    f"{GEOSERVER_URL}/wms",
                    params={
                        "service": "WMS", "version": "1.1.1",
                        "request": "GetFeatureInfo",
                        "layers": layer_name,
                        "query_layers": layer_name,
                        "info_format": "application/json",
                        "x": 128, "y": 128,
                        "width": 256, "height": 256,
                        "srs": "EPSG:3826",
                        "bbox": bbox_str,
                        "feature_count": 50
                    },
                    save_subdir="geoserver/feature_info",
                    save_filename=f"featureinfo_{bid}_{floor}.json"
                )

    # ── 2h. WFS GetFeature with property queries ──
    print("\n--- 2h. WFS GetFeature with property queries ---")
    # Try getting features with specific property filters for GIS layers
    for layer in ["gis_building", "gis_building_geom", "gis_campus",
                   "gis_parking", "gis_restaurant", "gis_busstop"]:
        # Get all features as GeoJSON
        probe_endpoint(
            f"wfs_geojson_{layer}",
            f"{GEOSERVER_URL}/wfs",
            params={
                "service": "WFS", "version": "1.1.0",
                "request": "GetFeature",
                "typeName": f"gis:{layer}",
                "outputFormat": "application/json",
                "maxFeatures": 1000
            },
            save_subdir="geoserver/wfs_geojson",
            save_filename=f"{layer}.geojson"
        )

        # Also try GML format
        probe_endpoint(
            f"wfs_gml_{layer}",
            f"{GEOSERVER_URL}/wfs",
            params={
                "service": "WFS", "version": "1.1.0",
                "request": "GetFeature",
                "typeName": f"gis:{layer}",
                "outputFormat": "GML3",
                "maxFeatures": 1000
            },
            save_subdir="geoserver/wfs_gml",
            save_filename=f"{layer}.gml"
        )

    # ── 2i. Try additional output formats ──
    print("\n--- 2i. Additional output formats ---")
    for fmt in ["csv", "application/json", "text/csv", "SHAPE-ZIP",
                 "application/vnd.google-earth.kml+xml", "application/vnd.google-earth.kml xml"]:
        probe_endpoint(
            f"wfs_format_{fmt}_building",
            f"{GEOSERVER_URL}/wfs",
            params={
                "service": "WFS", "version": "1.1.0",
                "request": "GetFeature",
                "typeName": "gis:gis_building_geom",
                "outputFormat": fmt,
                "maxFeatures": 100
            },
            save_subdir="geoserver/alt_formats",
            save_filename=f"building_geom.{fmt.split('/')[-1].replace(' ', '_')}",
            binary=("SHAPE" in fmt or "kml" in fmt.lower())
        )

    # ── 2j. Layer Groups ──
    print("\n--- 2j. Layer Groups ---")
    probe_endpoint(
        "wms_getmap_layergroup",
        f"{GEOSERVER_URL}/wms",
        params={
            "service": "WMS", "version": "1.1.1",
            "request": "GetCapabilities"
        },
        save_subdir="geoserver", save_filename="wms_full_capabilities.xml"
    )

    # ── 2k. REST API (may be restricted but worth trying) ──
    print("\n--- 2k. GeoServer REST API probe ---")
    rest_endpoints = [
        "rest/workspaces",
        "rest/layers",
        "rest/styles",
        "rest/layergroups",
        "rest/namespaces",
        "rest/fonts",
        "rest/about/version",
        "rest/about/manifests",
        "rest/about/system-status",
    ]
    for ep in rest_endpoints:
        probe_endpoint(
            f"rest_{ep.replace('/', '_')}",
            f"{GEOSERVER_URL}/{ep}.json",
            save_subdir="geoserver/rest",
            save_filename=f"{ep.replace('/', '_')}.json"
        )

    # ── 2l. WCS (Web Coverage Service) ──
    print("\n--- 2l. WCS probe ---")
    probe_endpoint(
        "wcs_capabilities",
        f"{GEOSERVER_URL}/wcs",
        params={"service": "WCS", "version": "1.1.1", "request": "GetCapabilities"},
        save_subdir="geoserver", save_filename="wcs_capabilities.xml"
    )

    # ── 2m. WMTS (Web Map Tile Service) ──
    print("\n--- 2m. WMTS probe ---")
    probe_endpoint(
        "wmts_capabilities",
        f"{GEOSERVER_URL}/gwc/service/wmts",
        params={"service": "WMTS", "version": "1.0.0", "request": "GetCapabilities"},
        save_subdir="geoserver", save_filename="wmts_capabilities.xml"
    )

    # ── 2n. TMS (Tile Map Service) ──
    print("\n--- 2n. TMS probe ---")
    probe_endpoint(
        "tms_root",
        f"{GEOSERVER_URL}/gwc/service/tms/1.0.0",
        save_subdir="geoserver", save_filename="tms_root.xml"
    )


# ════════════════════════════════════════════════════════════════════════════
# PHASE 3: Room Bounds Comprehensive Extraction
# ════════════════════════════════════════════════════════════════════════════

def phase3_room_bounds_extraction():
    """Extract room geometry bounds for ALL buildings and floors."""
    print("\n" + "=" * 80)
    print("PHASE 3: Room Bounds Comprehensive Extraction")
    print("=" * 80)

    buildings = load_building_ids()
    all_bounds = {}
    total_rooms = 0

    for bid in sorted(buildings.keys()):
        floors = buildings[bid]
        all_bounds[bid] = {}
        for floor in floors:
            print(f"  Getting rooms for {bid}/{floor}...")
            resp = safe_get(f"{PUBLIC_URL}/roominfo.htm",
                            params={"action": "findByFloor", "buildId": bid, "floor": floor},
                            timeout=15)
            if not resp or resp.status_code != 200:
                continue

            try:
                room_data = resp.json()
                if "data" not in room_data or not room_data["data"]:
                    continue

                all_bounds[bid][floor] = {}
                for room in room_data["data"]:
                    classnum = room.get("classnum", room.get("classNum", ""))
                    room_id = room.get("id", "")
                    room_name = room.get("name", "")
                    if not classnum:
                        continue

                    # Get the room bound
                    bound_resp = safe_get(
                        f"{PUBLIC_URL}/roominfo.htm",
                        params={
                            "action": "getBound",
                            "buildId": bid,
                            "floor": floor,
                            "classNum": classnum
                        },
                        timeout=10
                    )
                    if bound_resp and bound_resp.status_code == 200:
                        try:
                            bound_data = bound_resp.json()
                            all_bounds[bid][floor][room_id] = {
                                "name": room_name,
                                "classnum": classnum,
                                "bound": bound_data
                            }
                            total_rooms += 1
                        except Exception:
                            pass

                rooms_on_floor = len(all_bounds[bid][floor])
                if rooms_on_floor > 0:
                    print(f"    {bid}/{floor}: {rooms_on_floor} room bounds collected")

            except Exception as e:
                print(f"    [WARN] {bid}/{floor}: {e}")

            # Small delay to be polite
            time.sleep(0.1)

    # Save all bounds
    outdir = OUTPUT_DIR / "room_bounds"
    ensure_dir(outdir)
    with open(outdir / "all_room_bounds.json", "w", encoding="utf-8") as f:
        json.dump(all_bounds, f, ensure_ascii=False, indent=2)

    print(f"\n  Total room bounds collected: {total_rooms}")
    FINDINGS["new_data"].append({
        "name": "all_room_bounds",
        "file": str(outdir / "all_room_bounds.json"),
        "size": total_rooms
    })


# ════════════════════════════════════════════════════════════════════════════
# PHASE 4: Complete Room Details Extraction
# ════════════════════════════════════════════════════════════════════════════

def phase4_room_details_extraction():
    """Extract detailed room info (including English names) for ALL rooms."""
    print("\n" + "=" * 80)
    print("PHASE 4: Complete Room Details Extraction")
    print("=" * 80)

    buildings = load_building_ids()
    all_details = {}
    total_rooms = 0

    for bid in sorted(buildings.keys()):
        floors = buildings[bid]
        all_details[bid] = {}
        for floor in floors:
            resp = safe_get(f"{PUBLIC_URL}/roominfo.htm",
                            params={"action": "findByFloor", "buildId": bid, "floor": floor},
                            timeout=15)
            if not resp or resp.status_code != 200:
                continue

            try:
                room_data = resp.json()
                if "data" not in room_data or not room_data["data"]:
                    continue

                all_details[bid][floor] = []
                for room in room_data["data"]:
                    classnum = room.get("classnum", room.get("classNum", ""))
                    if not classnum:
                        continue

                    # Get full public data
                    detail_resp = safe_get(
                        f"{PUBLIC_URL}/roominfo.htm",
                        params={
                            "action": "loadPublicDataByClassNum",
                            "buildId": bid,
                            "floor": floor,
                            "classNum": classnum
                        },
                        timeout=10
                    )
                    if detail_resp and detail_resp.status_code == 200:
                        try:
                            detail_data = detail_resp.json()
                            if "data" in detail_data and detail_data["data"]:
                                all_details[bid][floor].append(detail_data["data"][0])
                                total_rooms += 1
                        except Exception:
                            pass

                rooms_on_floor = len(all_details[bid][floor])
                if rooms_on_floor > 0:
                    print(f"    {bid}/{floor}: {rooms_on_floor} room details")

            except Exception as e:
                print(f"    [WARN] {bid}/{floor}: {e}")

            time.sleep(0.1)

    # Save
    outdir = OUTPUT_DIR / "room_details"
    ensure_dir(outdir)
    with open(outdir / "all_room_details.json", "w", encoding="utf-8") as f:
        json.dump(all_details, f, ensure_ascii=False, indent=2)

    print(f"\n  Total room details collected: {total_rooms}")
    FINDINGS["new_data"].append({
        "name": "all_room_details",
        "file": str(outdir / "all_room_details.json"),
        "size": total_rooms
    })


# ════════════════════════════════════════════════════════════════════════════
# PHASE 5: dataTransmissionAPI Deep Probe
# ════════════════════════════════════════════════════════════════════════════

def phase5_data_transmission_api():
    """Deep probe of the dataTransmissionAPI endpoint with various queries."""
    print("\n" + "=" * 80)
    print("PHASE 5: dataTransmissionAPI Deep Probe")
    print("=" * 80)

    layers = load_all_layers()
    layer_keys = set()
    for layer in layers:
        nk = layer.get("navi_key", "")
        if nk:
            layer_keys.add(nk)

    # Try dataTransmissionAPI with different table names
    for table in sorted(layer_keys):
        probe_endpoint(
            f"dta_select_{table}",
            f"{PUBLIC_URL}/route.htm",
            params={
                "action": "dataTransmissionAPI",
                "tableName": table,
                "query": f"SELECT * FROM {table}"
            },
            save_subdir="dataTransAPI",
            save_filename=f"dta_{table}.json"
        )

    # Try special table names that might exist
    special_tables = [
        "r_build_info", "r_room_info", "r_floor_info",
        "r_campus", "r_image", "r_user", "r_report",
        "gis_building", "gis_room", "gis_floor",
        "building_photo", "room_photo", "floor_plan",
        "poi", "route", "navigation"
    ]
    for table in special_tables:
        probe_endpoint(
            f"dta_special_{table}",
            f"{PUBLIC_URL}/route.htm",
            params={
                "action": "dataTransmissionAPI",
                "tableName": table,
                "query": f"SELECT * FROM {table} LIMIT 10"
            },
            save_subdir="dataTransAPI",
            save_filename=f"dta_special_{table}.json"
        )


# ════════════════════════════════════════════════════════════════════════════
# PHASE 6: Additional Endpoint Discovery
# ════════════════════════════════════════════════════════════════════════════

def phase6_endpoint_discovery():
    """Try to discover additional endpoints."""
    print("\n" + "=" * 80)
    print("PHASE 6: Additional Endpoint Discovery")
    print("=" * 80)

    # ── 6a. Try various controller paths ──
    print("\n--- 6a. Controller path discovery ---")
    controllers = [
        "buildinfo", "roominfo", "route", "campus", "uploadfiles",
        "report", "map", "userrole",
        # Speculative
        "floor", "floorplan", "floorinfo", "poi", "poiinfo",
        "navigation", "parking", "photo", "image",
        "search", "admin", "api", "data", "export",
        "gis", "layer", "layerinfo", "group", "groupinfo",
        "statistics", "log", "news", "announcement",
        "building", "room", "user", "auth", "login",
        "config", "system", "version", "health", "status",
        "dataTransmission", "download", "file", "attachment"
    ]
    for ctrl in controllers:
        resp = safe_get(f"{PUBLIC_URL}/{ctrl}.htm", timeout=5)
        if resp and resp.status_code != 404:
            probe_endpoint(
                f"controller_{ctrl}",
                f"{PUBLIC_URL}/{ctrl}.htm",
                save_subdir="discovery",
                save_filename=f"ctrl_{ctrl}.html"
            )

    # ── 6b. Try /gisweb/ paths (not /gisweb/public/) ──
    print("\n--- 6b. Non-public paths ---")
    for path in ["buildinfo.htm", "roominfo.htm", "route.htm",
                  "map.htm", "admin.htm", "api.htm"]:
        probe_endpoint(
            f"nonpublic_{path}",
            f"{BASE_URL}/gisweb/{path}",
            save_subdir="discovery",
            save_filename=f"nonpublic_{path}"
        )

    # ── 6c. Map config and layers ──
    print("\n--- 6c. Map configuration ---")
    for action in ["getConfig", "getLayers", "getMapConfig", "init",
                    "getBaseLayers", "getOverlayLayers"]:
        probe_endpoint(
            f"map_{action}",
            f"{PUBLIC_URL}/map.htm",
            params={"action": action},
            save_subdir="discovery",
            save_filename=f"map_{action}.json"
        )

    # ── 6d. GeoServer web interface pages ──
    print("\n--- 6d. GeoServer web pages ---")
    for page in ["web/", "web/wicket/bookmarkable/org.geoserver.web.demo.MapPreviewPage",
                  "web/wicket/bookmarkable/org.geoserver.web.demo.DemoRequestsPage"]:
        probe_endpoint(
            f"gs_web_{page.replace('/', '_')}",
            f"{GEOSERVER_URL}/{page}",
            save_subdir="geoserver/web",
            save_filename=f"gs_{page.replace('/', '_')}.html"
        )


# ════════════════════════════════════════════════════════════════════════════
# PHASE 7: GeoServer WFS Room Layer Features
# ════════════════════════════════════════════════════════════════════════════

def phase7_wfs_room_features():
    """Get WFS features for room layers not yet downloaded."""
    print("\n" + "=" * 80)
    print("PHASE 7: WFS Room Layer Feature Extraction (Sampling)")
    print("=" * 80)

    buildings = load_building_ids()

    # Check which room CSVs we already have
    existing_csv_dir = EXISTING_DATA / "wfs_data" / "room_csv"
    existing_csvs = set()
    if existing_csv_dir.exists():
        for f in existing_csv_dir.iterdir():
            existing_csvs.add(f.stem)

    # Try to get GeoJSON for room layers we haven't downloaded
    missing_count = 0
    downloaded_count = 0
    for bid in sorted(buildings.keys()):
        for floor in buildings[bid]:
            layer_key = f"{bid}_{floor}"
            if layer_key in existing_csvs:
                continue  # Already have CSV

            missing_count += 1
            resp = safe_get(
                f"{GEOSERVER_URL}/wfs",
                params={
                    "service": "WFS", "version": "1.1.0",
                    "request": "GetFeature",
                    "typeName": f"gis_room:{layer_key}",
                    "outputFormat": "application/json",
                    "maxFeatures": 500
                },
                timeout=15
            )
            if resp and resp.status_code == 200 and len(resp.content) > 50:
                try:
                    data = resp.json()
                    if "features" in data and data["features"]:
                        outdir = OUTPUT_DIR / "wfs_room_geojson"
                        ensure_dir(outdir)
                        with open(outdir / f"{layer_key}.geojson", "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        downloaded_count += 1
                        print(f"    {layer_key}: {len(data['features'])} features")
                except Exception:
                    pass

    print(f"\n  Missing room layers: {missing_count}, Downloaded: {downloaded_count}")


# ════════════════════════════════════════════════════════════════════════════
# Generate Final Report
# ════════════════════════════════════════════════════════════════════════════

def generate_report():
    """Generate comprehensive report of all findings."""
    print("\n" + "=" * 80)
    print("GENERATING FINAL REPORT")
    print("=" * 80)

    report = {
        "timestamp": datetime.now().isoformat(),
        "total_probes": len(RESULTS),
        "successful_probes": sum(1 for r in RESULTS if r.get("status") == 200),
        "failed_probes": sum(1 for r in RESULTS if r.get("status") != 200),
        "new_data_items": len(FINDINGS["new_data"]),
        "interesting_findings": len(FINDINGS["interesting"]),
        "findings": FINDINGS,
        "all_results": RESULTS
    }

    ensure_dir(OUTPUT_DIR)

    # Save full results
    with open(OUTPUT_DIR / "probe_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Save summary
    with open(OUTPUT_DIR / "PROBE_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# Deep Probe V2 - Comprehensive Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- Total probes: {len(RESULTS)}\n")
        f.write(f"- Successful (HTTP 200): {report['successful_probes']}\n")
        f.write(f"- Failed: {report['failed_probes']}\n")
        f.write(f"- New data items saved: {len(FINDINGS['new_data'])}\n")
        f.write(f"- Interesting findings: {len(FINDINGS['interesting'])}\n\n")

        f.write("## New Data Saved\n\n")
        for item in FINDINGS["new_data"]:
            f.write(f"- **{item['name']}**: {item.get('file', 'N/A')} ({item.get('size', 'N/A')})\n")

        f.write("\n## Interesting Findings\n\n")
        for item in FINDINGS["interesting"]:
            f.write(f"- **{item['name']}**: {item.get('url', 'N/A')[:100]} ({item.get('size', 'N/A')} bytes)\n")
            if item.get("preview"):
                f.write(f"  ```\n  {item['preview'][:200]}\n  ```\n")

        f.write("\n## All Probe Results\n\n")
        f.write("| # | Name | Status | Size | Content-Type |\n")
        f.write("|---|------|--------|------|-------------|\n")
        for i, r in enumerate(RESULTS):
            f.write(f"| {i+1} | {r['name'][:40]} | {r['status']} | {r['size']} | {r.get('content_type', '')[:30]} |\n")

    print(f"\nReport saved to: {OUTPUT_DIR / 'PROBE_REPORT.md'}")
    print(f"Full results: {OUTPUT_DIR / 'probe_results.json'}")
    print(f"\nNew data items: {len(FINDINGS['new_data'])}")
    print(f"Interesting findings: {len(FINDINGS['interesting'])}")


# ════════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("DEEP PROBE V2 - NYCU Yangming Campus GIS Server")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 80)

    ensure_dir(OUTPUT_DIR)

    # Quick connectivity test
    print("\nConnectivity test...")
    resp = safe_get(f"{PUBLIC_URL}/buildinfo.htm",
                    params={"action": "search", "q": "%"}, timeout=10)
    if resp is None or resp.status_code != 200:
        print("WARNING: Server may be unreachable. Continuing anyway...")
    else:
        print(f"  Server OK (status {resp.status_code}, {len(resp.content)} bytes)")

    # Run all phases
    phase1_public_api_deep_probe()
    phase2_geoserver_deep_probe()
    phase3_room_bounds_extraction()
    phase4_room_details_extraction()
    phase5_data_transmission_api()
    phase6_endpoint_discovery()
    phase7_wfs_room_features()

    # Generate report
    generate_report()

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
