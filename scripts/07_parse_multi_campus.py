"""
Parse NLSC 3D building tiles for multiple NYCU campuses.
Reuses the proven parser from 03_parse_nlsc_tiles.py with campus-specific bbox filtering.

Usage:
  python scripts/07_parse_multi_campus.py [campus_key ...]
  python scripts/07_parse_multi_campus.py boai gueiren
  python scripts/07_parse_multi_campus.py  # all campuses
"""
import json
import math
import os
import struct
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- Parsing functions (from 03_parse_nlsc_tiles.py) ---

def ecef_to_lonlat(x, y, z):
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = 2 * f - f * f
    lon = math.atan2(y, x)
    p = math.sqrt(x * x + y * y)
    lat = math.atan2(z, p * (1 - e2))
    for _ in range(10):
        N = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
        lat = math.atan2(z + e2 * N * math.sin(lat), p)
    alt = p / math.cos(lat) - N
    return math.degrees(lon), math.degrees(lat), alt


def twd97_to_wgs84(e, n):
    a = 6378137.0
    f = 1 / 298.257222101
    lon0 = math.radians(121.0)
    k0 = 0.9999
    dx = 250000.0
    dy = 0.0
    x = e - dx
    y = n - dy
    M = y / k0
    mu = M / (a * (1 - f / 4 * (2 + f) - 3 / 64 * f * f * (1 + f)))
    e1 = (1 - math.sqrt(1 - (2 * f - f * f))) / (1 + math.sqrt(1 - (2 * f - f * f)))
    phi1 = mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu)
    phi1 += (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu)
    phi1 += (151 * e1 ** 3 / 96) * math.sin(6 * mu)
    e2 = 2 * f - f * f
    ep2 = e2 / (1 - e2)
    C1 = ep2 * math.cos(phi1) ** 2
    T1 = math.tan(phi1) ** 2
    N1 = a / math.sqrt(1 - e2 * math.sin(phi1) ** 2)
    R1 = a * (1 - e2) / ((1 - e2 * math.sin(phi1) ** 2) ** 1.5)
    D = x / (N1 * k0)
    lat = phi1 - (N1 * math.tan(phi1) / R1) * (
        D ** 2 / 2 - (5 + 3 * T1 + 10 * C1 - 4 * C1 ** 2 - 9 * ep2) * D ** 4 / 24
    )
    lon = lon0 + (
        D - (1 + 2 * T1 + C1) * D ** 3 / 6
        + (5 - 2 * C1 + 28 * T1 - 3 * C1 ** 2 + 8 * ep2 + 24 * T1 ** 2) * D ** 5 / 120
    ) / math.cos(phi1)
    return math.degrees(lon), math.degrees(lat)


def find_attribute_section(data):
    build_id_pos = data.find(b'BUILD_ID')
    if build_id_pos < 0:
        return None
    name_len_pos = build_id_pos - 4
    if name_len_pos < 0:
        return None
    name_len = struct.unpack_from('<I', data, name_len_pos)[0]
    if name_len != 8:
        return None
    for field_count_guess in [20, 15, 25, 10, 30]:
        type_codes_start = name_len_pos - field_count_guess * 4
        if type_codes_start < 0:
            continue
        all_eight = True
        for j in range(field_count_guess):
            v = struct.unpack_from('<I', data, type_codes_start + j * 4)[0]
            if v != 8:
                all_eight = False
                break
        if all_eight:
            field_lengths_start = type_codes_start - field_count_guess * 4
            meta_start = field_lengths_start - 8
            if meta_start < 0:
                continue
            fc = struct.unpack_from('<I', data, meta_start)[0]
            bc = struct.unpack_from('<I', data, meta_start + 4)[0]
            if fc == field_count_guess and 0 < bc < 10000:
                return {
                    'meta_offset': meta_start,
                    'field_count': fc,
                    'building_count': bc,
                    'field_lengths_offset': field_lengths_start,
                    'type_codes_offset': type_codes_start,
                    'field_names_offset': name_len_pos,
                }
    return None


