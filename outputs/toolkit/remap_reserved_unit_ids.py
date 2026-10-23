"""Move SWGB unit IDs out of DE's reserved group-ID range 900-999 (mandatory packaging step).

DE treats object IDs 900-999 as unit-class group IDs. Creating a unit whose ID is in that range
logs "Object Tracker Error: Added object with reserved group id" and corrupts the object tracker
(intermittent crash at AoE2DE_s.exe+0x1356be0). See reserved_unit_ids.py for the design: the
pipeline works in SWGB IDs and this committed table is applied at the DE boundary.

The table, reserved-unit-id-remap.json, is authoritative and is never recomputed implicitly:
900 -> 1431, 901..999 -> 1598..1695 (1621 skipped: unit 5012 has a dangling task reference to it;
929 and 956 are unused). Applying it is idempotent, so it is safe to run on any assembled mod pair:

  python outputs/toolkit/remap_reserved_unit_ids.py                 # payload/ + recipe.tsv hashes
  python outputs/toolkit/remap_reserved_unit_ids.py --logic <SWBG-Logic dir> --data <SWBG-Data dir>
  python outputs/toolkit/remap_reserved_unit_ids.py --extend-table  # only if a new 9xx unit appears

Then run check_reserved_unit_ids.py (package_installer.py and CI run it too).

NOT remapped on purpose (class groups or plain numbers, see reserved_unit_ids.CLASS_GROUP_*):
  * XS xsGetPlayerUnitIds(player, 903/904/911/958) and swgb_factions.xs aircraft categories
    900/913/920: DE class groups.
  * AI pop caps, timers, resource amounts, (defconst *-unit-max N), *-unit-worker-count-line 904
    (villager class), *-rt-*/*-ut-* tech IDs, comment lines.
  * widgetui/icons.json keys (icon IDs) and hotkeys.json (string/hotkey IDs).
  * String IDs derived from SWGB unit IDs (2000993 etc.): the DAT keeps pointing at them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reserved_unit_ids as R  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIRST = 1000  # first candidate slot for --extend-table


def extend_table(dat, table: dict[int, int]) -> dict[int, int]:
    """Give every unit in 900-999 that the table lacks the next free, unreferenced slot >= FIRST."""
    civs = dat.civs
    n = len(civs[0].units)
    missing = sorted({uid for _, uid, _ in R.unit_slots_in_range(dat)} - set(table))
    if not missing:
        return table
    refs = {get() for _, _, get, _ in R.unit_references(dat)}
    used = set(table.values())
    free = [i for i in range(FIRST, n)
            if all(c.units[i] is None for c in civs) and i not in refs and i not in used]
    if len(free) < len(missing):
        sys.exit(f'only {len(free)} free slots for {len(missing)} units')
    out = dict(table)
    out.update(zip(missing, free))
    return out


def refresh_recipe(payload: Path, recipe: Path, dry: bool) -> str:
    """Re-pin `ship` lines of the installer recipe to the payload bytes."""
    nl, tab = '\n', '\t'
    lines = recipe.read_bytes().decode('ascii').split(nl)
    n = 0
    for i, line in enumerate(lines):
        f = line.split(tab)
        if len(f) == 4 and f[0] == 'ship':
            path = payload / f[1] / f[2]
            if path.is_file():
                sha = hashlib.sha256(path.read_bytes()).hexdigest()
                if sha != f[3]:
                    lines[i] = tab.join(f[:3] + [sha])
                    n += 1
    if n and not dry:
        recipe.write_bytes(nl.join(lines).encode('ascii'))
    return f'{recipe.name}: re-pinned {n} ship hashes'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--payload', type=Path, default=ROOT / 'payload',
                    help='folder with SWBG-Logic/ and SWBG-Data/ (default: payload/)')
    ap.add_argument('--logic', type=Path, help='SWBG-Logic (or SWGB-DE-Factions-Draft) folder')
    ap.add_argument('--data', type=Path, help='SWBG-Data (or SWGB-DE-Factions-Assets) folder')
    ap.add_argument('--table', type=Path, default=R.TABLE_PATH)
    ap.add_argument('--recipe', type=Path, default=ROOT / 'outputs/installer/installer/recipe.tsv',
                    help='re-pin its ship hashes (payload mode only)')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--no-dat', action='store_true', help='leave the DAT alone (JSON/text only)')
    ap.add_argument('--extend-table', action='store_true',
                    help='append slots for new units found in 900-999, then apply')
    a = ap.parse_args()
    if bool(a.logic) != bool(a.data):
        ap.error('--logic and --data go together')
    explicit = bool(a.logic)
    logic = a.logic or a.payload / 'SWBG-Logic'
    data = a.data or a.payload / 'SWBG-Data'
    table = R.load_table(a.table)
    if a.extend_table:
        dat = R.parse_raw(zlib.decompress((logic / R.DAT_REL).read_bytes(), -15))
        names = {u.id: u.name for c in dat.civs for u in c.units if u is not None}
        new = extend_table(dat, table)
        added = {k: v for k, v in new.items() if k not in table}
        if added and not a.dry_run:
            doc = json.loads(a.table.read_text(encoding='utf-8'))
            for k, v in added.items():
                doc['remap'][str(k)] = {'new': v, 'name': names.get(k, '')}
            doc['remap'] = dict(sorted(doc['remap'].items(), key=lambda kv: int(kv[0])))
            a.table.write_text(json.dumps(doc, indent=2) + '\n')
            R._load.cache_clear()
        print('table: added', added or 'nothing')
        table = new
    log = R.remap_mod_pair(logic, data, table, dry_run=a.dry_run, dat=not a.no_dat)
    if not explicit:
        log.append(refresh_recipe(a.payload, a.recipe, a.dry_run))
    print('\n'.join(log))
    print(f'{len(table)} table entries ({min(table)}->{table[min(table)]} .. {max(table)}->{table[max(table)]})'
          + (' [dry run]' if a.dry_run else ''))


if __name__ == '__main__':
    main()
