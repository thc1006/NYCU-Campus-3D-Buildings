"""
Download GeoServer data in export formats not yet captured.
Targets: PDF, SVG, GeoRSS via WMS; REST API metadata; WCS probing.
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

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Fix encoding for Windows
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Configuration
BASE_DIR = Path(r"C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive\extra_formats")
WMS_BASE = "https://ymspace.ga.nycu.edu.tw:8080/geoserver/wms"
WFS_BASE = "https://ymspace.ga.nycu.edu.tw:8080/geoserver/wfs"
WCS_BASE = "https://ymspace.ga.nycu.edu.tw:8080/geoserver/wcs"
REST_BASE = "https://ymspace.ga.nycu.edu.tw:8080/geoserver/rest"
DELAY = 0.3
TIMEOUT = 30

# Campus layers to export
CAMPUS_LAYERS = [
    "gis:gis_building_geom",
    "gis:gis_campus",
    "gis:gis_parking",
    "gis:gis_busstop",
    "gis:gis_aed",
    "gis:gis_restaurant",
]

# Yangming campus bbox (EPSG:4326)
YM_BBOX = "121.505,25.115,121.535,25.140"

# Guangfu campus bbox (EPSG:4326)
GF_BBOX = "120.990,24.780,121.000,24.800"

# Combined wide bbox covering both campuses roughly
WIDE_BBOX = "120.950,24.750,121.600,25.200"

# Results tracking
results = {
    "timestamp": datetime.now().isoformat(),
    "categories": {},
    "summary": {"success": 0, "failed": 0, "empty": 0, "total": 0},
}


def safe_filename(layer_name):
    """Convert layer name to safe filename."""
    return layer_name.replace(":", "_").replace("/", "_")


def download_file(url, filepath, description=""):
    """Download a file with error handling and result tracking."""
    results["summary"]["total"] += 1
    print(f"  Downloading: {description or filepath.name}")
    print(f"    URL: {url[:120]}{'...' if len(url) > 120 else ''}")

    try:
        resp = requests.get(url, verify=False, timeout=TIMEOUT, stream=True)
        status = resp.status_code
        content_type = resp.headers.get("Content-Type", "unknown")
        content_length = len(resp.content)

        print(f"    Status: {status}, Content-Type: {content_type}, Size: {content_length} bytes")

        if status != 200:
            print(f"    FAILED: HTTP {status}")
            results["summary"]["failed"] += 1
            # Save error response for analysis
            error_path = filepath.with_suffix(filepath.suffix + ".error.txt")
            error_path.write_text(
                f"HTTP {status}\nContent-Type: {content_type}\n\n{resp.text[:2000]}",
                encoding="utf-8",
            )
            return {"status": "failed", "http_status": status, "content_type": content_type}

        if content_length == 0:
            print(f"    EMPTY: 0 bytes returned")
            results["summary"]["empty"] += 1
            return {"status": "empty", "http_status": status, "content_type": content_type}

        # Check if response is an XML error (ServiceException)
        if "xml" in content_type.lower() or "text" in content_type.lower():
            text_preview = resp.text[:500]
            if "ServiceException" in text_preview or "ExceptionReport" in text_preview:
                print(f"    SERVICE EXCEPTION detected")
                error_path = filepath.with_suffix(".error.xml")
                error_path.write_text(resp.text, encoding="utf-8")
                results["summary"]["failed"] += 1
                return {
                    "status": "service_exception",
                    "http_status": status,
                    "content_type": content_type,
                    "error_preview": text_preview[:200],
                }

        # Save the file
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(resp.content)

        print(f"    SAVED: {filepath.name} ({content_length:,} bytes)")
        results["summary"]["success"] += 1
        return {
            "status": "success",
            "http_status": status,
            "content_type": content_type,
            "size_bytes": content_length,
            "file": str(filepath),
        }

    except requests.exceptions.Timeout:
        print(f"    TIMEOUT after {TIMEOUT}s")
        results["summary"]["failed"] += 1
        return {"status": "timeout"}
    except requests.exceptions.ConnectionError as e:
        print(f"    CONNECTION ERROR: {e}")
        results["summary"]["failed"] += 1
        return {"status": "connection_error", "error": str(e)[:200]}
    except Exception as e:
        print(f"    ERROR: {e}")
        results["summary"]["failed"] += 1
        return {"status": "error", "error": str(e)[:200]}


def download_wms_format(layer, fmt_name, fmt_mime, ext, bbox, subdir):
    """Download a WMS GetMap in a specific format."""
    safe_layer = safe_filename(layer)
    filename = f"{safe_layer}.{ext}"
    filepath = BASE_DIR / subdir / filename

    url = (
        f"{WMS_BASE}?service=WMS&version=1.1.0&request=GetMap"
        f"&layers={layer}"
        f"&bbox={bbox}"
        f"&width=1200&height=1000"
        f"&srs=EPSG:4326"
        f"&styles="
        f"&format={fmt_mime}"
    )

    result = download_file(url, filepath, f"{layer} as {fmt_name}")
    time.sleep(DELAY)
    return result


# ============================================================
# PHASE 1: PDF exports via WMS
# ============================================================
def phase1_pdf_exports():
    print("\n" + "=" * 70)
    print("PHASE 1: PDF Exports via WMS GetMap")
    print("=" * 70)

    category_results = {}

    for layer in CAMPUS_LAYERS:
        result = download_wms_format(
            layer,
            fmt_name="PDF",
            fmt_mime="application/pdf",
            ext="pdf",
            bbox=YM_BBOX,
            subdir="pdf",
        )
        category_results[layer] = result

    # Also try a combined map with all layers
    combined_layers = ",".join(CAMPUS_LAYERS)
    safe_name = "combined_campus_layers"
    filepath = BASE_DIR / "pdf" / f"{safe_name}.pdf"
    url = (
        f"{WMS_BASE}?service=WMS&version=1.1.0&request=GetMap"
        f"&layers={combined_layers}"
        f"&bbox={YM_BBOX}"
        f"&width=1600&height=1200"
        f"&srs=EPSG:4326"
        f"&styles="
        f"&format=application/pdf"
    )
    result = download_file(url, filepath, "Combined campus layers as PDF")
    category_results["combined"] = result
    time.sleep(DELAY)

    results["categories"]["pdf_wms"] = category_results
    return category_results


# ============================================================
# PHASE 2: SVG exports via WMS
# ============================================================
def phase2_svg_exports():
    print("\n" + "=" * 70)
    print("PHASE 2: SVG Exports via WMS GetMap")
    print("=" * 70)

    category_results = {}

    for layer in CAMPUS_LAYERS:
        result = download_wms_format(
            layer,
            fmt_name="SVG",
            fmt_mime="image/svg+xml",
            ext="svg",
            bbox=YM_BBOX,
            subdir="svg",
        )
        category_results[layer] = result

    # Combined SVG
    combined_layers = ",".join(CAMPUS_LAYERS)
    filepath = BASE_DIR / "svg" / "combined_campus_layers.svg"
    url = (
        f"{WMS_BASE}?service=WMS&version=1.1.0&request=GetMap"
        f"&layers={combined_layers}"
        f"&bbox={YM_BBOX}"
        f"&width=1600&height=1200"
        f"&srs=EPSG:4326"
        f"&styles="
        f"&format=image/svg+xml"
    )
    result = download_file(url, filepath, "Combined campus layers as SVG")
    category_results["combined"] = result
    time.sleep(DELAY)

    results["categories"]["svg_wms"] = category_results
    return category_results


# ============================================================
# PHASE 3: GeoRSS exports via WMS
# ============================================================
def phase3_georss_exports():
    print("\n" + "=" * 70)
    print("PHASE 3: GeoRSS Exports via WMS")
    print("=" * 70)

    category_results = {}

    # Try multiple GeoRSS format strings
    georss_formats = [
        ("application/rss+xml", "rss_xml"),
        ("rss", "rss"),
        ("application/atom+xml", "atom_xml"),
        ("application/rss xml", "rss_xml_alt"),
    ]

    for layer in CAMPUS_LAYERS:
        layer_results = {}
        for fmt_mime, fmt_key in georss_formats:
            safe_layer = safe_filename(layer)
            filename = f"{safe_layer}_{fmt_key}.xml"
            filepath = BASE_DIR / "georss" / filename

            url = (
                f"{WMS_BASE}?service=WMS&version=1.1.0&request=GetMap"
                f"&layers={layer}"
                f"&bbox={YM_BBOX}"
                f"&width=800&height=600"
                f"&srs=EPSG:4326"
                f"&styles="
                f"&format={fmt_mime}"
            )

            result = download_file(url, filepath, f"{layer} as GeoRSS ({fmt_mime})")
            layer_results[fmt_key] = result
            time.sleep(DELAY)

            # If first format works, skip alternatives for this layer
            if result.get("status") == "success":
                break

        category_results[layer] = layer_results

    results["categories"]["georss_wms"] = category_results
    return category_results


# ============================================================
# PHASE 4: Additional WMS formats (GeoTIFF, UTFGrid, AtomPub)
# ============================================================
def phase4_additional_wms():
    print("\n" + "=" * 70)
    print("PHASE 4: Additional WMS Formats (GeoTIFF, UTFGrid, AtomPub)")
    print("=" * 70)

    category_results = {}

    additional_formats = [
        ("image/geotiff", "geotiff", "tiff"),
        ("image/tiff", "tiff", "tiff"),
        ("application/json;type=utfgrid", "utfgrid", "json"),
        ("application/openlayers", "openlayers", "html"),
    ]

    # Test with one representative layer first
    test_layer = "gis:gis_building_geom"

    for fmt_mime, fmt_name, ext in additional_formats:
        safe_layer = safe_filename(test_layer)
        filename = f"{safe_layer}.{ext}"
        filepath = BASE_DIR / "additional_wms" / fmt_name / filename

        url = (
            f"{WMS_BASE}?service=WMS&version=1.1.0&request=GetMap"
            f"&layers={test_layer}"
            f"&bbox={YM_BBOX}"
            f"&width=1200&height=1000"
            f"&srs=EPSG:4326"
            f"&styles="
            f"&format={fmt_mime}"
        )

        result = download_file(url, filepath, f"{test_layer} as {fmt_name}")
        category_results[fmt_name] = result
        time.sleep(DELAY)

        # If format works, download for all layers
        if result.get("status") == "success":
            print(f"  Format {fmt_name} works! Downloading all layers...")
            for layer in CAMPUS_LAYERS:
                if layer == test_layer:
                    continue
                safe_l = safe_filename(layer)
                fp = BASE_DIR / "additional_wms" / fmt_name / f"{safe_l}.{ext}"
                r = download_wms_format(
                    layer, fmt_name, fmt_mime, ext,
                    YM_BBOX, f"additional_wms/{fmt_name}"
                )
                category_results[f"{fmt_name}_{layer}"] = r

    results["categories"]["additional_wms"] = category_results
    return category_results


# ============================================================
# PHASE 5: WMS GetCapabilities - Metadata URLs
# ============================================================
def phase5_capabilities_metadata():
    print("\n" + "=" * 70)
    print("PHASE 5: WMS GetCapabilities & Metadata URLs")
    print("=" * 70)

    category_results = {}

    # Download GetCapabilities
    cap_url = f"{WMS_BASE}?service=WMS&version=1.1.1&request=GetCapabilities"
    cap_filepath = BASE_DIR / "metadata" / "wms_capabilities.xml"
    result = download_file(cap_url, cap_filepath, "WMS GetCapabilities")
    category_results["wms_capabilities"] = result
    time.sleep(DELAY)

    # Parse for MetadataURL elements
    if result.get("status") == "success":
        try:
            cap_text = cap_filepath.read_text(encoding="utf-8", errors="replace")

            # Simple text search for MetadataURL
            metadata_urls = []
            lines = cap_text.split("\n")
            for i, line in enumerate(lines):
                if "MetadataURL" in line or "metadataURL" in line:
                    # Grab surrounding context
                    context = "\n".join(lines[max(0, i - 2) : i + 5])
                    metadata_urls.append(context)

            if metadata_urls:
                print(f"  Found {len(metadata_urls)} MetadataURL references!")
                meta_report = "\n\n---\n\n".join(metadata_urls)
                (BASE_DIR / "metadata" / "metadata_urls_found.txt").write_text(
                    meta_report, encoding="utf-8"
                )
                category_results["metadata_urls_found"] = len(metadata_urls)
            else:
                print("  No MetadataURL elements found in capabilities.")
                category_results["metadata_urls_found"] = 0

            # Also extract supported formats
            formats_found = []
            for line in lines:
                if "<Format>" in line:
                    fmt = line.strip().replace("<Format>", "").replace("</Format>", "").strip()
                    if fmt and fmt not in formats_found:
                        formats_found.append(fmt)

            if formats_found:
                print(f"  Found {len(formats_found)} supported WMS formats:")
                for fmt in formats_found:
                    print(f"    - {fmt}")
                (BASE_DIR / "metadata" / "wms_supported_formats.json").write_text(
                    json.dumps(formats_found, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                category_results["supported_formats"] = formats_found

        except Exception as e:
            print(f"  Error parsing capabilities: {e}")
            category_results["parse_error"] = str(e)

    # Also get WFS capabilities
    wfs_cap_url = f"{WFS_BASE}?service=WFS&version=2.0.0&request=GetCapabilities"
    wfs_filepath = BASE_DIR / "metadata" / "wfs_capabilities.xml"
    result = download_file(wfs_cap_url, wfs_filepath, "WFS GetCapabilities")
    category_results["wfs_capabilities"] = result
    time.sleep(DELAY)

    results["categories"]["capabilities_metadata"] = category_results
    return category_results


# ============================================================
# PHASE 6: WCS (Web Coverage Service) probe
# ============================================================
def phase6_wcs_probe():
    print("\n" + "=" * 70)
    print("PHASE 6: WCS (Web Coverage Service) Probe")
    print("=" * 70)

    category_results = {}

    # First, check WCS capabilities
    wcs_cap_url = f"{WCS_BASE}?service=WCS&version=1.1.1&request=GetCapabilities"
    cap_filepath = BASE_DIR / "wcs" / "wcs_capabilities.xml"
    result = download_file(wcs_cap_url, cap_filepath, "WCS GetCapabilities")
    category_results["wcs_capabilities"] = result
    time.sleep(DELAY)

    # Try alternate WCS version
    wcs_cap_url_2 = f"{WCS_BASE}?service=WCS&version=2.0.1&request=GetCapabilities"
    cap_filepath_2 = BASE_DIR / "wcs" / "wcs_capabilities_v2.xml"
    result2 = download_file(wcs_cap_url_2, cap_filepath_2, "WCS GetCapabilities v2.0.1")
    category_results["wcs_capabilities_v2"] = result2
    time.sleep(DELAY)

    # If capabilities returned, parse for coverage IDs
    for cap_file in [cap_filepath, cap_filepath_2]:
        if cap_file.exists():
            try:
                text = cap_file.read_text(encoding="utf-8", errors="replace")
                if "ServiceException" not in text and "CoverageId" in text:
                    # Extract coverage identifiers
                    coverage_ids = []
                    for line in text.split("\n"):
                        if "CoverageId" in line or "Identifier" in line:
                            # Simple extraction
                            clean = (
                                line.strip()
                                .replace("<CoverageId>", "")
                                .replace("</CoverageId>", "")
                                .replace("<Identifier>", "")
                                .replace("</Identifier>", "")
                                .replace("<wcs:CoverageId>", "")
                                .replace("</wcs:CoverageId>", "")
                                .strip()
                            )
                            if clean and "<" not in clean:
                                coverage_ids.append(clean)

                    if coverage_ids:
                        print(f"  Found {len(coverage_ids)} WCS coverages: {coverage_ids}")
                        category_results["coverage_ids"] = coverage_ids

                        # Try to get coverage for each
                        for cov_id in coverage_ids[:5]:  # Limit to 5
                            safe_id = safe_filename(cov_id)
                            cov_url = (
                                f"{WCS_BASE}?service=WCS&version=2.0.1"
                                f"&request=GetCoverage"
                                f"&CoverageId={cov_id}"
                                f"&format=image/tiff"
                            )
                            cov_filepath = BASE_DIR / "wcs" / f"{safe_id}.tiff"
                            r = download_file(cov_url, cov_filepath, f"WCS Coverage: {cov_id}")
                            category_results[f"coverage_{cov_id}"] = r
                            time.sleep(DELAY)
                    else:
                        print("  No coverage IDs found in WCS capabilities.")
                elif "ServiceException" in text:
                    print(f"  WCS returned ServiceException (may not be enabled).")
                else:
                    print(f"  No CoverageId elements found.")
            except Exception as e:
                print(f"  Error parsing WCS capabilities: {e}")

    results["categories"]["wcs"] = category_results
    return category_results


# ============================================================
# PHASE 7: GeoServer REST API probe
# ============================================================
def phase7_rest_api():
    print("\n" + "=" * 70)
    print("PHASE 7: GeoServer REST API Probe")
    print("=" * 70)

    category_results = {}

    rest_endpoints = [
        ("about/version.json", "version"),
        ("about/status.json", "status"),
        ("about/manifest.json", "manifest"),
        ("workspaces.json", "workspaces"),
        ("layers.json", "layers"),
        ("styles.json", "styles"),
        ("fonts.json", "fonts"),
        ("about/system-status.json", "system_status"),
        ("settings.json", "settings"),
        ("security/self/user.json", "current_user"),
    ]

    for endpoint, name in rest_endpoints:
        url = f"{REST_BASE}/{endpoint}"
        filepath = BASE_DIR / "rest_api" / f"{name}.json"
        result = download_file(url, filepath, f"REST: {endpoint}")
        category_results[name] = result
        time.sleep(DELAY)

        # If the response is JSON, try to pretty-print it
        if result.get("status") == "success" and filepath.exists():
            try:
                raw = filepath.read_text(encoding="utf-8", errors="replace")
                parsed = json.loads(raw)
                filepath.write_text(
                    json.dumps(parsed, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            except (json.JSONDecodeError, Exception):
                pass  # Leave as-is if not valid JSON

    # Try workspace-specific endpoints if workspaces.json was successful
    ws_file = BASE_DIR / "rest_api" / "workspaces.json"
    if ws_file.exists():
        try:
            ws_data = json.loads(ws_file.read_text(encoding="utf-8"))
            workspaces = []
            if "workspaces" in ws_data and "workspace" in ws_data["workspaces"]:
                workspaces = ws_data["workspaces"]["workspace"]
            for ws in workspaces[:5]:
                ws_name = ws.get("name", "")
                if ws_name:
                    # Get layers for this workspace
                    url = f"{REST_BASE}/workspaces/{ws_name}/layers.json"
                    fp = BASE_DIR / "rest_api" / f"workspace_{ws_name}_layers.json"
                    r = download_file(url, fp, f"REST: {ws_name} workspace layers")
                    category_results[f"ws_{ws_name}_layers"] = r
                    time.sleep(DELAY)

                    # Get datastores
                    url2 = f"{REST_BASE}/workspaces/{ws_name}/datastores.json"
                    fp2 = BASE_DIR / "rest_api" / f"workspace_{ws_name}_datastores.json"
                    r2 = download_file(url2, fp2, f"REST: {ws_name} datastores")
                    category_results[f"ws_{ws_name}_datastores"] = r2
                    time.sleep(DELAY)
        except Exception as e:
            print(f"  Error processing workspaces: {e}")

    results["categories"]["rest_api"] = category_results
    return category_results


# ============================================================
# PHASE 8: GML 3.2 via WFS (if not already captured)
# ============================================================
def phase8_gml32_exports():
    print("\n" + "=" * 70)
    print("PHASE 8: GML 3.2 Exports via WFS")
    print("=" * 70)

    category_results = {}

    # GML 3.2 format
    for layer in CAMPUS_LAYERS:
        safe_layer = safe_filename(layer)
        filename = f"{safe_layer}_gml32.xml"
        filepath = BASE_DIR / "gml32" / filename

        url = (
            f"{WFS_BASE}?service=WFS&version=2.0.0&request=GetFeature"
            f"&typeName={layer}"
            f"&outputFormat=application/gml+xml;%20version=3.2"
            f"&count=100"
        )

        result = download_file(url, filepath, f"{layer} as GML 3.2")
        category_results[layer] = result
        time.sleep(DELAY)

    results["categories"]["gml32_wfs"] = category_results
    return category_results


# ============================================================
# PHASE 9: WFS DescribeFeatureType (schema info)
# ============================================================
def phase9_schema_info():
    print("\n" + "=" * 70)
    print("PHASE 9: WFS DescribeFeatureType (Schema Info)")
    print("=" * 70)

    category_results = {}

    for layer in CAMPUS_LAYERS:
        safe_layer = safe_filename(layer)
        filename = f"{safe_layer}_schema.xsd"
        filepath = BASE_DIR / "schemas" / filename

        url = (
            f"{WFS_BASE}?service=WFS&version=2.0.0&request=DescribeFeatureType"
            f"&typeName={layer}"
        )

        result = download_file(url, filepath, f"{layer} schema (XSD)")
        category_results[layer] = result
        time.sleep(DELAY)

    results["categories"]["schemas"] = category_results
    return category_results


# ============================================================
# PHASE 10: WMS GetLegendGraphic for each layer
# ============================================================
def phase10_legends():
    print("\n" + "=" * 70)
    print("PHASE 10: WMS GetLegendGraphic")
    print("=" * 70)

    category_results = {}

    for layer in CAMPUS_LAYERS:
        safe_layer = safe_filename(layer)

        # PNG legend
        filename = f"{safe_layer}_legend.png"
        filepath = BASE_DIR / "legends" / filename
        url = (
            f"{WMS_BASE}?service=WMS&version=1.1.0&request=GetLegendGraphic"
            f"&layer={layer}"
            f"&format=image/png"
            f"&width=200&height=200"
        )
        result = download_file(url, filepath, f"{layer} legend (PNG)")
        category_results[f"{layer}_png"] = result
        time.sleep(DELAY)

        # JSON legend (if supported)
        filename_json = f"{safe_layer}_legend.json"
        filepath_json = BASE_DIR / "legends" / filename_json
        url_json = (
            f"{WMS_BASE}?service=WMS&version=1.1.0&request=GetLegendGraphic"
            f"&layer={layer}"
            f"&format=application/json"
        )
        result_json = download_file(url_json, filepath_json, f"{layer} legend (JSON)")
        category_results[f"{layer}_json"] = result_json
        time.sleep(DELAY)

    results["categories"]["legends"] = category_results
    return category_results


# ============================================================
# PHASE 11: Guangfu campus bbox variants
# ============================================================
def phase11_guangfu_campus():
    print("\n" + "=" * 70)
    print("PHASE 11: Guangfu Campus PDF & SVG (alternate bbox)")
    print("=" * 70)

    category_results = {}

    # Try Guangfu campus bbox for key layers
    gf_layers = ["gis:gis_building_geom", "gis:gis_campus", "gis:gis_parking"]

    for layer in gf_layers:
        # PDF
        result = download_wms_format(
            layer,
            fmt_name="PDF (Guangfu)",
            fmt_mime="application/pdf",
            ext="pdf",
            bbox=GF_BBOX,
            subdir="pdf_guangfu",
        )
        category_results[f"{layer}_pdf_gf"] = result

        # SVG
        result = download_wms_format(
            layer,
            fmt_name="SVG (Guangfu)",
            fmt_mime="image/svg+xml",
            ext="svg",
            bbox=GF_BBOX,
            subdir="svg_guangfu",
        )
        category_results[f"{layer}_svg_gf"] = result

    results["categories"]["guangfu_campus"] = category_results
    return category_results


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("GeoServer Extra Format Downloader")
    print(f"Target: {BASE_DIR}")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    # Create base directory
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    # Run all phases
    phases = [
        ("Phase 1: PDF exports", phase1_pdf_exports),
        ("Phase 2: SVG exports", phase2_svg_exports),
        ("Phase 3: GeoRSS exports", phase3_georss_exports),
        ("Phase 4: Additional WMS formats", phase4_additional_wms),
        ("Phase 5: Capabilities & Metadata", phase5_capabilities_metadata),
        ("Phase 6: WCS probe", phase6_wcs_probe),
        ("Phase 7: REST API probe", phase7_rest_api),
        ("Phase 8: GML 3.2 exports", phase8_gml32_exports),
        ("Phase 9: Schema info", phase9_schema_info),
        ("Phase 10: Legends", phase10_legends),
        ("Phase 11: Guangfu campus", phase11_guangfu_campus),
    ]

    for phase_name, phase_func in phases:
        try:
            phase_func()
        except Exception as e:
            print(f"\n  PHASE ERROR in {phase_name}: {e}")
            traceback.print_exc()
            results["categories"][phase_name] = {"error": str(e)}

    # Save results summary
    results["completed"] = datetime.now().isoformat()
    summary_path = BASE_DIR / "DOWNLOAD_SUMMARY.json"
    summary_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    # Print final summary
    print("\n" + "=" * 70)
    print("DOWNLOAD COMPLETE - SUMMARY")
    print("=" * 70)
    s = results["summary"]
    print(f"  Total requests:  {s['total']}")
    print(f"  Successful:      {s['success']}")
    print(f"  Failed:          {s['failed']}")
    print(f"  Empty:           {s['empty']}")
    print(f"  Success rate:    {s['success']/max(s['total'],1)*100:.1f}%")
    print(f"\n  Results saved to: {summary_path}")

    # Generate human-readable summary
    generate_text_summary()


def generate_text_summary():
    """Generate a human-readable text summary of all downloads."""
    lines = [
        "=" * 70,
        "EXTRA FORMAT DOWNLOAD REPORT",
        f"Generated: {datetime.now().isoformat()}",
        "=" * 70,
        "",
    ]

    for cat_name, cat_data in results["categories"].items():
        lines.append(f"\n--- {cat_name.upper()} ---")
        if isinstance(cat_data, dict):
            for key, val in cat_data.items():
                if isinstance(val, dict):
                    status = val.get("status", "?")
                    size = val.get("size_bytes", 0)
                    ct = val.get("content_type", "")
                    icon = "OK" if status == "success" else "FAIL"
                    size_str = f" ({size:,} bytes)" if size else ""
                    lines.append(f"  [{icon}] {key}: {status}{size_str} [{ct}]")
                else:
                    lines.append(f"  {key}: {val}")
        else:
            lines.append(f"  {cat_data}")

    s = results["summary"]
    lines.extend([
        "",
        "=" * 70,
        "TOTALS",
        f"  Requests: {s['total']} | Success: {s['success']} | "
        f"Failed: {s['failed']} | Empty: {s['empty']}",
        "=" * 70,
    ])

    report_path = BASE_DIR / "DOWNLOAD_REPORT.txt"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Report saved to: {report_path}")


if __name__ == "__main__":
    main()
