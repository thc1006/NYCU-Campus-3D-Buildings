# NYCU Campus 3D Buildings Dataset

**TL;DR**: Comprehensive 3D building dataset for 5 NYCU campuses (~7,836 buildings) combining NLSC 3D models and OpenStreetMap data, suitable for civil engineering, architecture, and GIS research.

**簡介**: 陽明交大 5 校區（光復、博愛、陽明、六家、歸仁）約 7,836 棟建築的 3D 空間資料集，結合國土測繪中心 3D 模型與 OpenStreetMap 資料，適用於土木工程、建築與 GIS 研究。

---

## Dataset Overview / 資料集概述

### Coverage / 涵蓋範圍

| Campus / 校區 | Buildings / 建築數 | Data Source / 資料來源 | Layer / 圖層 |
|---------------|-------------------|----------------------|--------------|
| Guangfu / 光復 | 6,181 | NLSC + OSM | 112_O |
| Boai / 博愛 | 1,023 | NLSC | 112_O |
| Yangming / 陽明 | 446 | NLSC | 113_A |
| Liujia / 六家 | 169 | NLSC | 113_J |
| Gueiren / 歸仁 | 17 | NLSC | 112_D |
| **Total / 總計** | **~7,836** | | |

### Data Fields / 資料欄位

**From NLSC (20 attributes) / 國土測繪中心（20 個屬性）**:
- BUILD_ID, BUILD_H (height / 高度), BUILD_STR (structure / 結構類型)
- CENT_E_97, CENT_N_97 (TWD97 coordinates / TWD97 座標)
- Full list in processed data / 完整清單見處理後資料

**From OSM / OpenStreetMap**:
- name (Chinese / 中文), name:en (English / 英文)
- building type / 建築類型
- geometry / 幾何輪廓

---

## Quick Start / 快速開始

### Installation / 安裝

```bash
# Clone repository / 複製儲存庫
git clone https://github.com/thc1006/NYCU-Campus-3D-Buildings.git
cd NYCU-Campus-3D-Buildings

# Install dependencies / 安裝依賴套件
pip install -r examples/requirements.txt

# Download raw data from GitHub Releases (optional)
# 從 GitHub Releases 下載原始資料（可選）
# - NYCU-Campus-3D-Buildings_raw_osm_v1.0.0.zip (517.8 MB)
# - NYCU-Campus-3D-Buildings_raw_nlsc_v1.0.0.zip (114.5 MB)
```

### Basic Usage / 基本使用

```python
import geopandas as gpd

# Load merged dataset / 載入合併資料集
buildings = gpd.read_file('data/output/latest/buildings_merged.geojson')

# Filter by name / 依名稱過濾
named = buildings[buildings['name'].notna()]

# Get top 10 tallest buildings / 取得最高的 10 棟建築
top_10 = named.nlargest(10, 'nlsc_BUILD_H')
print(top_10[['name', 'nlsc_BUILD_H', 'nlsc_BUILD_STR']])

# Export to CSV / 匯出為 CSV
buildings.to_csv('buildings.csv', index=False)
```

---

## Repository Structure / 儲存庫結構

```
NYCU-Campus-3D-Buildings/
├── data/                          # Data files / 資料檔案
│   ├── raw/                       # Raw data (in Releases) / 原始資料（於 Releases）
│   ├── processed/                 # Processed data / 處理後資料
│   └── output/                    # Final outputs / 最終輸出
│       └── latest/
│           ├── buildings_merged.geojson  # Main dataset / 主要資料集
│           ├── buildings_table.csv       # Tabular format / 表格格式
│           ├── buildings_table.xlsx      # Excel format / Excel 格式
│           └── buildings_3d.html         # 3D viewer / 3D 檢視器
│
├── scripts/                       # Processing scripts / 處理腳本
│   ├── 01_download_nlsc_tiles.py  # Download NLSC data / 下載 NLSC 資料
│   ├── 02_extract_osm_buildings.py # Extract OSM data / 擷取 OSM 資料
│   ├── 03_parse_nlsc_tiles.py     # Parse NLSC tiles / 解析 NLSC 瓦片
│   └── 04_merge_datasets.py       # Merge datasets / 合併資料集
│
├── examples/                      # Example notebooks / 範例筆記本
│   ├── 01_basic_usage.ipynb       # Basic operations / 基本操作
│   ├── 02_data_analysis.ipynb     # Data analysis / 資料分析
│   └── 03_visualization.ipynb     # Visualization / 視覺化
│
└── docs/                          # Documentation / 文件
    ├── campus_maps/               # Campus maps / 校園地圖
    ├── 3d_models/                 # 3D models / 3D 模型
    └── DATA_SOURCES_AND_LICENSES.md  # License info / 授權資訊
```

