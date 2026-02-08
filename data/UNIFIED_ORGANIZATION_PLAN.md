# 統一數據整理方案
**基於 5 個並行代理的深度分析**

**建立日期**: 2026-02-08
**分析範圍**: raw/, processed/, output/, floor_plans/, ymmap_archive/
**總數據量**: ~4.06 GB

---

## 📊 執行摘要

經過 5 個專業代理的並行深度分析，我們識別了以下關鍵問題：

1. **raw/**: 版本碎片化（陽明校區 4 個版本）、命名不一致
2. **processed/**: 數據冗餘、缺乏分類
3. **output/**: 無版本控制、無元數據
4. **floor_plans/**: 1 個損壞文件、缺乏分類
5. **ymmap_archive/**: 已完美組織，作為參考標準 ✅

---

## 🎯 整理目標

### 短期目標（1-2 週）
- [ ] 修復損壞文件（fee_standard.pdf）
- [ ] 驗證極小型數據集（112_A, 113_J）
- [ ] 建立基本的目錄分類
- [ ] 為 output/ 建立版本控制

### 中期目標（3-4 週）
- [ ] 完成所有目錄的重組
- [ ] 生成所有元數據文件
- [ ] 建立完整的索引系統
- [ ] 壓縮舊版本數據

### 長期目標（2-3 個月）
- [ ] 建立自動化更新機制
- [ ] 實施持續監控
- [ ] 文檔完善和培訓

---

## 📁 統一目錄結構

```
data/
│
├── 📄 README.md                      # 主文檔（已存在）
├── 📄 DATA_ORGANIZATION_PLAN.md      # 詳細計劃（已存在）
├── 📄 UNIFIED_ORGANIZATION_PLAN.md   # 本文件
├── 📄 QUICK_START.md                 # 快速開始（已存在）
│
├── 📂 raw/                           # 原始數據 (641 MB)
│   ├── README.md                     # ✅ 新增
│   ├── NLSC_3D_tiles/
│   │   ├── metadata.json             # ✅ 新增
│   │   ├── current/                  # ✅ 重組
│   │   │   ├── 113_J_liujia/
│   │   │   ├── 112_A_yangming/
│   │   │   ├── 112_D_gueiren/
│   │   │   └── 112_O_guangfu/
│   │   ├── previous/
│   │   │   ├── 112_A_yangming/
│   │   │   ├── 111_A_yangming/
│   │   │   └── 109_A_yangming/
│   │   └── archive/                  # ✅ 壓縮舊版本
│   │       └── 109_A_yangming.tar.gz
│   │
│   ├── NLSC_quadtree/
│   │   ├── metadata.json             # ✅ 新增
│   │   ├── current/
│   │   │   ├── 113_A_yangming/
│   │   │   ├── 113_J_liujia/
│   │   │   ├── 112_A_yangming/
│   │   │   ├── 112_D_gueiren/
│   │   │   └── 112_O_boai/
│   │   └── legacy/
│   │       └── 111_J_v4_liujia/
│   │
│   └── auxiliary/                    # ✅ 新增
│       ├── taiwan-osm-latest.osm.pbf
│       └── taiwan-osm-latest-free.shp.zip
│
├── 📂 processed/                     # 處理數據 (9.7 MB)
│   ├── README.md                     # ✅ 新增
│   ├── metadata.json                 # ✅ 新增
│   ├── buildings/
│   │   ├── by_campus/                # ✅ 重組
│   │   │   ├── boai/
│   │   │   │   ├── NLSC_buildings.json
│   │   │   │   ├── NLSC_buildings.geojson
│   │   │   │   └── metadata.json     # ✅ 新增
│   │   │   ├── yangming/
│   │   │   ├── liujia/
│   │   │   ├── gueiren/
│   │   │   └── guangfu/
│   │   │       ├── OSM_buildings.geojson
│   │   │       ├── building_names.txt
│   │   │       └── metadata.json
│   │   │
│   │   ├── combined/                 # ✅ 重組
│   │   │   ├── all_campuses.json
│   │   │   ├── all_campuses.geojson
│   │   │   ├── with_surrounding.json
│   │   │   └── with_surrounding.geojson
│   │   │
│   │   └── osm/
│   │       ├── Guangfu_OSM_buildings.geojson
│   │       └── README.md
│   │
│   └── reference/                    # ✅ 新增
│       ├── building_list.txt
│       └── data_changelog.md
│
├── 📂 output/                        # 最終輸出 (1.6 MB)
│   ├── README.md                     # ✅ 新增
│   ├── latest/                       # ✅ 新增（符號連結）
│   │   ├── buildings_3d.geojson
│   │   ├── buildings_3d.html
│   │   ├── buildings_map.html
│   │   ├── buildings_merged.geojson
│   │   ├── buildings_table.csv
│   │   ├── buildings_table.xlsx
│   │   └── metadata.json             # ✅ 新增
│   │
│   ├── v1_2026-02-07/                # ✅ 新增（版本化）
│   │   ├── [same files as latest]
│   │   └── metadata.json
│   │
│   └── archive/                      # ✅ 新增
│       └── v0_2026-01-15.tar.gz
│
├── 📂 floor_plans/                   # 平面圖 (13 MB)
│   ├── README.md                     # ✅ 新增
│   ├── metadata.json                 # ✅ 新增
│   ├── pdf/                          # ✅ 重組
│   │   ├── auditorium/
│   │   │   ├── panorama.pdf
│   │   │   └── seatmap.pdf
│   │   ├── buildings/
│   │   │   ├── einfo_building_map.pdf
│   │   │   └── eng5_exam_floorplan.pdf
│   │   ├── campus/
│   │   │   ├── yangming_campus_map.pdf
│   │   │   └── yangming_map_old.pdf
│   │   └── administrative/
│   │       └── fee_standard.pdf      # ⚠️ 需修復
│   │
│   └── preview/                      # 保持現有結構
│       ├── auditorium/
│       ├── buildings/
│       └── campus/
│
├── 📂 ymmap_archive/                 # 歷史歸檔 (3.4 GB) 🔒
│   └── [不可修改，僅供參考]
│
├── 📂 backup/                        # 備份
│   ├── backup_20260208_HHMMSS/
│   └── backup_20260208_HHMMSS.tar.gz
│
└── 📂 scripts/                       # 工具腳本
    ├── organize_data.py
    ├── validate_organization.py
    └── backup_data.py
```

---

## 🔧 詳細整理步驟

### 階段 0: 準備工作（30 分鐘）

```bash
# 1. 創建完整備份
docker-compose run --rm backup-creator

# 2. 驗證損壞文件
ls -lh floor_plans/fee_standard.pdf
# 如果損壞，標記為待修復

# 3. 驗證極小型數據集
ls -lh raw/NLSC_3D_tiles_112_A_yangming/
ls -lh raw/NLSC_3D_tiles_113_J_liujia/
# 如果僅有 manifest.json，標記為待補充
```

### 階段 1: raw/ 整理（1 小時）

**參考 ymmap_archive 的版本控制模式**

```bash
# 1. 創建新目錄結構
mkdir -p raw/NLSC_3D_tiles/{current,previous,archive}
mkdir -p raw/NLSC_quadtree/{current,legacy}
mkdir -p raw/auxiliary

# 2. 移動 3D Tiles（最新版本 → current/）
mv raw/NLSC_3D_tiles_113_J_liujia raw/NLSC_3D_tiles/current/113_J_liujia
mv raw/NLSC_3D_tiles_112_A_yangming raw/NLSC_3D_tiles/current/112_A_yangming
mv raw/NLSC_3D_tiles_112_D_gueiren raw/NLSC_3D_tiles/current/112_D_gueiren
mv raw/NLSC_3D_tiles_112_O raw/NLSC_3D_tiles/current/112_O_guangfu

# 3. 移動舊版本 → previous/
mv raw/NLSC_3D_tiles_109_A_yangming raw/NLSC_3D_tiles/previous/109_A_yangming

# 4. 移動 Quadtree
mv raw/NLSC_quadtree_113_* raw/NLSC_quadtree/current/
mv raw/NLSC_quadtree_112_* raw/NLSC_quadtree/current/
mv raw/NLSC_quadtree_111_J_v4_liujia raw/NLSC_quadtree/legacy/

# 5. 移動外部數據
mv raw/taiwan-osm-*.* raw/auxiliary/

# 6. 生成元數據
python scripts/generate_raw_metadata.py
```

**生成 raw/NLSC_3D_tiles/metadata.json:**
```json
{
  "description": "NLSC 3D Building Tiles Data",
  "source": "National Land Surveying and Mapping Center",
  "coordinate_system": "TWD97 (EPSG:3826)",
  "current_versions": {
    "yangming": "112_A",
    "liujia": "113_J",
    "gueiren": "112_D",
    "guangfu": "112_O"
  },
  "version_history": {
    "yangming": ["109_A", "112_A"],
    "liujia": ["113_J"],
    "gueiren": ["112_D"],
    "guangfu": ["112_O"]
  },
  "last_updated": "2026-02-08",
  "total_size_mb": 103.52,
  "total_files": 643
}
```

### 階段 2: processed/ 整理（45 分鐘）

**參考 ymmap_archive 的分層組織**

```bash
# 1. 創建新目錄結構
mkdir -p processed/buildings/{by_campus/{boai,yangming,liujia,gueiren,guangfu},combined,osm}
mkdir -p processed/reference

# 2. 移動校區文件
mv processed/NYCU_boai_NLSC_buildings.json \
   processed/buildings/by_campus/boai/NLSC_buildings.json
mv processed/NYCU_yangming_NLSC_buildings.json \
   processed/buildings/by_campus/yangming/NLSC_buildings.json
# ... 類推其他校區

# 3. 移動合併文件
mv processed/NYCU_NLSC_buildings.json \
   processed/buildings/combined/with_surrounding.json
mv processed/NYCU_NLSC_buildings.geojson \
   processed/buildings/combined/with_surrounding.geojson

# 4. 移動 OSM 文件
mv processed/NYCU_Guangfu_OSM_buildings.geojson \
   processed/buildings/osm/Guangfu_OSM_buildings.geojson

# 5. 移動參考文件
mv processed/NYCU_building_list.txt \
   processed/reference/building_list.txt

# 6. 為每個校區生成 metadata.json
python scripts/generate_processed_metadata.py
```

### 階段 3: output/ 整理（30 分鐘）

**參考 ymmap_archive 的版本控制**

```bash
# 1. 創建版本化目錄
mkdir -p output/{latest,archive}
mkdir -p output/v1_2026-02-07

# 2. 複製文件到版本目錄
cp output/NYCU_buildings_*.* output/v1_2026-02-07/

# 3. 重命名（去掉 NYCU_ 前綴）
cd output/v1_2026-02-07
rename 's/NYCU_//' *

# 4. 創建 latest/ 符號連結（或複製）
cp -r output/v1_2026-02-07/* output/latest/

# 5. 生成版本元數據
python scripts/generate_output_metadata.py
```

**生成 output/latest/metadata.json:**
```json
{
  "version": "v1.0.0",
  "generated_date": "2026-02-07",
  "generated_timestamp": "2026-02-07T06:13:24+08:00",
  "data_sources": {
    "osm": "OpenStreetMap taiwan-osm-latest.osm.pbf",
    "nlsc": "NLSC 3D Maps Layer 112_O (2023)"
  },
  "statistics": {
    "osm_buildings": 319,
    "nlsc_buildings": 6181,
    "merged_features": 2309,
    "matching_rate": "83.7%"
  },
  "files": {
    "buildings_merged.geojson": {
      "size_mb": 1.24,
      "purpose": "Primary merged dataset",
      "features": 2309
    },
    "buildings_3d.geojson": {
      "size_mb": 0.23,
      "purpose": "3D variant/filtered subset"
    }
  }
}
```

### 階段 4: floor_plans/ 整理（30 分鐘）

**參考 ymmap_archive 的分類系統**

```bash
# 1. 創建分類目錄
mkdir -p floor_plans/pdf/{auditorium,buildings,campus,administrative}

# 2. 移動 PDF 文件
mv floor_plans/auditorium_panorama.pdf floor_plans/pdf/auditorium/panorama.pdf
mv floor_plans/auditorium_seatmap.pdf floor_plans/pdf/auditorium/seatmap.pdf
mv floor_plans/einfo_building_map.pdf floor_plans/pdf/buildings/
mv floor_plans/eng5_exam_floorplan.pdf floor_plans/pdf/buildings/
mv floor_plans/yangming_campus_map.pdf floor_plans/pdf/campus/
mv floor_plans/yangming_map_old.pdf floor_plans/pdf/campus/
mv floor_plans/fee_standard.pdf floor_plans/pdf/administrative/

# 3. 重組 preview/ 目錄
mkdir -p floor_plans/preview/{auditorium,buildings,campus}
mv floor_plans/preview/auditorium_* floor_plans/preview/auditorium/
mv floor_plans/preview/einfo_* floor_plans/preview/buildings/
mv floor_plans/preview/eng5_* floor_plans/preview/buildings/
mv floor_plans/preview/yangming_* floor_plans/preview/campus/

# 4. 生成元數據
python scripts/generate_floorplans_metadata.py
```

**生成 floor_plans/metadata.json:**
```json
{
  "organized_date": "2026-02-08",
  "categories": {
    "auditorium": {
      "label_zh": "禮堂",
      "label_en": "Auditorium",
      "files": ["panorama.pdf", "seatmap.pdf"],
      "preview_count": 4
    },
    "buildings": {
      "label_zh": "建築物",
      "label_en": "Buildings",
      "files": ["einfo_building_map.pdf", "eng5_exam_floorplan.pdf"],
      "preview_count": 3
    },
    "campus": {
      "label_zh": "校園地圖",
      "label_en": "Campus Maps",
      "files": ["yangming_campus_map.pdf", "yangming_map_old.pdf"],
      "preview_count": 3
    },
    "administrative": {
      "label_zh": "行政文件",
      "label_en": "Administrative",
      "files": ["fee_standard.pdf"],
      "status": "corrupted",
      "preview_count": 0
    }
  },
  "quality_issues": [
    {
      "file": "fee_standard.pdf",
      "issue": "File size 54 bytes - likely corrupted",
      "action_required": "Replace or remove",
      "priority": "high"
    }
  ]
}
```

### 階段 5: 文檔和驗證（30 分鐘）

```bash
# 1. 創建所有 README.md
python scripts/generate_all_readmes.py

# 2. 驗證整理結果
docker-compose run --rm data-validator

# 3. 生成整理報告
python scripts/generate_organization_report.py

# 4. 確認 ymmap_archive 未被修改
python scripts/verify_ymmap_integrity.py
```

---

## 📋 優先問題修復清單

### P0 - 緊急（本週完成）

- [ ] **修復 fee_standard.pdf**（54 bytes，損壞）
  - 選項 1: 找到原始文件並替換
  - 選項 2: 如果無法恢復，移除並在元數據中記錄

- [ ] **驗證極小型數據集**
  - `NLSC_3D_tiles_112_A_yangming`（294 bytes）
  - `NLSC_3D_tiles_113_J_liujia`（297 bytes）
  - 檢查是否為損壞下載或佔位符

### P1 - 高優先級（2 週內）

- [ ] **標記當前版本**
  - 為每個校區標記最新版本（current/）
  - 移動舊版本到 previous/ 或 legacy/

- [ ] **建立版本控制**
  - output/ 目錄版本化
  - 創建 latest/ 符號連結

- [ ] **基本元數據**
  - 為所有主要目錄創建 metadata.json
  - 生成 README.md

### P2 - 中優先級（3-4 週）

- [ ] **目錄重組**
  - raw/ 按版本和類型重組
  - processed/ 按校區和數據源重組
  - floor_plans/ 按類型分類

- [ ] **索引和映射**
  - 創建建築-文件映射表
  - 生成校區-數據集對應表

### P3 - 低優先級（1-2 個月）

- [ ] **壓縮歸檔**
  - 壓縮舊版本數據
  - 清理臨時文件

- [ ] **高級文檔**
  - 創建 DATA_DICTIONARY.md
  - 編寫使用範例

---

## 🎓 參考標準：ymmap_archive 最佳實踐

基於對 ymmap_archive（10,588 文件，3.29 GB）的深度分析，以下是核心原則：

### 1. 分層組織原則

```
功能分類 (L1)
  ↓
版本迭代 (L2)
  ↓
具體資源 (L3)

示例：
wfs_data/                    ← L1: 數據源類型
├── room_csv/                ← L2: 資料格式
    └── B005_1F.csv          ← L3: 建築 × 樓層（原子單位）
```

### 2. 版本命名規範

```
顯式版本標記：
├── deep_probe/              ← v1（初始）
├── deep_probe_v2/           ← v2（擴展）
└── route_data/
    ├── v2/
    ├── v3/
    ├── v4/
    ├── v5/
    └── v6_final/            ← 最終版本
```

### 3. 元數據標準

```
每個目錄應包含：
├── README.md                # 人類可讀
├── metadata.json            # 機器可讀
├── STATISTICS.json          # 統計資訊
└── INDEX.csv               # 文件索引（如適用）

頂層檔案應包含：
├── dublin_core.json         # Dublin Core 15 元素
├── iso19115_metadata.json   # ISO 19115（地理數據）
├── PROVENANCE.md            # W3C PROV-DM 數據血緣
└── manifest-sha256.txt      # 完整性驗證
```

### 4. 命名慣例

```
建築相關：
{BuildID}_{Resource}.{ext}
  例: B005_1F.csv, P003_38693.jpg

API 響應：
{controller}_{action}_{param}.json
  例: buildinfo_getFloorList_buildId_B005.json

階段性結果：
phase{N}_{description}.json
  例: phase2_results.json, phase8_gis_results.json

備份版本：
bak_{name}_v{N}
  例: bak_gis_building_geom_v1
```

### 5. 原子性原則

```
❌ 錯誤：一個文件包含整棟建築所有樓層
building_B005_all_floors.csv

✅ 正確：每個檔案 = 建築 × 樓層
B005_1F.csv
B005_2F.csv
B005_3F.csv
...

優點：
- 便於增量更新
- 降低文件大小
- 提高可維護性
```

---

## 📊 預期成果

### 整理前 vs 整理後

| 指標 | 整理前 | 整理後 | 改善 |
|------|--------|--------|------|
| **目錄層次** | 1-2 層 | 3-4 層 | +50% 組織性 |
| **版本控制** | 無 | 完整版本化 | ✅ |
| **元數據** | 0 個 | 15+ 個 JSON | ✅ |
| **README** | 1 個 | 10+ 個 | ✅ |
| **命名一致性** | 60% | 95% | +35% |
| **可發現性** | 低 | 高（多層索引）| ✅ |
| **完整性驗證** | 無 | SHA-256 | ✅ |

### 整理後的優勢

1. **易於導航**
   - 清晰的 3-4 層目錄結構
   - 每個目錄都有 README.md
   - 一致的命名規範

2. **版本追溯**
   - 當前版本明確標記
   - 歷史版本保留
   - 元數據記錄生成參數

3. **數據完整性**
   - SHA-256 完整性驗證
   - 備份和還原機制
   - 損壞文件識別

4. **協作友好**
   - 新成員快速上手
   - 數據來源清晰
   - 處理流程可複現

5. **符合標準**
   - Dublin Core 元數據
   - ISO 19115（地理數據）
   - W3C PROV-DM 數據血緣

---

## ⏱️ 時間估算

| 階段 | 時間 | 人力 |
|------|------|------|
| 階段 0: 準備工作 | 30 分鐘 | 1 人 |
| 階段 1: raw/ 整理 | 1 小時 | 1 人 |
| 階段 2: processed/ 整理 | 45 分鐘 | 1 人 |
| 階段 3: output/ 整理 | 30 分鐘 | 1 人 |
| 階段 4: floor_plans/ 整理 | 30 分鐘 | 1 人 |
| 階段 5: 文檔和驗證 | 30 分鐘 | 1 人 |
| **總計** | **3.5-4 小時** | **1 人** |

**建議執行時間**: 週末或非工作時間（避免中斷）

---

## 🚀 立即開始

### 選項 1: 使用自動化腳本（推薦）

```bash
# Windows
run_organize.bat

# 選擇選項 4（完整流程）
```

### 選項 2: 使用 Docker Compose

```bash
# 完整流程
docker-compose run --rm backup-creator    # 1. 備份
docker-compose run --rm data-organizer    # 2. 整理
docker-compose run --rm data-validator    # 3. 驗證
```

### 選項 3: 手動執行

```bash
# 依次執行各階段
python scripts/backup_data.py
python scripts/organize_data.py
python scripts/validate_organization.py
```

---

## 📞 問題回報

如遇到問題，請檢查：
1. `organization_report_*.json` - 整理報告
2. Docker 容器日誌
3. 驗證工具的詳細輸出
4. 各目錄的 README.md

---

**建立者**: NQSD Project Team
**版本**: 1.0.0
**最後更新**: 2026-02-08
**基於**: 5 個並行 Explore 代理的深度分析
