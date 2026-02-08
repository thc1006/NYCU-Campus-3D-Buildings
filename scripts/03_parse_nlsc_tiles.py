"""
Parse NLSC PilotGaea 3D building tiles and extract building attributes.
Supports the oview binary format discovered by reverse-engineering 3dmaps.nlsc.gov.tw.

Binary format structure:
  Header (12 bytes):
    uint32 level, uint32 row, uint32 col
  OBB (192 bytes):
    8 corners × 3 doubles (ECEF coordinates)
  Additional ECEF point (24 bytes)
  Child info (variable):
    uint32 child_count
    child_count × uint32 child_ids
  Mesh/texture data (variable):
    Building geometry and JPEG textures
  Attribute metadata:
    uint32 field_count
    uint32 building_count
    field_count × uint32 field_lengths
    field_count × uint32 type_codes
    field_count × (uint32 name_len + name_bytes) field_names
    5-byte separator (00 00 00 00 37)
    field_count × field_data blocks (column-oriented, uint32+string per value)
"""
import gzip
import json
import math
import os
import struct
import sys


def ecef_to_lonlat(x, y, z):
    """Convert ECEF coordinates to WGS84 lon/lat/alt."""
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
    """Approximate conversion from TWD97 (EPSG:3826) to WGS84."""
    # TWD97 uses TM2 projection with central meridian 121°E
    # This is a simplified conversion
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


def parse_tile_header(data):
    """Parse tile header: level, row, col, OBB."""
    if len(data) < 12:
        return None

    level, row, col = struct.unpack_from('<III', data, 0)

    # OBB: 8 corners in ECEF
    obb_corners = []
    for i in range(8):
        offset = 12 + i * 24
        if offset + 24 <= len(data):
            x, y, z = struct.unpack_from('<ddd', data, offset)
            obb_corners.append((x, y, z))

    return {
        'level': level,
        'row': row,
        'col': col,
        'obb_corners': obb_corners,
    }


def find_attribute_section(data):
    """Find the attribute metadata section by searching for the field name pattern."""
    # Search for "BUILD_ID" string which marks the field definitions
    build_id_pos = data.find(b'BUILD_ID')
    if build_id_pos < 0:
        return None

    # The field name "BUILD_ID" is preceded by uint32(8) = its length
    # Walk backwards to find the start of field definitions
    # Pattern: [type_codes: 20 × uint32(8)] [field_names] [data]
    # Before type_codes: [field_count][building_count][field_lengths...]

    # Find where the field name length prefix is
    name_len_pos = build_id_pos - 4
    if name_len_pos < 0:
        return None

    # Verify: uint32 at name_len_pos should be 8 (length of "BUILD_ID")
    name_len = struct.unpack_from('<I', data, name_len_pos)[0]
    if name_len != 8:
        return None

    # Find the type codes: 20 × uint32(8) before the first field name
    # The type codes should be right before name_len_pos
    # But we need to find the count first

    # Strategy: search backwards for a sequence of uint32(8) values
    # The type code section has exactly field_count values, all = 8
    # Try to find where this sequence starts

    # First, try common field counts (20 is typical)
    for field_count_guess in [20, 15, 25, 10, 30]:
        type_codes_start = name_len_pos - field_count_guess * 4
        if type_codes_start < 0:
            continue

        # Check if all values at this position are 8
        all_eight = True
        for j in range(field_count_guess):
            v = struct.unpack_from('<I', data, type_codes_start + j * 4)[0]
            if v != 8:
                all_eight = False
                break

        if all_eight:
            # Found the type codes section
            # Before it: field_lengths (field_count × uint32)
            # Before that: building_count (uint32)
            # Before that: field_count (uint32)
            field_lengths_start = type_codes_start - field_count_guess * 4
            meta_start = field_lengths_start - 8  # field_count + building_count

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
    """Parse building attributes from a tile's binary data."""
    attr_info = find_attribute_section(data)
    if attr_info is None:
        return None

    fc = attr_info['field_count']
    bc = attr_info['building_count']

    if bc == 0:
        return {'field_count': fc, 'building_count': 0, 'fields': [], 'buildings': []}

    # Read field lengths
    field_lengths = []
    pos = attr_info['field_lengths_offset']
    for i in range(fc):
        fl = struct.unpack_from('<I', data, pos)[0]
        field_lengths.append(fl)
        pos += 4

    # Read field names
    pos = attr_info['field_names_offset']
    fields = []
    for i in range(fc):
        nlen = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        name = data[pos:pos + nlen].decode('utf-8', errors='replace')
        pos += nlen
        fields.append(name)

    # Data starts after field names + 5-byte separator
    data_start = pos + 5

    # Parse column-oriented attribute data
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

    # Build per-building records
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
    """Parse a single tile file and extract all information."""
    with open(filepath, 'rb') as f:
        raw_data = f.read()

    # Decompress if gzipped
    if raw_data[:2] == b'\x1f\x8b':
        try:
            data = gzip.decompress(raw_data)
        except Exception:
            data = raw_data
    else:
        data = raw_data

    result = {
        'file': filepath,
        'raw_size': len(raw_data),
        'decompressed_size': len(data),
    }

    # Parse header
    header = parse_tile_header(data)
    if header:
        result.update(header)

        # Convert OBB corners to WGS84
        if header['obb_corners']:
            wgs84_corners = []
            for x, y, z in header['obb_corners']:
                if x != 0 or y != 0 or z != 0:
                    lon, lat, alt = ecef_to_lonlat(x, y, z)
                    wgs84_corners.append({'lon': lon, 'lat': lat, 'alt': alt})
            if wgs84_corners:
                result['obb_wgs84'] = wgs84_corners
                # Compute bounding box
                lons = [c['lon'] for c in wgs84_corners]
                lats = [c['lat'] for c in wgs84_corners]
                result['bbox'] = {
                    'lon_min': min(lons), 'lon_max': max(lons),
                    'lat_min': min(lats), 'lat_max': max(lats),
                }

    # Parse attributes
    attrs = parse_tile_attributes(data)
    if attrs and attrs['building_count'] > 0:
        result['building_count'] = attrs['building_count']
        result['fields'] = attrs['fields']
        result['buildings'] = attrs['buildings']

        # Add WGS84 coordinates from TWD97
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