---

## Data Sources and Licenses / 資料來源與授權

### 1. NLSC 3D Building Model Data / 國土測繪中心 3D 建築模型資料

**Source / 來源**: National Land Surveying and Mapping Center, Taiwan / 國土測繪中心
**License / 授權**: Open Government Data License, Taiwan (compatible with CC BY 4.0) / 政府資料開放授權條款（相容 CC BY 4.0）
**Website / 網站**: https://3dmaps.nlsc.gov.tw/

**Attribution / 標註**:
```
Data Source: National Land Surveying and Mapping Center (NLSC), Taiwan
資料來源：國土測繪中心
```

### 2. OpenStreetMap Data / OpenStreetMap 資料

**Source / 來源**: OpenStreetMap Contributors / OpenStreetMap 貢獻者
**License / 授權**: Open Database License (ODbL) 1.0
**Website / 網站**: https://www.openstreetmap.org/

**Required Attribution / 必須標註**:
```
© OpenStreetMap contributors
Data available under the Open Database License
資料採用開放資料庫授權
```

### 3. NYCU Official Data / 陽明交大官方資料

**Source / 來源**: National Yang Ming Chiao Tung University / 國立陽明交通大學
**Content / 內容**: Campus maps, floor plans / 校園地圖、平面圖
**Usage / 用途**: Fair use for educational and research purposes / 教育與研究用途合理使用

### Combined Dataset License / 合併資料集授權

**This project / 本專案**: CC BY 4.0 + ODbL Attribution Requirements

**When using this dataset, please cite / 使用本資料集時請引用**:
1. National Land Surveying and Mapping Center 3D Building Models / 國土測繪中心 3D 建築模型資料
2. OpenStreetMap contributors (ODbL 1.0) / OpenStreetMap 貢獻者（ODbL 1.0）
3. NYCU-Campus-3D-Buildings project (CC BY 4.0) / NYCU-Campus-3D-Buildings 專案（CC BY 4.0）

---

## Examples / 範例

See `examples/` directory for Jupyter notebooks / 參見 `examples/` 目錄的 Jupyter 筆記本：

1. **01_basic_usage.ipynb**: Load data, filter, export / 載入資料、過濾、匯出
2. **02_data_analysis.ipynb**: Height distribution, structure analysis / 高度分佈、結構分析
3. **03_visualization.ipynb**: Interactive maps, heatmaps / 互動式地圖、熱力圖

---

## Citation / 引用格式

See `CITATION.cff` for standard citation format / 標準引用格式請參考 `CITATION.cff`

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

---

## Contributing / 貢獻

See `CONTRIBUTING.md` for guidelines / 貢獻指南請參考 `CONTRIBUTING.md`

**Issue Reporting / 問題回報**: [GitHub Issues](https://github.com/thc1006/NYCU-Campus-3D-Buildings/issues)
**Discussions / 討論區**: [GitHub Discussions](https://github.com/thc1006/NYCU-Campus-3D-Buildings/discussions)

---

## Maintainer / 維護者

**Hsiu-Chi Tsai (thc1006) / 蔡秀吉**
Email: hctsai@linux.com
Affiliation: National Yang Ming Chiao Tung University / 國立陽明交通大學

---

## Changelog / 更新日誌

### v1.0.0 (2026-02-08)

- Initial release / 首次發布
- 5 campuses, ~7,836 buildings / 5 個校區，約 7,836 棟建築
- 20 NLSC attributes + OSM names / 20 個 NLSC 屬性 + OSM 名稱
- 3 example Jupyter notebooks / 3 個範例 Jupyter 筆記本
- Interactive 3D viewer / 互動式 3D 檢視器

---

**License**: Mixed (CC BY 4.0 + ODbL 1.0) / 混合授權（CC BY 4.0 + ODbL 1.0）
**Version**: 1.0.0
**Last Updated**: 2026-02-08
