"""Generate SHA-256 manifest for ymmap_archive data integrity verification."""

import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ARCHIVE_DIR = Path(__file__).parent.parent / "data" / "ymmap_archive"
MANIFEST_PATH = ARCHIVE_DIR / "manifest-sha256.txt"

# Files to skip (the manifest itself and any temp files)
SKIP_FILES = {"manifest-sha256.txt"}


def sha256_file(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def main():
    print(f"Scanning: {ARCHIVE_DIR}")

    all_files = sorted(
        f
        for f in ARCHIVE_DIR.rglob("*")
        if f.is_file() and f.name not in SKIP_FILES
    )

    print(f"Found {len(all_files)} files to hash")

    lines = []
    for i, filepath in enumerate(all_files, 1):
        rel = filepath.relative_to(ARCHIVE_DIR)
        digest = sha256_file(filepath)
        # BagIt-style: hash two-spaces relative-path
        lines.append(f"{digest}  {rel.as_posix()}")

        if i % 500 == 0 or i == len(all_files):
            print(f"  [{i}/{len(all_files)}] {rel.as_posix()}")

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nManifest written: {MANIFEST_PATH}")
    print(f"  Total files: {len(lines)}")


if __name__ == "__main__":
    main()
