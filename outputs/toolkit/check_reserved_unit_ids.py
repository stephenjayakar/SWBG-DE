"""Guard: no unit and no unit reference in DE's reserved group-ID range 900-999.

DE reads object IDs 900-999 as class groups; a real unit there corrupts the object tracker and
crashes the game (AoE2DE_s.exe+0x1356be0, see reserved_unit_ids.py). This check fails on:
  * any unit slot in 900-999 in any civ of the DAT;
  * any DAT unit reference in 900-999 (unit/copy/base/dead/blood IDs, tracking/projectile/
    stack/head/transform/pile/annex units, drop sites, train locations, task targets, effects,
    research locations, tech tree, random-map and terrain units);
  * any 900-999 unit ID in unitlines.json, civilizations.json, CivTechTrees, dropsites.json,
    airesourcetypes.json, the AI scripts, the RMS #const tables and the XS scripts, except the
    explicit class-group uses listed in reserved_unit_ids.CLASS_GROUP_*;
  * with the DAT, any JSON/AI unit ID that names no unit at all (e.g. an old ID left behind).

  python outputs/toolkit/check_reserved_unit_ids.py [--payload payload] [--logic DIR --data DIR] [--no-dat]

Needs genieutils-py 0.1.2 for the DAT part (pip install genieutils-py==0.1.2).
"""
from __future__ import annotations

import argparse
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reserved_unit_ids as R  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def check(logic: Path, data: Path, dat: bool = True) -> tuple[list[str], dict]:
    problems, info, present = [], {}, None
    if dat:
        raw = zlib.decompress((logic / R.DAT_REL).read_bytes(), -15)
        parsed = R.parse_raw(raw)
        dat_problems, present = R.scan_dat(parsed)
        problems += dat_problems
        table = R.load_table()
        info['units'] = len(present)
        info['table_targets_present'] = sum(v in present for v in table.values())
        info['table_sources_present'] = sum(k in present for k in table)
    problems += R.scan_mod_pair(logic, data, present)
    return problems, info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--payload', type=Path, default=ROOT / 'payload')
    ap.add_argument('--logic', type=Path)
    ap.add_argument('--data', type=Path)
    ap.add_argument('--no-dat', action='store_true', help='skip the DAT (text/JSON only, no genieutils-py)')
    a = ap.parse_args()
    if bool(a.logic) != bool(a.data):
        ap.error('--logic and --data go together')
    logic = a.logic or a.payload / 'SWBG-Logic'
    data = a.data or a.payload / 'SWBG-Data'
    problems, info = check(logic, data, dat=not a.no_dat)
    for p in problems[:60]:
        print('FAIL', p)
    if len(problems) > 60:
        print(f'... {len(problems) - 60} more')
    if problems:
        sys.exit(f'{len(problems)} reserved/dangling unit-ID problems; run remap_reserved_unit_ids.py')
    print('reserved unit IDs: OK', info or '(DAT not checked)')


if __name__ == '__main__':
    main()
