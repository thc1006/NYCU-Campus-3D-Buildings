"""
Download DescribeFeatureType XSD schemas from NYCU GIS GeoServer
for all specified layers, and produce a summary JSON.
"""

import json
import os
import ssl
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────────────────

BASE_URL = "https://ymspace.ga.nycu.edu.tw:8080/geoserver"
OUTPUT_DIR = r"C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive\api_data\schemas"

# SSL context that skips certificate verification
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

# Layers to fetch: (workspace, layer_name, description)
LAYERS = [
    # gis workspace
    ("gis", "gis_building_geom", "建築物幾何"),
    ("gis", "gis_aed", "AED"),
    ("gis", "gis_atm", "ATM"),
    ("gis", "gis_artwork", "公共藝術"),
    ("gis", "gis_restaurant", "餐廳"),
    ("gis", "gis_campusphotos", "校園照片"),
    ("gis", "gis_conveniencestore", "便利商店"),
    ("gis", "gis_postoffice", "郵局"),
    ("gis", "gis_emergencycall", "緊急電話"),
    ("gis", "gis_securityoffice", "警衛室"),
    ("gis", "gis_gateway", "校門"),
    ("gis", "gis_busstop", "公車站"),
    ("gis", "gis_busroutes_1", "公車路線"),
    ("gis", "gis_handicapparking2", "無障礙停車位"),
    ("gis", "gis_barrierfreetoilet2", "無障礙廁所"),
    ("gis", "gis_elevator2", "電梯"),
    ("gis", "gis_auditorium2", "禮堂/演講廳"),
    ("gis", "gis_wheelchairramp", "輪椅坡道"),
    ("gis", "gis_sport", "運動設施"),
    ("gis", "gis_sport_p", "運動設施(點)"),
    ("gis", "gis_block", "街廓"),
    ("gis", "gis_campus", "校區"),
    ("gis", "gis_parking", "停車場"),
    ("gis", "gis_sidewalk_1", "人行道"),
    ("gis", "gss_sidewalk", "人行道(gss)"),
    ("gis", "toilet", "廁所"),
    ("gis", "test_c", "測試圖層"),
    ("gis", "gis_parcel0821line", "地籍線0821"),
    ("gis", "gis_parcel0981line", "地籍線0981"),
    ("gis", "bak_gis_building_geom_v1", "建築物幾何備份v1"),
    # gis_room workspace
    ("gis_room", "B005_1F", "活動中心1樓"),
    ("gis_room", "P003_1F", "圖書資訊大樓1樓"),
    ("gis_room", "Y001_1F", "護理館1樓"),
]


# ── XSD namespace map ──────────────────────────────────────────────────────────

XSD_NS = "http://www.w3.org/2001/XMLSchema"
NS = {"xsd": XSD_NS}


def build_url(workspace: str, layer: str) -> str:
    """Build the DescribeFeatureType WFS URL."""
    return (
        f"{BASE_URL}/{workspace}/wfs"
        f"?service=WFS&version=1.1.0"
        f"&request=DescribeFeatureType"
        f"&typeName={workspace}:{layer}"
    )


def download_xsd(url: str, timeout: int = 30) -> str:
    """Download raw XSD text from the GeoServer."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def parse_xsd(xsd_text: str):
    """
    Parse an XSD schema returned by DescribeFeatureType.

    Returns a list of dicts:
        [{"name": "col_name", "type": "xsd_type", "nillable": True/False}, ...]
    and the geometry type string (or None).
    """
    root = ET.fromstring(xsd_text)

    columns = []
    geometry_type = None

    # Find all <xsd:element> inside the <xsd:sequence>
    for elem in root.iter(f"{{{XSD_NS}}}element"):
        name = elem.get("name")
        col_type = elem.get("type", "")
        nillable = elem.get("nillable", "false").lower() == "true"
        min_occurs = elem.get("minOccurs", "1")
        max_occurs = elem.get("maxOccurs", "1")

        if not name:
            continue

        # Skip the top-level feature type element (has no type= or has complexType child)
        if elem.find(f"{{{XSD_NS}}}complexType") is not None:
            continue

        # Detect geometry columns
        is_geom = False
        if "gml:" in col_type:
            is_geom = True
            geometry_type = col_type

        columns.append({
            "name": name,
            "type": col_type,
            "nillable": nillable,
            "minOccurs": min_occurs,
            "maxOccurs": max_occurs,
            "is_geometry": is_geom,
        })

    return columns, geometry_type


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    summary = {
        "generated_at": datetime.now().isoformat(),
        "geoserver_base": BASE_URL,
        "total_layers": len(LAYERS),
        "layers": [],
    }

    success_count = 0
    fail_count = 0

    for workspace, layer, description in LAYERS:
        url = build_url(workspace, layer)
        file_name = f"{workspace}__{layer}.xsd"
        file_path = os.path.join(OUTPUT_DIR, file_name)

        print(f"[{workspace}:{layer}] Downloading ... ", end="", flush=True)

        try:
            xsd_text = download_xsd(url)

            # Save raw XSD
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(xsd_text)

            # Parse schema
            columns, geom_type = parse_xsd(xsd_text)

            layer_info = {
                "workspace": workspace,
                "layer": layer,
                "description": description,
                "full_type_name": f"{workspace}:{layer}",
                "url": url,
                "xsd_file": file_name,
                "status": "success",
                "geometry_type": geom_type,
                "num_columns": len(columns),
                "columns": columns,
            }

            print(f"OK  ({len(columns)} columns, geom={geom_type})")
            success_count += 1

        except Exception as exc:
            layer_info = {
                "workspace": workspace,
                "layer": layer,
                "description": description,
                "full_type_name": f"{workspace}:{layer}",
                "url": url,
                "xsd_file": file_name,
                "status": "error",
                "error": str(exc),
                "geometry_type": None,
                "num_columns": 0,
                "columns": [],
            }
            print(f"FAILED  ({exc})")
            fail_count += 1

        summary["layers"].append(layer_info)

        # Be polite to the server
        time.sleep(0.3)

    # ── Summary stats ──────────────────────────────────────────────────────────
    summary["success_count"] = success_count
    summary["fail_count"] = fail_count

    summary_path = os.path.join(OUTPUT_DIR, "schema_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"Done!  Success: {success_count}  |  Failed: {fail_count}")
    print(f"XSD files saved to:  {OUTPUT_DIR}")
    print(f"Summary JSON saved:  {summary_path}")


if __name__ == "__main__":
    main()
