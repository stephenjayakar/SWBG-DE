"""Apply classic_ai_de_lines to the installed/staged Draft unitlines.json and the installed Classic AI.

Run from the repo root. Idempotent. Backs up originals under work/parity-backups/.
"""
import json, shutil, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import classic_ai_de_lines as L

LOCAL = Path(r'C:\Users\aj12a\Games\Age of Empires 2 DE\76561198022514833\mods\local')
UNITLINES = [LOCAL / 'SWGB-DE-Factions-Draft/resources/_common/dat/unitlines.json',
             Path('outputs/SWGB-DE-Factions-Draft/resources/_common/dat/unitlines.json')]
PER = LOCAL / 'SWGB-DE-Factions-Assets/resources/_common/ai/SWGB Classic AI.per'


def main():
    backup = Path('work/parity-backups') / (time.strftime('%Y%m%d-%H%M%S') + '-ailines')
    backup.mkdir(parents=True, exist_ok=True)
    for path in UNITLINES:
        if not path.exists():
            continue
        shutil.copy2(path, backup / (path.parent.parent.parent.parent.name + '-unitlines.json'))
        data, dropped = L.clean_unitlines(json.loads(path.read_text(encoding='utf-8')))
        path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        print(path, 'dropped', dropped, 'kept', len(data['UnitLines']))
    shutil.copy2(PER, backup / PER.name)
    text, counts = L.rewrite_per(PER.read_text(encoding='utf-8'))
    PER.write_text(text, encoding='utf-8')
    print(PER.name, counts)


if __name__ == '__main__':
    main()
