# NQSD 專案版本控制策略

> **建立日期**: 2026-02-08
> **專案**: NYCU 校園建築空間資料 (NLSC 3D + OSM)
> **性質**: 資料分析/研究專案，未來不頻繁修改

---

## 專案檔案盤點

| 分類 | 路徑 | 大小 | 檔案數 | 可重新取得？ |
|------|------|------|--------|------------|
| 處理腳本 | `scripts/*.py` | 544 KB | 34 | 否 (原創程式碼) |
| 資料整理腳本 | `data/scripts/*.py` | 68 KB | 4 | 否 (原創程式碼) |
| 最終輸出 | `data/output/` | 3.2 MB | ~10 | 可重新生成 |
| 中間處理結果 | `data/processed/` | 9.7 MB | ~8 | 可重新生成 |
| 平面圖 | `data/floor_plans/` | 24 MB | ~30 | 部分可重新下載 |
| 參考文件 | `docs/` | 61 MB | ~16 | 部分可重新下載 |
| 文件 | `README.md` + `data/*.md` | ~80 KB | 9 | 否 |
| Docker 配置 | `data/docker-compose.yml` 等 | ~12 KB | 3 | 否 |
| OSM 原始資料 | `data/raw/auxiliary/` | **523 MB** | 2 | 可重新下載 |
| NLSC 3D 瓦片 | `data/raw/NLSC_3D_tiles/` | **105 MB** | ~637 | 可重新下載 |
| NLSC Quadtree | `data/raw/NLSC_quadtree/` | **13 MB** | ~76 | 可重新下載 |
| **總計** | | **739 MB** | **869** | |

### 應清理的垃圾檔案

| 檔案 | 原因 |
|------|------|
| `data/.claude/` | Claude Code 工作殘留，非專案內容 |
| `data/bash.exe.stackdump` | crash dump，無用 |
| `building_analysis_output.txt` | 臨時輸出 (180 KB) |

---

## 方案比較

### 方案 A：Git + GitHub Release (推薦)

**策略**: 程式碼與成果用 Git 追蹤，大型原始資料打包成 GitHub Release 附件。

#### 進入 Git 的內容 (~100 MB)

```
scripts/                    # 34 個 Python 腳本 (544 KB)
data/scripts/               # 4 個資料整理腳本 (68 KB)
data/output/                # 最終成果 geojson/html/csv/xlsx (3.2 MB)
data/processed/             # 中間處理 GeoJSON/JSON (9.7 MB)
data/floor_plans/           # PDF 平面圖 + PNG 預覽 (24 MB)
data/*.md                   # 資料文件
data/docker-compose.yml     # Docker 配置
data/Dockerfile.organizer
data/run_organize.*
docs/                       # 校園地圖 PDF/JPG, 論文, 3D 模型 (61 MB)
README.md
.gitignore
```

#### 放入 GitHub Release 的內容 (~641 MB)

打包成 1-2 個 zip 附件 (GitHub Release 上限 2 GB/檔)：

```
data/raw/auxiliary/taiwan-osm-latest.osm.pbf         # 299 MB
data/raw/auxiliary/taiwan-osm-latest-free.shp.zip     # 225 MB
data/raw/NLSC_3D_tiles/                               # 105 MB (~637 .bin)
data/raw/NLSC_quadtree/                               # 13 MB (~76 .bin)
```

#### .gitignore 內容

```gitignore
# 大型原始資料 (放在 GitHub Release)
data/raw/auxiliary/
data/raw/NLSC_3D_tiles/
data/raw/NLSC_quadtree/

# 原始資料 metadata 保留
!data/raw/metadata.json
!data/raw/README.md

# 垃圾檔案
data/.claude/
*.stackdump
building_analysis_output.txt

# Python
__pycache__/
*.pyc
*.pyo

# OS
.DS_Store
Thumbs.db
desktop.ini
```

#### 優點

- 一次設定，長期免費 (無持續費用)
- 簡單直覺，不需額外工具
- Release 頁面提供完整資料下載連結
- 程式碼有完整版本歷史
- 適合不常更動的專案

#### 缺點

- `docs/` 內有多個 >5 MB 的 PDF，在 Git 裡不可改名/替換 (否則歷史膨脹)
- 但既然不常更動，這不是問題

