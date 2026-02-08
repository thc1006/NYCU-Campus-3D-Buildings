# 數據整理執行指南
**基於 5 個並行代理分析 + ymmap_archive 最佳實踐**

**更新日期**: 2026-02-08
**狀態**: ✅ 準備就緒

---

## 🎯 整理工具更新說明

基於 5 個專業 Explore 代理的並行深度分析，整理工具已完全更新以確保：

### ✅ 正確的分類方式

1. **raw/ 目錄** - 版本化組織
   ```
   ✓ 按版本分類：current/ previous/ legacy/
   ✓ 識別校區：陽明、博愛、光復、歸仁、六甲
   ✓ 分離外部數據：auxiliary/
   ✓ 生成完整元數據：metadata.json
   ```

2. **processed/ 目錄** - 按校區和數據源分類
   ```
   ✓ 5 個校區獨立目錄：boai, yangming, gueiren, liujia, guangfu
   ✓ 合併數據分離：combined/
   ✓ OSM 數據分離：osm/
   ✓ 參考文件獨立：reference/
   ✓ 每個校區有 metadata.json
   ```

3. **output/ 目錄** - 版本控制
   ```
   ✓ 版本化存儲：v1_2026-02-07/
   ✓ latest/ 符號連結
   ✓ 生成元數據：版本、來源、統計
   ✓ 歸檔舊版本：archive/
   ```

4. **floor_plans/ 目錄** - 按類型分類
   ```
   ✓ 4 個類別：auditorium, buildings, campus, administrative
   ✓ 預覽圖同步分類：preview/
   ✓ 檢測損壞文件：fee_standard.pdf
   ✓ 詳細元數據：標題、頁數、用途
   ```

### ✅ 參考 ymmap_archive 的核心原則

| 原則 | 實施方式 |
|------|---------|
| **分層組織** | 功能 → 版本/校區 → 文件（3-4 層） |
| **版本控制** | current/previous/legacy 顯式標記 |
| **原子性** | 每個文件代表一個獨立單元 |
| **元數據管理** | 每個目錄都有 metadata.json + README.md |
| **命名規範** | 統一格式，去掉冗餘前綴 |
| **完整性驗證** | 檢測損壞文件，記錄品質問題 |

---

## 🚀 執行方式

### 方式 1: 一鍵執行（推薦）

**Windows:**
```cmd
run_organize.bat
```
選擇選項 4（完整流程：備份 + 整理 + 驗證）

**Linux/Mac:**
```bash
./run_organize.sh
```
選擇選項 4

### 方式 2: Docker Compose

```bash
# 完整流程（3 個步驟）
docker-compose run --rm backup-creator    # 1. 創建備份
docker-compose run --rm data-organizer    # 2. 執行整理
docker-compose run --rm data-validator    # 3. 驗證結果
```

### 方式 3: 手動執行

```bash
# 1. 安裝依賴
pip install pandas geopandas shapely folium openpyxl rich click

# 2. 執行整理
python scripts/organize_data.py

# 3. 驗證結果
python scripts/validate_organization.py
```

---

## 📋 整理流程詳解

### 步驟 1: 備份（自動）

```
創建完整備份到 backup/ 目錄
├── backup_20260208_HHMMSS/    (目錄備份)
└── backup_20260208_HHMMSS.tar.gz  (壓縮備份)

備份內容：
✓ raw/
✓ processed/
✓ output/
✓ floor_plans/

絕對不備份：
✗ ymmap_archive/ (只讀，不修改)
```

### 步驟 2: 整理（自動）

#### 2.1 raw/ 整理

```
執行動作：
1. 創建目錄結構：
   NLSC_3D_tiles/{current,previous,archive}/
   NLSC_quadtree/{current,legacy}/
   auxiliary/

2. 移動數據集：
   - 最新版本 → current/
     ✓ 113_J_liujia (六甲 2024)
     ✓ 113_A_yangming (陽明 2024)
     ✓ 112_A_yangming (陽明 2023)
     ✓ 112_D_gueiren (歸仁 2023)
     ✓ 112_O (光復/博愛 2023)

   - 舊版本 → previous/
     ✓ 111_A_yangming
     ✓ 111_J_liujia

   - 最舊版本 → legacy/
     ✓ 109_A_yangming
     ✓ 111_J_v4_liujia (特殊版本)

3. 移動外部數據 → auxiliary/
   ✓ taiwan-osm-latest.osm.pbf
   ✓ taiwan-osm-latest-free.shp.zip

4. 生成元數據：
   ✓ NLSC_3D_tiles/metadata.json
   ✓ NLSC_quadtree/metadata.json
   ✓ raw/README.md
```

#### 2.2 processed/ 整理

