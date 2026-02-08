"""
Merge OSM building footprints with NLSC 3D building attributes.

- OSM: 319 buildings with polygon footprints, 185 named
- NLSC: 6,181 buildings with centroid points, heights, structure types

Strategy:
1. Point-in-polygon: check if NLSC centroid falls inside an OSM polygon
2. Nearest-neighbor: for unmatched buildings, find closest OSM polygon centroid
3. Output: merged GeoJSON with OSM footprints enriched with NLSC attributes
"""
import json
import math
import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def point_in_polygon(px, py, polygon):
    """Ray-casting algorithm for point-in-polygon test."""
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def polygon_centroid(polygon):
    """Compute centroid of a polygon."""
    n = len(polygon)
    if n == 0:
        return 0, 0
    # Exclude closing vertex if it duplicates the first
    if n > 1 and polygon[0][0] == polygon[-1][0] and polygon[0][1] == polygon[-1][1]:
        n -= 1
    cx = sum(polygon[i][0] for i in range(n)) / n
    cy = sum(polygon[i][1] for i in range(n)) / n
    return cx, cy


def haversine_m(lon1, lat1, lon2, lat2):
    """Haversine distance in meters."""
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def polygon_area(polygon):
    """Compute signed area of a polygon (shoelace formula) for sorting."""
    n = len(polygon)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += polygon[i][0] * polygon[j][1]
        area -= polygon[j][0] * polygon[i][1]
    return abs(area) / 2.0


