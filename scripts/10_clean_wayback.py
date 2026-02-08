"""Clean Wayback Machine artifacts from archived frontend files."""
import sys
import re
import os

sys.stdout.reconfigure(encoding="utf-8")

base = r"C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive"
skip_dirs = {"api_data", "floor_plans", "building_photos", "gis_layers", "preview"}

cleaned_count = 0
for root, dirs, files in os.walk(base):
    # Skip data directories
    if any(sd in root for sd in skip_dirs):
        continue
    for f in files:
        if not f.endswith((".js", ".css", ".html")):
            continue
        fpath = os.path.join(root, f)
        with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()

        orig_len = len(content)
        # Remove Wayback URL prefixes
        content = re.sub(
            r"https?://web\.archive\.org/web/\d+(?:id_|js_|cs_|im_)?/", "", content
        )
        # Remove Wayback archive comments
        content = re.sub(
            r"/\*\s*FILE ARCHIVED ON.*?\*/", "", content, flags=re.DOTALL
        )

        if len(content) != orig_len:
            with open(fpath, "w", encoding="utf-8") as fh:
                fh.write(content)
            cleaned_count += 1
            rel = os.path.relpath(fpath, base)
            print(f"  Cleaned: {rel} ({orig_len} -> {len(content)} chars)")
        else:
            rel = os.path.relpath(fpath, base)
            print(f"  OK:      {rel}")

print(f"\nCleaned {cleaned_count} files")
