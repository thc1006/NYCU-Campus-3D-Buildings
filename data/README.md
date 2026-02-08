# Data Directory / 資料目錄

**TL;DR**: Organized data directory containing raw, processed, and output data for NYCU campus buildings.

**簡介**: 有組織的資料目錄，包含陽明交大校園建築的原始、處理和輸出資料。

---

## Structure / 結構

### raw/ - Raw Data / 原始資料
**Note / 註**: Large files (641 MB) hosted in GitHub Releases
**說明**: 大檔案（641 MB）託管於 GitHub Releases

- auxiliary/ - OSM data / OSM 資料 (517.8 MB)
- NLSC_3D_tiles/ - NLSC tile data / NLSC 瓦片資料 (105 MB)
- NLSC_quadtree/ - NLSC quadtree / NLSC 四叉樹 (13 MB)

### processed/ - Processed Data / 處理後資料
- buildings/by_campus/ - Data by campus / 各校區資料
- buildings/combined/ - Combined datasets / 合併資料集

### output/ - Final Outputs / 最終輸出
- latest/ - Latest version / 最新版本
  - buildings_merged.geojson - Main dataset / 主要資料集
  - buildings_table.csv - Tabular format / 表格格式
  - buildings_table.xlsx - Excel format / Excel 格式
  - buildings_3d.html - 3D viewer / 3D 檢視器

---

## Download Raw Data / 下載原始資料

See GitHub Releases: https://github.com/thc1006/NYCU-Campus-3D-Buildings/releases

Download:
- NYCU-Campus-3D-Buildings_raw_osm_v1.0.0.zip
- NYCU-Campus-3D-Buildings_raw_nlsc_v1.0.0.zip

---

**Total Size / 總大小**: ~1.3 GB (including raw data / 包含原始資料)
