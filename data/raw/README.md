# Raw Data - 原始數據

此目錄包含從 NLSC（國土測繪中心）下載的原始 3D Tiles 和 Quadtree 數據。

## 整理日期

2026-02-08 - 已按版本和類型重組

## 目錄結構

```
raw/
├── NLSC_3D_tiles/              # 3D Tiles 數據集
│   ├── current/                # 最新版本 (113_*, 112_*)
│   │   ├── 113_J_liujia/
│   │   ├── 112_A_yangming/
│   │   ├── 112_D_gueiren/
│   │   ├── 112_O_guangfu/
│   │   └── 112_O_boai/
│   ├── previous/               # 前一版本 (111_*)
│   └── legacy/                 # 舊版本 (109_*)
│       └── 109_A_yangming/
│
├── NLSC_quadtree/              # Quadtree 數據集
│   ├── current/                # 最新版本
│   │   ├── 113_A_yangming/
│   │   ├── 113_J_liujia/
│   │   ├── 112_A_yangming/
│   │   ├── 112_D_gueiren/
│   │   └── 112_O_boai/
│   └── legacy/                 # 舊版本
│       ├── 111_A_yangming/
│       ├── 111_J_v4_liujia/
│       └── 109_A_yangming/
│
└── auxiliary/                  # 外部數據
    ├── taiwan-osm-latest.osm.pbf
    └── taiwan-osm-latest-free.shp.zip
```

## 數據來源

- **來源**: 國土測繪中心 (NLSC)
- **格式**: 3D Tiles (.bin), Quadtree
- **坐標系統**: TWD97 (EPSG:3826)

## 版本說明

- **current/**: 最新版本，建議使用
- **previous/**: 前一版本，備用
- **legacy/**: 舊版本，保留作為歷史參考

## 校區對應

- 陽明: 109_A, 112_A, 113_A
- 六甲: 113_J, 111_J_v4
- 歸仁: 112_D
- 光復/博愛: 112_O

## 使用說明

1. 建議使用 current/ 下的最新數據
2. 每個數據集包含多個層級（L5, L6 等）
3. manifest.json 記錄了 tiles 的索引資訊
4. 處理後的數據請查看 `../processed/` 目錄
