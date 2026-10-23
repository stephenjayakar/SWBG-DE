"""Apply classic_ai_de_lines.split_faction_lines to the installed/staged Draft unitlines.json and the installed Classic AI.

Run from the repo root with the game closed (DE caches the Data mod). Not idempotent: it refuses to run on
already-split lines. Backs up originals under work/parity-backups/.
"""
import json, shutil, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import classic_ai_de_lines as L

LOCAL = Path(r'C:\Users\aj12a\Games\Age of Empires 2 DE\76561198022514833\mods\local')
UNITLINES = [LOCAL / 'SWGB-DE-Factions-Draft/resources/_common/dat/unitlines.json',
             Path('outputs/SWGB-DE-Factions-Draft/resources/_common/dat/unitlines.json')]
PER = LOCAL / 'SWGB-DE-Factions-Assets/resources/_common/ai/SWGB Classic AI.per'
DAT = 'work/original-ai/current-dat'


def main():
    reach = L.faction_reach(DAT)
    backup = Path('work/parity-backups') / (time.strftime('%Y%m%d-%H%M%S') + '-factionlines')
    backup.mkdir(parents=True, exist_ok=True)
    per = PER.read_text(encoding='utf-8')
    split_per = None
    for path in UNITLINES:
        data = json.loads(path.read_text(encoding='utf-8'))
        assert not any('swgb-rebel-' in str(l['Identifier']) for l in data['UnitLines']), f'{path} already split'
        shutil.copy2(path, backup / (path.parent.parent.parent.parent.name + '-unitlines.json'))
        data, new_per, report = L.split_faction_lines(data, per, reach)
        assert split_per in (None, new_per), 'unitlines copies differ'
        split_per = new_per
        path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        print(path, 'lines', len(data['UnitLines']), 'split', sum(1 for r in report if r[3]))
    shutil.copy2(PER, backup / PER.name)
    PER.write_text(split_per, encoding='utf-8')
    print(PER.name, 'updated')


if __name__ == '__main__':
    main()
