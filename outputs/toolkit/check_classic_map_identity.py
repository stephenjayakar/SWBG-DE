"""Check that the Classic AI gets its map identity (resource 1997) from XS.

DE does not apply the maps' `effect_amount 1 1997 0 N` (probe 2026-10-21, see
classic_ai_map_identity.py). Checks:
- every SWGB Factions map has exactly one identity marker, and identities are unique;
- every copy of swgb_classic_ai.xs carries the identity table generated from those markers
  (map file name -> identity) and the observer calls classicSetMapIdentity right after its
  player check, before the once-per-second early return;
- the three XS copies are identical;
- the AI calls the observer in an unconditional rule that precedes every rule that reads
  resource 1997, so the first rule pass already sees the identity;
- each map identity has at least one source map branch in the AI;
- the Gaia water detection no longer counts the gas-vent type IDs 6482/7091 directly.

  python outputs/toolkit/check_classic_map_identity.py [--root payload/SWBG-Data]
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classic_ai_map_identity import CALL, PLAYER_CHECK, OBSERVE, XS_COPIES, table_from_maps, xs_block

cli = argparse.ArgumentParser()
cli.add_argument('--root', type=Path, default=Path('payload/SWBG-Data'))
args = cli.parse_args()
root = args.root
checks = 0


def check(ok, message):
    global checks
    checks += 1
    if not ok:
        raise SystemExit('FAIL ' + message)


table = table_from_maps(root)
maps = sorted((root / 'resources/_common/random-map-scripts').glob('SWGB Factions *.rms'))
check(len(maps) == 20 and set(table) == {m.stem for m in maps}, f'every SWGB Factions map has an identity: {sorted(table)}')
block = xs_block(table)
texts = []
for rel in XS_COPIES:
    path = root / rel
    check(path.is_file(), 'XS copy present: ' + rel)
    text = path.read_bytes().decode('utf-8').replace('\r\n', '\n')
    texts.append(text)
    check(text.count(block) == 1, 'identity table matches the maps: ' + rel)
    body = text.split(OBSERVE, 1)[1]
    check(body.startswith('    int player = xsGetGoal(104);\n' + PLAYER_CHECK + CALL + '\n'),
          'observer sets the identity before anything else: ' + rel)
check(len(set(texts)) == 1, 'XS copies identical')
for name, identity in table.items():
    check(f'if (name == "{name}") return({identity}.0);' in block, f'{name} -> {identity}')

per = (root / 'resources/_common/ai/SWGB Classic AI.per').read_bytes().decode('utf-8').replace('\r\n', '\n')
observer = per.find('(defrule (true) => (up-get-fact player-number 0 104) (xs-script-call "swgbClassicObserve"))')
first_read = per.find('(up-resource-amount 1997')
check(observer >= 0 and 0 < first_read and observer < first_read, 'observer rule precedes every resource-1997 rule')
check('(include "swgb_classic_ai.xs")' in per, 'AI includes the observer')
check(not re.search(r'unit-type-count[^)]*\b(?:6482|7091)\b', per),
      'no raw gas-vent type counts (DE counts other high IDs there, e.g. palms)')
check(len(re.findall(r'\(cc-players-unit-type-count 0 c[er]-gaia-fish-line >= 30\)', per)) == 6,
      'Gaia water detection keeps its fish-line test (3 Empire, 3 Rebel)')
used = {int(n) for n in re.findall(r'\(up-resource-amount 1997 == (\d+)\)', per)}
missing = sorted(v for v in table.values() if v not in used)
check(not missing, f'every map identity has a source map branch (missing {missing})')
print(f'PASS {checks} checks; {len(table)} maps; identity set from xsGetMapName (runtime verification pending)')
