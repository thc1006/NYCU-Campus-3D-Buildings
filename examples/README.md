# NQSD 範例與教學

本目錄包含使用 NYCU 校園建築資料集的 Jupyter Notebook 範例。

## 📚 可用範例

### 1. 基礎使用 (`01_basic_usage.ipynb`)
- 讀取 GeoJSON 資料
- 基本資料探索
- 過濾特定校區建築
- 簡單統計分析
- 匯出為 CSV

### 2. 資料分析 (`02_data_analysis.ipynb`)
- 建築高度分佈分析
- 校區比較分析
- 結構類型統計
- 空間密度分析

### 3. 視覺化 (`03_visualization.ipynb`)
- 2D 地圖視覺化（Folium）
- 建築高度熱力圖
- 互動式圖表
- 匯出為 HTML

## 🚀 快速開始

### 安裝依賴

```bash
pip install -r requirements.txt
```

### 執行範例

```bash
jupyter notebook
# 開啟瀏覽器後選擇 .ipynb 檔案
```

## 📊 範例資料

`sample_data/` 目錄包含精簡版範例資料：
- `sample_buildings.geojson` - 100 棟建築範例
- `sample_buildings.csv` - CSV 格式

完整資料集請參考：`../data/output/latest/`

## 📝 授權

範例程式碼採用 **MIT License**

資料來源：
- NLSC 3D Building Data (Open Government Data)
- OpenStreetMap (© OSM contributors, ODbL)

---

**最後更新**: 2026-02-08
