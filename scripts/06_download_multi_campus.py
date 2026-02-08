"""
Download NLSC 3D building tiles for ALL NYCU campuses.

Supports:
- Guangfu Campus (光復校區) - Hsinchu City [112_O] (already downloaded)
- Boai Campus (博愛校區) - Hsinchu City [112_O]
- Yangming Campus (陽明校區) - Taipei City [112_A]
- Liujia Campus (六家校區) - Hsinchu County [112_J]
- Gueiren Campus (歸仁校區) - Tainan City [112_D]

Tile coordinate formula (EPSG:4326, PilotGaea oview):
  Col = floor(lon * 2^L / 160)
  Row = floor(lat * 2^L / 60)
"""
import gzip
import json
import math
import os
import sys
import time
import urllib.request

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

SERVERS = [
    "https://mapserver01.nlsc.gov.tw/oview//oview",
    "https://mapserver02.nlsc.gov.tw/oview//oview",
    "https://mapserver51.nlsc.gov.tw/oview//oview",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://3dmaps.nlsc.gov.tw/",
}

# NYCU Campus definitions
# Each campus: name, center_lon, center_lat, nlsc_layer, bbox (lon_min, lon_max, lat_min, lat_max)
CAMPUSES = {
    'boai': {
        'name': '博愛校區 (Boai Campus)',
        'center': (120.9685, 24.8015),
        'bbox': (120.963, 120.975, 24.796, 24.807),
        'layer': '112_O',  # Hsinchu City
    },
    'yangming': {
        'name': '陽明校區 (Yangming Campus)',
        'center': (121.5155, 25.1195),
        'bbox': (121.508, 121.525, 25.112, 25.128),
        'layer': '109_A',  # Taipei City (109/2020 has more data than 112/2023)
    },
    'liujia': {
        'name': '六家校區 (Liujia Campus)',
        'center': (121.0135, 24.8385),
        'bbox': (121.008, 121.020, 24.833, 24.845),
        'layer': '113_J',  # Hsinchu County (112_J unavailable, using 113/2024)
    },
    'gueiren': {
        'name': '歸仁校區 (Gueiren Campus)',
        'center': (120.3045, 22.9325),
        'bbox': (120.298, 120.312, 22.926, 22.940),
        'layer': '112_D',  # Tainan City
    },
}

server_idx = 0


def get_server():
    global server_idx
    server = SERVERS[server_idx % len(SERVERS)]
    server_idx += 1
    return server


def lonlat_to_tile(lon, lat, level):
    """Convert lon/lat to tile column/row at given level."""
    col = int(math.floor(lon * (2 ** level) / 160.0))
    row = int(math.floor(lat * (2 ** level) / 60.0))
    return row, col


def bbox_to_tile_range(bbox, level, buffer_tiles=1):
    """Convert bounding box to tile range at given level, with buffer."""
    lon_min, lon_max, lat_min, lat_max = bbox
    r_min, c_min = lonlat_to_tile(lon_min, lat_min, level)
    r_max, c_max = lonlat_to_tile(lon_max, lat_max, level)
    # Add buffer
    r_min -= buffer_tiles
    c_min -= buffer_tiles
    r_max += buffer_tiles
    c_max += buffer_tiles
    return r_min, r_max, c_min, c_max


def fetch_tile(layer, level, row, col, retries=2):
    for attempt in range(retries + 1):
        server = get_server()
        url = (
            f"{server}?type=modelset&format=integrate"
            f"&name={layer}&level={level}&Row={row}&Col={col}"
            f"&docname=NODE&epsg=4326"
        )
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
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
    server = get_server()
    url = (
        f"{server}?type=modelset&format=integrate"
        f"&name={layer}&docname=LAYER"
    )
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 200:
                data = resp.read()
                try:
                    data = gzip.decompress(data)
                except Exception:
                    pass
                return data
    except Exception as e:
        return None


