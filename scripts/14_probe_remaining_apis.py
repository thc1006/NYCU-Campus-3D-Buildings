#!/usr/bin/env python3
"""
Probe ALL remaining/undiscovered API endpoints on ymspace.ga.nycu.edu.tw.
Tests every known action across all controllers to find hidden data.

Output: data/ymmap_archive/api_data/api_probe_results.json
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

API_BASE = "https://ymspace.ga.nycu.edu.tw/gisweb/public"


def fetch(url, method='GET', data=None, timeout=15):
    """Fetch URL, return (status, content_type, body_text)."""
    req = urllib.request.Request(url, method=method)
    if data:
        req.data = data.encode('utf-8')
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            body = resp.read()
            ct = resp.headers.get('Content-Type', '')
            try:
                text = body.decode('utf-8')
            except Exception:
                text = f"<binary {len(body)} bytes>"
            return resp.status, ct, text
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace') if e.fp else ''
        return e.code, '', body[:500]
    except Exception as e:
        return 0, '', str(e)


def main():
    results = {}

    # ================================================================
    # 1. userrole.htm endpoints (layer permissions)
    # ================================================================
    print("=== userrole.htm ===")

    tests_userrole = [
        ("findAllLayers", f"{API_BASE}/userrole.htm?action=findAllLayers"),
        ("findPublicDataOfAllLayers", f"{API_BASE}/userrole.htm?action=findPublicDataOfAllLayers"),
        ("findAllGroups", f"{API_BASE}/userrole.htm?action=findAllGroups"),
        ("findAll", f"{API_BASE}/userrole.htm?action=findAll"),
        ("listRoles", f"{API_BASE}/userrole.htm?action=listRoles"),
        ("getConfig", f"{API_BASE}/userrole.htm?action=getConfig"),
    ]
    for name, url in tests_userrole:
        status, ct, body = fetch(url)
        preview = body[:200] if len(body) > 200 else body
        results[f"userrole_{name}"] = {"status": status, "size": len(body), "preview": preview}
        print(f"  {name}: HTTP {status}, {len(body)} bytes")
        time.sleep(0.3)

    # ================================================================
    # 2. buildinfo.htm endpoints
    # ================================================================
    print("\n=== buildinfo.htm ===")

    tests_buildinfo = [
        ("loadPublicData_B005", f"{API_BASE}/buildinfo.htm?action=loadPublicData&buildId=B005"),
        ("loadPublicData_P003", f"{API_BASE}/buildinfo.htm?action=loadPublicData&buildId=P003"),
        ("getFloorList_B005", f"{API_BASE}/buildinfo.htm?action=getFloorList&buildId=B005"),
        ("getFloorList_P006", f"{API_BASE}/buildinfo.htm?action=getFloorList&buildId=P006"),
        ("search_empty", f"{API_BASE}/buildinfo.htm?action=search&locale=zh-tw&q=&limit=999"),
        ("search_star", f"{API_BASE}/buildinfo.htm?action=search&locale=zh-tw&q=*&limit=999"),
        ("search_percent", f"{API_BASE}/buildinfo.htm?action=search&locale=zh-tw&q=%25&limit=999"),
        ("getPublicBuildInfo_all", f"{API_BASE}/buildinfo.htm?action=getPublicBuildInfo"),
        ("listAll", f"{API_BASE}/buildinfo.htm?action=listAll"),
        ("findAll", f"{API_BASE}/buildinfo.htm?action=findAll"),
    ]
    for name, url in tests_buildinfo:
        status, ct, body = fetch(url)
        preview = body[:300] if len(body) > 300 else body
        results[f"buildinfo_{name}"] = {"status": status, "size": len(body), "preview": preview}
        print(f"  {name}: HTTP {status}, {len(body)} bytes")
        time.sleep(0.3)

    # ================================================================
    # 3. roominfo.htm endpoints
    # ================================================================
    print("\n=== roominfo.htm ===")

    tests_roominfo = [
        ("findByFloor_B005_1F", f"{API_BASE}/roominfo.htm?action=findByFloor&buildId=B005&floor=1F"),
        ("loadPublicDataByClassNum_B0051F001", f"{API_BASE}/roominfo.htm?action=loadPublicDataByClassNum&classNum=B0051F001"),
        ("findAll", f"{API_BASE}/roominfo.htm?action=findAll"),
        ("listAll", f"{API_BASE}/roominfo.htm?action=listAll"),
        ("search_room", f"{API_BASE}/roominfo.htm?action=search&q=101&limit=20"),
        ("findByBuild_B005", f"{API_BASE}/roominfo.htm?action=findByBuild&buildId=B005"),
        ("queryRoomExists_B005", f"{API_BASE}/roominfo.htm?action=queryRoomExists&tableName=B005_1F&roomId=B0051F001"),
    ]
    for name, url in tests_roominfo:
        status, ct, body = fetch(url)
        preview = body[:300] if len(body) > 300 else body
        results[f"roominfo_{name}"] = {"status": status, "size": len(body), "preview": preview}
        print(f"  {name}: HTTP {status}, {len(body)} bytes")
        time.sleep(0.3)

    # ================================================================
    # 4. route.htm endpoints
    # ================================================================
    print("\n=== route.htm ===")

    tests_route = [
        ("findGeom_B005", f"{API_BASE}/route.htm?action=findGeom&naviKey=gis_building&id=B005"),
        ("findGeom_gis_aed", f"{API_BASE}/route.htm?action=findGeom&naviKey=gis_aed&id=1"),
        ("getHeaders_gis_building", f"{API_BASE}/route.htm?action=getHeaders&naviKey=gis_building"),
        ("getHeaders_gis_campusphotos", f"{API_BASE}/route.htm?action=getHeaders&naviKey=gis_campusphotos"),
        ("findAll_gis_campusphotos", f"{API_BASE}/route.htm?action=findAll&naviKey=gis_campusphotos"),
        ("findAll_gis_block", f"{API_BASE}/route.htm?action=findAll&naviKey=gis_block"),
        ("searchByKeyword", f"{API_BASE}/route.htm?action=searchByKeyword&keyword=library"),
        ("searchByKeyword_zh", f"{API_BASE}/route.htm?action=searchByKeyword&keyword=%E5%9C%96%E6%9B%B8%E9%A4%A8"),
        ("getRouteData", f"{API_BASE}/route.htm?action=getRouteData"),
        ("listAll", f"{API_BASE}/route.htm?action=listAll"),
    ]
    for name, url in tests_route:
        status, ct, body = fetch(url)
        preview = body[:300] if len(body) > 300 else body
        results[f"route_{name}"] = {"status": status, "size": len(body), "preview": preview}
        print(f"  {name}: HTTP {status}, {len(body)} bytes")
        time.sleep(0.3)

    # ================================================================
    # 5. campus.htm endpoints
    # ================================================================
    print("\n=== campus.htm ===")

    tests_campus = [
        ("getCampusList", f"{API_BASE}/campus.htm?action=getCampusList"),
        ("listAllWithExtent", f"{API_BASE}/campus.htm?action=listAllWithExtent"),
        ("findAll", f"{API_BASE}/campus.htm?action=findAll"),
        ("getConfig", f"{API_BASE}/campus.htm?action=getConfig"),
        ("getBound", f"{API_BASE}/campus.htm?action=getBound"),
    ]
    for name, url in tests_campus:
        status, ct, body = fetch(url)
        preview = body[:300] if len(body) > 300 else body
        results[f"campus_{name}"] = {"status": status, "size": len(body), "preview": preview}
        print(f"  {name}: HTTP {status}, {len(body)} bytes")
        time.sleep(0.3)

    # ================================================================
    # 6. uploadfiles.htm endpoints
    # ================================================================
    print("\n=== uploadfiles.htm ===")

    tests_upload = [
        ("listAll", f"{API_BASE}/uploadfiles.htm?action=listAll"),
        ("findAll", f"{API_BASE}/uploadfiles.htm?action=findAll"),
        ("findBySourceType_build", f"{API_BASE}/uploadfiles.htm?action=findBySourceType&sourceType=buildinfo"),
        ("findBySourceType_floor", f"{API_BASE}/uploadfiles.htm?action=findBySourceType&sourceType=floorinfo"),
        ("count", f"{API_BASE}/uploadfiles.htm?action=count"),
        ("listImg_38675", f"{API_BASE}/uploadfiles.htm?action=listImg&q=38675"),
    ]
    for name, url in tests_upload:
        status, ct, body = fetch(url)
        if 'image' in ct:
            preview = f"<image {len(body)} bytes, Content-Type: {ct}>"
        else:
            preview = body[:300] if len(body) > 300 else body
        results[f"uploadfiles_{name}"] = {"status": status, "size": len(body), "content_type": ct, "preview": preview}
        print(f"  {name}: HTTP {status}, {len(body)} bytes, CT: {ct[:50]}")
        time.sleep(0.3)

    # ================================================================
    # 7. Other controllers (discovery)
    # ================================================================
    print("\n=== Discovery: other controllers ===")

    other_endpoints = [
        ("config.htm", f"{API_BASE}/config.htm"),
        ("config_getConfig", f"{API_BASE}/config.htm?action=getConfig"),
        ("system.htm", f"{API_BASE}/system.htm"),
        ("system_getVersion", f"{API_BASE}/system.htm?action=getVersion"),
        ("layer.htm", f"{API_BASE}/layer.htm?action=findAll"),
        ("group.htm", f"{API_BASE}/group.htm?action=findAll"),
        ("poi.htm", f"{API_BASE}/poi.htm?action=findAll"),
        ("navigation.htm", f"{API_BASE}/navigation.htm?action=findAll"),
        ("map.htm", f"{API_BASE}/map.htm"),
        ("auth.htm", f"{API_BASE}/auth.htm"),
        ("user.htm", f"{API_BASE}/user.htm?action=findAll"),
        ("report.htm", f"{API_BASE}/report.htm?action=listAll"),
        ("export.htm", f"{API_BASE}/export.htm?action=listAll"),
        ("statistics.htm", f"{API_BASE}/statistics.htm?action=getStats"),
        ("log.htm", f"{API_BASE}/log.htm?action=findAll"),
        ("news.htm", f"{API_BASE}/news.htm?action=findAll"),
        ("announcement.htm", f"{API_BASE}/announcement.htm?action=findAll"),
        ("file.htm", f"{API_BASE}/file.htm?action=listAll"),
        ("download.htm", f"{API_BASE}/download.htm"),
        ("image.htm", f"{API_BASE}/image.htm?action=listAll"),
        ("search.htm", f"{API_BASE}/search.htm?q=test"),
        ("floorplan.htm", f"{API_BASE}/floorplan.htm?action=findAll"),
    ]
    for name, url in other_endpoints:
        status, ct, body = fetch(url)
        preview = body[:200] if len(body) > 200 else body
        results[f"other_{name}"] = {"status": status, "size": len(body), "preview": preview}
        marker = "***" if status == 200 and len(body) > 10 else ""
        print(f"  {name}: HTTP {status}, {len(body)} bytes {marker}")
        time.sleep(0.2)

    # ================================================================
    # 8. POST-only endpoints
    # ================================================================
    print("\n=== POST-only endpoints ===")

    post_tests = [
        ("dataTransmissionAPI_gis_building",
         f"{API_BASE}/route.htm?action=dataTransmissionAPI",
         json.dumps({"target": "gis_building", "action": "find", "filter": []})),
        ("dataTransmissionAPI_gis_campus",
         f"{API_BASE}/route.htm?action=dataTransmissionAPI",
         json.dumps({"target": "gis_campus", "action": "find", "filter": []})),
        ("loadImage_B005_buildinfo",
         f"{API_BASE}/buildinfo.htm?action=loadImage",
         "buildId=B005&naviKey=buildinfo"),
    ]
    for name, url, data in post_tests:
        status, ct, body = fetch(url, method='POST', data=data)
        preview = body[:300] if len(body) > 300 else body
        results[f"post_{name}"] = {"status": status, "size": len(body), "preview": preview}
        print(f"  {name}: HTTP {status}, {len(body)} bytes")
        time.sleep(0.3)

    # Save all results
    out_path = os.path.join(OUT_DIR, "api_probe_results.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Summary
    print(f"\n=== SUMMARY ===")
    status_200 = sum(1 for v in results.values() if v.get('status') == 200)
    status_other = len(results) - status_200
    print(f"Total endpoints tested: {len(results)}")
    print(f"HTTP 200: {status_200}")
    print(f"Other status: {status_other}")
    print(f"Saved to: {out_path}")

    # Highlight interesting findings
    print(f"\n=== INTERESTING FINDINGS ===")
    for name, v in results.items():
        if v.get('status') == 200 and v.get('size', 0) > 50:
            if 'other_' in name or 'discovery' in name:
                print(f"  ** {name}: {v['size']} bytes - {v.get('preview', '')[:100]}")


if __name__ == "__main__":
    main()
