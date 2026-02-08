"""
Download NLSC 3D building tiles via quadtree BFS traversal from root.

This script starts from L0 R0 C0 and follows ALL branches that overlap the
target area, downloading every tile at every level. This is the most thorough
download method and serves to verify whether NLSC data exists for a given area.

Previous Script 06 failed because:
  1. Used coordinate formula + buffer=1 (too narrow)
  2. Only checked 9 tiles per level
  3. Didn't follow quadtree children properly

This script fixes all those issues by traversing the full quadtree.

Usage:
  python scripts/08_download_quadtree.py [campus_key ...]
  python scripts/08_download_quadtree.py boai yangming gueiren
  python scripts/08_download_quadtree.py --all-layers gueiren
"""
import collections
import gzip
import json
import math
import os
import struct
import sys
import time
import urllib.request

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- Configuration ---

SERVERS = [
    "https://mapserver01.nlsc.gov.tw/oview//oview",
    "https://mapserver02.nlsc.gov.tw/oview//oview",
    "https://mapserver51.nlsc.gov.tw/oview//oview",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://3dmaps.nlsc.gov.tw/",
}

# NYCU Campus definitions with correct layer names (verified 2025-02)
# Layers listed in order of preference (latest first)
CAMPUSES = {
    'guangfu': {
        'name': '光復校區',
        'name_en': 'Guangfu Campus',
        'center': (120.997, 24.787),
        'bbox': (120.980, 121.015, 24.773, 24.800),
        'layers': ['112_O'],
    },
    'boai': {
        'name': '博愛校區',
        'name_en': 'Boai Campus',
        'center': (120.968, 24.801),
        'bbox': (120.955, 120.982, 24.790, 24.815),
        'layers': ['112_O'],
    },
    'yangming': {
        'name': '陽明校區',
        'name_en': 'Yangming Campus',
        'center': (121.516, 25.120),
        'bbox': (121.503, 121.530, 25.107, 25.133),
        'layers': ['113_A', '112_A', '111_A', '109_A'],
    },
    'liujia': {
        'name': '六家校區',
        'name_en': 'Liujia Campus',
        'center': (121.014, 24.839),
        'bbox': (121.002, 121.025, 24.828, 24.850),
        'layers': ['113_J', '112_J', '111_J_v4'],
    },
    'gueiren': {
        'name': '歸仁校區',
        'name_en': 'Gueiren Campus',
        'center': (120.305, 22.933),
        'bbox': (120.290, 120.320, 22.918, 22.948),
        'layers': ['112_D', '111_D', '113_D'],
    },
}

server_idx = 0


def get_server():
    global server_idx
    server = SERVERS[server_idx % len(SERVERS)]
    server_idx += 1
    return server


def fetch_tile(layer, level, row, col, retries=2):
    """Fetch a single tile from the NLSC oview server."""
    for attempt in range(retries + 1):
        server = get_server()
        url = (
            f"{server}?type=modelset&format=integrate"
            f"&name={layer}&level={level}&Row={row}&Col={col}"
            f"&docname=NODE&epsg=4326"
        )
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                if resp.status == 200:
                    data = resp.read()
                    if len(data) > 0:
                        return data
                return None
        except Exception:
            if attempt < retries:
                time.sleep(0.5)
            continue
    return None


def fetch_layer_info(layer):
    """Fetch layer metadata."""
    server = get_server()
    url = (
        f"{server}?type=modelset&format=integrate"
        f"&name={layer}&docname=LAYER"
    )
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status == 200:
                data = resp.read()
                if len(data) > 0:
                    try:
                        data = gzip.decompress(data)
                    except Exception:
                        pass
                    return data
    except Exception:
        pass
    return None


def tile_geo_bbox(level, row, col):
    """
    Calculate geographic bounding box of a tile.
    PilotGaea formula: Col = floor(lon * 2^L / 160), Row = floor(lat * 2^L / 60)
    Inverse: lon = [C * 160/2^L, (C+1) * 160/2^L], lat = [R * 60/2^L, (R+1) * 60/2^L]
    """
    lon_size = 160.0 / (2 ** level)
    lat_size = 60.0 / (2 ** level)
    return (
        col * lon_size,           # lon_min
        (col + 1) * lon_size,     # lon_max
        row * lat_size,           # lat_min
        (row + 1) * lat_size,     # lat_max
    )


def bbox_overlap(bbox1, bbox2):
    """Check if two (lon_min, lon_max, lat_min, lat_max) bboxes overlap."""
    return (bbox1[0] < bbox2[1] and bbox1[1] > bbox2[0] and
            bbox1[2] < bbox2[3] and bbox1[3] > bbox2[2])