def download_campus(campus_key, output_base_dir, levels=(5, 6, 7)):
    """Download tiles for a specific campus."""
    campus = CAMPUSES[campus_key]
    name = campus['name']
    layer = campus['layer']
    bbox = campus['bbox']

    print(f'\n{"=" * 60}')
    print(f'Downloading: {name}')
    print(f'Layer: {layer}')
    print(f'BBox: {bbox}')
    print(f'{"=" * 60}')

    # Check if layer exists
    print(f'\nChecking layer {layer}...')
    layer_data = fetch_layer_info(layer)
    if not layer_data:
        print(f'  WARNING: Layer {layer} not available or returned empty data.')
        print(f'  Trying alternative layer names...')
        # Try without year prefix
        for year in ['112', '111', '110', '109']:
            alt_layer = f"{year}_{layer.split('_')[1]}"
            layer_data = fetch_layer_info(alt_layer)
            if layer_data:
                print(f'  Found alternative: {alt_layer}')
                layer = alt_layer
                break
        if not layer_data:
            print(f'  FAILED: No available layer found. Skipping campus.')
            return []

    print(f'  Layer {layer} exists ({len(layer_data):,} bytes metadata)')

    # Create output directory
    output_dir = os.path.join(output_base_dir, f'NLSC_3D_tiles_{layer}_{campus_key}')
    os.makedirs(output_dir, exist_ok=True)

    # Save layer metadata
    layer_file = os.path.join(output_dir, 'LAYER.bin')
    with open(layer_file, 'wb') as f:
        f.write(layer_data)

    all_downloaded = []

    for level in levels:
        r_min, r_max, c_min, c_max = bbox_to_tile_range(bbox, level, buffer_tiles=1)
        total = (r_max - r_min + 1) * (c_max - c_min + 1)
        print(f'\nLevel {level}: R[{r_min}-{r_max}] x C[{c_min}-{c_max}] ({total} tiles)')

        tile_dir = os.path.join(output_dir, f'L{level}')
        os.makedirs(tile_dir, exist_ok=True)

        count = 0
        found = 0
        for row in range(r_min, r_max + 1):
            for col in range(c_min, c_max + 1):
                count += 1
                data = fetch_tile(layer, level, row, col)
                if data is not None:
                    filename = os.path.join(tile_dir, f'R{row}_C{col}.bin')
                    with open(filename, 'wb') as f:
                        f.write(data)
                    all_downloaded.append({
                        'campus': campus_key,
                        'level': level,
                        'row': row,
                        'col': col,
                        'size': len(data),
                    })
                    found += 1
                    sys.stdout.write(
                        f'\r  L{level}: {count}/{total} | '
                        f'R{row}_C{col}: {len(data):,} bytes | '
                        f'Found: {found}  '
                    )
                    sys.stdout.flush()
                else:
                    sys.stdout.write(
                        f'\r  L{level}: {count}/{total} | '
                        f'R{row}_C{col}: empty | '
                        f'Found: {found}  '
                    )
                    sys.stdout.flush()
                time.sleep(0.05)

        print(f'\r  Level {level}: {found} tiles downloaded' + ' ' * 40)

        if found == 0 and level > min(levels):
            print(f'  No data at level {level}, stopping deeper levels')
            break

    # Also download deeper levels (8-9) for core area
    if all_downloaded:
        # Find the core area from level 7 tiles
        l7_tiles = [t for t in all_downloaded if t['level'] == 7]
        if l7_tiles:
            core_r_min = min(t['row'] for t in l7_tiles)
            core_r_max = max(t['row'] for t in l7_tiles)
            core_c_min = min(t['col'] for t in l7_tiles)
            core_c_max = max(t['col'] for t in l7_tiles)

            for target_level in [8, 9]:
                scale = 2 ** (target_level - 7)
                rmin = core_r_min * scale
                rmax = core_r_max * scale + (scale - 1)
                cmin = core_c_min * scale
                cmax = core_c_max * scale + (scale - 1)
                total = (rmax - rmin + 1) * (cmax - cmin + 1)

                if total > 500:
                    print(f'\n  Level {target_level}: {total} tiles (too many, skipping)')
                    continue

                print(f'\n  Level {target_level}: R[{rmin}-{rmax}] x C[{cmin}-{cmax}] ({total} tiles)')

                tile_dir = os.path.join(output_dir, f'L{target_level}')
                os.makedirs(tile_dir, exist_ok=True)

                count = 0
                found = 0
                for row in range(rmin, rmax + 1):
                    for col in range(cmin, cmax + 1):
                        count += 1
                        data = fetch_tile(layer, target_level, row, col)
                        if data is not None:
                            filename = os.path.join(tile_dir, f'R{row}_C{col}.bin')
                            with open(filename, 'wb') as f:
                                f.write(data)
                            all_downloaded.append({
                                'campus': campus_key,
                                'level': target_level,
                                'row': row,
                                'col': col,
                                'size': len(data),
                            })
                            found += 1
                        time.sleep(0.03)

                    sys.stdout.write(
                        f'\r  L{target_level}: {count}/{total} | Found: {found}  '
                    )
                    sys.stdout.flush()

                print(f'\r  Level {target_level}: {found} tiles downloaded' + ' ' * 40)

                if found == 0:
                    break

    # Save manifest
    total_bytes = sum(t['size'] for t in all_downloaded)
    manifest = {
        'campus': campus_key,
        'campus_name': name,
        'layer': layer,
        'bbox': {
            'lon_min': bbox[0], 'lon_max': bbox[1],
            'lat_min': bbox[2], 'lat_max': bbox[3],
        },
        'tiles': all_downloaded,
        'total_tiles': len(all_downloaded),
        'total_bytes': total_bytes,
    }
    manifest_file = os.path.join(output_dir, 'manifest.json')
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f'\n  Total: {len(all_downloaded)} tiles, {total_bytes / 1024 / 1024:.2f} MB')
    print(f'  Output: {output_dir}')

    return all_downloaded