#### GitHub Release 建議格式

```
Tag:    v1.0
Title:  NYCU Campus Building Dataset - 2026-02

Assets:
  - NQSD_raw_osm_data.zip        (~524 MB) — OSM PBF + SHP
  - NQSD_raw_nlsc_tiles.zip      (~118 MB) — NLSC 3D tiles + quadtree
```

---

### 方案 B：Git + Git LFS

**策略**: 所有檔案都進 Git，大型二進位用 LFS 追蹤。

#### LFS 追蹤規則

```gitattributes
*.bin filter=lfs diff=lfs merge=lfs -text
*.pbf filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
*.pdf filter=lfs diff=lfs merge=lfs -text
*.glb filter=lfs diff=lfs merge=lfs -text
*.usdz filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.png filter=lfs diff=lfs merge=lfs -text
*.webp filter=lfs diff=lfs merge=lfs -text
*.xlsx filter=lfs diff=lfs merge=lfs -text
```

#### 優點

- `git clone` 即得完整專案
- 版本追蹤最完整 (含二進位檔異動歷史)
- 檔案管理最一致

#### 缺點

- GitHub LFS 免費額度：**1 GB 儲存 + 1 GB/月頻寬**
- 本專案 LFS 部分約 **730 MB**，幾乎用盡免費額度
- 超額需付費 ($5/月 per 50 GB data pack)
- 對不常更動的存檔專案而言是不必要的持續成本
- clone 速度慢

---

### 方案 C：Git + GitHub Packages (OCI Artifact)

**策略**: 程式碼用 Git，資料打包成 OCI artifact 推到 GitHub Container Registry。

#### 使用方式

```bash
# 推送資料
oras push ghcr.io/USER/nqsd-data:v1 ./data/raw/

# 拉取資料
oras pull ghcr.io/USER/nqsd-data:v1
```

#### 優點

- 公開 repo 免費，無頻寬限制
- 可版本化大型資料

#### 缺點

- **過度工程**: 這是資料分析專案，不是套件/服務
- 使用者需安裝 `oras` CLI 或 Docker
- 不直覺，無法在 GitHub 網頁直接瀏覽/下載
- 維護成本高於收益

---

## 最終決策

### 採用方案 A：Git + GitHub Release

理由：

1. **專案性質**: 資料分析/研究存檔，非活躍開發的軟體專案
2. **更新頻率**: 低 — Release 足以應對
3. **成本**: 完全免費，無持續費用
4. **簡易性**: 設定一次即可，門檻最低
5. **可重現性**: 腳本在 Git，原始資料在 Release，任何人可完整重建

### 執行步驟

```bash
# 1. 清理垃圾檔案
rm -rf data/.claude/
rm -f data/bash.exe.stackdump
rm -f building_analysis_output.txt

# 2. 建立 .gitignore

# 3. 初始化 Git
git init
git add .
git commit -m "feat: initial commit - NYCU campus building dataset"

# 4. 連結 GitHub remote
git remote add origin https://github.com/USER/REPO.git
git push -u origin main

# 5. 打包原始資料
cd data/raw
zip -r ../../NQSD_raw_osm_data.zip auxiliary/
zip -r ../../NQSD_raw_nlsc_tiles.zip NLSC_3D_tiles/ NLSC_quadtree/

# 6. 建立 GitHub Release (透過 gh CLI)
gh release create v1.0 \
  --title "NYCU Campus Building Dataset - 2026-02" \
  --notes "完整原始資料，配合 scripts/ 可重新生成所有成果" \
  NQSD_raw_osm_data.zip \
  NQSD_raw_nlsc_tiles.zip
```

---

## 附註：檔案大小分佈

```
523 MB ██████████████████████████████████████░░░ data/raw/auxiliary/ (OSM, 可重新下載)
105 MB ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ data/raw/NLSC_3D_tiles/ (可重新下載)
 61 MB █████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ docs/ (PDF/3D模型)
 24 MB ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ data/floor_plans/
 13 MB █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ data/raw/NLSC_quadtree/ (可重新下載)
9.7 MB █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ data/processed/
3.2 MB ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ data/output/
544 KB ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ scripts/ (核心程式碼)
       ├── Git repo: ~100 MB ──┤├── Release: ~641 MB ──┤
```
