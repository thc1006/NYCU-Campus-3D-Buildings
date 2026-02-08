# Data Sources and Licenses

**Last Updated**: 2026-02-08

---

## 📊 Data Sources Overview

This dataset combines data from multiple authoritative sources to provide comprehensive building information for NYCU campuses.

| Source | Content | Coverage | License |
|--------|---------|----------|---------|
| **NLSC 3D Maps** | Building heights, coordinates, structure types | ~7,836 buildings (5 campuses) | Open Government Data (Taiwan) |
| **OpenStreetMap** | Building footprints, names (bilingual) | 319 buildings (Guangfu campus) | ODbL 1.0 |
| **NYCU Official** | Campus maps, floor plans | 5 campuses | Fair Use (Educational) |

---

## 🗺️ 1. NLSC 3D Building Data

### Source Information

- **Provider**: National Land Surveying and Mapping Center (NLSC), Taiwan
- **Website**: https://3dmaps.nlsc.gov.tw/
- **Data Type**: 3D Building Models with 20 attribute fields

### What NLSC Provides

- ✅ **Precise Building Heights** (BUILD_H, in meters)
- ✅ **TWD97 Coordinates** (CENT_E_97, CENT_N_97)
- ✅ **Structure Types** (BUILD_STR: R=Reinforced Concrete, B=Brick, S=Steel)

### License

**Open Government Data License (Taiwan)** - Compatible with CC BY 4.0

### Attribution

Simply cite in README.md:
```
Data Source: National Land Surveying and Mapping Center (NLSC), Taiwan
```

---

## 🗺️ 2. OpenStreetMap Data

### Source Information

- **Provider**: OpenStreetMap Contributors
- **Website**: https://www.openstreetmap.org/
- **Coverage**: Guangfu Campus (319 buildings, 185 with names)

### What OpenStreetMap Provides

- ✅ **Building Footprints** (Polygon geometries)
- ✅ **Bilingual Names** (e.g., "工程四館 / Engineering Building 4")
- ✅ **Building Types** and floor levels

### License

**Open Database License (ODbL) 1.0**

**Attribution (Required)**:
```
© OpenStreetMap contributors
Data available under the Open Database License
```

### Important ODbL Requirements

⚠️ **You must**:
1. Credit OpenStreetMap contributors
2. Share derived databases under ODbL
3. Keep data open

📖 More info: https://www.openstreetmap.org/copyright

---

## 🔄 Merged Dataset (This Project)

### License

- **Processing Scripts**: MIT License
- **Documentation**: CC BY 4.0
- **Merged Data**: CC BY 4.0 + ODbL Attribution (contains OSM data)

### How to Cite

See `CITATION.cff` for standard citation format.

---

**For full details**, see the complete license documentation in `LICENSE` file.