def parse_tile_header(data):
    """Parse tile header to get level, row, col, and children."""
    if data[:2] == b'\x1f\x8b':
        try:
            data = gzip.decompress(data)
        except Exception:
            pass

    info = {'size': len(data)}
    if len(data) >= 12:
        info['level'], info['row'], info['col'] = struct.unpack_from('<III', data, 0)

    # Children at offset 228
    if len(data) >= 232:
        child_count = struct.unpack_from('<I', data, 228)[0]
        if 0 < child_count <= 10:
            children = []
            for i in range(child_count):
                if 232 + i * 4 + 4 <= len(data):
                    children.append(struct.unpack_from('<I', data, 232 + i * 4)[0])
            info['children'] = children
        else:
            info['children'] = []
    else:
        info['children'] = []

    info['has_build_id'] = b'BUILD_ID' in data
    return info


def quadtree_download(layer, target_bbox, output_dir, max_level=15, margin=0.02):
    """
    Download tiles by BFS quadtree traversal from root L0 R0 C0.

    At each level, only follows branches that geographically overlap the
    target bbox (expanded by margin). This ensures complete coverage while
    being efficient.
    """
    expanded_bbox = (
        target_bbox[0] - margin,
        target_bbox[1] + margin,
        target_bbox[2] - margin,
        target_bbox[3] + margin,
    )

    queue = collections.deque([(0, 0, 0)])  # (level, row, col)
    visited = set()
    downloaded = []
    empty_count = 0
    requests_made = 0
    level_stats = {}

    while queue:
        level, row, col = queue.popleft()
        key = (level, row, col)
        if key in visited:
            continue
        visited.add(key)

        # Geographic filtering: skip tiles that don't overlap target area
        # (skip filter at L0-L1 as tiles cover the entire world)
        if level >= 2:
            t_bbox = tile_geo_bbox(level, row, col)
            if not bbox_overlap(t_bbox, expanded_bbox):
                continue

        # Download tile
        requests_made += 1
        data = fetch_tile(layer, level, row, col)

        if data is None or len(data) < 12:
            empty_count += 1
            continue

        # Parse header
        info = parse_tile_header(data)

        # Save tile
        tile_dir = os.path.join(output_dir, f'L{level}')
        os.makedirs(tile_dir, exist_ok=True)
        filename = os.path.join(tile_dir, f'R{row}_C{col}.bin')
        with open(filename, 'wb') as f:
            f.write(data)

        tile_record = {
            'level': level, 'row': row, 'col': col,
            'size': len(data),
            'has_build_id': info['has_build_id'],
            'children': info.get('children', []),
        }
        downloaded.append(tile_record)

        # Update level stats
        if level not in level_stats:
            level_stats[level] = {'tiles': 0, 'bytes': 0, 'with_bldg': 0}
        level_stats[level]['tiles'] += 1
        level_stats[level]['bytes'] += len(data)
        if info['has_build_id']:
            level_stats[level]['with_bldg'] += 1

        # Progress
        sys.stdout.write(
            f'\r  L{level} R{row}_C{col}: {len(data):,}B '
            f'| Total: {len(downloaded)} tiles, {requests_made} reqs  '
        )
        sys.stdout.flush()

        # Add children to queue
        if level < max_level and info.get('children'):
            for dr in range(2):
                for dc in range(2):
                    child = (level + 1, 2 * row + dr, 2 * col + dc)
                    if child not in visited:
                        queue.append(child)

        time.sleep(0.03)  # Rate limiting

    print(f'\n  Traversal complete: {len(downloaded)} tiles, '
          f'{requests_made} requests, {empty_count} empty')

    # Print level breakdown
    if level_stats:
        print(f'\n  Level breakdown:')
        for lvl in sorted(level_stats):
            s = level_stats[lvl]
            print(f'    L{lvl}: {s["tiles"]} tiles, {s["bytes"]/1024:.1f} KB, '
                  f'{s["with_bldg"]} with BUILD_ID')

    return downloaded


def find_working_layer(campus):
    """Try each layer option and return the first that exists."""
    for layer in campus['layers']:
        print(f'  Checking layer {layer}...')
        layer_data = fetch_layer_info(layer)
        if layer_data and len(layer_data) > 10:
            print(f'  ✓ Layer {layer} exists ({len(layer_data):,} bytes)')
            return layer, layer_data
        else:
            print(f'  ✗ Layer {layer} not available')
    return None, None


