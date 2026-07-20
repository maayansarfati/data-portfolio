import json
import re
from pathlib import Path

path = Path('Analysis_Water_Breaks.ipynb')
with path.open('r', encoding='utf-8') as f:
    nb = json.load(f)
pattern = re.compile(r'[\u0590-\u05FF]')
for i, cell in enumerate(nb['cells'], 1):
    if cell['cell_type'] == 'code':
        for j, line in enumerate(cell['source'], 1):
            if pattern.search(line):
                print(f'CELL {i} LINE {j}: {line.rstrip()}')
