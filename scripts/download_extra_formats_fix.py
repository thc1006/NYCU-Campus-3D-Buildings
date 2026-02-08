"""
Fix script for Phase 6 (WCS), Phase 7 (REST), Phase 8 (GML 3.2) issues.
Also adds KML/KMZ exports and Atom feed format.
"""

import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(r"C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive\extra_formats")
WMS_BASE = "https://ymspace.ga.nycu.edu.tw:8080/geoserver/wms"
WFS_BASE = "https://ymspace.ga.nycu.edu.tw:8080/geoserver/wfs"
WCS_BASE = "https://ymspace.ga.nycu.edu.tw:8080/geoserver/wcs"
DELAY = 0.3
TIMEOUT = 30

CAMPUS_LAYERS = [
    "gis:gis_building_geom",
    "gis:gis_campus",
    "gis:gis_parking",
    "gis:gis_busstop",
    "gis:gis_aed",
    "gis:gis_restaurant",
]

YM_BBOX = "121.505,25.115,121.535,25.140"

results = {"timestamp": datetime.now().isoformat(), "fixes": {}}


def safe_filename(name):
    return name.replace(":", "_").replace("/", "_")


def download(url, filepath, desc=""):
    print(f"  [{desc}]")
    print(f"    URL: {url[:140]}...")
    filepath.parent.mkdir(parents=True, exist_ok=True)
    try:
        resp = requests.get(url, verify=False, timeout=TIMEOUT)
        ct = resp.headers.get("Content-Type", "unknown")
        size = len(resp.content)
        print(f"    Status: {resp.status_code}, Type: {ct}, Size: {size:,} bytes")

        if resp.status_code != 200:
            print(f"    FAILED: HTTP {resp.status_code}")
            return {"status": "failed", "http": resp.status_code, "ct": ct}

        # Check for service exception
        if size > 0 and ("xml" in ct.lower() or "text" in ct.lower()):
            preview = resp.text[:500]
            if "ServiceException" in preview or "ExceptionReport" in preview:
                print(f"    SERVICE EXCEPTION")
                filepath.with_suffix(filepath.suffix + ".error.xml").write_text(
                    resp.text, encoding="utf-8"
                )
                return {"status": "exception", "ct": ct, "preview": preview[:200]}

        filepath.write_bytes(resp.content)
        print(f"    SAVED: {filepath.name} ({size:,} bytes)")
        return {"status": "ok", "size": size, "ct": ct, "file": str(filepath)}

    except Exception as e:
        print(f"    ERROR: {e}")
        return {"status": "error", "msg": str(e)[:200]}


