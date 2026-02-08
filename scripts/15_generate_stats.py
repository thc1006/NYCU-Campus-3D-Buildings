#!/usr/bin/env python3
"""
Generate comprehensive statistics for the ymmap archive.
Output: data/ymmap_archive/ARCHIVE_STATS.json
"""

import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE = os.path.join(BASE_DIR, "data", "ymmap_archive")
API_DATA = os.path.join(ARCHIVE, "api_data")


def count_dir(path):
    """Count files and total size in directory tree."""
    total_files = 0
    total_size = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            total_files += 1
            total_size += os.path.getsize(fp)
    return total_files, total_size


def main():
    stats = {"sections": {}}

    # 1. Building data
    buildings_path = os.path.join(API_DATA, "all_buildings_search.json")
    if os.path.exists(buildings_path):
        with open(buildings_path, 'r', encoding='utf-8') as f:
            bdata = json.load(f)
        buildings = bdata.get('data', [])
        stats["buildings"] = {
            "total": len(buildings),
            "ids": [b['id'] for b in buildings],
            "with_descriptions": sum(1 for b in buildings if b.get('desc')),
        }

    # 2. Room data from WFS
    rooms_dir = os.path.join(ARCHIVE, "wfs_data", "rooms")
    if os.path.exists(rooms_dir):
        total_rooms = 0
        rooms_per_building = {}
        for f in os.listdir(rooms_dir):
            if not f.endswith('.json'):
                continue
            fp = os.path.join(rooms_dir, f)
            with open(fp, 'r', encoding='utf-8') as fh:
                gj = json.load(fh)
            n = len(gj.get('features', []))
            total_rooms += n
            bid = f.split('_')[0]
            rooms_per_building[bid] = rooms_per_building.get(bid, 0) + n
        stats["rooms_wfs"] = {
            "total_geojson_files": len(os.listdir(rooms_dir)),
            "total_rooms": total_rooms,
            "buildings_with_rooms": len(rooms_per_building),
            "top_buildings": sorted(rooms_per_building.items(), key=lambda x: -x[1])[:10],
        }

    # 3. Room data from search API
    rooms_search_path = os.path.join(API_DATA, "room_search_results.json")
    if os.path.exists(rooms_search_path):
        with open(rooms_search_path, 'r', encoding='utf-8') as f:
            rooms_search = json.load(f)
        stats["rooms_search"] = {
            "total_unique_rooms": len(rooms_search),
        }

    # 4. Floor plans
    fp_dir = os.path.join(ARCHIVE, "floor_plans")
    if os.path.exists(fp_dir):
        fp_files, fp_size = count_dir(fp_dir)
        stats["floor_plans_wms"] = {
            "total_files": fp_files,
            "total_size_mb": round(fp_size / 1024 / 1024, 1),
        }

    # 5. Building photos
    bp_dir = os.path.join(ARCHIVE, "building_photos")
    if os.path.exists(bp_dir):
        bp_files, bp_size = count_dir(bp_dir)
        stats["building_photos"] = {
            "total_files": bp_files,
            "total_size_mb": round(bp_size / 1024 / 1024, 1),
        }

    # 6. POI photos
    poi_dir = os.path.join(ARCHIVE, "poi_photos")
    if os.path.exists(poi_dir):
        poi_index_path = os.path.join(poi_dir, "poi_photo_index.json")
        poi_stats = {}
        if os.path.exists(poi_index_path):
            with open(poi_index_path, 'r', encoding='utf-8') as f:
                poi_index = json.load(f)
            for layer, pois in poi_index.items():
                total = sum(len(ids) for ids in pois.values())
                poi_stats[layer] = total
        poi_files, poi_size = count_dir(poi_dir)
        stats["poi_photos"] = {
            "total_files": poi_files - 1,  # exclude index json
            "total_size_mb": round(poi_size / 1024 / 1024, 1),
            "by_layer": poi_stats,
        }

    # 7. GIS layers
    layers_path = os.path.join(API_DATA, "findAllLayers_full.json")
    if os.path.exists(layers_path):
        with open(layers_path, 'r', encoding='utf-8') as f:
            layers_data = json.load(f)
        rows = layers_data.get('rows', [])
        groups = {}
        for row in rows:
            gid = row.get('group_id')
            groups.setdefault(gid, []).append(row['navi_name'])
        stats["gis_layers"] = {
            "total_layers": len(rows),
            "groups": {str(k): v for k, v in groups.items()},
        }

    # 8. dataTransmissionAPI
    dt_stats_path = os.path.join(API_DATA, "dataTransmissionAPI_stats.json")
    if os.path.exists(dt_stats_path):
        with open(dt_stats_path, 'r', encoding='utf-8') as f:
            dt_stats = json.load(f)
        total_records = sum(v for v in dt_stats.values() if isinstance(v, int))
        accessible = sum(1 for v in dt_stats.values() if isinstance(v, int) and v > 0)
        stats["data_transmission_api"] = {
            "layers_tested": len(dt_stats),
            "accessible": accessible,
            "total_records": total_records,
        }

    # 9. Image IDs
    img_path = os.path.join(API_DATA, "all_image_ids.json")
    if os.path.exists(img_path):
        with open(img_path, 'r', encoding='utf-8') as f:
            img_data = json.load(f)
        stats["image_ids"] = {
            "unique_ids": img_data['total_unique_images'],
            "id_range": img_data['id_range'],
        }

    # 10. Grand total
    grand_files, grand_size = count_dir(ARCHIVE)
    stats["grand_total"] = {
        "total_files": grand_files,
        "total_size_mb": round(grand_size / 1024 / 1024, 1),
    }

    # Save
    out_path = os.path.join(ARCHIVE, "ARCHIVE_STATS.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # Print summary
    print("=== YMMAP ARCHIVE STATISTICS ===\n")
    print(f"Buildings: {stats.get('buildings', {}).get('total', '?')}")
    print(f"Rooms (WFS GeoJSON): {stats.get('rooms_wfs', {}).get('total_rooms', '?')}")
    print(f"Rooms (Search API): {stats.get('rooms_search', {}).get('total_unique_rooms', '?')}")
    print(f"GIS Layers: {stats.get('gis_layers', {}).get('total_layers', '?')}")
    print(f"Floor Plan PNGs: {stats.get('floor_plans_wms', {}).get('total_files', '?')} ({stats.get('floor_plans_wms', {}).get('total_size_mb', '?')} MB)")
    print(f"Building Photos: {stats.get('building_photos', {}).get('total_files', '?')} ({stats.get('building_photos', {}).get('total_size_mb', '?')} MB)")
    print(f"POI Photos: {stats.get('poi_photos', {}).get('total_files', '?')} ({stats.get('poi_photos', {}).get('total_size_mb', '?')} MB)")
    print(f"dataTransmissionAPI: {stats.get('data_transmission_api', {}).get('total_records', '?')} records")
    print(f"Image IDs: {stats.get('image_ids', {}).get('unique_ids', '?')}")
    print(f"\nGRAND TOTAL: {stats['grand_total']['total_files']} files, {stats['grand_total']['total_size_mb']} MB")
    print(f"\nSaved to: {out_path}")


if __name__ == "__main__":
    main()
