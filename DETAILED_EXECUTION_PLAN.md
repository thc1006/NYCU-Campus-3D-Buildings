# NQSD Repository 完整重組執行計劃
## 基於 FAIR 原則的深度規劃

**制定日期**: 2026-02-08
**執行模式**: Phase 3-7 完整重組
**預估時間**: 約 2.5-3 小時（不含 Zenodo 手動操作）

---

## 🚨 關鍵議題：授權相容性

### 問題分析

根據調研 ([OpenStreetMap License Compatibility](https://osmfoundation.org/wiki/Licence/Licence_Compatibility), [CC BY 4.0 + ODbL Issues](https://blog.openstreetmap.org/2017/03/17/use-of-cc-by-data/))：

**ODbL (OpenStreetMap) 和 CC BY 4.0 有相容性問題**：

| 授權 | 適用範圍 | 限制 |
|------|----------|------|
| **ODbL** | 僅資料庫結構 | 不涵蓋個別內容 |
| **CC BY 4.0** | 資料庫結構 + 所有內容 | 包含鄰接權 |

**不相容點**：
1. 需要明確豁免 "Technological Effective Measures"（CC BY 4.0 Section 2a5B）
2. 歸屬（Attribution）要求不同
3. 衍生作品的授權傳播機制不同

### 解決方案：混合授權策略

**採用分層授權 + 明確歸屬**：

```
NQSD Dataset
├── 原始資料來源（不同授權）
│   ├── NLSC 3D Building Data → Open Government Data License (Taiwan)
│   ├── OpenStreetMap Data → ODbL 1.0
│   └── NYCU Campus Data → Fair Use (Educational)
│
└── 衍生資料集（本專案貢獻）
    ├── 處理腳本 → MIT License
    ├── 合併資料集 → CC BY 4.0（附加 ODbL 歸屬）
    └── 文件和範例 → CC BY 4.0
```

**具體做法**：
1. LICENSE 檔案改為**混合授權說明**
2. CITATION.cff 明確標註每個來源
3. .zenodo.json 在 notes 中說明授權複雜性
4. README.md 建立專門的「資料來源與授權」章節

---

## 📊 當前狀態分析

### 檔案分佈

| 目錄 | 檔案數 | 大小 | 狀態 |
|------|--------|------|------|
| `scripts/` | 34 個 .py | 544 KB | ✅ 良好 |
| `data/processed/` | 8 個 | 9.7 MB | 🟡 需分類 |
| `data/output/` | ~10 個 | 3.2 MB | ✅ 已版本化 |
| `data/floor_plans/` | ~30 個 | 24 MB | 🟡 需分類 |
| `docs/campus_maps/` | 12 個 | 61 MB | 🟡 需重組 |
| `docs/references/` | 2 個 | ~5 MB | ✅ 良好 |
| `data/*.md` | 11 個 | ~150 KB | 🔴 需整合 |

### 需要整合的 MD 文件（11 個）

| 檔案 | 大小 | 整合目標 | 動作 |
|------|------|----------|------|
| `data/DATA_ORGANIZATION_PLAN.md` | ~30 KB | `docs/PROCESSING_PIPELINE.md` | 整合 |
| `data/EXECUTION_GUIDE.md` | ~20 KB | `docs/QUICK_START.md` | 整合 |
| `data/SUMMARY.md` | ~15 KB | `README.md` | 整合部分內容 |
| `data/UNIFIED_ORGANIZATION_PLAN.md` | ~25 KB | `docs/PROCESSING_PIPELINE.md` | 整合 |
| `data/QUICK_START.md` | ~10 KB | `docs/QUICK_START.md` | 整合 |
| `data/ORGANIZATION_COMPLETION_REPORT.md` | ~5 KB | - | 刪除（已完成） |
| `data/README.md` | ~10 KB | 保留簡化版 | 重寫 |
| `data/raw/README.md` | ~5 KB | 保留 | 更新 |
| `data/processed/README.md` | ~5 KB | 保留 | 更新 |
| `data/output/README.md` | ~5 KB | 保留 | 更新 |
| `data/floor_plans/README.md` | ~5 KB | 保留 | 更新 |

---

## 🎯 完整執行計劃（Phase 3-7）

### Phase 3: 重組文件結構（預估 30-40 分鐘）

#### 3.1 建立 docs/ 目錄結構
```bash
docs/
├── README.md                         # 文件索引
├── QUICK_START.md                    # 整合版快速開始
├── DATA_DICTIONARY.md                # 資料欄位說明（新建）
├── PROCESSING_PIPELINE.md            # 處理流程（整合）
├── NLSC_PROTOCOL.md                  # NLSC 協定技術文件（新建）
├── DATA_SOURCES_AND_LICENSES.md      # 資料來源與授權（新建）
│
├── references/                       # 參考文獻
│   ├── NCTU_thesis_teaching_space_653101.pdf
│   └── NLSC_3D_building_model_attributes.pdf
│
├── campus_maps/                      # 校園地圖（重組）
│   ├── README.md
│   ├── guangfu/
│   │   ├── NYCU_Guangfu_campus_map.pdf
│   │   └── NYCU_Guangfu_campus_map.jpg
│   ├── boai/
│   │   ├── NYCU_Boai_campus_map.pdf
│   │   └── NYCU_Boai_campus_map.jpg
│   ├── yangming/
│   │   ├── NYCU_Yangming_campus_map.pdf
│   │   ├── NYCU_Yangming_campus_map.jpg
│   │   └── NYCU_Yangming_campus_map_IPU.pdf
│   ├── liujia/
│   │   └── NYCU_Liujia_campus_map.pdf
│   ├── gueiren/
│   │   └── NYCU_Gueiren_campus_map.jpg
│   └── general/
│       ├── NYCU_GA_document.pdf
│       ├── NYCU_GA_facilities_map.pdf
│       └── NYCU_CS_dept_campus_map.pdf
│
└── 3d_models/                        # 3D 模型範例
    ├── README.md
    ├── NCTU_Engineering_Building_IV.glb
    ├── NCTU_Engineering_Building_IV.usdz
    └── previews/
        ├── NCTU_Eng4_preview_front.webp
        ├── NCTU_Eng4_preview_large.webp
        ├── NCTU_Eng4_preview_side.webp
        └── NCTU_Eng4_preview_top.jpg
```

#### 3.2 文件整合內容規劃

**docs/QUICK_START.md**（整合 3 個來源）：
- data/QUICK_START.md（基礎內容）
- data/EXECUTION_GUIDE.md（執行指南）
- 新增：環境設定、依賴安裝

**docs/PROCESSING_PIPELINE.md**（整合 2 個來源）：
- data/DATA_ORGANIZATION_PLAN.md（處理計劃）
- data/UNIFIED_ORGANIZATION_PLAN.md（統一計劃）
- 新增：資料流程圖、技術細節

**docs/DATA_SOURCES_AND_LICENSES.md**（新建，最重要）：
- NLSC 資料來源和授權
- OpenStreetMap 資料和 ODbL 說明
- NYCU 官方資料使用說明
- 混合資料集授權策略
- 如何正確引用

**docs/NLSC_PROTOCOL.md**（從 README.md 提取）：
- PilotGaea oview 協定技術文件
- 二進位格式說明
- API 端點文件

**docs/DATA_DICTIONARY.md**（新建）：
- 所有 20 個 NLSC 欄位說明
- OSM 欄位說明
- 合併資料集欄位說明

---

### Phase 4: 建立範例和教程（預估 40-50 分鐘）

#### 4.1 目錄結構
```bash
examples/
├── README.md                         # 範例索引和說明
├── requirements.txt                  # 範例所需套件
│
├── 01_basic_usage.ipynb              # 基礎使用
├── 02_data_analysis.ipynb            # 資料分析
├── 03_visualization.ipynb            # 視覺化
│
├── sample_data/                      # 範例資料（精簡版）
│   ├── sample_buildings.geojson      # 100 棟建築範例
│   └── sample_buildings.csv          # CSV 格式
│
└── outputs/                          # 範例輸出（gitignore）
    ├── analysis_results.csv
    └── map_visualization.html
```

#### 4.2 Notebook 內容規劃

**01_basic_usage.ipynb**（基礎使用）：
```python
# 1. 環境設定
# 2. 讀取 GeoJSON 資料
# 3. 基礎資料探索（shape, columns, dtypes）
# 4. 過濾特定校區建築
# 5. 簡單統計（建築數量、平均高度）
# 6. 匯出為 CSV
```

**02_data_analysis.ipynb**（資料分析）：
```python
# 1. 載入所有校區資料
# 2. 建築高度分佈分析（直方圖、箱型圖）
# 3. 校區比較分析（建築數量、平均高度）
# 4. 結構類型分析（R, B, S 等）
# 5. 空間分析（密度、聚類）
# 6. 時間序列分析（不同年份資料比較）
```

**03_visualization.ipynb**（視覺化）：
```python
# 1. 2D 地圖視覺化（Folium）
# 2. 建築高度熱力圖
# 3. 3D 視覺化（plotly）
# 4. 互動式圖表（bokeh）
# 5. 校區對比圖表
# 6. 匯出為 HTML
```

---

### Phase 5: 整合和測試（預估 25-30 分鐘）

#### 5.1 更新主 README.md

**新結構**：
```markdown
# NYCU Campus Building Spatial Dataset

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXX)
[![License: Mixed](https://img.shields.io/badge/License-Mixed-blue.svg)](LICENSE)
[![Data: NLSC + OSM](https://img.shields.io/badge/Data-NLSC%20%2B%20OSM-green.svg)]()

## 📊 資料集概述
【簡短描述】

## 🎯 主要特色
- 5 個校區，~7,836 棟建築
- 3D 建築模型 + 平面圖
- 20 個屬性欄位
- 開放格式（GeoJSON, CSV, Excel）

## 🚀 快速開始
【3 個步驟】

## 📁 專案結構
【簡化的目錄樹】

## 📚 資料來源與授權
【連結到 docs/DATA_SOURCES_AND_LICENSES.md】

## 📖 文件
- [Quick Start Guide](docs/QUICK_START.md)
- [Data Dictionary](docs/DATA_DICTIONARY.md)
- [Processing Pipeline](docs/PROCESSING_PIPELINE.md)
- [NLSC Protocol](docs/NLSC_PROTOCOL.md)

## 🔬 範例
【連結到 examples/】

## 📝 引用
【從 CITATION.cff】

## 🤝 貢獻
【連結到 .github/CONTRIBUTING.md】

## 📄 授權
【混合授權說明】
```

#### 5.2 更新授權文件

**LICENSE（重寫為混合授權）**：
```
Mixed Licensing for NYCU Campus Building Spatial Dataset

This dataset combines data from multiple sources with different licenses:

1. NLSC 3D Building Data
   License: Open Government Data License (Taiwan)
   Compatible with: CC BY 4.0

2. OpenStreetMap Data
   License: Open Database License (ODbL) 1.0
   URL: https://opendatacommons.org/licenses/odbl/

3. NYCU Campus Maps and Floor Plans
   Usage: Fair Use for Educational and Research Purposes

4. Derived Dataset (Processing Scripts and Merged Data)
   License: CC BY 4.0 (with ODbL attribution requirements)

ATTRIBUTION REQUIREMENTS:
- When using data derived from OSM: Must comply with ODbL attribution
- When using NLSC data: Must cite National Land Surveying Center
- When using merged dataset: Must cite this project + original sources

See docs/DATA_SOURCES_AND_LICENSES.md for detailed information.
```

**CITATION.cff（更新資料來源）**：
```yaml
references:
  - type: dataset
    title: "NLSC 3D Building Model Data"
    authors:
      - name: "National Land Surveying and Mapping Center"
    url: "https://3dmaps.nlsc.gov.tw/"

  - type: dataset
    title: "OpenStreetMap Taiwan"
    authors:
      - name: "OpenStreetMap Contributors"
    url: "https://www.openstreetmap.org/"
    license: "ODbL-1.0"

  - type: other
    title: "NYCU Official Campus Maps"
    authors:
      - name: "National Yang Ming Chiao Tung University"
```

#### 5.3 檢查清單

- [ ] 所有路徑引用正確（相對路徑）
- [ ] 所有 README.md 已更新
- [ ] metadata.json 完整
- [ ] .gitignore 正確設定
- [ ] 授權文件一致
- [ ] 範例 Notebooks 可執行
- [ ] 無死連結

---

### Phase 6: Git 初始化和 GitHub Release（預估 20-25 分鐘）

#### 6.1 Git 初始化

```bash
# 1. 初始化 Git
cd "C:\Users\thc1006\Desktop\NQSD\新增資料夾"
git init

# 2. 檢查 .gitignore
git status

# 3. 第一次 commit（只包含 ~100 MB 內容）
git add .
git commit -m "feat: initial commit - NYCU campus building dataset

- Add 34 processing scripts for NLSC 3D tiles and OSM data
- Include processed data for 5 campuses (Guangfu, Boai, Yangming, Liujia, Gueiren)
- Add documentation following FAIR principles
- Implement mixed licensing strategy (NLSC + ODbL + CC BY 4.0)
- Total: ~7,836 buildings with 20 attribute fields

Data sources:
- NLSC 3D Building Models (Open Government Data)
- OpenStreetMap Taiwan (ODbL)
- NYCU Official Campus Maps (Fair Use)

See docs/DATA_SOURCES_AND_LICENSES.md for details."

# 4. 建立 GitHub repository（需要在 GitHub 網頁操作）
# 5. 連結 remote
git remote add origin https://github.com/YOUR_USERNAME/NQSD.git
git branch -M main

# 6. 首次推送
git push -u origin main
```

#### 6.2 打包原始資料

```bash
# 切換到 data/raw
cd data/raw

# 打包 OSM 資料（523 MB）
zip -r ../../releases/NQSD_raw_osm_data_v1.0.0.zip auxiliary/
# 或使用 7z（更高壓縮率）
7z a -tzip ../../releases/NQSD_raw_osm_data_v1.0.0.zip auxiliary/

# 打包 NLSC 3D tiles（105 MB）和 quadtree（13 MB）
zip -r ../../releases/NQSD_raw_nlsc_tiles_v1.0.0.zip NLSC_3D_tiles/ NLSC_quadtree/

# 回到根目錄
cd ../..
```

#### 6.3 建立 GitHub Release

```bash
# 使用 gh CLI（推薦）
gh release create v1.0.0 \
  --title "NQSD v1.0.0 - NYCU Campus Building Dataset (2026-02)" \
  --notes "## 📊 資料集概述

完整的陽明交大校園建築空間資料，結合 NLSC 3D 建築模型和 OpenStreetMap 資料。

### 📦 包含內容
- **5 個校區**: 光復、博愛、陽明、六家、歸仁
- **~7,836 棟建築**: 包含 20 個屬性欄位
- **處理腳本**: 34 個 Python 腳本，完整處理管線
- **視覺化**: 互動式地圖、3D 檢視器

### 📥 原始資料下載
此 Release 包含大型原始資料（641 MB）：
- \`NQSD_raw_osm_data_v1.0.0.zip\` (523 MB) - OSM Taiwan 資料
- \`NQSD_raw_nlsc_tiles_v1.0.0.zip\` (118 MB) - NLSC 3D Tiles

### 🔧 使用方式
1. Clone repository: \`git clone https://github.com/YOUR_USERNAME/NQSD.git\`
2. 下載此 Release 的原始資料 ZIP 檔案
3. 解壓縮到 \`data/raw/\` 目錄
4. 參考 [Quick Start Guide](https://github.com/YOUR_USERNAME/NQSD/blob/main/docs/QUICK_START.md)

### 📝 資料來源與授權
- NLSC 3D Building Data: Open Government Data License (Taiwan)
- OpenStreetMap Data: ODbL 1.0
- NYCU Campus Maps: Fair Use (Educational)

詳見 [LICENSE](https://github.com/YOUR_USERNAME/NQSD/blob/main/LICENSE) 和 [Data Sources](https://github.com/YOUR_USERNAME/NQSD/blob/main/docs/DATA_SOURCES_AND_LICENSES.md)

### 📚 引用
請參考 [CITATION.cff](https://github.com/YOUR_USERNAME/NQSD/blob/main/CITATION.cff)

---
**發布日期**: 2026-02-08
**資料版本**: v1.0.0" \
  releases/NQSD_raw_osm_data_v1.0.0.zip \
  releases/NQSD_raw_nlsc_tiles_v1.0.0.zip
```

---

### Phase 7: Zenodo 整合（預估 10-15 分鐘 + 等待時間）

#### 7.1 啟用 Zenodo GitHub 整合

**步驟**：
1. 前往 [Zenodo](https://zenodo.org/) 並登入
2. 使用 GitHub 帳號登入（或連結現有帳號）
3. 前往 [GitHub Integration Settings](https://zenodo.org/account/settings/github/)
4. 找到 `NQSD` repository 並啟用（打開開關）
5. 返回 GitHub，建立新 Release（或編輯現有 Release）
6. Zenodo 將自動歸檔並分配 DOI

#### 7.2 等待 DOI 分配

**預估時間**: 5-30 分鐘（自動處理）

Zenodo 完成後會：
- 建立 Zenodo record
- 分配 DOI（格式：`10.5281/zenodo.XXXXXX`）
- 傳送通知郵件

#### 7.3 更新專案文件

**獲得 DOI 後，更新以下檔案**：

**README.md**（加入 DOI badge）：
```markdown
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXX)
```

**CITATION.cff**（加入 DOI）：
```yaml
identifiers:
  - type: doi
    value: "10.5281/zenodo.XXXXXX"
    description: "Zenodo DOI"
```

**.zenodo.json**（加入 DOI 到 related_identifiers）：
```json
"related_identifiers": [
  {
    "identifier": "10.5281/zenodo.XXXXXX",
    "relation": "isIdenticalTo",
    "scheme": "doi"
  }
]
```

**Commit 更新**：
```bash
git add README.md CITATION.cff .zenodo.json
git commit -m "docs: add Zenodo DOI badge and identifiers"
git push
```

---

## ⚙️ 自動化腳本建議

### auto_reorganize.sh（可選）

```bash
#!/bin/bash
# 自動執行 Phase 3-5

set -e

echo "🚀 開始自動重組..."

# Phase 3: 建立目錄結構
mkdir -p docs/{references,campus_maps/{guangfu,boai,yangming,liujia,gueiren,general},3d_models/previews}
mkdir -p examples/{sample_data,outputs}

# Phase 4: 移動檔案
echo "📁 重組校園地圖..."
mv docs/campus_maps/NYCU_Guangfu_*.* docs/campus_maps/guangfu/
mv docs/campus_maps/NYCU_Boai_*.* docs/campus_maps/boai/
# ... (其他移動操作)

# Phase 5: 生成 README
echo "📝 生成 README 檔案..."
python scripts/generate_readmes.py

echo "✅ 重組完成！"
```

---

## 📋 完整檢查清單

### Phase 3: 文件重組
- [ ] 建立 docs/ 目錄結構
- [ ] 重組校園地圖（按校區分類）
- [ ] 移動 3D 模型和預覽圖
- [ ] 整合 MD 文件（11 個 → 6 個）
- [ ] 建立 docs/DATA_SOURCES_AND_LICENSES.md
- [ ] 建立 docs/DATA_DICTIONARY.md
- [ ] 建立 docs/NLSC_PROTOCOL.md
- [ ] 刪除 data/ORGANIZATION_COMPLETION_REPORT.md

### Phase 4: 範例和教程
- [ ] 建立 examples/ 目錄結構
- [ ] 撰寫 01_basic_usage.ipynb
- [ ] 撰寫 02_data_analysis.ipynb
- [ ] 撰寫 03_visualization.ipynb
- [ ] 準備 sample_data/sample_buildings.geojson
- [ ] 建立 examples/README.md
- [ ] 建立 examples/requirements.txt

### Phase 5: 整合和測試
- [ ] 重寫主 README.md
- [ ] 更新 LICENSE 為混合授權
- [ ] 更新 CITATION.cff（加入資料來源）
- [ ] 更新 .zenodo.json（加入 notes）
- [ ] 更新所有子目錄 README.md
- [ ] 檢查所有路徑引用
- [ ] 測試範例 Notebooks
- [ ] 驗證 .gitignore 正確性

### Phase 6: Git 和 Release
- [ ] Git 初始化
- [ ] 建立 .gitignore
- [ ] 第一次 commit
- [ ] 建立 GitHub repository
- [ ] 推送到 GitHub
- [ ] 打包原始資料（2 個 ZIP）
- [ ] 建立 GitHub Release v1.0.0
- [ ] 上傳 ZIP 附件

### Phase 7: Zenodo
- [ ] 連結 Zenodo 帳號
- [ ] 啟用 repository 整合
- [ ] 等待 DOI 分配
- [ ] 更新 README.md（DOI badge）
- [ ] 更新 CITATION.cff（DOI）
- [ ] Commit 和 push

---

## 🔍 品質保證

### 測試範例 Notebooks

```bash
# 建立測試環境
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# 安裝依賴
pip install -r examples/requirements.txt

# 執行 Notebooks（使用 nbconvert）
jupyter nbconvert --to notebook --execute examples/01_basic_usage.ipynb
jupyter nbconvert --to notebook --execute examples/02_data_analysis.ipynb
jupyter nbconvert --to notebook --execute examples/03_visualization.ipynb
```

### 驗證授權一致性

```bash
# 檢查所有提及授權的檔案
grep -r "license\|License\|LICENSE" . --include="*.md" --include="*.cff" --include="*.json"

# 確保一致
```

---

## ⏱️ 時間預估總結

| Phase | 任務 | 預估時間 |
|-------|------|----------|
| 3 | 文件重組 | 30-40 分鐘 |
| 4 | 範例和教程 | 40-50 分鐘 |
| 5 | 整合和測試 | 25-30 分鐘 |
| 6 | Git 和 Release | 20-25 分鐘 |
| 7 | Zenodo 整合 | 10-15 分鐘 + 等待 |
| **總計** | | **~2.5-3 小時** |

---

## 📞 問題處理

### 常見問題

**Q1: ZIP 檔案太大，GitHub Release 上傳失敗？**
A: 使用更高壓縮率的 7z，或分割成多個檔案（每個 < 2 GB）

**Q2: Zenodo 整合沒有自動觸發？**
A: 檢查 repository 是否已啟用，確認 Release 是 "published" 狀態

**Q3: ODbL 授權如何正確標註？**
A: 參考 docs/DATA_SOURCES_AND_LICENSES.md，在 README 中明確標註 OSM contributors

---

## ✅ 完成標準

重組完成後應達成：

1. ✅ **FAIR 原則符合**
   - Findable: Zenodo DOI + 完整 metadata
   - Accessible: GitHub 公開 + 明確授權
   - Interoperable: 標準格式 + 開放協定
   - Reusable: 詳細文件 + 範例代碼

2. ✅ **學術標準**
   - CITATION.cff 可引用
   - LICENSE 明確
   - README 完整
   - 範例可執行

3. ✅ **授權合規**
   - 所有資料來源已標註
   - ODbL 歸屬要求已滿足
   - 混合授權策略已說明

4. ✅ **可重現性**
   - 所有腳本可執行
   - 範例可運行
   - 文件完整

---

**制定者**: NQSD Project Team
**最後更新**: 2026-02-08
**版本**: 2.0（深度規劃版）