def process_all_tiles(tiles_dir):
    """Process all downloaded tiles and extract building data."""
    all_buildings = []
    seen_ids = set()
    tile_info = []

    # Find all .bin files
    for root, dirs, files in os.walk(tiles_dir):
        for fname in sorted(files):
            if not fname.endswith('.bin') or fname == 'LAYER.bin':
                continue

            filepath = os.path.join(root, fname)
            rel_path = os.path.relpath(filepath, tiles_dir)

            try:
                result = parse_tile_file(filepath)
            except Exception as e:
                print(f'  ERROR: {rel_path}: {e}')
                continue

            level = result.get('level', '?')
            row = result.get('row', '?')
            col = result.get('col', '?')
            bc = result.get('building_count', 0)

            if bc > 0:
                tile_info.append({
                    'file': rel_path,
                    'level': level,
                    'row': row,
                    'col': col,
                    'building_count': bc,
                })

                # Add unique buildings (highest LOD wins)
                for bldg in result.get('buildings', []):
                    bid = bldg.get('BUILD_ID', '')
                    if bid and bid not in seen_ids:
                        seen_ids.add(bid)
                        bldg['_tile'] = f'L{level}/R{row}_C{col}'
                        all_buildings.append(bldg)

                sys.stdout.write(f'\r  {rel_path}: L{level} R{row} C{col} - {bc} buildings (total unique: {len(all_buildings)})  ')
                sys.stdout.flush()

    print()
    return all_buildings, tile_info


def main():
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tiles_dir = os.path.join(project_dir, 'data', 'raw', 'NLSC_3D_tiles_112_O')

    if not os.path.isdir(tiles_dir):
        print(f'Tiles directory not found: {tiles_dir}')
        return

    print('NLSC 3D Building Tile Parser')
    print(f'Tiles directory: {tiles_dir}')
    print()

    # Process all tiles
    print('Processing tiles...')
    buildings, tile_info = process_all_tiles(tiles_dir)

    print(f'\nTotal unique buildings extracted: {len(buildings)}')
    print(f'Tiles with building data: {len(tile_info)}')

    # Sort buildings by height (descending)
    buildings_with_height = [b for b in buildings if b.get('BUILD_H')]
    buildings_with_height.sort(key=lambda x: -float(x.get('BUILD_H', '0')))

    # Print tallest buildings
    print(f'\n=== Top 20 Tallest Buildings ===')
    for i, b in enumerate(buildings_with_height[:20]):
        bid = b.get('BUILD_ID', '?')
        name = b.get('BUILDNAME', '-')
        height = b.get('BUILD_H', '?')
        lon = b.get('lon', '')
        lat = b.get('lat', '')
        tile = b.get('_tile', '')
        coord = f'({lon}, {lat})' if lon else ''
        print(f'  {i + 1:3d}. {bid:15s}  H={height:>7s}m  {coord:30s}  {tile}')

    # Save all buildings as JSON
    output_file = os.path.join(project_dir, 'data', 'processed', 'NYCU_NLSC_buildings.json')
    output = {
        'source': 'NLSC 3D Maps (3dmaps.nlsc.gov.tw)',
        'layer': '112_O (2023 Hsinchu City)',
        'protocol': 'PilotGaea oview',
        'total_buildings': len(buildings),
        'tiles_processed': len(tile_info),
        'buildings': buildings,
    }
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f'\nSaved {len(buildings)} buildings to {output_file}')

    # Save as GeoJSON
    geojson_file = os.path.join(project_dir, 'data', 'processed', 'NYCU_NLSC_buildings.geojson')
    features = []
    for b in buildings:
        lon = b.get('lon')
        lat = b.get('lat')
        if lon and lat:
            props = {k: v for k, v in b.items() if k not in ('lon', 'lat', '_tile')}
            props['tile'] = b.get('_tile', '')
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [lon, lat],
                },
                'properties': props,
            }
            features.append(feature)

    geojson = {
        'type': 'FeatureCollection',
        'name': 'NYCU_NLSC_3D_Buildings',
        'features': features,
    }
    with open(geojson_file, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print(f'Saved {len(features)} buildings as GeoJSON to {geojson_file}')

    # Summary statistics
    if buildings_with_height:
        heights = [float(b['BUILD_H']) for b in buildings_with_height]
        print(f'\n=== Height Statistics ===')
        print(f'  Count: {len(heights)}')
        print(f'  Min: {min(heights):.2f}m')
        print(f'  Max: {max(heights):.2f}m')
        print(f'  Mean: {sum(heights) / len(heights):.2f}m')
        print(f'  Median: {sorted(heights)[len(heights) // 2]:.2f}m')


if __name__ == '__main__':
    main()