def parse_tile_attributes(data):
    attr_info = find_attribute_section(data)
    if attr_info is None:
        return None
    fc = attr_info['field_count']
    bc = attr_info['building_count']
    if bc == 0:
        return {'field_count': fc, 'building_count': 0, 'fields': [], 'buildings': []}
    field_lengths = []
    pos = attr_info['field_lengths_offset']
    for i in range(fc):
        fl = struct.unpack_from('<I', data, pos)[0]
        field_lengths.append(fl)
        pos += 4
    pos = attr_info['field_names_offset']
    fields = []
    for i in range(fc):
        nlen = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        name = data[pos:pos + nlen].decode('utf-8', errors='replace')
        pos += nlen
        fields.append(name)
    data_start = pos + 5
    all_values = {}
    field_offset = data_start
    for f_idx in range(fc):
        field_name = fields[f_idx]
        values = []
        read_pos = field_offset
        field_end = field_offset + field_lengths[f_idx]
        for b_idx in range(bc):
            if read_pos + 4 > field_end:
                values.append('')
                continue
            vlen = struct.unpack_from('<I', data, read_pos)[0]
            read_pos += 4
            if vlen > 0 and read_pos + vlen <= field_end + 50:
                val = data[read_pos:read_pos + vlen].decode('utf-8', errors='replace')
                read_pos += vlen
            else:
                val = ''
            values.append(val)
        all_values[field_name] = values
        field_offset += field_lengths[f_idx]
    buildings = []
    for b_idx in range(bc):
        bldg = {}
        for fname in fields:
            val = all_values[fname][b_idx]
            if val and val != 'NA':
                bldg[fname] = val
        buildings.append(bldg)
    return {
        'field_count': fc,
        'building_count': bc,
        'fields': fields,
        'buildings': buildings,
    }


def parse_tile_file(filepath):
    import gzip
    with open(filepath, 'rb') as f:
        raw_data = f.read()
    if raw_data[:2] == b'\x1f\x8b':
        try:
            data = gzip.decompress(raw_data)
        except Exception:
            data = raw_data
    else:
        data = raw_data
    result = {'file': filepath, 'raw_size': len(raw_data), 'decompressed_size': len(data)}
    if len(data) >= 12:
        level, row, col = struct.unpack_from('<III', data, 0)
        result['level'] = level
        result['row'] = row
        result['col'] = col
    attrs = parse_tile_attributes(data)
    if attrs and attrs['building_count'] > 0:
        result['building_count'] = attrs['building_count']
        result['fields'] = attrs['fields']
        result['buildings'] = attrs['buildings']
        for bldg in result['buildings']:
            e97 = bldg.get('CENT_E_97', '')
            n97 = bldg.get('CENT_N_97', '')
            if e97 and n97:
                try:
                    lon, lat = twd97_to_wgs84(float(e97), float(n97))
                    bldg['lon'] = round(lon, 7)
                    bldg['lat'] = round(lat, 7)
                except (ValueError, ZeroDivisionError):
                    pass
    return result


# --- Campus definitions ---

CAMPUSES = {
    'boai': {
        'name': '博愛校區',
        'name_en': 'Boai Campus',
        'tiles_dir': 'NLSC_3D_tiles_112_O_boai',
        'layer': '112_O',
        'bbox': (120.960, 120.978, 24.793, 24.810),  # slightly wider than download bbox
    },
    'yangming': {
        'name': '陽明校區',
        'name_en': 'Yangming Campus',
        'tiles_dir': 'NLSC_3D_tiles_109_A_yangming',
        'layer': '109_A',
        'bbox': (121.505, 121.528, 25.109, 25.131),
    },
    'liujia': {
        'name': '六家校區',
        'name_en': 'Liujia Campus',
        'tiles_dir': 'NLSC_3D_tiles_113_J_liujia',
        'layer': '113_J',
        'bbox': (121.005, 121.023, 24.830, 24.848),
    },
    'gueiren': {
        'name': '歸仁校區',
        'name_en': 'Gueiren Campus',
        'tiles_dir': 'NLSC_3D_tiles_112_D_gueiren',
        'layer': '112_D',
        'bbox': (120.295, 120.315, 22.923, 22.943),
    },
}


