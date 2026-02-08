# NYCU Campus 3D Buildings Dataset

[![DOI](https://zenodo.org/badge/1152618335.svg)](https://doi.org/10.5281/zenodo.18522926)

Comprehensive 3D building dataset for 5 NYCU campuses (~7,836 buildings) combining NLSC 3D models and OpenStreetMap data.

陽明交大 5 校區約 7,836 棟建築的 3D 空間資料集，結合國土測繪中心 3D 模型與 OpenStreetMap 資料。

## Dataset Overview

### Coverage

| Campus | Buildings | Data Source | Layer |
|--------|-----------|-------------|-------|
| Guangfu (光復) | 6,181 | NLSC + OSM | 112_O |
| Boai (博愛) | 1,023 | NLSC | 112_O |
| Yangming (陽明) | 446 | NLSC | 113_A |
| Liujia (六家) | 169 | NLSC | 113_J |
| Gueiren (歸仁) | 17 | NLSC | 112_D |
| **Total** | **~7,836** | | |

### Data Fields

**From NLSC (20 attributes)**
- BUILD_ID, BUILD_H (height), BUILD_STR (structure type)
- CENT_E_97, CENT_N_97 (TWD97 coordinates)
- Full list in processed data

**From OpenStreetMap**
- name (Chinese), name:en (English)
- building type
- geometry

## Quick Start

### Installation

```bash
git clone https://github.com/thc1006/NYCU-Campus-3D-Buildings.git
cd NYCU-Campus-3D-Buildings
pip install -r examples/requirements.txt
```

### Download Raw Data (Optional)

Download from [GitHub Releases](https://github.com/thc1006/NYCU-Campus-3D-Buildings/releases):
- `NYCU-Campus-3D-Buildings_raw_osm_v1.0.0.zip` (517.8 MB)
- `NYCU-Campus-3D-Buildings_raw_nlsc_v1.0.0.zip` (114.5 MB)

### Basic Usage

```python
import geopandas as gpd

# Load merged dataset
buildings = gpd.read_file('data/output/latest/buildings_merged.geojson')

# Filter by name
named = buildings[buildings['name'].notna()]

# Get top 10 tallest buildings
top_10 = named.nlargest(10, 'nlsc_BUILD_H')
print(top_10[['name', 'nlsc_BUILD_H', 'nlsc_BUILD_STR']])
```

## Repository Structure

```
NYCU-Campus-3D-Buildings/
├── data/
│   ├── raw/              # Raw data (in Releases)
│   ├── processed/        # Processed data by campus
│   └── output/
│       └── latest/
│           ├── buildings_merged.geojson  # Main dataset
│           ├── buildings_table.csv
│           ├── buildings_table.xlsx
│           └── buildings_3d.html         # 3D viewer
│
├── scripts/              # Processing scripts (01-08)
├── examples/             # Jupyter notebooks
└── docs/                 # Documentation
```

## Data Sources and Licenses

### 1. NLSC 3D Building Model Data

國土測繪中心 3D 建築模型資料

- **Source**: National Land Surveying and Mapping Center, Taiwan
- **License**: Open Government Data License (compatible with CC BY 4.0)
- **Website**: https://3dmaps.nlsc.gov.tw/

**Attribution**:
```
Data Source: National Land Surveying and Mapping Center (NLSC), Taiwan
資料來源：國土測繪中心
```

### 2. OpenStreetMap Data

開放街圖資料

- **Source**: OpenStreetMap Contributors
- **License**: Open Database License (ODbL) 1.0
- **Website**: https://www.openstreetmap.org/

**REQUIRED Attribution**:
```
© OpenStreetMap contributors
Data available under the Open Database License
資料採用開放資料庫授權
```

### 3. NYCU Official Data

陽明交大官方資料

- **Source**: National Yang Ming Chiao Tung University
- **Content**: Campus maps, floor plans
- **Usage**: Fair use for educational and research purposes

**Attribution**:
```
Campus maps courtesy of National Yang Ming Chiao Tung University
校園地圖由國立陽明交通大學提供
```

### Combined Dataset License

**This project**: CC BY 4.0 + ODbL Attribution Requirements

**When using this dataset, please cite**:
1. National Land Surveying and Mapping Center 3D Building Models
2. OpenStreetMap contributors (ODbL 1.0)
3. NYCU-Campus-3D-Buildings project (CC BY 4.0)

## Examples

See `examples/` directory for Jupyter notebooks:

1. **01_basic_usage.ipynb**: Load, filter, export
2. **02_data_analysis.ipynb**: Height distribution, structure analysis
3. **03_visualization.ipynb**: Interactive maps, heatmaps

## Citation

See `CITATION.cff` for standard citation format.

**BibTeX**:
```bibtex
@dataset{tsai2026nycu,
  author = {Tsai, Hsiu-Chi},
  title = {NYCU Campus 3D Buildings Dataset},
  year = {2026},
  publisher = {GitHub},
  url = {https://github.com/thc1006/NYCU-Campus-3D-Buildings}
}
```

## Contributing

See `CONTRIBUTING.md` for guidelines.

- **Issues**: [GitHub Issues](https://github.com/thc1006/NYCU-Campus-3D-Buildings/issues)
- **Discussions**: [GitHub Discussions](https://github.com/thc1006/NYCU-Campus-3D-Buildings/discussions)

## Maintainer

**Hsiu-Chi Tsai (thc1006) / 蔡秀吉**
- Email: hctsai@linux.com
- Affiliation: National Yang Ming Chiao Tung University (國立陽明交通大學)

### **License**
- Mixed (CC BY 4.0 + ODbL 1.0) - See LICENSE for details
**Version**: 1.0.0
**Last Updated**: 2026-02-08