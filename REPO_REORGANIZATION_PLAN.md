# NQSD Repository Reorganization Plan
## 基於 FAIR 原則的學術研究資料倉儲最佳實踐

**制定日期**: 2026-02-08
**專案性質**: 陽明交大校園建築空間資料（土木、建築、圖資研究）
**目標用戶**: NYCU 學生、研究人員、土木/建築/GIS 領域研究者

---

## 📊 當前狀態分析

### 優勢（保留）
- ✅ 清晰的資料處理流程：raw → processed → output
- ✅ 完整的 Python 處理腳本（34 個）
- ✅ 詳細的技術文件（README.md, VERSION_CONTROL_STRATEGY.md）
- ✅ 多校區資料覆蓋（光復、博愛、陽明、六家、歸仁）
- ✅ 多格式輸出（GeoJSON, CSV, Excel, HTML）
- ✅ 良好的版本控制策略（latest/ + v1_2026-02-07/）

### 問題（需改善）
- ❌ 缺乏學術標準檔案（CITATION.cff, LICENSE, .zenodo.json）
- ❌ 文件過多且分散（7 個 MD 檔案在 data/ 目錄）
- ❌ 垃圾檔案（.claude/, stackdump, 臨時輸出）
- ❌ 未遵循 FAIR 資料原則
- ❌ 缺乏引用資訊和授權說明
- ❌ 未整合 Zenodo 以獲取 DOI

---

## 🎯 整理目標

### 1. 符合 FAIR 原則
- **Findable**: DOI（透過 Zenodo）+ 詳細 metadata
- **Accessible**: GitHub 公開 + 開放格式（GeoJSON, CSV）
- **Interoperable**: 標準地理資料格式 + ISO 19115 metadata
- **Reusable**: 明確授權（CC BY 4.0）+ 完整文件

### 2. 學術倉儲最佳實踐
- 清晰的目錄結構
- 完整的 README 和文件
- 標準引用格式（CITATION.cff）
- 可重現的工作流程
- 範例和教程

### 3. GitHub Release 策略
- 程式碼和文件進入 Git（~100 MB）
- 原始資料進入 GitHub Release（~641 MB）
- Zenodo 自動歸檔並分配 DOI

---

## 📁 新目錄結構

```
NQSD/
├── 📄 README.md                          主要專案說明（整合版）
├── 📄 CITATION.cff                       引用資訊（標準格式）
├── 📄 LICENSE                            授權條款（建議 CC BY 4.0）
├── 📄 .zenodo.json                       Zenodo metadata
├── 📄 .gitignore                         Git 忽略規則
├── 📄 VERSION_CONTROL_STRATEGY.md        版本控制策略（保留）
│
├── 📂 docs/                              文件目錄（整合後）
│   ├── README.md                         文件索引
│   ├── QUICK_START.md                    快速開始指南
│   ├── DATA_DICTIONARY.md                資料欄位說明
│   ├── PROCESSING_PIPELINE.md            處理流程說明
│   ├── NLSC_PROTOCOL.md                  NLSC 協定技術文件
│   ├── API_REFERENCE.md                  API 參考（如適用）
│   │
│   ├── 📂 references/                    參考文獻
│   │   ├── NCTU_thesis_teaching_space_653101.pdf
│   │   └── NLSC_3D_building_model_attributes.pdf
│   │
│   ├── 📂 campus_maps/                   校園地圖（11 個 PDF/JPG）
│   │   ├── guangfu/
│   │   ├── boai/
│   │   ├── yangming/
│   │   ├── liujia/
│   │   └── gueiren/
│   │
│   └── 📂 3d_models/                     3D 模型範例
│       ├── NCTU_Engineering_Building_IV.glb
│       ├── NCTU_Engineering_Building_IV.usdz
│       └── previews/
│
├── 📂 scripts/                           處理腳本（34 個）
│   ├── README.md                         腳本使用說明
│   ├── requirements.txt                  Python 相依套件
│   ├── 01_download_nlsc_tiles.py
│   ├── 02_extract_osm_buildings.py
│   ├── 03_parse_nlsc_tiles.py
│   ├── 04_merge_datasets.py
│   ├── 05_export_building_table.py
│   ├── 06-22_*.py                        其他腳本
│   └── utils/                            輔助工具
│
├── 📂 data/                              資料目錄
│   ├── README.md                         資料說明（簡化版）
│   │
│   ├── 📂 processed/                     處理後資料（9.7 MB）
│   │   ├── README.md
│   │   ├── metadata.json
│   │   ├── buildings/
│   │   │   ├── by_campus/                按校區分類
│   │   │   │   ├── guangfu/
│   │   │   │   ├── boai/
│   │   │   │   ├── yangming/
│   │   │   │   ├── liujia/
│   │   │   │   └── gueiren/
│   │   │   ├── combined/                 合併資料
│   │   │   └── osm/                      OSM 資料
│   │   └── reference/
│   │
│   ├── 📂 output/                        最終輸出（3.2 MB）
│   │   ├── README.md
│   │   ├── latest/                       最新版本
│   │   │   ├── buildings_3d.geojson
│   │   │   ├── buildings_3d.html
│   │   │   ├── buildings_map.html
│   │   │   ├── buildings_merged.geojson
│   │   │   ├── buildings_table.csv
│   │   │   └── buildings_table.xlsx
│   │   └── archive/                      舊版本歸檔
│   │       └── v1_2026-02-07/
│   │
│   └── 📂 floor_plans/                   平面圖（24 MB）
│       ├── README.md
│       ├── metadata.json
│       ├── pdf/
│       │   ├── administrative/
│       │   ├── auditorium/
│       │   ├── buildings/
│       │   └── campus/
│       └── preview/                      PNG 預覽圖
│
├── 📂 examples/                          範例和教程（新增）
│   ├── README.md
│   ├── 01_basic_usage.ipynb              Jupyter Notebook 基礎範例
│   ├── 02_data_analysis.ipynb            資料分析範例
│   ├── 03_visualization.ipynb            視覺化範例
│   └── sample_data/                      範例資料
│
└── 📂 .github/                           GitHub 配置（新增）
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   └── feature_request.md
    ├── workflows/
    │   └── zenodo_release.yml            自動化 Zenodo 歸檔
    └── CONTRIBUTING.md                   貢獻指南
```

