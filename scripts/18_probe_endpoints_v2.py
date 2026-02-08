"""Probe additional API endpoints on ymspace.ga.nycu.edu.tw for data extraction."""
import sys
import requests
import json
import os
import time

sys.stdout.reconfigure(encoding='utf-8')
requests.packages.urllib3.disable_warnings()

BASE = 'https://ymspace.ga.nycu.edu.tw/gisweb/public'
OUTDIR = r'C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive\endpoint_probe_v2'
os.makedirs(OUTDIR, exist_ok=True)

results = []

# Define all test cases
tests = [
    # buildinfo actions
    ('buildinfo.htm', {'action': 'search', 'q': '%', 'limit': '999', 'locale': 'ja'}),
    ('buildinfo.htm', {'action': 'search', 'q': '%', 'limit': '999', 'locale': 'ko'}),
    ('buildinfo.htm', {'action': 'findAll'}),
    ('buildinfo.htm', {'action': 'list'}),
    ('buildinfo.htm', {'action': 'getById', 'buildId': 'B005'}),
    ('buildinfo.htm', {'action': 'getDetail', 'buildId': 'B005'}),
    ('buildinfo.htm', {'action': 'getFloorPlan', 'buildId': 'B005', 'floor': '1F'}),
    ('buildinfo.htm', {'action': 'getFloorDetail', 'buildId': 'B005', 'floor': '1F'}),
    ('buildinfo.htm', {'action': 'getFloorListOfFloorPlain', 'buildId': 'B005'}),
    ('buildinfo.htm', {'action': 'getHistory'}),
    ('buildinfo.htm', {'action': 'export'}),
    ('buildinfo.htm', {'action': 'loadImage', 'buildId': 'B005'}),
    ('buildinfo.htm', {'action': 'loadImage', 'buildId': 'Y009'}),
    ('buildinfo.htm', {'action': 'loadImage', 'buildId': 'P005'}),
    ('buildinfo.htm', {'action': 'loadImage', 'buildId': 'B020'}),
    ('buildinfo.htm', {'action': 'loadImage', 'buildId': 'G005'}),
    # roominfo actions
    ('roominfo.htm', {'action': 'search', 'q': '%', 'limit': '999'}),
    ('roominfo.htm', {'action': 'findAll'}),
    ('roominfo.htm', {'action': 'findAll', 'limit': '10'}),
    ('roominfo.htm', {'action': 'findByBuildId', 'buildId': 'B005'}),
    ('roominfo.htm', {'action': 'getDetail', 'id': 'Y0091F001'}),
    ('roominfo.htm', {'action': 'getBound', 'classNum': '101', 'buildId': 'B005', 'floor': '1F'}),
    ('roominfo.htm', {'action': 'getBound', 'buildId': 'B005', 'floor': '1F'}),
    ('roominfo.htm', {'action': 'export'}),
    ('roominfo.htm', {'action': 'queryRoomExists', 'q': 'B005-101'}),
    ('roominfo.htm', {'action': 'queryRoomExists', 'buildId': 'B005', 'classNum': '101'}),
    # route actions
    ('route.htm', {'action': 'findRoute', 'from': 'B005', 'to': 'B020'}),
    ('route.htm', {'action': 'navigate', 'startBuildId': 'B005', 'endBuildId': 'B020'}),
    ('route.htm', {'action': 'findGeom', 'buildId': 'B005', 'floor': '1F'}),
    ('route.htm', {'action': 'findAll'}),
    ('route.htm', {'action': 'list'}),
    ('route.htm', {'action': 'loadImageByApKey', 'apKey': '1'}),
    ('route.htm', {'action': 'loadImageByApKey', 'apKey': '100'}),
    # campus
    ('campus.htm', {'action': 'findAll'}),
    ('campus.htm', {'action': 'list'}),
    ('campus.htm', {'action': 'getDetail', 'id': '1'}),
    # userrole
    ('userrole.htm', {'action': 'findAllLayers'}),
    ('userrole.htm', {'action': 'findAllRoles'}),
    ('userrole.htm', {'action': 'findAllUsers'}),
    ('userrole.htm', {'action': 'getCurrentUser'}),
    # new controllers
    ('attachment.htm', {'action': 'list'}),
    ('attachment.htm', {'action': 'findAll'}),
    ('layer.htm', {'action': 'list'}),
    ('layer.htm', {'action': 'findAll'}),
    ('poi.htm', {'action': 'findAll'}),
    ('poi.htm', {'action': 'search', 'q': '%'}),
    ('facility.htm', {'action': 'findAll'}),
    ('parking.htm', {'action': 'findAll'}),
    ('space.htm', {'action': 'findAll'}),
    ('photo.htm', {'action': 'findAll'}),
    ('document.htm', {'action': 'findAll'}),
    ('asset.htm', {'action': 'findAll'}),
    ('statistics.htm', {'action': 'list'}),
    ('notification.htm', {'action': 'list'}),
    # uploadfiles
    ('uploadfiles.htm', {'action': 'listImg', 'q': '38540'}),
    ('uploadfiles.htm', {'action': 'listImg', 'q': '38541'}),
    ('uploadfiles.htm', {'action': 'listImg', 'q': '38542'}),
    ('uploadfiles.htm', {'action': 'listImg', 'q': '38543'}),
    ('uploadfiles.htm', {'action': 'list'}),
    ('uploadfiles.htm', {'action': 'findAll'}),
]

