"""
Download NLSC 3D building tiles for NYCU Guangfu Campus area.
Uses PilotGaea oview protocol discovered by reverse-engineering 3dmaps.nlsc.gov.tw.

Tile URL pattern:
  https://mapserver01.nlsc.gov.tw/oview//oview?
    type=modelset&format=integrate&name={LAYER}&
    level={L}&Row={R}&Col={C}&docname=NODE&epsg=4326

Available layers:
  112_O = 2023 Hsinchu City buildings (most recent)
  109_O = 2020 Hsinchu City buildings
  108_O = 2019 Hsinchu City buildings

NYCU Guangfu Campus tile coordinates (from browser network capture):
  L5: R12-15, C22-25
  L6: R26-29, C46-51
  L7: R52-55, C96-99
  Higher levels: computed by doubling row/col from parent
"""
import gzip
import json
import os
import struct
import sys
import time
import urllib.request

# Configuration
SERVERS = [
    "https://mapserver01.nlsc.gov.tw/oview//oview",
    "https://mapserver02.nlsc.gov.tw/oview//oview",
    "https://mapserver51.nlsc.gov.tw/oview//oview",
]
LAYER_NAME = "112_O"  # 2023 Hsinchu City

# NYCU Guangfu Campus tile ranges (confirmed via browser network capture)
# Format: {level: (row_min, row_max, col_min, col_max)}
NYCU_TILE_RANGES = {
    5: (12, 15, 22, 25),
    6: (24, 31, 44, 51),   # expanded slightly from observed 26-29, 46-51
    7: (48, 63, 88, 103),  # expanded from observed 52-55, 96-99
}

# Output directory (project root: one level up from scripts/)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'data', 'raw')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://3dmaps.nlsc.gov.tw/",
}

server_idx = 0


def get_server():
    """Round-robin server selection."""
    global server_idx
    server = SERVERS[server_idx % len(SERVERS)]
    server_idx += 1
    return server


def fetch_tile(layer, level, row, col, docname="NODE", retries=2):
    """Fetch a single tile from the oview server with retry and server rotation."""
    for attempt in range(retries + 1):
        server = get_server()
        url = (
            f"{server}?type=modelset&format=integrate"
            f"&name={layer}&level={level}&Row={row}&Col={col}"
            f"&docname={docname}&epsg=4326"
        )
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    data = resp.read()
                    if len(data) > 0:
                        return data
                return None
        except Exception as e:
            if attempt < retries:
                time.sleep(0.5)
            continue
    return None


