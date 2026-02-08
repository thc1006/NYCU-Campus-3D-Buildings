# Processed Data - 處理後的數據

此目錄包含從原始 3D Tiles 提取並處理後的建築數據。

## 整理日期

2026-02-08 - 已按校區和數據源重組

## 目錄結構

```
processed/
├── buildings/
│   ├── by_campus/              # 按校區分類
│   │   ├── boai/               # 博愛校區 (1,023 棟)
│   │   │   └── NLSC_buildings.json
│   │   ├── yangming/           # 陽明校區 (446 棟)
│   │   │   └── NLSC_buildings.json
│   │   ├── gueiren/            # 歸仁校區 (17 棟)
│   │   │   └── NLSC_buildings.json
│   │   ├── liujia/             # 六甲校區 (169 棟)
│   │   │   └── NLSC_buildings.json
│   │   └── guangfu/            # 光復校區 (319 棟)
│   │       └── OSM_buildings.geojson
│   │
│   ├── combined/               # 合併數據
│   │   ├── with_surrounding.json      # 包含周邊建物 (6,181 棟)
│   │   └── with_surrounding.geojson
│   │
│   └── osm/                    # OpenStreetMap 數據
│
└── reference/                  # 參考文件
    └── building_names_list.txt
```

## 數據格式

- **JSON**: 原始建築資訊（包含高度、樓層等）
- **GeoJSON**: 地理空間格式（可用於 GIS 軟體）

## 校區統計

| 校區 | 建築數量 | 數據來源 |
|------|---------|---------|
| 博愛 | 1,023 棟 | NLSC Layer 112_O |
| 陽明 | 446 棟 | NLSC Layer 112_A/113_A |
| 六甲 | 169 棟 | NLSC Layer 113_J |
| 歸仁 | 17 棟 | NLSC Layer 112_D |
| 光復 | 319 棟 | OpenStreetMap |

## 使用範例

```python
import json
import geopandas as gpd

# 讀取特定校區的數據
with open("buildings/by_campus/yangming/NLSC_buildings.json") as f:
    yangming_data = json.load(f)

# 讀取合併數據（GeoJSON 格式）
gdf = gpd.read_file("buildings/combined/with_surrounding.geojson")
```