for endpoint, params in tests:
    url = f'{BASE}/{endpoint}'
    try:
        r = requests.get(url, params=params, verify=False, timeout=10)
        action = params.get('action', '?')
        extra = '&'.join(f'{k}={v}' for k, v in params.items() if k != 'action')
        label = f'{endpoint}?action={action}'
        if extra:
            label += f'&{extra}'

        result = {'endpoint': label, 'status': r.status_code, 'size': len(r.content)}

        if r.status_code == 200 and len(r.content) > 20:
            try:
                data = r.json()
                result['type'] = 'json'
                result['preview'] = str(data)[:200]
                safe = label.replace('?', '_').replace('&', '_').replace('=', '-').replace('%', 'pct').replace(':', '-')
                fpath = os.path.join(OUTDIR, f'{safe}.json')
                with open(fpath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)
                print(f'[JSON] {label}: {r.status_code}, {len(r.content):,} bytes')
            except Exception:
                result['type'] = 'html/other'
                result['preview'] = r.text[:200]
                ct = r.headers.get('content-type', '')
                if 'image' in ct:
                    safe = label.replace('?', '_').replace('&', '_').replace('=', '-').replace('%', 'pct').replace(':', '-')
                    ext = 'jpg' if 'jpeg' in ct else 'png' if 'png' in ct else 'bin'
                    fpath = os.path.join(OUTDIR, f'{safe}.{ext}')
                    with open(fpath, 'wb') as f:
                        f.write(r.content)
                    print(f'[IMG] {label}: {r.status_code}, {len(r.content):,} bytes ({ct})')
                elif len(r.content) > 50:
                    safe = label.replace('?', '_').replace('&', '_').replace('=', '-').replace('%', 'pct').replace(':', '-')
                    fpath = os.path.join(OUTDIR, f'{safe}.txt')
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(r.text)
                    print(f'[HTML] {label}: {r.status_code}, {len(r.content):,} bytes')
                else:
                    print(f'[TINY] {label}: {r.status_code}, {len(r.content)} bytes: {r.text[:100]}')
        elif r.status_code == 200:
            result['preview'] = r.text[:200]
            print(f'[EMPTY] {label}: {r.status_code}, {len(r.content)} bytes: {r.text}')
        else:
            result['preview'] = r.text[:200]
            print(f'[{r.status_code}] {label}: {len(r.content)} bytes')
        results.append(result)
    except Exception as e:
        results.append({'endpoint': str(params), 'status': 'error', 'error': str(e)})
        print(f'[ERR] {endpoint}: {e}')
    time.sleep(0.3)

# Save summary
with open(os.path.join(OUTDIR, '_probe_summary.json'), 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

accessible = [r for r in results if r.get('status') == 200 and r.get('size', 0) > 20]
print(f'\nTotal tested: {len(results)}')
print(f'Accessible with data: {len(accessible)}')
print('Summary saved to endpoint_probe_v2/_probe_summary.json')