def main():
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_base_dir = os.path.join(project_dir, 'data', 'raw')

    print('=' * 60)
    print('NLSC 3D Building Tile Downloader - Multi-Campus')
    print('=' * 60)
    print(f'Output: {output_base_dir}')

    # Determine which campuses to download
    import argparse
    parser = argparse.ArgumentParser(description='Download NLSC 3D tiles for NYCU campuses')
    parser.add_argument('campuses', nargs='*', default=list(CAMPUSES.keys()),
                        help=f'Campus keys to download: {list(CAMPUSES.keys())}')
    parser.add_argument('--levels', type=str, default='5,6,7',
                        help='Comma-separated levels to download (default: 5,6,7)')
    args = parser.parse_args()

    levels = tuple(int(x) for x in args.levels.split(','))

    print(f'\nCampuses to download:')
    for key in args.campuses:
        if key in CAMPUSES:
            c = CAMPUSES[key]
            print(f'  - {c["name"]} | Layer: {c["layer"]} | Center: {c["center"]}')
        else:
            print(f'  - {key}: UNKNOWN (skipping)')

    all_results = {}
    for key in args.campuses:
        if key not in CAMPUSES:
            continue
        tiles = download_campus(key, output_base_dir, levels=levels)
        all_results[key] = tiles

    # Summary
    print(f'\n{"=" * 60}')
    print('DOWNLOAD SUMMARY')
    print(f'{"=" * 60}')
    grand_total_tiles = 0
    grand_total_bytes = 0
    for key, tiles in all_results.items():
        campus = CAMPUSES[key]
        total_bytes = sum(t['size'] for t in tiles)
        grand_total_tiles += len(tiles)
        grand_total_bytes += total_bytes
        status = f'{len(tiles)} tiles, {total_bytes / 1024 / 1024:.2f} MB' if tiles else 'FAILED'
        print(f'  {campus["name"]}: {status}')

    print(f'\n  Grand total: {grand_total_tiles} tiles, {grand_total_bytes / 1024 / 1024:.2f} MB')


if __name__ == '__main__':
    main()
