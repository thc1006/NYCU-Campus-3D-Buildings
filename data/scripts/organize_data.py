#!/usr/bin/env python3
"""
NQSD 數據整理工具
參考 ymmap_archive 的歸檔模式進行數據整理
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from rich.console import Console
from rich.progress import track
from rich.table import Table

console = Console()

class DataOrganizer:
    """數據整理器"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.raw_path = base_path / "raw"
        self.processed_path = base_path / "processed"
        self.output_path = base_path / "output"
        self.floor_plans_path = base_path / "floor_plans"
        self.backup_path = base_path / "backup"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def create_backup(self) -> Path:
        """創建備份"""
        console.print("\n[bold blue]📦 創建備份...[/bold blue]")

        backup_dir = self.backup_path / f"backup_{self.timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 備份各個目錄
        dirs_to_backup = ["raw", "processed", "output", "floor_plans"]

        for dir_name in track(dirs_to_backup, description="備份中"):
            src = self.base_path / dir_name
            if src.exists():
                dst = backup_dir / dir_name
                shutil.copytree(src, dst, dirs_exist_ok=True)

        console.print(f"[green]✓ 備份完成: {backup_dir}[/green]")
        return backup_dir

    def organize_raw(self):
        """整理 raw/ 目錄 - 基於 ymmap_archive 最佳實踐"""
        console.print("\n[bold blue]📁 整理 raw/ 目錄（參考 ymmap_archive 模式）...[/bold blue]")

        # 創建版本化目錄結構（參考 ymmap_archive）
        tiles_dir = self.raw_path / "NLSC_3D_tiles"
        quadtree_dir = self.raw_path / "NLSC_quadtree"
        auxiliary_dir = self.raw_path / "auxiliary"

        for d in [tiles_dir / "current", tiles_dir / "previous", tiles_dir / "archive",
                  quadtree_dir / "current", quadtree_dir / "legacy", auxiliary_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # 版本映射（基於代理分析）
        version_mapping = {
            "current": ["113_J", "113_A", "112_A", "112_D", "112_O"],
            "previous": ["111_A", "111_J"],
            "legacy": ["109_A"]
        }

        # 處理 3D Tiles
        tiles_datasets = list(self.raw_path.glob("NLSC_3D_tiles_*"))
        tiles_metadata = []

        for dataset in track(tiles_datasets, description="整理 3D Tiles"):
            if not dataset.is_dir():
                continue

            # 提取版本資訊
            parts = dataset.name.replace("NLSC_3D_tiles_", "").split("_")
            year = parts[0] if parts else "unknown"
            campus_code = "_".join(parts[1:]) if len(parts) > 1 else "unknown"

            # 確定版本分類
            version_category = "previous"  # 預設
            for category, patterns in version_mapping.items():
                if any(year.startswith(p) or campus_code.startswith(p) for p in patterns):
                    version_category = category
                    break

            # 生成元數據
            metadata = self._generate_dataset_metadata(dataset, year)
            metadata["version_category"] = version_category
            metadata["campus"] = self._identify_campus(campus_code)
            tiles_metadata.append(metadata)

            # 移動到適當的版本目錄
            new_name = f"{year}_{campus_code}"
            target_dir = tiles_dir / version_category / new_name

            if not target_dir.exists() and target_dir != dataset:
                shutil.move(str(dataset), str(target_dir))
                console.print(f"  移動: {dataset.name} → {version_category}/{new_name}")

        # 處理 Quadtree
        quadtree_datasets = list(self.raw_path.glob("NLSC_quadtree_*"))
        quadtree_metadata = []

        for dataset in track(quadtree_datasets, description="整理 Quadtree"):
            if not dataset.is_dir():
                continue

            parts = dataset.name.replace("NLSC_quadtree_", "").split("_")
            year = parts[0] if parts else "unknown"
            campus_code = "_".join(parts[1:]) if len(parts) > 1 else "unknown"

            # v4 版本特殊處理
            if "v4" in campus_code.lower():
                version_category = "legacy"
            else:
                version_category = "current" if year.startswith("113") or year.startswith("112") else "legacy"

            metadata = self._generate_dataset_metadata(dataset, year)
            metadata["version_category"] = version_category
            metadata["campus"] = self._identify_campus(campus_code)
            quadtree_metadata.append(metadata)

            new_name = f"{year}_{campus_code}"
            target_dir = quadtree_dir / version_category / new_name

            if not target_dir.exists() and target_dir != dataset:
                shutil.move(str(dataset), str(target_dir))
                console.print(f"  移動: {dataset.name} → {version_category}/{new_name}")

        # 移動外部數據到 auxiliary/
        osm_files = list(self.raw_path.glob("taiwan-osm-*.*"))
        for osm_file in osm_files:
            target = auxiliary_dir / osm_file.name
            if not target.exists():
                shutil.move(str(osm_file), str(target))
                console.print(f"  移動: {osm_file.name} → auxiliary/")

        # 保存元數據（參考 ymmap_archive 的元數據結構）
        self._save_raw_metadata(tiles_dir, tiles_metadata, "3D_tiles")
        self._save_raw_metadata(quadtree_dir, quadtree_metadata, "quadtree")

        # 創建 README
        self._create_raw_readme()

        console.print("[green]✓ raw/ 目錄整理完成（已分類：current/previous/legacy）[/green]")

    def _identify_campus(self, campus_code: str) -> str:
        """識別校區名稱"""
        campus_map = {
            "yangming": "陽明",
            "A": "陽明",
            "boai": "博愛",
            "O": "光復/博愛",
            "gueiren": "歸仁",
            "D": "歸仁",
            "liujia": "六甲",
            "J": "六甲"
        }
        for key, value in campus_map.items():
            if key.lower() in campus_code.lower():
                return value
        return "未知"

    def _save_raw_metadata(self, base_dir: Path, metadata_list: List[Dict], data_type: str):
        """保存 raw 目錄元數據"""
        metadata = {
            "description": f"NLSC {data_type} Data - Versioned Organization",
            "source": "National Land Surveying and Mapping Center (NLSC)",
            "coordinate_system": "TWD97 (EPSG:3826)",
            "organized_date": self.timestamp,
            "version_strategy": {
                "current": "Latest versions (113_*, 112_*)",
                "previous": "Previous versions (111_*)",
                "legacy": "Older versions (109_*, special v4)"
            },
            "datasets": metadata_list,
            "total_count": len(metadata_list),
            "total_size_mb": sum(d.get("total_size_mb", 0) for d in metadata_list)
        }

        metadata_file = base_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def organize_processed(self):
        """整理 processed/ 目錄 - 按校區和數據源正確分類"""
        console.print("\n[bold blue]📁 整理 processed/ 目錄（按校區和數據源分類）...[/bold blue]")

        # 創建詳細的目錄結構（參考 ymmap_archive 的分類方式）
        buildings_dir = self.processed_path / "buildings"
        reference_dir = self.processed_path / "reference"

        # 為每個校區創建目錄
        campus_list = ["boai", "yangming", "gueiren", "liujia", "guangfu"]
        for campus in campus_list:
            (buildings_dir / "by_campus" / campus).mkdir(parents=True, exist_ok=True)

        (buildings_dir / "combined").mkdir(parents=True, exist_ok=True)
        (buildings_dir / "osm").mkdir(parents=True, exist_ok=True)
        reference_dir.mkdir(parents=True, exist_ok=True)

        # 校區文件映射（參考代理分析結果）
        campus_mapping = {
            "boai": {
                "json": "NYCU_boai_NLSC_buildings.json",
                "building_count": 1023,
                "data_source": "NLSC Layer 112_O"
            },
            "yangming": {
                "json": "NYCU_yangming_NLSC_buildings.json",
                "building_count": 446,
                "data_source": "NLSC Layer 112_A/113_A"
            },
            "gueiren": {
                "json": "NYCU_gueiren_NLSC_buildings.json",
                "building_count": 17,
                "data_source": "NLSC Layer 112_D"
            },
            "liujia": {
                "json": "NYCU_liujia_NLSC_buildings.json",
                "building_count": 169,
                "data_source": "NLSC Layer 113_J"
            },
            "guangfu": {
                "geojson": "NYCU_Guangfu_OSM_buildings.geojson",
                "building_count": 319,
                "data_source": "OpenStreetMap"
            }
        }

        # 處理校區文件
        for campus, info in track(campus_mapping.items(), description="分類校區數據"):
            campus_dir = buildings_dir / "by_campus" / campus

            # 移動主文件
            for file_type in ["json", "geojson"]:
                if file_type in info:
                    src_file = self.processed_path / info[file_type]
                    if src_file.exists():
                        # 統一命名格式（去掉 NYCU_ 前綴）
                        if campus == "guangfu":
                            dst_name = "OSM_buildings.geojson"
                        else:
                            dst_name = f"NLSC_buildings.{file_type}"

                        dst_path = campus_dir / dst_name
                        if not dst_path.exists():
                            shutil.copy2(src_file, dst_path)
                            console.print(f"  ✓ {campus}: {info[file_type]} → {dst_name}")

            # 為每個校區生成元數據
            campus_metadata = {
                "campus": campus,
                "campus_name_zh": self._get_campus_name_zh(campus),
                "campus_name_en": self._get_campus_name_en(campus),
                "data_source": info["data_source"],
                "building_count": info["building_count"],
                "files": []
            }

            # 檢查實際文件
            for f in campus_dir.glob("*.*"):
                if f.is_file():
                    campus_metadata["files"].append({
                        "filename": f.name,
                        "size_bytes": f.stat().st_size,
                        "format": f.suffix[1:]
                    })

            # 保存校區元數據
            with open(campus_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(campus_metadata, f, indent=2, ensure_ascii=False)

        # 處理合併文件
        combined_mapping = {
            "NYCU_NLSC_buildings.json": {
                "new_name": "with_surrounding.json",
                "description": "包含周邊建物的完整數據（6,181 棟）"
            },
            "NYCU_NLSC_buildings.geojson": {
                "new_name": "with_surrounding.geojson",
                "description": "GeoJSON 格式（6,181 棟）"
            }
        }

        console.print("\n  處理合併數據...")
        for src_name, info in combined_mapping.items():
            src_file = self.processed_path / src_name
            if src_file.exists():
                dst_path = buildings_dir / "combined" / info["new_name"]
                if not dst_path.exists():
                    shutil.copy2(src_file, dst_path)
                    console.print(f"  ✓ 合併: {src_name} → {info['new_name']}")

        # 移動參考文件
        building_list = self.processed_path / "NYCU_building_list.txt"
        if building_list.exists():
            dst = reference_dir / "building_names_list.txt"
            if not dst.exists():
                shutil.copy2(building_list, dst)
                console.print(f"  ✓ 參考: NYCU_building_list.txt → reference/")

        # 生成總體元數據
        overall_metadata = {
            "organized_date": self.timestamp,
            "organization_principle": "ymmap_archive style - hierarchical by campus and source",
            "structure": {
                "buildings/by_campus/{campus}/": "各校區的獨立數據",
                "buildings/combined/": "所有校區合併數據（含周邊建物）",
                "buildings/osm/": "OpenStreetMap 來源數據",
                "reference/": "參考和索引文件"
            },
            "campuses": list(campus_mapping.keys()),
            "total_buildings_by_campus": sum(info["building_count"] for info in campus_mapping.values()),
            "data_sources": {
                "NLSC": "4 campuses (boai, yangming, gueiren, liujia)",
                "OSM": "1 campus (guangfu)"
            }
        }

        with open(self.processed_path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(overall_metadata, f, indent=2, ensure_ascii=False)

        self._create_processed_readme()

        console.print("[green]✓ processed/ 目錄整理完成（5 個校區已分類）[/green]")

    def _get_campus_name_zh(self, campus: str) -> str:
        """獲取校區中文名稱"""
        names = {
            "boai": "博愛校區",
            "yangming": "陽明校區",
            "gueiren": "歸仁校區",
            "liujia": "六甲校區",
            "guangfu": "光復校區"
        }
        return names.get(campus, campus)

    def _get_campus_name_en(self, campus: str) -> str:
        """獲取校區英文名稱"""
        names = {
            "boai": "Boai Campus",
            "yangming": "Yangming Campus",
            "gueiren": "Gueiren Campus",
            "liujia": "Liujia Campus",
            "guangfu": "Guangfu Campus"
        }
        return names.get(campus, campus.title())

    def organize_output(self):
        """整理 output/ 目錄 - 建立版本控制"""
        console.print("\n[bold blue]📁 整理 output/ 目錄...[/bold blue]")

        # 創建版本化目錄
        version_name = f"v1_{datetime.now().strftime('%Y-%m-%d')}"
        version_dir = self.output_path / version_name
        version_dir.mkdir(exist_ok=True)

        latest_dir = self.output_path / "latest"

        # 當前的輸出文件
        output_files = [
            "NYCU_buildings_3d.geojson",
            "NYCU_buildings_3d.html",
            "NYCU_buildings_map.html",
            "NYCU_buildings_merged.geojson",
            "NYCU_buildings_table.csv",
            "NYCU_buildings_table.xlsx",
        ]

        # 複製到版本目錄
        for filename in track(output_files, description="版本化文件"):
            src = self.output_path / filename
            if src.exists():
                # 去掉 NYCU_ 前綴
                new_name = filename.replace("NYCU_", "")
                dst = version_dir / new_name
                shutil.copy2(src, dst)

        # 生成版本元數據
        metadata = {
            "version": version_name,
            "created_date": datetime.now().isoformat(),
            "files": output_files,
            "source": "processed/buildings/combined/",
            "generator": "building_merger_v2.py"
        }

        with open(version_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # 創建或更新 latest/ 符號連結（Windows 使用目錄複製）
        if latest_dir.exists():
            shutil.rmtree(latest_dir)
        shutil.copytree(version_dir, latest_dir)

        self._create_output_readme()

        console.print("[green]✓ output/ 目錄整理完成[/green]")

    def organize_floor_plans(self):
        """整理 floor_plans/ 目錄 - 按類型分類並生成詳細元數據"""
        console.print("\n[bold blue]📁 整理 floor_plans/ 目錄（按類型分類）...[/bold blue]")

        # 創建詳細的目錄結構
        pdf_dir = self.floor_plans_path / "pdf"
        categories = {
            "auditorium": {
                "label_zh": "禮堂",
                "label_en": "Auditorium",
                "building": "Main Auditorium",
                "campus": "Yangming"
            },
            "buildings": {
                "label_zh": "建築物",
                "label_en": "Buildings",
                "building": "Various",
                "campus": "Yangming"
            },
            "campus": {
                "label_zh": "校園地圖",
                "label_en": "Campus Maps",
                "building": "Campus-wide",
                "campus": "Yangming"
            },
            "administrative": {
                "label_zh": "行政文件",
                "label_en": "Administrative",
                "building": "Administrative",
                "campus": "All"
            }
        }

        for category in categories:
            (pdf_dir / category).mkdir(parents=True, exist_ok=True)

        # 詳細的文件映射（基於代理分析）
        pdf_mapping = {
            "auditorium_panorama.pdf": {
                "category": "auditorium",
                "new_name": "panorama.pdf",
                "title_zh": "禮堂全景圖",
                "title_en": "Auditorium Panorama",
                "pages": 2,
                "use_cases": ["event_planning", "capacity_planning"]
            },
            "auditorium_seatmap.pdf": {
                "category": "auditorium",
                "new_name": "seatmap.pdf",
                "title_zh": "禮堂座位圖",
                "title_en": "Auditorium Seat Map",
                "pages": 2,
                "use_cases": ["seating_assignment", "ticket_planning"]
            },
            "einfo_building_map.pdf": {
                "category": "buildings",
                "new_name": "einfo_building_map.pdf",
                "title_zh": "資訊大樓平面圖",
                "title_en": "E-Info Building Map",
                "pages": 2,
                "use_cases": ["navigation", "room_finding"]
            },
            "eng5_exam_floorplan.pdf": {
                "category": "buildings",
                "new_name": "eng5_exam_floorplan.pdf",
                "title_zh": "工程五館考試配置圖",
                "title_en": "ENG5 Exam Floor Plan",
                "pages": 1,
                "use_cases": ["exam_planning", "seating_arrangement"]
            },
            "yangming_campus_map.pdf": {
                "category": "campus",
                "new_name": "yangming_campus_map.pdf",
                "title_zh": "陽明校區地圖",
                "title_en": "Yangming Campus Map",
                "pages": 1,
                "use_cases": ["navigation", "wayfinding"]
            },
            "yangming_map_old.pdf": {
                "category": "campus",
                "new_name": "yangming_map_old.pdf",
                "title_zh": "陽明校區地圖（舊版）",
                "title_en": "Yangming Campus Map (Old)",
                "pages": 2,
                "use_cases": ["historical_reference"]
            },
            "fee_standard.pdf": {
                "category": "administrative",
                "new_name": "fee_standard.pdf",
                "title_zh": "收費標準",
                "title_en": "Fee Standard",
                "pages": 0,  # 損壞
                "status": "corrupted",
                "use_cases": ["fee_reference"]
            }
        }

        # 移動和分類 PDF 文件
        file_stats = {}
        for src_name, info in track(pdf_mapping.items(), description="分類 PDF 文件"):
            src_file = self.floor_plans_path / src_name
            category = info["category"]
            dst_path = pdf_dir / category / info["new_name"]

            if src_file.exists() and not dst_path.exists():
                # 檢查文件大小（檢測損壞）
                file_size = src_file.stat().st_size
                if file_size < 1000:  # 小於 1 KB 可能損壞
                    console.print(f"  ⚠️  {src_name}: 檔案可能損壞（{file_size} bytes）")
                    info["status"] = "corrupted"
                    info["size_bytes"] = file_size

                shutil.copy2(src_file, dst_path)
                console.print(f"  ✓ {category}: {src_name} → {info['new_name']}")

            # 統計
            if category not in file_stats:
                file_stats[category] = {
                    "count": 0,
                    "total_size": 0,
                    "files": []
                }
            file_stats[category]["count"] += 1
            file_stats[category]["files"].append(info)
            if src_file.exists():
                file_stats[category]["total_size"] += src_file.stat().st_size

        # 重組 preview/ 目錄（保持與 PDF 一致的結構）
        console.print("\n  重組 preview/ 目錄...")
        preview_base = self.floor_plans_path / "preview"

        preview_mapping = {
            "auditorium": ["auditorium_panorama_", "auditorium_seatmap_"],
            "buildings": ["einfo_building_map_", "eng5_exam_floorplan_"],
            "campus": ["yangming_campus_map_", "yangming_map_old_"]
        }

        for category, prefixes in preview_mapping.items():
            category_preview_dir = preview_base / category
            category_preview_dir.mkdir(parents=True, exist_ok=True)

            for prefix in prefixes:
                for preview_file in preview_base.glob(f"{prefix}*.png"):
                    dst = category_preview_dir / preview_file.name
                    if not dst.exists():
                        shutil.copy2(preview_file, dst)

        # 生成詳細的元數據
        metadata = {
            "organized_date": self.timestamp,
            "organization_principle": "ymmap_archive style - hierarchical by document type",
            "categories": {}
        }

        for category, info in categories.items():
            stats = file_stats.get(category, {"count": 0, "files": []})

            # 統計預覽圖
            preview_count = len(list((preview_base / category).glob("*.png"))) if (preview_base / category).exists() else 0

            metadata["categories"][category] = {
                "label_zh": info["label_zh"],
                "label_en": info["label_en"],
                "building": info["building"],
                "campus": info["campus"],
                "document_count": stats["count"],
                "preview_count": preview_count,
                "total_size_mb": round(stats.get("total_size", 0) / (1024 * 1024), 2),
                "documents": []
            }

            # 添加文件詳情
            for file_info in stats.get("files", []):
                doc_meta = {
                    "id": file_info["new_name"].replace(".pdf", ""),
                    "filename": file_info["new_name"],
                    "title_zh": file_info.get("title_zh", ""),
                    "title_en": file_info.get("title_en", ""),
                    "pages": file_info.get("pages", 0),
                    "use_cases": file_info.get("use_cases", [])
                }

                if "status" in file_info:
                    doc_meta["status"] = file_info["status"]
                    doc_meta["size_bytes"] = file_info.get("size_bytes", 0)

                metadata["categories"][category]["documents"].append(doc_meta)

        # 添加品質問題記錄
        metadata["quality_issues"] = []
        for src_name, info in pdf_mapping.items():
            if info.get("status") == "corrupted":
                metadata["quality_issues"].append({
                    "document": src_name,
                    "category": info["category"],
                    "issue": f"File size {info.get('size_bytes', 0)} bytes - likely corrupted",
                    "action_required": "Replace with valid file or remove",
                    "priority": "high"
                })

        with open(self.floor_plans_path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        self._create_floor_plans_readme()

        total_issues = len(metadata["quality_issues"])
        if total_issues > 0:
            console.print(f"[yellow]⚠️  發現 {total_issues} 個品質問題（詳見 metadata.json）[/yellow]")

        console.print("[green]✓ floor_plans/ 目錄整理完成（4 個類別已分類）[/green]")

    def _generate_dataset_metadata(self, dataset_path: Path, year: str) -> Dict[str, Any]:
        """生成數據集元數據"""
        bin_files = list(dataset_path.rglob("*.bin"))
        layers = set([f.parent.name for f in bin_files if f.parent.name.startswith("L")])

        total_size = sum(f.stat().st_size for f in bin_files) / (1024 * 1024)  # MB

        return {
            "name": dataset_path.name,
            "year": year,
            "file_count": len(bin_files),
            "total_size_mb": round(total_size, 2),
            "layers": sorted(list(layers)),
            "has_manifest": (dataset_path / "manifest.json").exists()
        }

    def _create_raw_readme(self):
        """創建 raw/ 目錄的 README"""
        readme_content = """# Raw Data - 原始數據

此目錄包含從 NLSC（國土測繪中心）下載的原始 3D Tiles 數據。

## 目錄結構

```
raw/
├── README.md                    # 本文件
├── NLSC_3D_tiles/              # 3D Tiles 數據集
│   ├── metadata.json           # 數據集元數據
│   ├── 109_A_yangming/         # 109 年陽明校區
│   ├── 112_A_yangming/         # 112 年陽明校區
│   ├── 112_D_gueiren/          # 112 年歸仁校區
│   ├── 112_O/                  # 112 年其他
│   ├── 112_O_boai/             # 112 年博愛校區
│   └── 113_J_liujia/           # 113 年六甲校區
└── archive/                    # 歸檔的舊版本（壓縮）
```

## 數據來源

- **來源**: 國土測繪中心 (NLSC)
- **格式**: 3D Tiles (.bin)
- **坐標系統**: TWD97 (EPSG:3826)

## 使用說明

1. 每個數據集包含多個層級（L5, L6 等）的 3D Tiles
2. `manifest.json` 記錄了 tiles 的索引資訊
3. 不建議直接修改此目錄下的文件
4. 數據處理請使用 `processed/` 目錄的結果

## 更新記錄

- 2026-02-08: 整理並建立新的目錄結構
"""

        with open(self.raw_path / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

    def _create_processed_readme(self):
        """創建 processed/ 目錄的 README"""
        readme_content = """# Processed Data - 處理後的數據

此目錄包含從原始 3D Tiles 提取並處理後的建築數據。

## 目錄結構

```
processed/
├── README.md                           # 本文件
├── metadata.json                       # 處理元數據
├── buildings/
│   ├── by_campus/                      # 按校區分類
│   │   ├── boai_NLSC_buildings.json
│   │   ├── gueiren_NLSC_buildings.json
│   │   ├── liujia_NLSC_buildings.json
│   │   └── yangming_NLSC_buildings.json
│   ├── combined/                       # 合併數據
│   │   ├── NLSC_buildings.json
│   │   └── NLSC_buildings.geojson
│   └── osm/                            # OpenStreetMap 數據
│       └── Guangfu_OSM_buildings.geojson
└── building_list.txt                   # 建築清單
```

## 數據格式

- **JSON**: 原始建築資訊（包含高度、樓層等）
- **GeoJSON**: 地理空間格式（可用於 GIS 軟體）

## 處理流程

1. 從 raw/ 讀取 3D Tiles
2. 提取建築多邊形
3. 計算建築高度和樓層
4. 按校區分類
5. 合併為完整數據集

## 使用範例

```python
import json
import geopandas as gpd

# 讀取 GeoJSON
gdf = gpd.read_file("buildings/combined/NLSC_buildings.geojson")

# 讀取 JSON
with open("buildings/by_campus/yangming_NLSC_buildings.json") as f:
    data = json.load(f)
```
"""

        with open(self.processed_path / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

    def _create_output_readme(self):
        """創建 output/ 目錄的 README"""
        readme_content = """# Output - 最終輸出

此目錄包含最終的可視化和分析結果。

## 目錄結構

```
output/
├── README.md                    # 本文件
├── latest/                      # 最新版本（符號連結）
│   ├── buildings_3d.geojson
│   ├── buildings_3d.html
│   ├── buildings_map.html
│   ├── buildings_merged.geojson
│   ├── buildings_table.csv
│   ├── buildings_table.xlsx
│   └── metadata.json
├── v1_2026-02-07/              # 版本化存檔
│   └── [same files as latest]
└── archive/                     # 舊版本（壓縮）
```

## 文件說明

| 文件 | 格式 | 描述 |
|------|------|------|
| `buildings_3d.geojson` | GeoJSON | 3D 建築數據 |
| `buildings_3d.html` | HTML | 3D 可視化地圖 |
| `buildings_map.html` | HTML | 2D 互動地圖 |
| `buildings_merged.geojson` | GeoJSON | 合併的完整數據 |
| `buildings_table.csv` | CSV | 建築資料表 |
| `buildings_table.xlsx` | Excel | 建築資料表（帶格式） |

## 版本管理

- `latest/`: 永遠指向最新版本
- `vX_YYYY-MM-DD/`: 帶時間戳的版本存檔
- `archive/`: 壓縮的舊版本（節省空間）

## 使用說明

1. **查看地圖**: 直接開啟 `latest/buildings_map.html`
2. **數據分析**: 使用 CSV 或 GeoJSON 文件
3. **版本追溯**: 查看特定日期的版本目錄
"""

        with open(self.output_path / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

    def _create_floor_plans_readme(self):
        """創建 floor_plans/ 目錄的 README"""
        readme_content = """# Floor Plans - 平面圖

此目錄包含校園建築的平面圖和相關文件。

## 目錄結構

```
floor_plans/
├── README.md                    # 本文件
├── metadata.json                # 平面圖索引
├── pdf/
│   ├── auditorium/              # 禮堂相關
│   │   ├── panorama.pdf
│   │   └── seatmap.pdf
│   ├── buildings/               # 建築物平面圖
│   │   ├── einfo_building_map.pdf
│   │   └── eng5_exam_floorplan.pdf
│   ├── campus/                  # 校園地圖
│   │   ├── yangming_campus_map.pdf
│   │   └── yangming_map_old.pdf
│   └── administrative/          # 行政文件
│       └── fee_standard.pdf
└── preview/                     # PNG 預覽圖
    ├── auditorium/
    ├── buildings/
    └── campus/
```

## 文件分類

### 🏛️ Auditorium (禮堂)
- `panorama.pdf`: 禮堂全景圖
- `seatmap.pdf`: 座位配置圖

### 🏢 Buildings (建築物)
- `einfo_building_map.pdf`: 資訊大樓平面圖
- `eng5_exam_floorplan.pdf`: 工程五館考場配置

### 🗺️ Campus (校園)
- `yangming_campus_map.pdf`: 陽明校區地圖（新）
- `yangming_map_old.pdf`: 陽明校區地圖（舊）

### 📋 Administrative (行政)
- `fee_standard.pdf`: 收費標準

## 預覽圖

`preview/` 目錄包含所有 PDF 的 PNG 預覽圖（每頁一張）。

## 使用建議

- 需要列印時使用 PDF 原檔
- 快速查看時使用 preview/ 的 PNG 圖片
- 建議使用 PDF 閱讀器開啟以獲得最佳體驗
"""

        with open(self.floor_plans_path / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

    def generate_report(self) -> str:
        """生成整理報告"""
        console.print("\n[bold blue]📊 生成整理報告...[/bold blue]")

        # 統計各目錄
        stats = {}
        for dir_name in ["raw", "processed", "output", "floor_plans"]:
            dir_path = self.base_path / dir_name
            if dir_path.exists():
                files = list(dir_path.rglob("*"))
                total_size = sum(f.stat().st_size for f in files if f.is_file())
                stats[dir_name] = {
                    "files": len([f for f in files if f.is_file()]),
                    "dirs": len([f for f in files if f.is_dir()]),
                    "size_mb": round(total_size / (1024 * 1024), 2)
                }

        # 創建表格
        table = Table(title="數據整理統計")
        table.add_column("目錄", style="cyan")
        table.add_column("文件數", justify="right", style="green")
        table.add_column("子目錄數", justify="right", style="blue")
        table.add_column("大小 (MB)", justify="right", style="magenta")

        for dir_name, stat in stats.items():
            table.add_row(
                dir_name,
                str(stat["files"]),
                str(stat["dirs"]),
                f"{stat['size_mb']:.2f}"
            )

        console.print(table)

        # 生成報告文件
        report = {
            "organized_date": self.timestamp,
            "statistics": stats,
            "actions": [
                "創建備份",
                "整理 raw/ 目錄並生成元數據",
                "整理 processed/ 目錄按校區分類",
                "整理 output/ 目錄並建立版本控制",
                "整理 floor_plans/ 目錄按類型分類",
                "為所有目錄創建 README.md"
            ],
            "next_steps": [
                "驗證文件完整性",
                "壓縮舊版本數據",
                "更新主 README.md"
            ]
        }

        report_file = self.base_path / f"organization_report_{self.timestamp}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        console.print(f"\n[green]✓ 報告已保存: {report_file.name}[/green]")

        return str(report_file)


def main():
    """主程序"""
    console.print("[bold cyan]🚀 NQSD 數據整理工具[/bold cyan]\n")

    base_path = Path("/data")
    organizer = DataOrganizer(base_path)

    try:
        # 1. 創建備份
        organizer.create_backup()

        # 2. 整理各目錄
        organizer.organize_raw()
        organizer.organize_processed()
        organizer.organize_output()
        organizer.organize_floor_plans()

        # 3. 生成報告
        organizer.generate_report()

        console.print("\n[bold green]✅ 所有數據整理完成！[/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]❌ 錯誤: {e}[/bold red]")
        raise


if __name__ == "__main__":
    main()