def process_campus(campus_key, raw_dir, output_dir):
    """Parse all tiles for a campus and extract buildings within bbox."""
    campus = CAMPUSES[campus_key]
    tiles_dir = os.path.join(raw_dir, campus['tiles_dir'])

    if not os.path.isdir(tiles_dir):
        print(f'  Tiles directory not found: {tiles_dir}')
        return None

    bbox = campus['bbox']
    lon_min, lon_max, lat_min, lat_max = bbox

    print(f'\n{"=" * 60}')
    print(f'Parsing: {campus["name"]} ({campus["name_en"]})')
    print(f'Layer: {campus["layer"]}')
    print(f'Tiles: {tiles_dir}')
    print(f'Filter bbox: lon[{lon_min:.3f},{lon_max:.3f}] lat[{lat_min:.3f},{lat_max:.3f}]')
    print(f'{"=" * 60}')

    # Collect all tile files
    tile_files = []
    for root, dirs, files in os.walk(tiles_dir):
        for fname in sorted(files):
            if fname.endswith('.bin') and fname != 'LAYER.bin':
                tile_files.append(os.path.join(root, fname))

    print(f'  Found {len(tile_files)} tile files')

    all_buildings = []
    seen_ids = set()
    total_raw_buildings = 0
    tiles_with_data = 0
    coord_stats = {'lon_min': 999, 'lon_max': -999, 'lat_min': 999, 'lat_max': -999}

    for i, filepath in enumerate(tile_files):
        rel_path = os.path.relpath(filepath, tiles_dir)
        try:
            result = parse_tile_file(filepath)
        except Exception as e:
            print(f'\n  ERROR parsing {rel_path}: {e}')
            continue

        bc = result.get('building_count', 0)
        if bc == 0:
            continue

        tiles_with_data += 1
        level = result.get('level', '?')
        row = result.get('row', '?')
        col = result.get('col', '?')

        for bldg in result.get('buildings', []):
            total_raw_buildings += 1
            lon = bldg.get('lon')
            lat = bldg.get('lat')
            bid = bldg.get('BUILD_ID', '')

            # Track coordinate range for debugging
            if lon is not None and lat is not None:
                coord_stats['lon_min'] = min(coord_stats['lon_min'], lon)
                coord_stats['lon_max'] = max(coord_stats['lon_max'], lon)
                coord_stats['lat_min'] = min(coord_stats['lat_min'], lat)
                coord_stats['lat_max'] = max(coord_stats['lat_max'], lat)

            # Skip if no coordinates
            if lon is None or lat is None:
                continue

            # Bbox filter
            if not (lon_min <= lon <= lon_max and lat_min <= lat <= lat_max):
                continue

            # Dedup by BUILD_ID
            if bid and bid in seen_ids:
                continue
            if bid:
                seen_ids.add(bid)

            bldg['_tile'] = f'L{level}/R{row}_C{col}'
            all_buildings.append(bldg)

        sys.stdout.write(
            f'\r  [{i+1}/{len(tile_files)}] {rel_path}: L{level} R{row} C{col} '
            f'- {bc} bldgs | Campus: {len(all_buildings)}  '
        )
        sys.stdout.flush()

    print(f'\n\n  Raw buildings in all tiles: {total_raw_buildings}')
    print(f'  Tiles with building data: {tiles_with_data}')
    if total_raw_buildings > 0:
        print(f'  Coordinate range of ALL parsed buildings:')
        print(f'    lon: [{coord_stats["lon_min"]:.6f}, {coord_stats["lon_max"]:.6f}]')
        print(f'    lat: [{coord_stats["lat_min"]:.6f}, {coord_stats["lat_max"]:.6f}]')
    print(f'  Buildings within campus bbox: {len(all_buildings)}')

    # Sort by height descending
    all_buildings.sort(key=lambda x: -float(x.get('BUILD_H', '0') or '0'))

    # Save output
    output_data = {
        'campus': campus_key,
        'name': campus['name'],
        'name_en': campus['name_en'],
        'layer': campus['layer'],
        'bbox': {
            'lon_min': lon_min, 'lon_max': lon_max,
            'lat_min': lat_min, 'lat_max': lat_max,
        },
        'total_raw_buildings': total_raw_buildings,
        'buildings': all_buildings,
        'total': len(all_buildings),
    }

    output_file = os.path.join(output_dir, f'NYCU_{campus_key}_NLSC_buildings.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f'  Saved to {output_file}')

    # Print top buildings
    if all_buildings:
        print(f'\n  Top 10 buildings by height:')
        for i, b in enumerate(all_buildings[:10]):
            bid = b.get('BUILD_ID', '?')
            h = b.get('BUILD_H', '?')
            name = b.get('BUILDNAME', '-')
            lon = b.get('lon', '')
            lat = b.get('lat', '')
            print(f'    {i+1:2d}. {bid:15s} H={h:>6s}m  ({lon}, {lat})  {name}')

    return output_data


def main():
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(project_dir, 'data', 'raw')
    output_dir = os.path.join(project_dir, 'data', 'processed')

    import argparse
    parser = argparse.ArgumentParser(description='Parse NLSC tiles for NYCU campuses')
    parser.add_argument('campuses', nargs='*', default=list(CAMPUSES.keys()),
                        help=f'Campus keys: {list(CAMPUSES.keys())}')
    args = parser.parse_args()

    print('=' * 60)
    print('NLSC 3D Building Tile Parser - Multi-Campus')
    print('=' * 60)

    results = {}
    for key in args.campuses:
        if key not in CAMPUSES:
            print(f'  Unknown campus: {key}')
            continue
        result = process_campus(key, raw_dir, output_dir)
        if result:
            results[key] = result

    # Summary
    print(f'\n{"=" * 60}')
    print('PARSING SUMMARY')
    print(f'{"=" * 60}')
    grand_total = 0
    for key, r in results.items():
        campus = CAMPUSES[key]
        n = r['total']
        raw = r['total_raw_buildings']
        grand_total += n
        print(f'  {campus["name"]:8s} ({campus["name_en"]:18s}): '
              f'{n:5d} buildings (from {raw:5d} raw)')

    print(f'\n  Grand total: {grand_total} buildings across {len(results)} campuses')


if __name__ == '__main__':
    main()
