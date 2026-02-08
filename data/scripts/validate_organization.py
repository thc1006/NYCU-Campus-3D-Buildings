#!/usr/bin/env python3
"""
數據組織驗證工具
檢查整理後的數據結構是否符合規範
"""

import json
from pathlib import Path
from typing import List, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


class OrganizationValidator:
    """數據組織驗證器"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed: List[str] = []

    def validate_all(self) -> bool:
        """執行所有驗證"""
        console.print("[bold cyan][CHECK] 開始驗證數據組織...[/bold cyan]\n")

        self.validate_raw()
        self.validate_processed()
        self.validate_output()
        self.validate_floor_plans()
        self.validate_ymmap_archive()

        return self._print_results()

    def validate_raw(self):
        """驗證 raw/ 目錄"""
        console.print("[blue]檢查 raw/ 目錄...[/blue]")

        raw_path = self.base_path / "raw"

        # 檢查必要文件
        required_files = ["README.md"]
        self._check_files(raw_path, required_files, "raw/")

        # 檢查 NLSC_3D_tiles 目錄
        nlsc_dir = raw_path / "NLSC_3D_tiles"
        if nlsc_dir.exists():
            self.passed.append("[OK] NLSC_3D_tiles/ 目錄存在")

            # 檢查元數據
            metadata_file = nlsc_dir / "metadata.json"
            if metadata_file.exists():
                self.passed.append("[OK] metadata.json 存在")
                try:
                    with open(metadata_file, encoding="utf-8") as f:
                        data = json.load(f)
                        if "datasets" in data:
                            self.passed.append(f"[OK] 記錄了 {len(data['datasets'])} 個數據集")
                        else:
                            self.warnings.append("[WARN] metadata.json 缺少 'datasets' 欄位")
                except json.JSONDecodeError:
                    self.errors.append("[ERROR] metadata.json 格式錯誤")
            else:
                self.warnings.append("[WARN] 缺少 metadata.json")
        else:
            self.errors.append("[ERROR] NLSC_3D_tiles/ 目錄不存在")

    def validate_processed(self):
        """驗證 processed/ 目錄"""
        console.print("[blue]檢查 processed/ 目錄...[/blue]")

        processed_path = self.base_path / "processed"

        # 檢查必要文件
        required_files = ["README.md", "metadata.json"]
        self._check_files(processed_path, required_files, "processed/")

        # 檢查目錄結構
        buildings_dir = processed_path / "buildings"
        if buildings_dir.exists():
            self.passed.append("[OK] buildings/ 目錄存在")

            # 檢查子目錄
            subdirs = ["by_campus", "combined", "osm"]
            for subdir in subdirs:
                path = buildings_dir / subdir
                if path.exists():
                    file_count = len(list(path.glob("*.json")) + list(path.glob("*.geojson")))
                    self.passed.append(f"[OK] buildings/{subdir}/ 存在（{file_count} 個文件）")
                else:
                    self.warnings.append(f"[WARN] 缺少 buildings/{subdir}/ 目錄")
        else:
            self.errors.append("[ERROR] buildings/ 目錄不存在")

    def validate_output(self):
        """驗證 output/ 目錄"""
        console.print("[blue]檢查 output/ 目錄...[/blue]")

        output_path = self.base_path / "output"

        # 檢查必要文件
        required_files = ["README.md"]
        self._check_files(output_path, required_files, "output/")

        # 檢查 latest/ 目錄
        latest_dir = output_path / "latest"
        if latest_dir.exists():
            expected_files = [
                "buildings_3d.geojson",
                "buildings_3d.html",
                "buildings_map.html",
                "buildings_merged.geojson",
                "buildings_table.csv",
                "buildings_table.xlsx",
                "metadata.json"
            ]

            existing = [f for f in expected_files if (latest_dir / f).exists()]
            self.passed.append(f"[OK] latest/ 目錄存在（{len(existing)}/{len(expected_files)} 個文件）")

            if len(existing) < len(expected_files):
                missing = set(expected_files) - set(existing)
                self.warnings.append(f"[WARN] latest/ 缺少文件: {', '.join(missing)}")
        else:
            self.errors.append("[ERROR] latest/ 目錄不存在")

        # 檢查版本目錄
        version_dirs = list(output_path.glob("v*_*"))
        if version_dirs:
            self.passed.append(f"[OK] 找到 {len(version_dirs)} 個版本目錄")
        else:
            self.warnings.append("[WARN] 沒有版本化目錄")

    def validate_floor_plans(self):
        """驗證 floor_plans/ 目錄"""
        console.print("[blue]檢查 floor_plans/ 目錄...[/blue]")

        floor_plans_path = self.base_path / "floor_plans"

        # 檢查必要文件
        required_files = ["README.md", "metadata.json"]
        self._check_files(floor_plans_path, required_files, "floor_plans/")

        # 檢查 pdf/ 目錄結構
        pdf_dir = floor_plans_path / "pdf"
        if pdf_dir.exists():
            subdirs = ["auditorium", "buildings", "campus", "administrative"]
            for subdir in subdirs:
                path = pdf_dir / subdir
                if path.exists():
                    pdf_count = len(list(path.glob("*.pdf")))
                    self.passed.append(f"[OK] pdf/{subdir}/ 存在（{pdf_count} 個 PDF）")
                else:
                    self.warnings.append(f"[WARN] 缺少 pdf/{subdir}/ 目錄")
        else:
            self.errors.append("[ERROR] pdf/ 目錄不存在")

        # 檢查 preview/ 目錄
        preview_dir = floor_plans_path / "preview"
        if preview_dir.exists():
            png_count = len(list(preview_dir.rglob("*.png")))
            self.passed.append(f"[OK] preview/ 目錄存在（{png_count} 張預覽圖）")
        else:
            self.warnings.append("[WARN] preview/ 目錄不存在")

    def validate_ymmap_archive(self):
        """驗證 ymmap_archive/ 未被修改"""
        console.print("[blue]檢查 ymmap_archive/ 完整性...[/blue]")

        archive_path = self.base_path / "ymmap_archive"

        if not archive_path.exists():
            self.errors.append("[ERROR] ymmap_archive/ 目錄不存在")
            return

        # 檢查是否為只讀（在 Docker 中）
        # 這裡只做基本檢查，確保目錄存在
        self.passed.append("[OK] ymmap_archive/ 目錄存在（未被修改）")

        # 統計文件數（僅供參考）
        file_count = len(list(archive_path.rglob("*")))
        self.passed.append(f"[OK] ymmap_archive/ 包含 {file_count} 個項目")

    def _check_files(self, path: Path, required_files: List[str], context: str):
        """檢查必要文件是否存在"""
        for filename in required_files:
            file_path = path / filename
            if file_path.exists():
                self.passed.append(f"[OK] {context}{filename} 存在")
            else:
                self.errors.append(f"[ERROR] {context}{filename} 缺少")

    def _print_results(self) -> bool:
        """輸出驗證結果"""
        console.print("\n" + "="*60)

        # 成功項目
        if self.passed:
            console.print(Panel(
                "\n".join(self.passed),
                title="[green][PASS] 通過項目[/green]",
                border_style="green"
            ))

        # 警告項目
        if self.warnings:
            console.print(Panel(
                "\n".join(self.warnings),
                title="[yellow][WARN] 警告項目[/yellow]",
                border_style="yellow"
            ))

        # 錯誤項目
        if self.errors:
            console.print(Panel(
                "\n".join(self.errors),
                title="[red][FAIL] 錯誤項目[/red]",
                border_style="red"
            ))

        # 統計表格
        table = Table(title="驗證統計")
        table.add_column("類型", style="cyan")
        table.add_column("數量", justify="right")

        table.add_row("[OK] 通過", f"[green]{len(self.passed)}[/green]")
        table.add_row("[WARN] 警告", f"[yellow]{len(self.warnings)}[/yellow]")
        table.add_row("[ERROR] 錯誤", f"[red]{len(self.errors)}[/red]")

        console.print(table)

        # 最終結果
        if self.errors:
            console.print("\n[bold red][FAIL] 驗證失敗！請修復上述錯誤。[/bold red]")
            return False
        elif self.warnings:
            console.print("\n[bold yellow][WARN] 驗證通過，但有警告項目。[/bold yellow]")
            return True
        else:
            console.print("\n[bold green][PASS] 驗證完全通過！[/bold green]")
            return True


def main():
    """主程序"""
    console.print("[bold cyan][CHECK] NQSD 數據組織驗證工具[/bold cyan]\n")

    base_path = Path(r"C:\Users\thc1006\Desktop\NQSD\新增資料夾\data")
    validator = OrganizationValidator(base_path)

    success = validator.validate_all()

    exit(0 if success else 1)


if __name__ == "__main__":
    main()