---

## 🗑️ 需要刪除的檔案

### 垃圾檔案（立即刪除）
```bash
# 1. Claude Code 工作殘留（140 KB）
data/.claude/

# 2. 崩潰日誌（4 KB）
data/bash.exe.stackdump

# 3. 臨時分析輸出（180 KB）
building_analysis_output.txt
```

### 重複/過時文件（整合後刪除）
```bash
# data/ 目錄下的多個 MD 文件（整合到 docs/ 後刪除）
data/DATA_ORGANIZATION_PLAN.md          → 整合到 docs/PROCESSING_PIPELINE.md
data/EXECUTION_GUIDE.md                 → 整合到 docs/QUICK_START.md
data/ORGANIZATION_COMPLETION_REPORT.md  → 刪除（已完成的報告）
data/SUMMARY.md                         → 整合到 README.md
data/UNIFIED_ORGANIZATION_PLAN.md       → 整合到 docs/PROCESSING_PIPELINE.md

# data/scripts/ 下的整理腳本（非核心功能）
data/scripts/organize_data.py           → 移到 scripts/utils/
data/scripts/validate_organization.py   → 移到 scripts/utils/
data/scripts/backup_data.py             → 移到 scripts/utils/
data/scripts/backup_to_d_drive.py       → 移到 scripts/utils/

# Docker 配置（非必要，可選擇保留或移到 scripts/）
data/docker-compose.yml                 → 移到 scripts/docker/
data/Dockerfile.organizer               → 移到 scripts/docker/
data/run_organize.bat                   → 移到 scripts/docker/
data/run_organize.sh                    → 移到 scripts/docker/
```

---

## 📝 需要新增的檔案

### 1. CITATION.cff（引用資訊）
```yaml
cff-version: 1.2.0
message: "If you use this dataset, please cite it as below."
title: "NYCU Campus Building Spatial Dataset"
authors:
  - family-names: "Your Name"
    given-names: "Your Given Name"
    affiliation: "National Yang Ming Chiao Tung University"
    orcid: "https://orcid.org/0000-0000-0000-0000"
repository-code: "https://github.com/YOUR_USERNAME/NQSD"
type: dataset
keywords:
  - GIS
  - building data
  - 3D models
  - geospatial
  - NLSC
  - OpenStreetMap
  - Taiwan
  - university campus
license: CC-BY-4.0
version: "1.0.0"
date-released: "2026-02-08"
```

### 2. LICENSE（建議 CC BY 4.0）
```
Creative Commons Attribution 4.0 International License

適用於研究資料，允許：
- 分享：複製和重新發布資料
- 改編：重混、轉換和基於資料進行創作
- 商業使用：可用於商業目的

條件：
- 姓名標示：必須給予適當表彰、提供授權條款連結
```

