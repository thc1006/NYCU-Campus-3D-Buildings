#!/usr/bin/env python3
"""
建立 GitHub Release 所需的壓縮檔
"""
import sys
import zipfile
import os
from pathlib import Path
from datetime import datetime

# 修復 Windows cp950 編碼問題
sys.stdout.reconfigure(encoding='utf-8')

def create_zip_archive(source_dir, output_file, description):
    """
    建立 ZIP 壓縮檔

    Args:
        source_dir: 來源目錄路徑
        output_file: 輸出檔案路徑
        description: 檔案描述（用於顯示進度）
    """
    print(f"\n📦 正在打包 {description}...")
    print(f"   來源: {source_dir}")
    print(f"   目標: {output_file}")

    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"   ❌ 來源目錄不存在: {source_dir}")
        return False

    file_count = 0
    start_time = datetime.now()

    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(source_path.parent)
                zipf.write(file_path, arcname)
                file_count += 1
                if file_count % 100 == 0:
                    print(f"   已處理 {file_count} 個檔案...")

    # 檢查檔案大小
    output_path = Path(output_file)
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    elapsed = (datetime.now() - start_time).total_seconds()

    print(f"   ✅ 完成！")
    print(f"   檔案數: {file_count}")
    print(f"   大小: {file_size_mb:.1f} MB")
    print(f"   耗時: {elapsed:.1f} 秒")
    return True

def main():
    # 設定路徑
    base_dir = Path(__file__).parent
    data_raw_dir = base_dir / "data" / "raw"
    releases_dir = base_dir / "releases"

    # 確保 releases 目錄存在
    releases_dir.mkdir(exist_ok=True)

    print("=" * 70)
    print("🚀 NYCU-Campus-3D-Buildings Repository - Release 資料打包工具")
    print("=" * 70)

    # 打包 1: OSM auxiliary 資料
    success1 = create_zip_archive(
        source_dir=data_raw_dir / "auxiliary",
        output_file=releases_dir / "NYCU-Campus-3D-Buildings_raw_osm_v1.0.0.zip",
        description="OSM 輔助資料 (auxiliary/)"
    )

    # 打包 2: NLSC 瓦片資料
    print(f"\n📦 正在打包 NLSC 瓦片資料...")
    print(f"   包含: NLSC_3D_tiles/ + NLSC_quadtree/")

    nlsc_zip_path = releases_dir / "NYCU-Campus-3D-Buildings_raw_nlsc_v1.0.0.zip"
    file_count = 0
    start_time = datetime.now()

    with zipfile.ZipFile(nlsc_zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        # 打包 NLSC_3D_tiles
        tiles_dir = data_raw_dir / "NLSC_3D_tiles"
        if tiles_dir.exists():
            for root, dirs, files in os.walk(tiles_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(data_raw_dir)
                    zipf.write(file_path, arcname)
                    file_count += 1
                    if file_count % 100 == 0:
                        print(f"   已處理 {file_count} 個檔案...")

        # 打包 NLSC_quadtree
        quadtree_dir = data_raw_dir / "NLSC_quadtree"
        if quadtree_dir.exists():
            for root, dirs, files in os.walk(quadtree_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(data_raw_dir)
                    zipf.write(file_path, arcname)
                    file_count += 1
                    if file_count % 100 == 0:
                        print(f"   已處理 {file_count} 個檔案...")

    file_size_mb = nlsc_zip_path.stat().st_size / (1024 * 1024)
    elapsed = (datetime.now() - start_time).total_seconds()

    print(f"   ✅ 完成！")
    print(f"   檔案數: {file_count}")
    print(f"   大小: {file_size_mb:.1f} MB")
    print(f"   耗時: {elapsed:.1f} 秒")
    success2 = True

    # 總結
    print("\n" + "=" * 70)
    print("📊 打包完成總結")
    print("=" * 70)

    if success1:
        osm_size = (releases_dir / "NYCU-Campus-3D-Buildings_raw_osm_v1.0.0.zip").stat().st_size / (1024 * 1024)
        print(f"✅ NYCU-Campus-3D-Buildings_raw_osm_v1.0.0.zip ({osm_size:.1f} MB)")
    else:
        print(f"❌ NYCU-Campus-3D-Buildings_raw_osm_v1.0.0.zip (失敗)")

    if success2:
        nlsc_size = nlsc_zip_path.stat().st_size / (1024 * 1024)
        print(f"✅ NYCU-Campus-3D-Buildings_raw_nlsc_v1.0.0.zip ({nlsc_size:.1f} MB)")
    else:
        print(f"❌ NYCU-Campus-3D-Buildings_raw_nlsc_v1.0.0.zip (失敗)")

    total_size = sum([
        (releases_dir / "NYCU-Campus-3D-Buildings_raw_osm_v1.0.0.zip").stat().st_size if success1 else 0,
        nlsc_zip_path.stat().st_size if success2 else 0
    ]) / (1024 * 1024)

    print(f"\n📦 總大小: {total_size:.1f} MB")
    print(f"📁 輸出目錄: {releases_dir}")
    print("\n🎯 下一步:")
    print("   1. ✅ GitHub repository 已建立: https://github.com/thc1006/NYCU-Campus-3D-Buildings")
    print("   2. 執行 git remote add origin https://github.com/thc1006/NYCU-Campus-3D-Buildings.git")
    print("   3. 執行 git push -u origin main")
    print("   4. 在 GitHub 建立 Release v1.0.0")
    print("   5. 上傳這兩個 ZIP 檔案作為 Release 附件")

if __name__ == "__main__":
    main()
