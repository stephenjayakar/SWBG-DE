"""Export native icon table bounds without rebuilding texture atlases."""
import json
from pathlib import Path

def write_limits(icons):
    lines = []
    for category in ('Buildings', 'Units', 'Techs'):
        indices = sorted(map(int, icons[category]))
        assert indices == list(range(len(indices))), category
        lines.append(f'{category}\t{len(indices)}\n')
    Path('work/faction-ui-icon-limits.tsv').write_text(''.join(lines))

if __name__ == '__main__':
    write_limits(json.loads(Path(r'E:\SteamLibrary\steamapps\common\AoE2DE\widgetui\icons.json').read_text()))