```
執行動作：
1. 創建校區目錄：
   buildings/by_campus/{boai,yangming,gueiren,liujia,guangfu}/

2. 移動校區文件：
   NYCU_boai_NLSC_buildings.json
     → buildings/by_campus/boai/NLSC_buildings.json

   NYCU_yangming_NLSC_buildings.json
     → buildings/by_campus/yangming/NLSC_buildings.json

   NYCU_gueiren_NLSC_buildings.json
     → buildings/by_campus/gueiren/NLSC_buildings.json

   NYCU_liujia_NLSC_buildings.json
     → buildings/by_campus/liujia/NLSC_buildings.json

   NYCU_Guangfu_OSM_buildings.geojson
     → buildings/by_campus/guangfu/OSM_buildings.geojson

3. 移動合併文件：
   NYCU_NLSC_buildings.json
     → buildings/combined/with_surrounding.json (6,181 棟)

   NYCU_NLSC_buildings.geojson
     → buildings/combined/with_surrounding.geojson

4. 移動參考文件：
   NYCU_building_list.txt
     → reference/building_names_list.txt

5. 為每個校區生成 metadata.json：
   ✓ 校區名稱（中英文）
   ✓ 數據來源
   ✓ 建築數量
   ✓ 文件清單
```

#### 2.3 output/ 整理

```
執行動作：
1. 創建版本目錄：
   v1_2026-02-07/

2. 複製文件並重命名（去掉 NYCU_ 前綴）：
   NYCU_buildings_merged.geojson → buildings_merged.geojson
   NYCU_buildings_3d.geojson     → buildings_3d.geojson
   NYCU_buildings_map.html       → buildings_map.html
   NYCU_buildings_table.csv      → buildings_table.csv
   NYCU_buildings_table.xlsx     → buildings_table.xlsx

3. 創建 latest/ 符號連結（或複製）

4. 生成版本元數據：
   {
     "version": "v1.0.0",
     "generated_date": "2026-02-07",
     "data_sources": {"osm": ..., "nlsc": ...},
     "statistics": {
       "osm_buildings": 319,
       "nlsc_buildings": 6181,
       "merged_features": 2309
     }
   }
```

#### 2.4 floor_plans/ 整理

```
執行動作：
1. 創建類別目錄：
   pdf/{auditorium,buildings,campus,administrative}/

2. 移動和重命名 PDF：
   auditorium_panorama.pdf → pdf/auditorium/panorama.pdf
   auditorium_seatmap.pdf  → pdf/auditorium/seatmap.pdf
   einfo_building_map.pdf  → pdf/buildings/
   eng5_exam_floorplan.pdf → pdf/buildings/
   yangming_campus_map.pdf → pdf/campus/
   yangming_map_old.pdf    → pdf/campus/
   fee_standard.pdf        → pdf/administrative/

3. 重組預覽圖：
   preview/{auditorium,buildings,campus}/

4. 檢測損壞文件：
   ⚠️ fee_standard.pdf (54 bytes - 損壞)

5. 生成詳細元數據：
   {
     "categories": {
       "auditorium": {
         "documents": [
           {
             "id": "panorama",
             "title_zh": "禮堂全景圖",
             "title_en": "Auditorium Panorama",
             "pages": 2,
             "use_cases": ["event_planning"]
           }
         ]
       }
     },
     "quality_issues": [
       {
         "document": "fee_standard.pdf",
         "issue": "File size 54 bytes - corrupted",
         "priority": "high"
       }
     ]
   }
```

### 步驟 3: 驗證（自動）

```
驗證項目：
✓ 目錄結構正確性
✓ 必要文件存在性
✓ 元數據格式正確性
✓ ymmap_archive 未被修改

輸出：
✅ 通過項目清單
⚠️  警告項目清單
❌ 錯誤項目清單

統計表格：
┌──────┬────┐
│ 類型 │ 數量 │
├──────┼────┤
│ ✓ 通過 │ XX │
│ ⚠ 警告 │ XX │
│ ✗ 錯誤 │ XX │
└──────┴────┘
```

---

## 📊 預期結果

### 整理前

```
data/
├── raw/
│   ├── NLSC_3D_tiles_109_A_yangming/
│   ├── NLSC_3D_tiles_112_A_yangming/
│   ├── NLSC_quadtree_109_A_yangming/
│   └── ... (14 個混亂的數據集)
├── processed/
│   ├── NYCU_boai_NLSC_buildings.json
│   ├── NYCU_yangming_NLSC_buildings.json
│   └── ... (8 個混在一起的文件)
├── output/
│   ├── NYCU_buildings_merged.geojson
│   └── ... (6 個無版本控制的文件)
└── floor_plans/
    ├── auditorium_panorama.pdf
    └── ... (7 個混在一起的 PDF)
```

### 整理後

