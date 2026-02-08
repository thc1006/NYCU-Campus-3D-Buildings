# NYCU Campus Building Spatial Dataset

[![License: Mixed](https://img.shields.io/badge/License-Mixed-blue.svg)](LICENSE)
[![Data: NLSC + OSM](https://img.shields.io/badge/Data-NLSC%20%2B%20OSM-green.svg)](docs/DATA_SOURCES_AND_LICENSES.md)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)

> 結合國土測繪中心 3D 建築模型與 OpenStreetMap 資料的陽明交大校園建築空間資料集
>
> A comprehensive geospatial dataset combining NLSC 3D building models and OpenStreetMap data for NYCU campuses

---

## 📊 資料集概述

本專案整合兩大開放資料來源，建立完整的陽明交大校園建築資料集，涵蓋 **5 個校區**，共約 **7,836 棟建築**，包含 3D 幾何、建築屬性與平面圖資料。

| 資料來源 | 內容 | 數量 | 特色 |
|---------|------|------|------|
| **NLSC 3D Maps** | 建築高度、座標、結構類型 | ~7,836 棟 | 精確高度、20 個屬性欄位 |
| **OpenStreetMap** | 建築輪廓、中英文名稱 | 319 棟（光復校區） | 完整幾何形狀 + 雙語名稱 |

### 校區涵蓋範圍

| 校區 | 建築數量 | NLSC 圖層 | 備註 |
|------|---------|----------|------|
| 光復校區 Guangfu | 6,181 | 112_O (2023) | 完整資料，含 OSM 輪廓 |
| 博愛校區 Boai | 1,023 | 112_O (2023) | NLSC 資料 |
| 陽明校區 Yangming | 446 | 113_A | NLSC 資料 |
| 六家校區 Liujia | 169 | 113_J | NLSC 資料 |
| 歸仁校區 Gueiren | 17 | 112_D | 稀疏資料 |
| **總計** | **~7,836** | | |

---

## 🎯 主要特色

- ✅ **5 個校區完整涵蓋** - 光復、博愛、陽明、六家、歸仁
- ✅ **20 個建築屬性欄位** - 高度、座標、結構類型、測量日期等
- ✅ **3D 建築模型** - NLSC 官方 3D 資料
- ✅ **雙語建築名稱** - 中英文對照（光復校區）
- ✅ **開放格式** - GeoJSON, CSV, Excel, HTML
- ✅ **完整處理管線** - 34 個 Python 腳本，可重現所有處理步驟
- ✅ **互動式視覺化** - HTML 地圖檢視器
- ✅ **FAIR 原則符合** - Findable, Accessible, Interoperable, Reusable

---

## 🚀 快速開始

### 1. 下載資料集

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/NQSD.git
cd NQSD

# 下載原始資料（從 GitHub Release）
# 請前往 Releases 頁面下載：
# - NQSD_raw_osm_data_v1.0.0.zip (523 MB)
# - NQSD_raw_nlsc_tiles_v1.0.0.zip (118 MB)
#
# 解壓縮到 data/raw/ 目錄
```

### 2. 查看處理後的資料

```bash
# 最終合併資料集（GeoJSON 格式）
data/output/latest/buildings_merged.geojson  # 1.2 MB, 2,309 features

# 建築清單（CSV 和 Excel）
data/output/latest/buildings_table.csv
data/output/latest/buildings_table.xlsx

# 互動式地圖
data/output/latest/buildings_3d.html  # 在瀏覽器中開啟
```

### 3. 執行處理腳本（選用）

```bash
# 安裝依賴（僅需一次）
pip install geopandas shapely pandas openpyxl

# 執行完整處理管線
python scripts/01_download_nlsc_tiles.py      # 下載 NLSC 3D 瓦片
python scripts/02_extract_osm_buildings.py    # 提取 OSM 建築
python scripts/03_parse_nlsc_tiles.py         # 解析 NLSC 二進位格式
python scripts/04_merge_datasets.py           # 合併 OSM + NLSC
```

---

## 📁 專案結構

```
NQSD/
├── README.md                     本文件
├── CITATION.cff                  引用資訊（標準格式）
├── LICENSE                       混合授權說明
├── .gitignore                    Git 忽略規則
│
├── scripts/                      處理管線腳本（34 個）
│   ├── 01_download_nlsc_tiles.py
│   ├── 02_extract_osm_buildings.py
│   ├── 03_parse_nlsc_tiles.py
│   ├── 04_merge_datasets.py
│   └── ... (其他腳本)
│
├── data/
│   ├── processed/                處理後資料（9.7 MB）
│   │   └── buildings/
│   │       ├── by_campus/        按校區分類
│   │       ├── combined/         合併資料
│   │       └── osm/              OSM 資料
│   │
│   ├── output/                   最終輸出（3.2 MB）
│   │   └── latest/
│   │       ├── buildings_merged.geojson
│   │       ├── buildings_3d.html
│   │       ├── buildings_table.csv
│   │       └── buildings_table.xlsx
│   │
│   └── floor_plans/              平面圖（24 MB）
│
├── docs/                         文件目錄
│   ├── DATA_SOURCES_AND_LICENSES.md
│   ├── campus_maps/              校園地圖（61 MB）
│   ├── references/               參考文獻
│   └── 3d_models/                3D 模型範例
│
└── examples/                     Jupyter Notebook 範例
    ├── 01_basic_usage.ipynb
    ├── 02_data_analysis.ipynb
    ├── 03_visualization.ipynb
    └── sample_data/
```

---

## 📊 資料欄位說明

### OSM 來源欄位

| 欄位名稱 | 說明 | 範例 |
|---------|------|------|
| `geometry` | 建築輪廓（多邊形） | Polygon |
| `name` | 中文名稱 | 工程四館 |
| `name:en` | 英文名稱 | Engineering Building 4 |
| `building` | 建築類型 | university |
| `building:levels` | 樓層數 | 11 |

### NLSC 來源欄位

| 欄位名稱 | 說明 | 範例 |
|---------|------|------|
| `nlsc_BUILD_H` | 建築高度（公尺） | 40.45 |
| `nlsc_BUILD_ID` | NLSC 建物 ID | 2BUEV72Q94 |
| `nlsc_BUILD_STR` | 結構類型 | R（鋼筋混凝土） |
| `nlsc_CENT_E_97` | TWD97 東距座標 | 249321.456 |
| `nlsc_CENT_N_97` | TWD97 北距座標 | 2741234.789 |
| `nlsc_MDATE` | 測量日期 | 201802 |

完整欄位說明請參考 [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md)（待建立）

---

## 🔬 使用範例

### Python（GeoPandas）

```python
import geopandas as gpd

# 讀取合併資料集
buildings = gpd.read_file('data/output/latest/buildings_merged.geojson')

# 過濾有名稱的建築
named = buildings[buildings['name'].notna()]

# 找出最高的 10 棟建築
top_10 = named.nlargest(10, 'nlsc_BUILD_H')[['name', 'nlsc_BUILD_H']]
print(top_10)
```

### Jupyter Notebook

查看 [`examples/`](examples/) 目錄中的範例：
- `01_basic_usage.ipynb` - 基礎使用
- `02_data_analysis.ipynb` - 資料分析
- `03_visualization.ipynb` - 視覺化

---

## 📝 資料來源與授權

### 資料來源

1. **NLSC 3D 建築模型資料**
   - 提供單位：國土測繪中心（National Land Surveying and Mapping Center）
   - 網址：https://3dmaps.nlsc.gov.tw/
   - 內容：建築高度、座標、結構類型

2. **OpenStreetMap 資料**
   - 提供單位：OpenStreetMap 貢獻者
   - 網址：https://www.openstreetmap.org/
   - 內容：建築輪廓、名稱

3. **NYCU 官方資料**
   - 提供單位：國立陽明交通大學
   - 內容：校園地圖、平面圖

### 授權條款

- **NLSC 資料**：政府資料開放授權條款（相容 CC BY 4.0）
- **OSM 資料**：Open Database License (ODbL) 1.0
- **本專案腳本**：MIT License
- **本專案文件**：CC BY 4.0

**重要**：使用本資料集時請標註：
```
資料來源：
1. 國土測繪中心 3D 建築模型資料
2. © OpenStreetMap 貢獻者（Open Database License）
```

詳細授權資訊請參考：[`LICENSE`](LICENSE) 和 [`docs/DATA_SOURCES_AND_LICENSES.md`](docs/DATA_SOURCES_AND_LICENSES.md)

---

## 📖 文件

- [**快速開始指南**](docs/QUICK_START.md) - 詳細安裝和使用說明
- [**資料來源與授權**](docs/DATA_SOURCES_AND_LICENSES.md) - 完整授權資訊
- [**處理流程**](docs/PROCESSING_PIPELINE.md) - 資料處理管線說明（待建立）
- [**NLSC 協定**](docs/NLSC_PROTOCOL.md) - NLSC 3D Maps 技術文件（待建立）
- [**校園地圖**](docs/campus_maps/) - 5 個校區官方地圖
- [**3D 模型**](docs/3d_models/) - 範例 3D 建築模型

---

## 🤝 如何引用

如果您在研究中使用本資料集，請引用：

```bibtex
@dataset{nqsd_2026,
  author = {待填入您的姓名},
  title = {NYCU Campus Building Spatial Dataset},
  year = {2026},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.XXXXXX},
  url = {https://github.com/YOUR_USERNAME/NQSD}
}
```

或使用 [`CITATION.cff`](CITATION.cff) 標準格式。

**資料來源標註**：
```
本研究使用之建築資料結合：
1. 國土測繪中心 3D 建築模型資料（政府資料開放授權）
2. OpenStreetMap 建築輪廓資料（© OSM 貢獻者，ODbL 1.0）
3. NQSD 專案整合處理（CC BY 4.0）
```

---

## 🛠️ 技術細節

### NLSC 3D Maps 協定

本專案透過逆向工程解析了 NLSC 3D Maps 的 PilotGaea oview 協定：

- **伺服器**: mapserver{01,02,51}.nlsc.gov.tw
- **格式**: 專有二進位瓦片（.bin）
- **資料結構**: 標頭（12 bytes）+ OBB 包圍盒（192 bytes）+ 屬性區段
- **屬性儲存**: Column-oriented 格式，20 個欄位

詳細技術文件請參考原始 README 或 `docs/NLSC_PROTOCOL.md`（待整理）

### 相依套件

- Python 3.8+
- GeoPandas, Shapely - 地理空間資料處理
- Pandas - 資料分析
- Matplotlib, Folium - 視覺化

完整清單請參考 `examples/requirements.txt`

---

## 📊 統計資料

### 光復校區建築高度（前 15 名）

| 建築名稱 | 高度 (m) |
|---------|---------|
| 梅竹山莊 | 79.7 |
| 和選旅 (The HO) | 61.7 |
| 太空計畫室高層廠房 | 55.6 |
| 奈米電子研究大樓 | 48.2 |
| 女二舍A棟 | 46.8 |
| 工程五館 | 45.8 |
| 綜合一館 | 45.4 |
| 女二舍B棟 | 44.7 |
| 研三舍 | 43.2 |
| 清齋 | 41.1 |
| 工程四館 | 40.5 |
| 田家炳光電大樓 | 40.0 |
| 工程一館 | 39.3 |
| 電子資訊大樓 | 39.1 |
| （更多...） | |

### 合併成果統計

| 項目 | 數值 |
|------|------|
| OSM 建築總數 | 319（185 有名稱） |
| NLSC 建築總數 | 6,181 |
| OSM 成功匹配 NLSC | 267 / 319（83.7%） |
| 合併資料集總特徵數 | 2,309 |

---

## 🤝 貢獻

歡迎貢獻！請參考 [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md)

**貢獻方式**：
- 🐛 回報資料錯誤或問題
- 📝 改進文件
- 🔧 提交處理腳本改進
- 🎨 分享您的使用案例

---

## 📞 聯絡與支援

- **問題回報**: [GitHub Issues](https://github.com/YOUR_USERNAME/NQSD/issues)
- **討論區**: [GitHub Discussions](https://github.com/YOUR_USERNAME/NQSD/discussions)

---

## 📜 版本歷史

- **v1.0.0** (2026-02-08) - 初始版本
  - 5 個校區完整資料
  - 34 個處理腳本
  - 完整文件與範例

---

## 🙏 致謝

感謝以下單位提供開放資料：
- 國土測繪中心（NLSC）
- OpenStreetMap 貢獻者
- 國立陽明交通大學

---

**專案維護**: 蔡秀吉 (thc1006) <hctsai@linux.com>
**最後更新**: 2026-02-08
**資料版本**: v1.0.0
