"""Download all data from ymmap GIS API backend (ymspace.ga.nycu.edu.tw)."""
import sys
import json
import urllib.request
import urllib.parse
import os
import time
import ssl

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://ymspace.ga.nycu.edu.tw/gisweb/public"
OUT_DIR = r"C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive\api_data"

with open(os.path.join(OUT_DIR, "buildings.json"), "r", encoding="utf-8") as f:
    bdata = json.load(f)

# 1. POST to loadImage for each building
building_images = {}
for b in bdata["buildings"]:
    bid = b["id"]
    url = f"{BASE}/buildinfo.htm?action=loadImage"
    data = f"buildId={bid}&naviKey=buildinfo".encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            d = result.get("data")
            if d is not None and str(d) not in ("null", "None", ""):
                building_images[bid] = d
                print(f'  {bid:8s} | {b["name"]:20s} | images found')
    except Exception as e:
        pass
    time.sleep(0.1)

print(f"Buildings with images: {len(building_images)}")
with open(os.path.join(OUT_DIR, "building_images.json"), "w", encoding="utf-8") as f:
    json.dump(building_images, f, ensure_ascii=False, indent=2)

# 2. Building boundaries (polygon)
all_bounds = {}
for b in bdata["buildings"]:
    bid = b["id"]
    url = f"{BASE}/buildinfo.htm?action=getBoundByBuildId&buildId={urllib.parse.quote(bid)}&proj=EPSG:4326"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("data"):
                all_bounds[bid] = result["data"]
    except Exception:
        pass
    time.sleep(0.05)

print(f"Buildings with boundaries: {len(all_bounds)}")
with open(os.path.join(OUT_DIR, "building_bounds.json"), "w", encoding="utf-8") as f:
    json.dump(all_bounds, f, ensure_ascii=False, indent=2)

# 3. Building bounding boxes
all_bboxes = {}
for b in bdata["buildings"]:
    bid = b["id"]
    url = f"{BASE}/buildinfo.htm?action=getBoundingBoxByBuildId&buildId={urllib.parse.quote(bid)}&proj=EPSG:4326"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("data"):
                all_bboxes[bid] = result["data"]
    except Exception:
        pass
    time.sleep(0.05)

print(f"Buildings with bboxes: {len(all_bboxes)}")
with open(os.path.join(OUT_DIR, "building_bboxes.json"), "w", encoding="utf-8") as f:
    json.dump(all_bboxes, f, ensure_ascii=False, indent=2)

# 4. Centroids
all_centroids = {}
for b in bdata["buildings"]:
    bid = b["id"]
    url = f"{BASE}/buildinfo.htm?action=getCentroidByBuildId&buildId={urllib.parse.quote(bid)}&proj=EPSG:4326"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("data"):
                all_centroids[bid] = result["data"]
    except Exception:
        pass
    time.sleep(0.05)

print(f"Buildings with centroids: {len(all_centroids)}")
with open(os.path.join(OUT_DIR, "centroids.json"), "w", encoding="utf-8") as f:
    json.dump(all_centroids, f, ensure_ascii=False, indent=2)

# 5. GIS layers (overlay layers from GeoServer)
gis_url = "https://ymspace.ga.nycu.edu.tw:8080/geoserver"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Get WFS capabilities for vector data
wfs_url = f"{gis_url}/wfs?service=WFS&version=1.1.0&request=GetCapabilities"
try:
    req = urllib.request.Request(wfs_url)
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        wfs_data = resp.read()
        with open(os.path.join(OUT_DIR, "wfs_capabilities.xml"), "wb") as f:
            f.write(wfs_data)
        print(f"WFS capabilities: {len(wfs_data)} bytes")
except Exception as e:
    print(f"WFS error: {e}")

print("\nAll API data saved!")