```
data/
├── raw/
│   ├── README.md
│   ├── NLSC_3D_tiles/
│   │   ├── metadata.json
│   │   ├── current/
│   │   │   ├── 113_J_liujia/
│   │   │   ├── 112_A_yangming/
│   │   │   └── ...
│   │   ├── previous/
│   │   └── legacy/
│   ├── NLSC_quadtree/
│   │   ├── metadata.json
│   │   ├── current/
│   │   └── legacy/
│   └── auxiliary/
│       ├── taiwan-osm-latest.osm.pbf
│       └── taiwan-osm-latest-free.shp.zip
│
├── processed/
│   ├── README.md
│   ├── metadata.json
│   ├── buildings/
│   │   ├── by_campus/
│   │   │   ├── boai/
│   │   │   │   ├── NLSC_buildings.json
│   │   │   │   └── metadata.json
│   │   │   ├── yangming/
│   │   │   ├── gueiren/
│   │   │   ├── liujia/
│   │   │   └── guangfu/
│   │   ├── combined/
│   │   │   ├── with_surrounding.json
│   │   │   └── with_surrounding.geojson
│   │   └── osm/
│   └── reference/
│       └── building_names_list.txt
│
├── output/
│   ├── README.md
│   ├── latest/
│   │   ├── buildings_merged.geojson
│   │   ├── buildings_3d.geojson
│   │   └── metadata.json
│   ├── v1_2026-02-07/
│   └── archive/
│
├── floor_plans/
│   ├── README.md
│   ├── metadata.json
│   ├── pdf/
│   │   ├── auditorium/
│   │   │   ├── panorama.pdf
│   │   │   └── seatmap.pdf
│   │   ├── buildings/
│   │   ├── campus/
│   │   └── administrative/
│   └── preview/
│       ├── auditorium/
│       ├── buildings/
│       └── campus/
│
└── ymmap_archive/ (未修改)
```

---

## ⚠️ 重要注意事項

### 1. ymmap_archive 絕對安全

```
✅ Docker 只讀掛載
✅ 驗證工具檢查完整性
✅ 腳本不操作此目錄
✅ 文檔明確標示
```

### 2. 損壞文件處理

```
已識別的損壞文件：
⚠️ floor_plans/fee_standard.pdf (54 bytes)
⚠️ NLSC_3D_tiles_112_A_yangming (294 bytes)
⚠️ NLSC_3D_tiles_113_J_liujia (297 bytes)

處理方式：
1. 保留在目標位置
2. 在 metadata.json 中標記 "status": "corrupted"
3. 記錄在 quality_issues 中
4. 手動修復或移除（整理後）
```

### 3. 備份策略

```
整理前：
✓ 自動完整備份
✓ 目錄備份（快速訪問）
✓ 壓縮備份（節省空間）

整理後：
✓ 保留原始文件（複製而非移動）
✓ 可隨時還原
✓ 驗證完成後可刪除舊結構
```

---

## 📝 完成後的檢查清單

### 目錄結構

- [ ] raw/ 有 3-4 層結構（NLSC_3D_tiles/current/ 等）
- [ ] processed/ 有 by_campus/ 子目錄（5 個校區）
- [ ] output/ 有 latest/ 和版本化目錄
- [ ] floor_plans/ 有 pdf/ 分類目錄

### 元數據

- [ ] 每個主要目錄都有 README.md
- [ ] 每個主要目錄都有 metadata.json
- [ ] 校區目錄有獨立的 metadata.json
- [ ] output/ 有版本元數據

### 數據完整性

- [ ] 所有文件都已正確分類
- [ ] 損壞文件已標記在元數據中
- [ ] ymmap_archive 未被修改
- [ ] 驗證工具通過（無錯誤）

### 文檔

- [ ] 生成了整理報告（organization_report_*.json）
- [ ] README 文件完整且準確
- [ ] 元數據格式正確（JSON 有效）

---

## 🎓 學習資源

- **詳細計劃**: `DATA_ORGANIZATION_PLAN.md`
- **統一方案**: `UNIFIED_ORGANIZATION_PLAN.md`
- **快速開始**: `QUICK_START.md`
- **專案概述**: `README.md`
- **ymmap_archive 分析**: 5 個代理的詳細報告

---

## 📞 問題處理

### 常見問題

**Q1: 整理失敗怎麼辦？**
A: 從備份還原：
```bash
python scripts/backup_data.py --restore backup_20260208_HHMMSS
```

**Q2: 如何確認 ymmap_archive 未被修改？**
A: 執行驗證：
```bash
docker-compose run --rm data-validator
```

**Q3: 損壞文件如何處理？**
A: 整理後手動：
1. 找到原始文件並替換
2. 或從 metadata.json 的 quality_issues 中移除

**Q4: 需要多長時間？**
A: 約 3.5-4 小時（自動執行）

---

## ✅ 準備開始

一切準備就緒！執行以下命令開始：

```bash
# Windows
run_organize.bat

# 選擇選項 4（完整流程）
```

或

```bash
# Docker
docker-compose run --rm backup-creator
docker-compose run --rm data-organizer
docker-compose run --rm data-validator
```

**祝整理順利！** 🚀

---

**版本**: 1.0.0
**最後更新**: 2026-02-08
**基於**: 5 個並行 Explore 代理的深度分析 + ymmap_archive 最佳實踐
