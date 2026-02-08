#!/usr/bin/env python3
"""
Fix Jupyter notebooks for Google Colab compatibility
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

def fix_notebook(notebook_path):
    """Fix a notebook for Colab compatibility"""
    print(f"Processing {notebook_path}...")

    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    cells = nb['cells']
    new_cells = []

    # Add Colab setup cell at the beginning
    colab_setup = {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# Google Colab Setup\n",
            "\n",
            "**Note**: If running on Google Colab, run the cell below to download data first.\n",
            "\n",
            "**註**: 如在 Google Colab 執行，請先執行下方 cell 下載資料。"
        ]
    }

    colab_download = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Google Colab: Download dataset\n",
            "# 下載資料集（僅 Colab 需要）\n",
            "import os\n",
            "\n",
            "if 'COLAB_GPU' in os.environ or not os.path.exists('../data'):\n",
            "    print('Downloading dataset from GitHub...')\n",
            "    print('下載資料集...')\n",
            "    \n",
            "    # Clone repository\n",
            "    !git clone --depth 1 https://github.com/thc1006/NYCU-Campus-3D-Buildings.git\n",
            "    \n",
            "    # Change to repository directory\n",
            "    os.chdir('NYCU-Campus-3D-Buildings/examples')\n",
            "    \n",
            "    print('Done! / 完成！')\n",
            "else:\n",
            "    print('Running locally / 本地執行')"
        ]
    }

    new_cells.append(colab_setup)
    new_cells.append(colab_download)

    for i, cell in enumerate(cells):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']

            # Fix Chinese font for Colab
            if 'Microsoft JhengHei' in source:
                source = source.replace(
                    "plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS']",
                    "# Font setup for Chinese characters\n"
                    "# Colab uses different fonts than Windows\n"
                    "import matplotlib.font_manager as fm\n"
                    "plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif']"
                )

            # Remove emoji
            source = source.replace('✓', 'OK')
            source = source.replace('✅', '[OK]')
            source = source.replace('❌', '[ERROR]')

            # Fix output directory creation
            if 'outputs/' in source and 'mkdir' not in source:
                # Add directory creation before saving
                lines = source.split('\n')
                for j, line in enumerate(lines):
                    if "to_csv('outputs/" in line or "savefig('outputs/" in line or "save('outputs/" in line:
                        lines.insert(j, "os.makedirs('outputs', exist_ok=True)")
                        break
                source = '\n'.join(lines)

            cell['source'] = source.split('\n') if '\n' in source else [source]

        elif cell['cell_type'] == 'markdown':
            source = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']

            # Remove emoji from markdown
            source = source.replace('✓', 'OK')
            source = source.replace('✅', '[OK]')
            source = source.replace('❌', '[ERROR]')

            cell['source'] = source.split('\n') if '\n' in source else [source]

        new_cells.append(cell)

    nb['cells'] = new_cells

    # Write back
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)

    print(f"  Fixed {len(new_cells)} cells")
    return True

def main():
    examples_dir = Path(__file__).parent / 'examples'

    notebooks = [
        examples_dir / '01_basic_usage.ipynb',
        examples_dir / '02_data_analysis.ipynb',
        examples_dir / '03_visualization.ipynb'
    ]

    print("=" * 60)
    print("Fixing Jupyter Notebooks for Google Colab Compatibility")
    print("=" * 60)

    for nb_path in notebooks:
        if nb_path.exists():
            fix_notebook(nb_path)
        else:
            print(f"  Notebook not found: {nb_path}")

    print("\n" + "=" * 60)
    print("All notebooks fixed!")
    print("=" * 60)
    print("\nChanges:")
    print("- Added Colab setup cells (data download)")
    print("- Fixed Chinese font for Colab (DejaVu Sans)")
    print("- Removed all emoji")
    print("- Added output directory creation")
    print("\nNotebooks are now ready for Google Colab!")

if __name__ == '__main__':
    main()
