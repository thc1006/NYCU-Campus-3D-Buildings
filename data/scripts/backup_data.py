#!/usr/bin/env python3
"""
數據備份工具
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
    """數據備份器"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.backup_path = base_path / "backup"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def create_full_backup(self):
        """創建完整備份"""
        console.print("[bold cyan]📦 創建完整數據備份[/bold cyan]\n")

        # 創建備份目錄
        backup_dir = self.backup_path / f"backup_{self.timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 要備份的目錄
        dirs_to_backup = ["raw", "processed", "output", "floor_plans"]

        # 1. 創建目錄備份
        console.print("[blue]步驟 1/2: 複製目錄...[/blue]")
        for dir_name in track(dirs_to_backup, description="備份中"):
            src = self.base_path / dir_name
            if src.exists():
                dst = backup_dir / dir_name
                shutil.copytree(src, dst, dirs_exist_ok=True)
                console.print(f"  ✓ {dir_name}/ 已備份")
            else:
                console.print(f"  ⚠ {dir_name}/ 不存在，跳過")

        # 2. 創建壓縮檔案（可選）
        console.print("\n[blue]步驟 2/2: 創建壓縮檔案...[/blue]")
        archive_name = f"backup_{self.timestamp}.tar.gz"
        archive_path = self.backup_path / archive_name

        with tarfile.open(archive_path, "w:gz") as tar:
            for dir_name in track(dirs_to_backup, description="壓縮中"):
                src = backup_dir / dir_name
                if src.exists():
                    tar.add(src, arcname=dir_name)

        # 統計資訊
        backup_size = sum(f.stat().st_size for f in backup_dir.rglob("*") if f.is_file())
        archive_size = archive_path.stat().st_size

        console.print(f"\n[green]✅ 備份完成！[/green]")
        console.print(f"  備份目錄: {backup_dir}")
        console.print(f"  備份大小: {backup_size / (1024**3):.2f} GB")
        console.print(f"  壓縮檔案: {archive_path}")
        console.print(f"  壓縮大小: {archive_size / (1024**3):.2f} GB")
        console.print(f"  壓縮率: {(1 - archive_size/backup_size)*100:.1f}%")

        return backup_dir

    def list_backups(self):
        """列出所有備份"""
        console.print("\n[cyan]📋 現有備份列表:[/cyan]\n")

        if not self.backup_path.exists():
            console.print("  [yellow]沒有找到備份目錄[/yellow]")
            return

        # 列出目錄備份
        dir_backups = sorted(self.backup_path.glob("backup_*"))
        dir_backups = [d for d in dir_backups if d.is_dir()]

        # 列出壓縮備份
        archive_backups = sorted(self.backup_path.glob("backup_*.tar.gz"))

        if not dir_backups and not archive_backups:
            console.print("  [yellow]沒有找到任何備份[/yellow]")
            return

        # 顯示目錄備份
        if dir_backups:
            console.print("[bold]目錄備份:[/bold]")
            for backup in dir_backups:
                size = sum(f.stat().st_size for f in backup.rglob("*") if f.is_file())
                console.print(f"  📁 {backup.name} ({size / (1024**2):.1f} MB)")

        # 顯示壓縮備份
        if archive_backups:
            console.print("\n[bold]壓縮備份:[/bold]")
            for backup in archive_backups:
                size = backup.stat().st_size
                console.print(f"  📦 {backup.name} ({size / (1024**2):.1f} MB)")

    def restore_backup(self, backup_name: str):
        """從備份還原"""
        console.print(f"[bold yellow]⚠️  還原備份: {backup_name}[/bold yellow]\n")

        backup_dir = self.backup_path / backup_name

        if not backup_dir.exists():
            # 嘗試解壓縮檔案
            archive_path = self.backup_path / f"{backup_name}.tar.gz"
            if archive_path.exists():
                console.print(f"[blue]解壓縮 {archive_path.name}...[/blue]")
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(path=backup_dir)
            else:
                console.print(f"[red]✗ 備份不存在: {backup_name}[/red]")
                return

        # 還原各目錄
        dirs_to_restore = ["raw", "processed", "output", "floor_plans"]

        console.print("[yellow]這將覆蓋現有數據！[/yellow]")
        console.print("[bold]確定要繼續嗎？ (yes/no):[/bold] ", end="")

        # 在實際使用時需要用戶確認
        # 這裡僅作示範
        console.print("\n[blue]開始還原...[/blue]")

        for dir_name in track(dirs_to_restore, description="還原中"):
            src = backup_dir / dir_name
            dst = self.base_path / dir_name

            if src.exists():
                # 刪除現有目錄
                if dst.exists():
                    shutil.rmtree(dst)

                # 複製備份
                shutil.copytree(src, dst)
                console.print(f"  ✓ {dir_name}/ 已還原")
            else:
                console.print(f"  ⚠ {dir_name}/ 不在備份中，跳過")

        console.print(f"\n[green]✅ 還原完成！[/green]")


def main():
    """主程序"""
    console.print("[bold cyan]💾 NQSD 數據備份工具[/bold cyan]\n")

    base_path = Path("/data")
    backup = DataBackup(base_path)

    # 創建備份
    backup.create_full_backup()

    # 列出現有備份
    backup.list_backups()


if __name__ == "__main__":
    main()
