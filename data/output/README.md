# Output - 最終輸出

此目錄包含最終的可視化和分析結果。

## 整理日期

2026-02-08 - 已建立版本控制

## 目錄結構

```
output/
├── latest/                      # 最新版本（自動更新）
│   ├── buildings_merged.geojson
│   ├── buildings_3d.geojson
│   ├── buildings_3d.html
│   ├── buildings_map.html
│   ├── buildings_table.csv
│   └── buildings_table.xlsx
│
├── v1_2026-02-07/              # 版本化存檔
│   └── [same files as latest]
│
└── archive/                     # 舊版本（壓縮）
```

## 文件說明

| 文件 | 格式 | 大小 | 描述 |
|------|------|------|------|
| buildings_merged.geojson | GeoJSON | 1.24 MB | 合併的完整建築數據 (2,309 棟) |
| buildings_3d.geojson | GeoJSON | 232 KB | 3D 建築數據 |
| buildings_3d.html | HTML | 13 KB | 3D 互動地圖 |
| buildings_map.html | HTML | 9 KB | 2D 互動地圖 |
| buildings_table.csv | CSV | 29 KB | 建築資料表 |
| buildings_table.xlsx | Excel | 52 KB | Excel 格式資料表 |

## 數據來源

- **NLSC**: 6,181 棟建築（含周邊）
- **OSM**: 319 棟建築（光復校區）
- **合併**: 2,309 個特徵（去重後）

## 版本管理

- **latest/**: 永遠指向最新版本
- **vX_YYYY-MM-DD/**: 帶時間戳的版本存檔
- **archive/**: 壓縮的舊版本（節省空間）

## 使用說明

1. **查看地圖**: 直接開啟 `latest/buildings_map.html`
2. **數據分析**: 使用 `latest/buildings_table.csv`
3. **GIS 應用**: 使用 `latest/buildings_merged.geojson`