def download_campus(campus_key, raw_dir, max_level=15, margin=0.02, try_all_layers=False):
    """Download tiles for a single campus."""
    campus = CAMPUSES[campus_key]

    print(f'\n{"=" * 60}')
    print(f'{campus["name"]} ({campus["name_en"]})')
    print(f'Center: {campus["center"]}')
    print(f'BBox: {campus["bbox"]}')
    print(f'{"=" * 60}')

    layers_to_try = campus['layers'] if try_all_layers else campus['layers'][:1]
    results = {}

    for layer in layers_to_try:
        print(f'\n  Checking layer {layer}...')
        layer_data = fetch_layer_info(layer)
        if not layer_data or len(layer_data) < 10:
            print(f'  ✗ Layer {layer} not available')
            if not try_all_layers:
                # Try next layer
                remaining = campus['layers'][1:]
                for alt in remaining:
                    print(f'  Trying alternative: {alt}...')
                    layer_data = fetch_layer_info(alt)
                    if layer_data and len(layer_data) > 10:
                        print(f'  ✓ Layer {alt} exists')
                        layer = alt
                        break
                else:
                    print(f'  FAILED: No available layer found')
                    return None
            else:
                continue

        print(f'  ✓ Layer {layer} ({len(layer_data):,} bytes)')

        # Create output directory
        output_dir = os.path.join(raw_dir, f'NLSC_quadtree_{layer}_{campus_key}')
        os.makedirs(output_dir, exist_ok=True)

        # Save layer metadata
        with open(os.path.join(output_dir, 'LAYER.bin'), 'wb') as f:
            f.write(layer_data)

        # Download via quadtree traversal
        print(f'\n  Starting quadtree traversal (max level: {max_level}, margin: {margin})...')
        tiles = quadtree_download(
            layer, campus['bbox'], output_dir,
            max_level=max_level, margin=margin,
        )

        total_bytes = sum(t['size'] for t in tiles)
        bldg_tiles = sum(1 for t in tiles if t['has_build_id'])

        # Save manifest
        manifest = {
            'campus': campus_key,
            'name': campus['name'],
            'name_en': campus['name_en'],
            'layer': layer,
            'method': 'quadtree_bfs_from_root',
            'max_level': max_level,
            'margin': margin,
            'bbox': {
                'lon_min': campus['bbox'][0], 'lon_max': campus['bbox'][1],
                'lat_min': campus['bbox'][2], 'lat_max': campus['bbox'][3],
            },
            'tiles': tiles,
            'total_tiles': len(tiles),
            'total_bytes': total_bytes,
            'tiles_with_build_id': bldg_tiles,
        }
        manifest_file = os.path.join(output_dir, 'manifest.json')
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        print(f'\n  Result: {len(tiles)} tiles ({bldg_tiles} with BUILD_ID), '
              f'{total_bytes / 1024 / 1024:.2f} MB')
        print(f'  Output: {output_dir}')

        results[layer] = {
            'tiles': len(tiles),
            'bytes': total_bytes,
            'bldg_tiles': bldg_tiles,
        }

        if not try_all_layers:
            break

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Download NLSC 3D building tiles via quadtree traversal')
    parser.add_argument('campuses', nargs='*', default=list(CAMPUSES.keys()),
                        help=f'Campus keys: {list(CAMPUSES.keys())}')
    parser.add_argument('--max-level', type=int, default=15,
                        help='Maximum quadtree depth (default: 15)')
    parser.add_argument('--margin', type=float, default=0.02,
                        help='Geographic margin in degrees (default: 0.02)')
    parser.add_argument('--all-layers', action='store_true',
                        help='Try all layer versions for each campus')
    args = parser.parse_args()

    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(project_dir, 'data', 'raw')

    print('=' * 60)
    print('NLSC 3D Building Tile Downloader - Quadtree BFS')
    print('=' * 60)
    print(f'Output: {raw_dir}')
    print(f'Max level: {args.max_level}')
    print(f'Margin: {args.margin}°')

    all_results = {}
    for key in args.campuses:
        if key not in CAMPUSES:
            print(f'\nUnknown campus: {key}')
            continue
        result = download_campus(
            key, raw_dir,
            max_level=args.max_level,
            margin=args.margin,
            try_all_layers=args.all_layers,
        )
        if result:
            all_results[key] = result

    # Summary
    print(f'\n{"=" * 60}')
    print('DOWNLOAD SUMMARY')
    print(f'{"=" * 60}')
    for key, layers_result in all_results.items():
        campus = CAMPUSES[key]
        for layer, stats in layers_result.items():
            print(f'  {campus["name"]:8s} [{layer:6s}]: '
                  f'{stats["tiles"]:4d} tiles ({stats["bldg_tiles"]} w/BUILD_ID), '
                  f'{stats["bytes"] / 1024 / 1024:.2f} MB')
    print(f'{"=" * 60}')


if __name__ == '__main__':
    main()
