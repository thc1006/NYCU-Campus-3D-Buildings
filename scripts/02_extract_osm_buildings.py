"""
Extract NYCU Guangfu Campus buildings from Taiwan OSM PBF file.
Outputs GeoJSON with building footprints.
"""
import json
import osmium

# NYCU Guangfu Campus bounding box
# Approximate bounds covering the main campus area
MIN_LON = 120.990
MAX_LON = 121.005
MIN_LAT = 24.780
MAX_LAT = 24.795

class BuildingHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.buildings = []
        self.node_cache = {}
        # We need two passes: first collect nodes, then process ways

class NodeCollector(osmium.SimpleHandler):
    """First pass: collect all node coordinates."""
    def __init__(self):
        super().__init__()
        self.nodes = {}

    def node(self, n):
        if MIN_LON - 0.01 <= n.location.lon <= MAX_LON + 0.01 and \
           MIN_LAT - 0.01 <= n.location.lat <= MAX_LAT + 0.01:
            self.nodes[n.id] = (n.location.lon, n.location.lat)


class BuildingExtractor(osmium.SimpleHandler):
    """Second pass: extract buildings using cached nodes."""
    def __init__(self, nodes):
        super().__init__()
        self.nodes = nodes
        self.buildings = []

    def way(self, w):
        tags = dict(w.tags)
        if 'building' not in tags:
            return

        # Build coordinate list
        coords = []
        for node_ref in w.nodes:
            if node_ref.ref in self.nodes:
                coords.append(self.nodes[node_ref.ref])

        if len(coords) < 3:
            return

        # Check if building centroid is within bounding box
        avg_lon = sum(c[0] for c in coords) / len(coords)
        avg_lat = sum(c[1] for c in coords) / len(coords)

        if not (MIN_LON <= avg_lon <= MAX_LON and MIN_LAT <= avg_lat <= MAX_LAT):
            return

        # Close the polygon if needed
        if coords[0] != coords[-1]:
            coords.append(coords[0])

        properties = {
            "osm_id": w.id,
            "building": tags.get("building", "yes"),
        }
        # Add useful tags
        for key in ["name", "name:en", "name:zh", "height", "building:levels",
                     "addr:street", "addr:housenumber", "amenity", "operator"]:
            if key in tags:
                properties[key] = tags[key]

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            },
            "properties": properties
        }
        self.buildings.append(feature)


def main():
    import pathlib
    project_dir = pathlib.Path(__file__).parent.parent
    pbf_file = str(project_dir / "data" / "raw" / "taiwan-osm-latest.osm.pbf")
    output_file = str(project_dir / "data" / "processed" / "NYCU_Guangfu_OSM_buildings.geojson")

    print(f"Bounding box: [{MIN_LON}, {MIN_LAT}] to [{MAX_LON}, {MAX_LAT}]")

    # Pass 1: Collect nodes in the area
    print("Pass 1: Collecting nodes...")
    node_collector = NodeCollector()
    node_collector.apply_file(pbf_file)
    print(f"  Found {len(node_collector.nodes)} nodes in area")

    # Pass 2: Extract buildings
    print("Pass 2: Extracting buildings...")
    extractor = BuildingExtractor(node_collector.nodes)
    extractor.apply_file(pbf_file)
    print(f"  Found {len(extractor.buildings)} buildings")

    # Create GeoJSON FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "name": "NYCU_Guangfu_Campus_Buildings",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}
        },
        "features": extractor.buildings
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(extractor.buildings)} buildings to {output_file}")

    # Print summary of named buildings
    named = [b for b in extractor.buildings if "name" in b["properties"]]
    if named:
        print(f"\nNamed buildings ({len(named)}):")
        for b in sorted(named, key=lambda x: x["properties"].get("name", "")):
            props = b["properties"]
            name = props.get("name", "")
            name_en = props.get("name:en", "")
            levels = props.get("building:levels", "?")
            display = f"  - {name}"
            if name_en:
                display += f" ({name_en})"
            display += f" [levels: {levels}, type: {props.get('building', 'yes')}]"
            print(display)


if __name__ == "__main__":
    main()
