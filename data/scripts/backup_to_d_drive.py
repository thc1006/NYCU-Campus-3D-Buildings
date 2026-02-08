#!/usr/bin/env python3
"""
數據備份工具 - 備份到 D:\backup
在整理前創建完整的備份
"""

import shutil
import tarfile
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.progress import track

console = Console()


class DataBackup:
    """數據備份器 - 備份到 D 槽"""

    def __init__(self, source_path: Path, backup_base: Path):
        self.source_path = source_path
        self.backup_base = backup_base
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def create_full_backup(self):
        """創建完整備份到 D:\backup"""
        console.print(f"[bold cyan]創建完整數據備份到 {self.backup_base}[/bold cyan]\n")

        # 創建備份目錄
        self.backup_base.mkdir(parents=True, exist_ok=True)
        backup_dir = self.backup_base / f"NQSD_data_backup_{self.timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 要備份的目錄
        dirs_to_backup = ["raw", "processed", "output", "floor_plans"]

        # 1. 創建目錄備份
        console.print("[blue]步驟 1/3: 複製目錄...[/blue]")
        total_size = 0
        file_count = 0

        for dir_name in track(dirs_to_backup, description="備份中"):
            src = self.source_path / dir_name
            if src.exists():
                dst = backup_dir / dir_name

                # 計算大小
                dir_size = sum(f.stat().st_size for f in src.rglob("*") if f.is_file())
                dir_files = len([f for f in src.rglob("*") if f.is_file()])

                # 複製
                shutil.copytree(src, dst, dirs_exist_ok=True)

                total_size += dir_size
                file_count += dir_files

                console.print(f"  ✓ {dir_name}/ 已備份 ({dir_files} 個文件, {dir_size / (1024**2):.2f} MB)")
            else:
                console.print(f"  ⚠ {dir_name}/ 不存在，跳過")

        # 2. 創建壓縮檔案
        console.print("\n[blue]步驟 2/3: 創建壓縮檔案...[/blue]")
        archive_name = f"NQSD_data_backup_{self.timestamp}.tar.gz"
        archive_path = self.backup_base / archive_name

        with tarfile.open(archive_path, "w:gz") as tar:
            for dir_name in track(dirs_to_backup, description="壓縮中"):
                src = backup_dir / dir_name
                if src.exists():
                    tar.add(src, arcname=dir_name)

        archive_size = archive_path.stat().st_size

        # 3. 創建備份清單
        console.print("\n[blue]步驟 3/3: 生成備份清單...[/blue]")
        manifest_path = backup_dir / "BACKUP_MANIFEST.txt"

        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(f"NQSD 數據備份清單\n")
            f.write(f"=" * 60 + "\n\n")
            f.write(f"備份時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"備份位置: {backup_dir}\n")
            f.write(f"壓縮檔案: {archive_path}\n\n")
            f.write(f"統計資訊:\n")
            f.write(f"  總文件數: {file_count}\n")
            f.write(f"  總大小: {total_size / (1024**3):.2f} GB\n")
            f.write(f"  壓縮後: {archive_size / (1024**3):.2f} GB\n")
            f.write(f"  壓縮率: {(1 - archive_size/total_size)*100:.1f}%\n\n")
            f.write(f"備份目錄:\n")
            for dir_name in dirs_to_backup:
                if (backup_dir / dir_name).exists():
                    f.write(f"  ✓ {dir_name}/\n")

        # 統計資訊
        console.print(f"\n[green]備份完成！[/green]")
        console.print(f"  備份目錄: {backup_dir}")
        console.print(f"  總文件數: {file_count}")
        console.print(f"  備份大小: {total_size / (1024**3):.2f} GB")
        console.print(f"  壓縮檔案: {archive_path}")
        console.print(f"  壓縮大小: {archive_size / (1024**3):.2f} GB")
        console.print(f"  壓縮率: {(1 - archive_size/total_size)*100:.1f}%")
        console.print(f"  備份清單: {manifest_path}")

        return backup_dir, archive_path


def main():
    """主程序"""
    console.print("[bold cyan]NQSD 數據備份工具 - 備份到 D 槽[/bold cyan]\n")

    source_path = Path(r"C:\Users\thc1006\Desktop\NQSD\新增資料夾\data")
    backup_base = Path(r"D:\backup")

    # 確認來源路徑
    if not source_path.exists():
        console.print(f"[red]來源路徑不存在: {source_path}[/red]")
        return

    console.print(f"[yellow]來源路徑: {source_path}[/yellow]")
    console.print(f"[yellow]備份路徑: {backup_base}[/yellow]\n")

    backup = DataBackup(source_path, backup_base)

    try:
        backup_dir, archive_path = backup.create_full_backup()

        console.print("\n[bold green]備份成功完成！[/bold green]")
        console.print("\n[yellow]下一步: 可以安全地進行數據整理[/yellow]")

    except Exception as e:
        console.print(f"\n[bold red]錯誤: {e}[/bold red]")
        raise


if __name__ == "__main__":
    main()