def main():
    print("=" * 70)
    print("EXTRA FORMAT FIX SCRIPT")
    print("=" * 70)

    # ======================================
    # FIX 1: GML 3.2 via WFS (correct format param)
    # ======================================
    print("\n--- FIX 1: GML 3.2 via WFS (correct format parameter) ---")
    gml_results = {}

    # GeoServer WFS 2.0 default output is GML 3.2; try without explicit outputFormat
    for layer in CAMPUS_LAYERS:
        sf = safe_filename(layer)
        fp = BASE_DIR / "gml32" / f"{sf}_gml32.xml"
        url = (
            f"{WFS_BASE}?service=WFS&version=2.0.0&request=GetFeature"
            f"&typeNames={layer}"
            f"&count=50"
        )
        r = download(url, fp, f"GML 3.2 (default WFS 2.0): {layer}")
        gml_results[layer] = r
        time.sleep(DELAY)

    results["fixes"]["gml32_default"] = gml_results

    # Also try explicit GML 3.2 with proper URL-encoded format
    print("\n--- FIX 1b: GML 3.2 with explicit format ---")
    gml_results2 = {}
    for layer in CAMPUS_LAYERS:
        sf = safe_filename(layer)
        fp = BASE_DIR / "gml32" / f"{sf}_gml32_explicit.xml"
        url = (
            f"{WFS_BASE}?service=WFS&version=2.0.0&request=GetFeature"
            f"&typeNames={layer}"
            f"&outputFormat=gml32"
            f"&count=50"
        )
        r = download(url, fp, f"GML 3.2 (explicit gml32): {layer}")
        gml_results2[layer] = r
        time.sleep(DELAY)

    results["fixes"]["gml32_explicit"] = gml_results2

    # ======================================
    # FIX 2: WCS - Parse capabilities properly
    # ======================================
    print("\n--- FIX 2: WCS Coverage Extraction ---")
    wcs_results = {}

    # Read the WCS v2 capabilities we already downloaded
    wcs_v2_file = BASE_DIR / "wcs" / "wcs_capabilities_v2.xml"
    if wcs_v2_file.exists():
        text = wcs_v2_file.read_text(encoding="utf-8", errors="replace")
        print(f"  WCS v2 capabilities: {len(text):,} chars")

        # Search for coverage identifiers more broadly
        import re

        # Look for CoverageId, Identifier, CoverageSummary patterns
        coverage_ids = set()

        # Pattern 1: <wcs:CoverageId>xxx</wcs:CoverageId>
        for m in re.finditer(r"<(?:\w+:)?CoverageId>([^<]+)</(?:\w+:)?CoverageId>", text):
            coverage_ids.add(m.group(1))

        # Pattern 2: <Identifier>xxx</Identifier> within CoverageSummary
        for m in re.finditer(r"<(?:\w+:)?Identifier>([^<]+)</(?:\w+:)?Identifier>", text):
            coverage_ids.add(m.group(1))

        # Pattern 3: <CoverageSubtype>
        coverage_subtypes = set()
        for m in re.finditer(r"<(?:\w+:)?CoverageSubtype>([^<]+)", text):
            coverage_subtypes.add(m.group(1))

        if coverage_ids:
            print(f"  Found {len(coverage_ids)} coverage IDs: {coverage_ids}")
            for cov_id in list(coverage_ids)[:5]:
                sf = safe_filename(cov_id)

                # Try DescribeCoverage first
                dc_url = (
                    f"{WCS_BASE}?service=WCS&version=2.0.1"
                    f"&request=DescribeCoverage"
                    f"&CoverageId={cov_id}"
                )
                dc_fp = BASE_DIR / "wcs" / f"{sf}_describe.xml"
                r = download(dc_url, dc_fp, f"DescribeCoverage: {cov_id}")
                wcs_results[f"describe_{cov_id}"] = r
                time.sleep(DELAY)

                # Try GetCoverage
                gc_url = (
                    f"{WCS_BASE}?service=WCS&version=2.0.1"
                    f"&request=GetCoverage"
                    f"&CoverageId={cov_id}"
                    f"&format=image/tiff"
                )
                gc_fp = BASE_DIR / "wcs" / f"{sf}_coverage.tiff"
                r = download(gc_url, gc_fp, f"GetCoverage: {cov_id}")
                wcs_results[f"coverage_{cov_id}"] = r
                time.sleep(DELAY)
        else:
            print("  No CoverageId found in WCS capabilities.")

            # Check WCS v1.1 capabilities
            wcs_v1_file = BASE_DIR / "wcs" / "wcs_capabilities.xml"
            if wcs_v1_file.exists():
                v1_text = wcs_v1_file.read_text(encoding="utf-8", errors="replace")
                for m in re.finditer(r"<(?:\w+:)?Identifier>([^<]+)</(?:\w+:)?Identifier>", v1_text):
                    coverage_ids.add(m.group(1))
                if coverage_ids:
                    print(f"  Found in v1.1: {coverage_ids}")
                    for cov_id in list(coverage_ids)[:5]:
                        sf = safe_filename(cov_id)
                        dc_url = (
                            f"{WCS_BASE}?service=WCS&version=1.1.1"
                            f"&request=DescribeCoverage"
                            f"&identifiers={cov_id}"
                        )
                        dc_fp = BASE_DIR / "wcs" / f"{sf}_describe_v1.xml"
                        r = download(dc_url, dc_fp, f"DescribeCoverage v1.1: {cov_id}")
                        wcs_results[f"describe_v1_{cov_id}"] = r
                        time.sleep(DELAY)

        if coverage_subtypes:
            print(f"  Coverage subtypes found: {coverage_subtypes}")
            wcs_results["subtypes"] = list(coverage_subtypes)

    else:
        print("  WCS capabilities file not found, downloading fresh...")
        wcs_cap_url = f"{WCS_BASE}?service=WCS&version=2.0.1&request=GetCapabilities"
        fp = BASE_DIR / "wcs" / "wcs_capabilities_v2_fresh.xml"
        r = download(wcs_cap_url, fp, "WCS GetCapabilities v2.0.1 (fresh)")
        wcs_results["capabilities_fresh"] = r
        time.sleep(DELAY)

    results["fixes"]["wcs"] = wcs_results

    # ======================================
    # FIX 3: KML/KMZ via WMS
    # ======================================
    print("\n--- FIX 3: KML/KMZ Exports via WMS ---")
    kml_results = {}

    for layer in CAMPUS_LAYERS:
        sf = safe_filename(layer)

        # KML
        fp = BASE_DIR / "kml_kmz" / f"{sf}.kml"
        url = (
            f"{WMS_BASE}?service=WMS&version=1.1.0&request=GetMap"
            f"&layers={layer}"
            f"&bbox={YM_BBOX}"
            f"&width=1200&height=1000"
            f"&srs=EPSG:4326"
            f"&styles="
            f"&format=application/vnd.google-earth.kml+xml"
        )
        r = download(url, fp, f"KML: {layer}")
        kml_results[f"{layer}_kml"] = r
        time.sleep(DELAY)

        # KMZ
        fp = BASE_DIR / "kml_kmz" / f"{sf}.kmz"
        url = (
            f"{WMS_BASE}?service=WMS&version=1.1.0&request=GetMap"
            f"&layers={layer}"
            f"&bbox={YM_BBOX}"
            f"&width=1200&height=1000"
            f"&srs=EPSG:4326"
            f"&styles="
            f"&format=application/vnd.google-earth.kmz"
        )
        r = download(url, fp, f"KMZ: {layer}")
        kml_results[f"{layer}_kmz"] = r
        time.sleep(DELAY)

    results["fixes"]["kml_kmz"] = kml_results

    # ======================================
    # FIX 4: Atom feed via WMS
    # ======================================
    print("\n--- FIX 4: Atom Feed via WMS ---")
    atom_results = {}

    for layer in CAMPUS_LAYERS:
        sf = safe_filename(layer)
        fp = BASE_DIR / "atom" / f"{sf}.atom.xml"
        url = (
            f"{WMS_BASE}?service=WMS&version=1.1.0&request=GetMap"
            f"&layers={layer}"
            f"&bbox={YM_BBOX}"
            f"&width=800&height=600"
            f"&srs=EPSG:4326"
            f"&styles="
            f"&format=application/atom+xml"
        )
        r = download(url, fp, f"Atom: {layer}")
        atom_results[layer] = r
        time.sleep(DELAY)

    results["fixes"]["atom"] = atom_results

    # ======================================
    # FIX 5: WFS CSV and other output formats
    # ======================================
    print("\n--- FIX 5: WFS alternate output formats ---")
    wfs_alt_results = {}

    wfs_formats = [
        ("csv", "csv"),
        ("application/json", "json"),
        ("application/vnd.google-earth.kml+xml", "kml"),
    ]

    for layer in CAMPUS_LAYERS:
        sf = safe_filename(layer)
        for fmt, ext in wfs_formats:
            fp = BASE_DIR / "wfs_formats" / ext / f"{sf}.{ext}"
            url = (
                f"{WFS_BASE}?service=WFS&version=2.0.0&request=GetFeature"
                f"&typeNames={layer}"
                f"&outputFormat={fmt}"
                f"&count=200"
            )
            r = download(url, fp, f"WFS {ext}: {layer}")
            wfs_alt_results[f"{layer}_{ext}"] = r
            time.sleep(DELAY)

    results["fixes"]["wfs_alt_formats"] = wfs_alt_results

    # ======================================
    # FIX 6: WMS GetFeatureInfo (identify features at a point)
    # ======================================
    print("\n--- FIX 6: WMS GetFeatureInfo samples ---")
    fi_results = {}

    # Sample points on Yangming campus
    sample_points = [
        ("center", 620, 500),
        ("north", 600, 200),
        ("south", 600, 800),
    ]

    for layer in CAMPUS_LAYERS[:3]:  # Just test with 3 layers
        sf = safe_filename(layer)
        for pt_name, x, y in sample_points:
            fp = BASE_DIR / "feature_info" / f"{sf}_{pt_name}.json"
            url = (
                f"{WMS_BASE}?service=WMS&version=1.1.0&request=GetFeatureInfo"
                f"&layers={layer}"
                f"&query_layers={layer}"
                f"&bbox={YM_BBOX}"
                f"&width=1200&height=1000"
                f"&srs=EPSG:4326"
                f"&x={x}&y={y}"
                f"&info_format=application/json"
                f"&feature_count=10"
            )
            r = download(url, fp, f"FeatureInfo {pt_name}: {layer}")
            fi_results[f"{layer}_{pt_name}"] = r
            time.sleep(DELAY)

    results["fixes"]["feature_info"] = fi_results

    # ======================================
    # FIX 7: Animated GIF (multi-layer composite)
    # ======================================
    print("\n--- FIX 7: Animated GIF and PNG8 composites ---")
    special_results = {}

    special_formats = [
        ("image/gif;subtype=animated", "animated.gif"),
        ("image/png8", "png8.png"),
        ("image/vnd.jpeg-png", "jpeg-png.png"),
    ]

    combined = ",".join(CAMPUS_LAYERS)
    for fmt_mime, filename in special_formats:
        fp = BASE_DIR / "special" / f"combined_{filename}"
        url = (
            f"{WMS_BASE}?service=WMS&version=1.1.0&request=GetMap"
            f"&layers={combined}"
            f"&bbox={YM_BBOX}"
            f"&width=1600&height=1200"
            f"&srs=EPSG:4326"
            f"&styles="
            f"&format={fmt_mime}"
        )
        r = download(url, fp, f"Special format: {fmt_mime}")
        special_results[fmt_mime] = r
        time.sleep(DELAY)

    results["fixes"]["special_formats"] = special_results

    # ======================================
    # FIX 8: WMS GetStyles (SLD)
    # ======================================
    print("\n--- FIX 8: WMS GetStyles (SLD) ---")
    sld_results = {}

    for layer in CAMPUS_LAYERS:
        sf = safe_filename(layer)
        fp = BASE_DIR / "sld_styles" / f"{sf}_style.sld"
        url = (
            f"{WMS_BASE}?service=WMS&version=1.1.1"
            f"&request=GetStyles"
            f"&layers={layer}"
        )
        r = download(url, fp, f"SLD Style: {layer}")
        sld_results[layer] = r
        time.sleep(DELAY)

    results["fixes"]["sld_styles"] = sld_results

    # ======================================
    # Save results
    # ======================================
    results["completed"] = datetime.now().isoformat()
    (BASE_DIR / "FIX_DOWNLOAD_SUMMARY.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    # Count successes
    total = 0
    success = 0
    failed = 0
    for cat_name, cat_data in results["fixes"].items():
        if isinstance(cat_data, dict):
            for key, val in cat_data.items():
                if isinstance(val, dict) and "status" in val:
                    total += 1
                    if val["status"] == "ok":
                        success += 1
                    else:
                        failed += 1

    print("\n" + "=" * 70)
    print("FIX SCRIPT COMPLETE")
    print(f"  Total: {total} | Success: {success} | Failed: {failed}")
    print(f"  Success rate: {success/max(total,1)*100:.1f}%")
    print("=" * 70)


if __name__ == "__main__":
    main()