def main():
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_dir, 'data')

    # Load OSM buildings
    osm_file = os.path.join(data_dir, 'processed', 'NYCU_Guangfu_OSM_buildings.geojson')
    with open(osm_file, 'r', encoding='utf-8') as f:
        osm_data = json.load(f)
    osm_features = osm_data['features']
    print(f'Loaded {len(osm_features)} OSM buildings')

    # Load NLSC buildings
    nlsc_file = os.path.join(data_dir, 'processed', 'NYCU_NLSC_buildings.json')
    with open(nlsc_file, 'r', encoding='utf-8') as f:
        nlsc_data = json.load(f)
    nlsc_buildings = nlsc_data['buildings']
    print(f'Loaded {len(nlsc_buildings)} NLSC buildings')

    # Precompute OSM polygon info
    osm_polys = []
    for feat in osm_features:
        geom = feat['geometry']
        if geom['type'] != 'Polygon':
            continue
        ring = geom['coordinates'][0]  # outer ring
        cx, cy = polygon_centroid(ring)
        props = feat['properties']
        osm_polys.append({
            'ring': ring,
            'centroid': (cx, cy),
            'props': props,
            'feature': feat,
            'nlsc_matches': [],
        })

    print(f'OSM polygons: {len(osm_polys)}')

    # Phase 1: Point-in-polygon matching
    print('\nPhase 1: Point-in-polygon matching...')
    matched_nlsc = set()
    pip_count = 0

    for i, nlsc in enumerate(nlsc_buildings):
        lon = nlsc.get('lon')
        lat = nlsc.get('lat')
        if lon is None or lat is None:
            continue

        for j, osm in enumerate(osm_polys):
            if point_in_polygon(lon, lat, osm['ring']):
                osm['nlsc_matches'].append(i)
                matched_nlsc.add(i)
                pip_count += 1
                break

        if (i + 1) % 500 == 0:
            sys.stdout.write(f'\r  Checked {i + 1}/{len(nlsc_buildings)} NLSC buildings ({pip_count} matched)')
            sys.stdout.flush()

    print(f'\r  Point-in-polygon: {pip_count} NLSC buildings matched to OSM polygons')

    # Phase 2: Nearest-neighbor for remaining NLSC buildings within 50m of an OSM polygon
    print('\nPhase 2: Nearest-neighbor matching (within 30m)...')
    nn_count = 0
    MAX_DIST = 30.0  # meters

    for i, nlsc in enumerate(nlsc_buildings):
        if i in matched_nlsc:
            continue
        lon = nlsc.get('lon')
        lat = nlsc.get('lat')
        if lon is None or lat is None:
            continue

        best_dist = float('inf')
        best_j = -1
        for j, osm in enumerate(osm_polys):
            d = haversine_m(lon, lat, osm['centroid'][0], osm['centroid'][1])
            if d < best_dist:
                best_dist = d
                best_j = j

        if best_dist <= MAX_DIST and best_j >= 0:
            osm_polys[best_j]['nlsc_matches'].append(i)
            matched_nlsc.add(i)
            nn_count += 1

    print(f'  Nearest-neighbor: {nn_count} additional matches')

    # Build merged features
    print('\nBuilding merged dataset...')
    merged_features = []

    # Count stats
    osm_with_nlsc = 0
    osm_without_nlsc = 0
    multi_match = 0

    for osm in osm_polys:
        feat = json.loads(json.dumps(osm['feature']))  # deep copy
        props = feat['properties']

        if osm['nlsc_matches']:
            osm_with_nlsc += 1
            if len(osm['nlsc_matches']) > 1:
                multi_match += 1

            # Use the tallest NLSC building as the primary match
            matches = osm['nlsc_matches']
            best_nlsc = None
            best_height = -1.0
            for idx in matches:
                h = 0.0
                try:
                    h = float(nlsc_buildings[idx].get('BUILD_H', '0'))
                except ValueError:
                    pass
                if h > best_height:
                    best_height = h
                    best_nlsc = nlsc_buildings[idx]

            if best_nlsc:
                # Add NLSC attributes to OSM properties
                props['nlsc_BUILD_ID'] = best_nlsc.get('BUILD_ID', '')
                props['nlsc_BUILD_H'] = best_nlsc.get('BUILD_H', '')
                props['nlsc_BUILD_STR'] = best_nlsc.get('BUILD_STR', '')
                props['nlsc_MODEL_LOD'] = best_nlsc.get('MODEL_LOD', '')
                props['nlsc_MODEL_NAME'] = best_nlsc.get('MODEL_NAME', '')
                props['nlsc_MDATE'] = best_nlsc.get('MDATE', '')
                props['nlsc_M_MDATE'] = best_nlsc.get('M_MDATE', '')
                props['nlsc_CENT_E_97'] = best_nlsc.get('CENT_E_97', '')
                props['nlsc_CENT_N_97'] = best_nlsc.get('CENT_N_97', '')
                props['nlsc_match_count'] = len(matches)

                # If OSM has no height but NLSC does, add it as the primary height
                if 'height' not in props and best_nlsc.get('BUILD_H'):
                    props['height'] = best_nlsc['BUILD_H']
        else:
            osm_without_nlsc += 1

        merged_features.append(feat)

    # Also add NLSC-only buildings (not matched to any OSM polygon) as Point features
    nlsc_only_count = 0
    for i, nlsc in enumerate(nlsc_buildings):
        if i in matched_nlsc:
            continue
        lon = nlsc.get('lon')
        lat = nlsc.get('lat')
        if lon is None or lat is None:
            continue

        # Only include buildings within the NYCU campus area
        if not (120.990 <= lon <= 121.005 and 24.780 <= lat <= 24.795):
            continue

        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [lon, lat],
            },
            'properties': {
                'source': 'NLSC_only',
                'BUILD_ID': nlsc.get('BUILD_ID', ''),
                'BUILD_H': nlsc.get('BUILD_H', ''),
                'BUILD_STR': nlsc.get('BUILD_STR', ''),
                'height': nlsc.get('BUILD_H', ''),
                'MODEL_NAME': nlsc.get('MODEL_NAME', ''),
                'MDATE': nlsc.get('MDATE', ''),
            }
        }
        merged_features.append(feature)
        nlsc_only_count += 1

    # Save merged GeoJSON
    merged_geojson = {
        'type': 'FeatureCollection',
        'name': 'NYCU_Buildings_Merged',
        'metadata': {
            'description': 'Merged OSM footprints + NLSC 3D building attributes',
            'osm_source': 'OpenStreetMap (taiwan-osm-latest.osm.pbf)',
            'nlsc_source': 'NLSC 3D Maps (3dmaps.nlsc.gov.tw) layer 112_O (2023)',
            'osm_buildings': len(osm_polys),
            'nlsc_buildings': len(nlsc_buildings),
            'osm_with_nlsc_match': osm_with_nlsc,
            'osm_without_nlsc_match': osm_without_nlsc,
            'osm_with_multi_nlsc': multi_match,
            'nlsc_only_in_campus': nlsc_only_count,
            'total_merged_features': len(merged_features),
        },
        'features': merged_features,
    }

    output_file = os.path.join(data_dir, 'output', 'NYCU_buildings_merged.geojson')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_geojson, f, ensure_ascii=False, indent=2)
    print(f'\nSaved merged dataset to {output_file}')

    # Print summary
    print(f'\n{"=" * 60}')
    print(f'MERGE SUMMARY')
    print(f'{"=" * 60}')
    print(f'OSM buildings total:          {len(osm_polys)}')
    print(f'NLSC buildings total:         {len(nlsc_buildings)}')
    print(f'')
    print(f'OSM matched to NLSC:          {osm_with_nlsc} ({100 * osm_with_nlsc / len(osm_polys):.1f}%)')
    print(f'  - via point-in-polygon:     {pip_count}')
    print(f'  - via nearest neighbor:     {nn_count}')
    print(f'  - with multiple NLSC:       {multi_match}')
    print(f'OSM without NLSC match:       {osm_without_nlsc}')
    print(f'NLSC-only (campus area):      {nlsc_only_count}')
    print(f'')
    print(f'Total merged features:        {len(merged_features)}')

    # Print named buildings with heights
    print(f'\n{"=" * 60}')
    print(f'NAMED BUILDINGS WITH NLSC HEIGHT DATA')
    print(f'{"=" * 60}')
    named_with_height = []
    for feat in merged_features:
        props = feat['properties']
        name = props.get('name', '')
        name_en = props.get('name:en', '')
        nlsc_h = props.get('nlsc_BUILD_H', '')
        osm_levels = props.get('building:levels', '')
        if name and nlsc_h:
            named_with_height.append((name, name_en, nlsc_h, osm_levels))

    named_with_height.sort(key=lambda x: -float(x[2]))
    for name, name_en, h, levels in named_with_height:
        en_str = f' ({name_en})' if name_en else ''
        lv_str = f' [{levels}F]' if levels else ''
        print(f'  {name}{en_str}{lv_str}: {h}m')

    # Print OSM buildings that didn't match any NLSC data
    print(f'\n{"=" * 60}')
    print(f'OSM BUILDINGS WITHOUT NLSC MATCH')
    print(f'{"=" * 60}')
    unmatched_named = []
    for osm in osm_polys:
        if not osm['nlsc_matches']:
            name = osm['props'].get('name', '')
            if name:
                unmatched_named.append(name)
    if unmatched_named:
        for n in sorted(unmatched_named):
            print(f'  - {n}')
    else:
        print('  (none with names)')


if __name__ == '__main__':
    main()
