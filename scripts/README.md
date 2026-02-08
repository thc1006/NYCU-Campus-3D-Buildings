# Processing Scripts / 處理腳本

**TL;DR**: Core scripts (01-08) for processing NLSC 3D tiles and OSM data. Run in sequence to reproduce the dataset.

**簡介**: 核心腳本（01-08）用於處理 NLSC 3D 瓦片和 OSM 資料。依序執行以重現資料集。

---

## Core Pipeline / 核心流程

### Guangfu Campus / 光復校區 (Scripts 01-04)

**01_download_nlsc_tiles.py**
- Download NLSC 3D tiles for Guangfu campus / 下載光復校區 NLSC 3D 瓦片
- Output: `data/raw/NLSC_3D_tiles/current/112_O_guangfu/`

**02_extract_osm_buildings.py**
- Extract building data from OpenStreetMap / 從 OpenStreetMap 擷取建築資料
- Output: `data/processed/buildings/by_campus/guangfu/OSM_buildings.geojson`

**03_parse_nlsc_tiles.py**
- Parse NLSC binary tiles and extract attributes / 解析 NLSC 二進位瓦片並擷取屬性
- Output: Parsed building data with 20 attributes / 20 個屬性的建築資料

**04_merge_datasets.py**
- Merge NLSC and OSM data / 合併 NLSC 和 OSM 資料
- Output: `data/output/latest/buildings_merged.geojson`

### Export / 匯出 (Script 05)

**05_export_building_table.py**
- Export building data to CSV/Excel formats / 匯出建築資料為 CSV/Excel 格式
- Output:
  - `data/output/latest/buildings_table.csv`
  - `data/output/latest/buildings_table.xlsx`

### Multi-Campus / 多校區 (Scripts 06-08)

**06_download_multi_campus.py**
- Download NLSC tiles for other campuses / 下載其他校區的 NLSC 瓦片
- Campuses: Boai, Yangming, Liujia, Gueiren / 博愛、陽明、六家、歸仁

**07_parse_multi_campus.py**
- Parse tiles for all campuses / 解析所有校區的瓦片
- Output: Individual campus JSON files / 各校區 JSON 檔案

**08_download_quadtree.py**
- Download using quadtree BFS method (correct method) / 使用四叉樹 BFS 方法下載（正確方法）
- Output: `data/raw/NLSC_quadtree/`

---

## Usage / 使用方式

### Prerequisites / 前置需求

```bash
pip install geopandas shapely pandas requests tqdm
```

### Run Pipeline / 執行流程

```bash
# Full Guangfu campus pipeline / 完整光復校區流程
python 01_download_nlsc_tiles.py
python 02_extract_osm_buildings.py
python 03_parse_nlsc_tiles.py
python 04_merge_datasets.py
python 05_export_building_table.py

# Multi-campus / 多校區
python 06_download_multi_campus.py
python 07_parse_multi_campus.py
python 08_download_quadtree.py
```

---

## Notes / 注意事項

- Scripts use relative paths / 腳本使用相對路徑
- Run from repository root / 從儲存庫根目錄執行
- Large downloads may take time / 大量下載可能需要時間
- Check `../data/` for outputs / 輸出檔案在 `../data/` 目錄

---

## Local Archive / 本地存檔

`local_archive/` directory contains historical scripts (not tracked by Git) / `local_archive/` 目錄包含歷史腳本（不被 Git 追蹤）
