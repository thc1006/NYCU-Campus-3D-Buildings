"""Generate detailed inventory of ymmap_archive."""
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\thc1006\Desktop\NQSD\新增資料夾\data\ymmap_archive'
results = []
ext_stats = {}

for entry in sorted(os.listdir(base)):
    path = os.path.join(base, entry)
    if os.path.isdir(path):
        count = 0
        size = 0
        for dp, _, fns in os.walk(path):
            for f in fns:
                fp = os.path.join(dp, f)
                try:
                    s = os.path.getsize(fp)
                    size += s
                    count += 1
                    ext = os.path.splitext(f)[1].lower()
                    ext_stats[ext] = ext_stats.get(ext, [0, 0])
                    ext_stats[ext][0] += 1
                    ext_stats[ext][1] += s
                except:
                    pass
        results.append((size, count, entry + '/'))
    else:
        size = os.path.getsize(path)
        ext = os.path.splitext(entry)[1].lower()
        ext_stats[ext] = ext_stats.get(ext, [0, 0])
        ext_stats[ext][0] += 1
        ext_stats[ext][1] += size
        results.append((size, 1, entry))

results.sort(key=lambda x: -x[0])
total_files = sum(r[1] for r in results)
total_size = sum(r[0] for r in results)

print("=" * 60)
print("ymmap_archive Inventory")
print("=" * 60)
for size, count, name in results:
    if size > 1024*1024:
        print(f'  {size/1024/1024:8.1f} MB  {count:5d} files  {name}')
    else:
        print(f'  {size/1024:8.1f} KB  {count:5d} files  {name}')

print(f'\nTotal: {total_files:,} files, {total_size/1024/1024:.1f} MB ({total_size/1024/1024/1024:.2f} GB)')

print("\n" + "=" * 60)
print("By file extension:")
print("=" * 60)
for ext, (cnt, sz) in sorted(ext_stats.items(), key=lambda x: -x[1][1]):
    if sz > 1024*1024:
        print(f'  {ext or "(none)":8s}  {cnt:5d} files  {sz/1024/1024:8.1f} MB')
    else:
        print(f'  {ext or "(none)":8s}  {cnt:5d} files  {sz/1024:8.1f} KB')
