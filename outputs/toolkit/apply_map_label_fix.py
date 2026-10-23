"""Install regenerated SWGB Factions maps (faction_maps.py output) keeping the Classic AI map identity.

faction_maps.py now namespaces SWGB's ARENA/FORTRESS/MIGRATION labels (DE predefines them as
always-true map types), aliases REGICIDE->TERMINATE and LUDIKRIS_MAP->GIGANTIC_MAP, and drops the
Savannah workarounds. port_classic_ai.py (which inserts `effect_amount 1 1997 0 N` into
<PLAYER_SETUP>) cannot currently regenerate, so the identity line is carried over from the
installed copy. Run from the repo root after faction_maps.py.
"""
import hashlib, re, sys
from pathlib import Path

GENERATED = Path('work/faction-package/resources/_common/random-map-scripts')
TARGETS = [Path(r'C:\Users\aj12a\Games\Age of Empires 2 DE\76561198022514833\mods\local\SWGB-DE-Factions-Assets\resources\_common\random-map-scripts'),
           Path('outputs/SWGB-DE-Factions-Draft/resources/_common/random-map-scripts')]
IDENTITY = re.compile(r'/\* Classic AI map identity[^\n]*\*/\neffect_amount 1 1997 0 \d+')


def main():
    installed = TARGETS[0]
    changed = []
    for src in sorted(GENERATED.glob('SWGB Factions *.rms')):
        text = src.read_text(encoding='ascii')
        old = (installed / src.name).read_text(encoding='ascii')
        m = IDENTITY.search(old)
        assert m, ('missing Classic AI identity in installed map', src.name)
        assert text.count('<PLAYER_SETUP>') == 1
        text = text.replace('<PLAYER_SETUP>', '<PLAYER_SETUP>\n' + m[0] + '\n', 1)
        assert not re.search(r'(?:#define|\bif|\belseif)\s+(ARENA|FORTRESS|MIGRATION)\b', text), src.name
        for target in TARGETS:
            if not target.exists():
                continue
            (target / src.name).write_text(text, encoding='ascii', newline='\n')
        changed.append((src.name, hashlib.sha256(text.encode()).hexdigest()[:12]))
    for name, digest in changed:
        print(digest, name)
    print(len(changed), 'maps installed')


if __name__ == '__main__':
    main()