def fetch_terrain_tile(level, row, col, terrain_name="2023_10M"):
    """Fetch a terrain tile."""
    server = get_server()
    url = (
        f"{server}?type=terrain&format=integrate"
        f"&name={terrain_name}&level={level}&Row={row}&Col={col}"
        f"&docname=DEMNODE&epsg=4326"
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
        return None


def fetch_layer_info(layer):
    """Fetch the LAYER metadata."""
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
        print(f"  Error fetching layer info: {e}")
        return None


def compute_children(level, row_min, row_max, col_min, col_max):
    """Compute child tile range for the next level."""
    return (
        level + 1,
        row_min * 2, row_max * 2 + 1,
        col_min * 2, col_max * 2 + 1,
    )


def download_level_range(layer, level, row_min, row_max, col_min, col_max,
                         output_dir, delay=0.05):
    """Download all tiles in a given range at a specific level."""
    downloaded = []
    total = (row_max - row_min + 1) * (col_max - col_min + 1)
    count = 0

    tile_dir = os.path.join(output_dir, f"L{level}")
    os.makedirs(tile_dir, exist_ok=True)

    for row in range(row_min, row_max + 1):
        for col in range(col_min, col_max + 1):
            count += 1
            data = fetch_tile(layer, level, row, col)
            if data is not None:
                filename = os.path.join(tile_dir, f"R{row}_C{col}.bin")
                with open(filename, "wb") as f:
                    f.write(data)
                downloaded.append((level, row, col, len(data)))
                sys.stdout.write(
                    f"\r  L{level}: {count}/{total} | "
                    f"R{row}_C{col}: {len(data):,} bytes | "
                    f"Found: {len(downloaded)}  "
                )
                sys.stdout.flush()
            else:
                sys.stdout.write(
                    f"\r  L{level}: {count}/{total} | "
                    f"R{row}_C{col}: empty | "
                    f"Found: {len(downloaded)}  "
                )
                sys.stdout.flush()

            if delay > 0:
                time.sleep(delay)

    print()
    return downloaded


def analyze_binary(data, label=""):
    """Analyze binary tile data to understand the format."""
    print(f"\n{'='*60}")
    print(f"Binary Analysis: {label}")
    print(f"{'='*60}")
    print(f"Total size: {len(data):,} bytes")

    # Check if gzip compressed
    is_gzip = data[:2] == b'\x1f\x8b'
    if is_gzip:
        try:
            decompressed = gzip.decompress(data)
            print(f"GZIP compressed! Decompressed: {len(decompressed):,} bytes")
            data = decompressed
        except Exception as e:
            print(f"GZIP header but decompress failed: {e}")

    # First 64 bytes as hex
    print(f"\nFirst 128 bytes (hex):")
    for i in range(0, min(128, len(data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {i:04x}: {hex_str:<48s} {ascii_str}")

    # Try reading as various struct formats
    print(f"\nFirst values as different formats:")
    if len(data) >= 4:
        print(f"  uint32 LE: {struct.unpack_from('<I', data, 0)[0]}")
        print(f"  int32 LE:  {struct.unpack_from('<i', data, 0)[0]}")
        print(f"  float32:   {struct.unpack_from('<f', data, 0)[0]}")
    if len(data) >= 8:
        print(f"  uint64 LE: {struct.unpack_from('<Q', data, 0)[0]}")
        print(f"  float64:   {struct.unpack_from('<d', data, 0)[0]}")

    # Look for magic bytes / known formats
    magic_checks = [
        (b'glTF', "glTF binary"),
        (b'b3dm', "Batched 3D Model (3DTiles)"),
        (b'i3dm', "Instanced 3D Model (3DTiles)"),
        (b'pnts', "Point Cloud (3DTiles)"),
        (b'cmpt', "Composite (3DTiles)"),
        (b'PK', "ZIP/PKZip archive"),
        (b'OBJ', "OBJ mesh"),
        (b'\x89PNG', "PNG image"),
        (b'\xff\xd8\xff', "JPEG image"),
        (b'RIFF', "RIFF container (WebP etc)"),
        (b'DDS ', "DDS texture"),
        (b'KTX', "KTX texture"),
    ]
    for magic, name in magic_checks:
        if data[:len(magic)] == magic:
            print(f"\n  *** DETECTED: {name} ***")

    # Search for embedded strings
    print(f"\nEmbedded strings (ASCII, min 4 chars):")
    current = []
    string_count = 0
    for i, b in enumerate(data[:min(4096, len(data))]):
        if 32 <= b < 127:
            current.append(chr(b))
        else:
            if len(current) >= 4:
                s = ''.join(current)
                print(f"  @{i-len(current):04x}: '{s}'")
                string_count += 1
                if string_count > 20:
                    print("  ... (truncated)")
                    break
            current = []

    # Look for float arrays (vertex data?)
    print(f"\nSearching for float patterns (potential vertex data):")
    float_count = 0
    for offset in range(0, min(1024, len(data) - 12), 4):
        try:
            x, y, z = struct.unpack_from('<fff', data, offset)
            # Check if values look like coordinates (reasonable range)
            if (119 < x < 122 and 24 < y < 26 and -1000 < z < 10000):
                print(f"  @{offset:04x}: lon={x:.6f}, lat={y:.6f}, z={z:.2f}")
                float_count += 1
                if float_count > 5:
                    break
            elif (13400000 < x < 13500000 and 2800000 < y < 2900000):
                # Web Mercator
                print(f"  @{offset:04x}: x={x:.2f}, y={y:.2f}, z={z:.2f} (Web Mercator?)")
                float_count += 1
                if float_count > 5:
                    break
        except struct.error:
            pass

    # Look for double arrays
    print(f"\nSearching for double patterns (potential coordinates):")
    double_count = 0
    for offset in range(0, min(2048, len(data) - 24), 8):
        try:
            x, y, z = struct.unpack_from('<ddd', data, offset)
            if (119 < x < 122 and 24 < y < 26 and -1000 < z < 10000):
                print(f"  @{offset:04x}: lon={x:.10f}, lat={y:.10f}, z={z:.4f}")
                double_count += 1
                if double_count > 5:
                    break
        except struct.error:
            pass

    return data


def main():
    output_dir = os.path.join(OUTPUT_DIR, f"NLSC_3D_tiles_{LAYER_NAME}")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("NLSC 3D Building Tile Downloader - NYCU Guangfu Campus")
    print("=" * 60)
    print(f"Layer: {LAYER_NAME} (2023 Hsinchu City)")
    print(f"Target: NYCU Guangfu Campus")
    print(f"Output: {output_dir}")
    print()

    all_downloaded = []

    # Step 1: Get layer info
    print("Step 1: Fetching layer metadata...")
    layer_data = fetch_layer_info(LAYER_NAME)
    if layer_data:
        layer_file = os.path.join(output_dir, "LAYER.bin")
        with open(layer_file, "wb") as f:
            f.write(layer_data)
        print(f"  Saved LAYER metadata ({len(layer_data):,} bytes)")
        analyze_binary(layer_data, "LAYER metadata")

    # Step 2: Download NYCU area tiles at levels 5-7 (confirmed coordinates)
    print("\n" + "=" * 60)
    print("Step 2: Downloading NYCU area tiles at confirmed levels")
    print("=" * 60)

    for level, (rmin, rmax, cmin, cmax) in sorted(NYCU_TILE_RANGES.items()):
        print(f"\nLevel {level}: R[{rmin}-{rmax}] x C[{cmin}-{cmax}]")
        tiles = download_level_range(
            LAYER_NAME, level, rmin, rmax, cmin, cmax,
            output_dir, delay=0.05
        )
        all_downloaded.extend(tiles)
        print(f"  Downloaded: {len(tiles)} tiles")

    # Step 3: Go deeper - levels 8, 9, 10 for NYCU core area
    # Core NYCU area from L7 observation: R52-55, C96-99
    print("\n" + "=" * 60)
    print("Step 3: Downloading deeper levels (8-10) for NYCU core")
    print("=" * 60)

    # NYCU core at L7: R52-55, C96-99
    core_row_min, core_row_max = 52, 55
    core_col_min, core_col_max = 96, 99

    for target_level in [8, 9, 10]:
        # Each level doubles the coordinate
        scale = 2 ** (target_level - 7)
        rmin = core_row_min * scale
        rmax = core_row_max * scale + (scale - 1)
        cmin = core_col_min * scale
        cmax = core_col_max * scale + (scale - 1)

        total_tiles = (rmax - rmin + 1) * (cmax - cmin + 1)
        print(f"\nLevel {target_level}: R[{rmin}-{rmax}] x C[{cmin}-{cmax}] ({total_tiles} tiles)")

        if total_tiles > 1000:
            print(f"  Too many tiles ({total_tiles}), skipping...")
            continue

        tiles = download_level_range(
            LAYER_NAME, target_level, rmin, rmax, cmin, cmax,
            output_dir, delay=0.03
        )
        all_downloaded.extend(tiles)
        print(f"  Downloaded: {len(tiles)} tiles")

        if len(tiles) == 0:
            print(f"  No data at level {target_level}, stopping deeper scan")
            break

    # Step 4: Analyze a sample tile
    print("\n" + "=" * 60)
    print("Step 4: Analyzing sample tiles")
    print("=" * 60)

    # Find the largest tile for analysis
    if all_downloaded:
        largest = max(all_downloaded, key=lambda x: x[3])
        l, r, c, s = largest
        sample_file = os.path.join(output_dir, f"L{l}", f"R{r}_C{c}.bin")
        print(f"\nLargest tile: L{l}/R{r}_C{c} ({s:,} bytes)")
        with open(sample_file, "rb") as f:
            sample_data = f.read()
        analyze_binary(sample_data, f"L{l}/R{r}_C{c}")

        # Also analyze a mid-size tile
        mid_tiles = sorted(all_downloaded, key=lambda x: x[3])
        mid = mid_tiles[len(mid_tiles) // 2]
        l2, r2, c2, s2 = mid
        sample_file2 = os.path.join(output_dir, f"L{l2}", f"R{r2}_C{c2}.bin")
        print(f"\nMid-size tile: L{l2}/R{r2}_C{c2} ({s2:,} bytes)")
        with open(sample_file2, "rb") as f:
            sample_data2 = f.read()
        analyze_binary(sample_data2, f"L{l2}/R{r2}_C{c2}")

    # Step 5: Also download terrain tiles for the same area
    print("\n" + "=" * 60)
    print("Step 5: Downloading terrain tiles for NYCU area")
    print("=" * 60)

    terrain_dir = os.path.join(output_dir, "terrain")
    os.makedirs(terrain_dir, exist_ok=True)

    terrain_downloaded = []
    for level in [7, 8]:
        if level == 7:
            rmin, rmax = 52, 55
            cmin, cmax = 96, 99
        else:
            rmin, rmax = 104, 111
            cmin, cmax = 192, 199

        t_dir = os.path.join(terrain_dir, f"L{level}")
        os.makedirs(t_dir, exist_ok=True)

        for row in range(rmin, rmax + 1):
            for col in range(cmin, cmax + 1):
                data = fetch_terrain_tile(level, row, col)
                if data:
                    filename = os.path.join(t_dir, f"R{row}_C{col}.bin")
                    with open(filename, "wb") as f:
                        f.write(data)
                    terrain_downloaded.append((level, row, col, len(data)))
                    print(f"  Terrain L{level}/R{row}_C{col}: {len(data):,} bytes")
                time.sleep(0.05)

    # Summary
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)

    total_tiles = len(all_downloaded)
    total_bytes = sum(d[3] for d in all_downloaded)
    print(f"Building tiles: {total_tiles}")
    print(f"Building data:  {total_bytes / 1024 / 1024:.2f} MB")

    if terrain_downloaded:
        terrain_bytes = sum(d[3] for d in terrain_downloaded)
        print(f"Terrain tiles:  {len(terrain_downloaded)}")
        print(f"Terrain data:   {terrain_bytes / 1024 / 1024:.2f} MB")

    # By level breakdown
    from collections import Counter
    level_counts = Counter(d[0] for d in all_downloaded)
    level_sizes = {}
    for d in all_downloaded:
        level_sizes[d[0]] = level_sizes.get(d[0], 0) + d[3]
    print(f"\nBy level:")
    for lvl in sorted(level_counts):
        print(f"  L{lvl}: {level_counts[lvl]} tiles, {level_sizes[lvl]/1024:.1f} KB")

    # Save manifest
    manifest = {
        "layer": LAYER_NAME,
        "target_area": {
            "name": "NYCU Guangfu Campus",
            "lon_range": [120.990, 121.005],
            "lat_range": [24.780, 24.795],
        },
        "tile_ranges": {
            str(k): {"row": [v[0], v[1]], "col": [v[2], v[3]]}
            for k, v in NYCU_TILE_RANGES.items()
        },
        "building_tiles": [
            {"level": d[0], "row": d[1], "col": d[2], "size": d[3]}
            for d in all_downloaded
        ],
        "terrain_tiles": [
            {"level": d[0], "row": d[1], "col": d[2], "size": d[3]}
            for d in terrain_downloaded
        ],
        "total_building_tiles": total_tiles,
        "total_building_bytes": total_bytes,
        "total_terrain_tiles": len(terrain_downloaded),
    }
    manifest_file = os.path.join(output_dir, "manifest.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\nManifest: {manifest_file}")


if __name__ == "__main__":
    main()
