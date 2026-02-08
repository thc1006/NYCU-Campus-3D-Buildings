"""Download all building images from ymspace.ga.nycu.edu.tw uploadfiles API."""
import sys
import requests
import json
import os
import time

sys.stdout.reconfigure(encoding='utf-8')
requests.packages.urllib3.disable_warnings()

OUTDIR = r'C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive\building_images'
MAPPING_FILE = os.path.join(OUTDIR, 'image_id_mapping.json')

with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
    mapping = json.load(f)

BASE = 'https://ymspace.ga.nycu.edu.tw/gisweb/public/uploadfiles.htm'

total_downloaded = 0
total_skipped = 0
total_errors = 0
total_bytes = 0

for bid, image_ids in sorted(mapping.items()):
    bdir = os.path.join(OUTDIR, bid)
    os.makedirs(bdir, exist_ok=True)

    for img_id in sorted(image_ids, key=int):
        outpath = os.path.join(bdir, f'{img_id}.jpg')
        if os.path.exists(outpath) and os.path.getsize(outpath) > 100:
            total_skipped += 1
            continue

        try:
            r = requests.get(BASE, params={'action': 'listImg', 'q': img_id},
                             verify=False, timeout=30)
            ct = r.headers.get('content-type', '')
            if r.status_code == 200 and ('image' in ct or len(r.content) > 1000):
                with open(outpath, 'wb') as f:
                    f.write(r.content)
                total_downloaded += 1
                total_bytes += len(r.content)
                print(f'[OK] {bid}/{img_id}: {len(r.content):,} bytes')
            else:
                total_errors += 1
                print(f'[ERR] {bid}/{img_id}: {r.status_code}, {len(r.content)} bytes, ct={ct}')
        except Exception as e:
            total_errors += 1
            print(f'[ERR] {bid}/{img_id}: {e}')
        time.sleep(0.3)

print(f'\n=== Summary ===')
print(f'Downloaded: {total_downloaded}')
print(f'Skipped (existing): {total_skipped}')
print(f'Errors: {total_errors}')
print(f'Total bytes: {total_bytes:,} ({total_bytes/1024/1024:.1f} MB)')