### 3. .zenodo.json（Zenodo metadata）
```json
{
  "title": "NYCU Campus Building Spatial Dataset",
  "description": "A comprehensive geospatial dataset combining NLSC 3D building models and OpenStreetMap data for National Yang Ming Chiao Tung University campuses (Guangfu, Boai, Yangming, Liujia, Gueiren).",
  "creators": [
    {
      "name": "Your Name",
      "affiliation": "National Yang Ming Chiao Tung University",
      "orcid": "0000-0000-0000-0000"
    }
  ],
  "keywords": [
    "GIS",
    "building data",
    "3D models",
    "geospatial",
    "NLSC",
    "OpenStreetMap",
    "Taiwan",
    "university campus",
    "civil engineering",
    "architecture"
  ],
  "license": "CC-BY-4.0",
  "upload_type": "dataset",
  "access_right": "open",
  "related_identifiers": [
    {
      "identifier": "https://github.com/YOUR_USERNAME/NQSD",
      "relation": "isSupplementTo",
      "scheme": "url"
    }
  ]
}
```

### 4. .gitignore
```gitignore
# 大型原始資料（放在 GitHub Release）
data/raw/auxiliary/
data/raw/NLSC_3D_tiles/
data/raw/NLSC_quadtree/
data/raw/archive/

# 保留 metadata
!data/raw/metadata.json
!data/raw/README.md

# ymmap 歷史歸檔（太大，不進 Git）
data/ymmap_archive/

# 垃圾檔案
data/.claude/
*.stackdump
building_analysis_output.txt

# 備份目錄
data/backup/

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
.pytest_cache/
.coverage
htmlcov/

# Jupyter Notebook
.ipynb_checkpoints/
*.ipynb_checkpoints

# OS
.DS_Store
Thumbs.db
desktop.ini
*.swp
*.swo
*~

# IDE
.vscode/
.idea/
*.sublime-*

# Temporary files
*.tmp
*.bak
*.log
```

### 5. examples/01_basic_usage.ipynb（Jupyter Notebook 範例）
```python
# 提供基礎使用範例：
# - 讀取 GeoJSON 資料
# - 過濾特定校區建築
# - 簡單的統計分析
# - 基礎視覺化
```

### 6. docs/QUICK_START.md（整合版快速開始）
整合 data/QUICK_START.md 和 data/EXECUTION_GUIDE.md

### 7. docs/DATA_DICTIONARY.md（資料欄位說明）
詳細說明每個欄位的意義、單位、範例

### 8. .github/workflows/zenodo_release.yml（自動化）
```yaml
name: Archive Release to Zenodo

on:
  release:
    types: [published]

jobs:
  zenodo-archive:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Zenodo webhook
        run: |
          echo "Zenodo will automatically archive this release"
```

---

## 🔄 執行步驟

### Phase 1: 清理垃圾檔案（5 分鐘）

```bash
cd "C:\Users\thc1006\Desktop\NQSD\新增資料夾"

# 刪除垃圾檔案
rm -rf data/.claude/
rm -f data/bash.exe.stackdump
rm -f building_analysis_output.txt

echo "✅ Phase 1 完成：垃圾檔案已清除"
```

### Phase 2: 建立新標準檔案（15 分鐘）

```bash
# 1. 建立 CITATION.cff（需填寫作者資訊）
# 2. 建立 LICENSE（選擇 CC BY 4.0）
# 3. 建立 .zenodo.json（需填寫作者資訊）
# 4. 建立 .gitignore
# 5. 建立 .github/ 目錄和配置檔案

echo "✅ Phase 2 完成：標準檔案已建立"
```

### Phase 3: 重組文件結構（30 分鐘）

```bash
# 1. 建立 docs/ 目錄結構
mkdir -p docs/references docs/campus_maps docs/3d_models/previews

# 2. 移動現有文件
mv docs/* docs/                    # 保留現有 docs/ 內容
# （需手動整合 data/ 下的 MD 文件）

# 3. 重組校園地圖
mkdir -p docs/campus_maps/{guangfu,boai,yangming,liujia,gueiren}
# （按校區分類現有地圖）

echo "✅ Phase 3 完成：文件結構已重組"
```

### Phase 4: 建立範例和教程（45 分鐘）

```bash
# 1. 建立 examples/ 目錄
mkdir -p examples/sample_data

# 2. 撰寫 Jupyter Notebook 範例
# - 01_basic_usage.ipynb
# - 02_data_analysis.ipynb
# - 03_visualization.ipynb

echo "✅ Phase 4 完成：範例已建立"
```

### Phase 5: 整合和測試（30 分鐘）

```bash
# 1. 更新所有 README.md（反映新結構）
# 2. 檢查所有路徑引用（確保正確）
# 3. 測試腳本執行（確保路徑正確）
# 4. 驗證 metadata.json（確保完整）

echo "✅ Phase 5 完成：整合測試完成"
```

### Phase 6: Git 初始化和 GitHub Release（20 分鐘）

```bash
# 1. 初始化 Git
git init
git add .
git commit -m "feat: initial commit - NYCU campus building dataset (FAIR compliant)"

# 2. 連結 GitHub
git remote add origin https://github.com/YOUR_USERNAME/NQSD.git
git branch -M main
git push -u origin main

# 3. 打包原始資料
cd data/raw
zip -r ../../NQSD_raw_osm_data.zip auxiliary/
zip -r ../../NQSD_raw_nlsc_tiles.zip NLSC_3D_tiles/ NLSC_quadtree/

# 4. 建立 GitHub Release（透過 gh CLI）
cd ../..
gh release create v1.0.0 \
  --title "NYCU Campus Building Dataset - 2026-02" \
  --notes "完整原始資料，配合 scripts/ 可重新生成所有成果。\n\n資料涵蓋：光復、博愛、陽明、六家、歸仁五個校區。" \
  NQSD_raw_osm_data.zip \
  NQSD_raw_nlsc_tiles.zip

echo "✅ Phase 6 完成：Git 和 GitHub Release 已完成"
```

### Phase 7: Zenodo 整合（10 分鐘）

```bash
# 1. 前往 Zenodo (https://zenodo.org/)
# 2. 登入並連結 GitHub 帳號
# 3. 啟用 NQSD repository 的自動歸檔
# 4. 建立新 Release 觸發 Zenodo 歸檔
# 5. 獲取 DOI 並更新 README.md 和 CITATION.cff

echo "✅ Phase 7 完成：Zenodo DOI 已獲取"
```

---

## 📊 預期成果

### 檔案大小分佈（整理後）

| 位置 | 大小 | 說明 |
|------|------|------|
| **Git Repository** | ~100 MB | 程式碼、文件、處理後資料 |
| **GitHub Release** | ~641 MB | 原始資料 ZIP 檔案 |
| **Zenodo Archive** | ~741 MB | 完整專案快照 + DOI |

### 刪除的檔案

| 類別 | 大小 | 數量 |
|------|------|------|
| 垃圾檔案 | ~324 KB | 3 個 |
| 重複文件 | ~150 KB | 7 個 MD + 4 個腳本 |
| **總計** | ~474 KB | 14 個 |

### 新增的檔案

| 類別 | 數量 | 說明 |
|------|------|------|
| 學術標準檔案 | 4 個 | CITATION.cff, LICENSE, .zenodo.json, .gitignore |
| 文件（整合版） | 6 個 | 在 docs/ 目錄 |
| 範例 Notebook | 3 個 | 在 examples/ 目錄 |
| GitHub 配置 | 4 個 | 在 .github/ 目錄 |
| **總計** | 17 個 | |

---

## ✅ 完成後檢查清單

### FAIR 原則符合度

- [ ] **Findable**
  - [ ] 已獲得 Zenodo DOI
  - [ ] README 包含完整 metadata
  - [ ] 關鍵字標籤完整

- [ ] **Accessible**
  - [ ] GitHub 公開存取
  - [ ] 資料下載連結清晰
  - [ ] 提供多種格式

- [ ] **Interoperable**
  - [ ] 使用標準格式（GeoJSON, CSV）
  - [ ] 包含 metadata.json
  - [ ] 遵循 ISO 19115

- [ ] **Reusable**
  - [ ] 明確授權（CC BY 4.0）
  - [ ] 完整文件和範例
  - [ ] CITATION.cff 可引用

### 學術倉儲標準

- [ ] 清晰的目錄結構
- [ ] 完整的 README 文件
- [ ] 標準引用格式（CITATION.cff）
- [ ] 範例和教程（Jupyter Notebooks）
- [ ] 貢獻指南（CONTRIBUTING.md）
- [ ] 問題範本（GitHub Issues）

### Git 和 GitHub

- [ ] .gitignore 正確設定
- [ ] 初始 commit 完成
- [ ] GitHub Release 建立
- [ ] Zenodo 整合完成
- [ ] DOI badge 加入 README

---

## 📚 參考資源

### FAIR 原則
- [GO FAIR Principles](https://www.go-fair.org/fair-principles/)
- [Nature Scientific Data - FAIR Guiding Principles](https://www.nature.com/articles/sdata201618)

### Zenodo + GitHub
- [Zenodo GitHub Integration](https://help.zenodo.org/docs/github/)
- [Archive a GitHub Release](https://help.zenodo.org/docs/github/archive-software/github-upload/)

### 研究資料管理
- [Research Data Management Best Practices](https://guides.library.cmu.edu/researchdatamanagement/FAIR_principles)
- [Reproducible Research Guidelines](https://dimewiki.worldbank.org/Reproducible_Research)

### GIS 資料倉儲
- [NYU Spatial Data Repository](https://guides.nyu.edu/gis/data)
- [Harvard GIS Research Guides](https://guides.library.harvard.edu/gsd/GIS/data-US)

---

## 📞 問題與支援

如有任何問題，請：
1. 檢查 docs/QUICK_START.md
2. 查看 GitHub Issues
3. 聯絡專案維護者

---

**制定者**: NQSD Project Team
**最後更新**: 2026-02-08
**版本**: 1.0.0
