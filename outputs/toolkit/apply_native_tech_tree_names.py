"""Give the factions DE-native tech tree names (fixes the empty lobby and in-game technology trees).

DE 101.103.54800 (build 185872) resolves civilizations.json ``tech_tree_name`` only against its own
civs. With the custom names SWGB_EMPIRE / SWGB_REBELS both trees rendered empty, although the files
were present and valid; with a native name DE loads the data mod's CivTechTrees/<name>.json (verified
in game 2026-10-21, see CHANGELOG.md). faction_civs.FACTIONS holds the names (BRITONS / FRANKS, the
native civs of slots 1 and 2, like ``data_name``); faction_tree_ui.py writes new panels under them.

This script applies the rename to an already assembled SWBG-Logic, so an integrator can re-apply it
to any copy without regenerating from work/. It is deterministic and idempotent:
  * CivTechTrees/<legacy>.json -> CivTechTrees/<native>.json with ``civ_id`` set to the native name
    (all other bytes as faction_tree_ui.py writes them: json.dumps(indent=2), CRLF);
  * civilizations.json ``tech_tree_name`` of each faction (internal_name match), same formatting;
  * in payload mode, recipe.tsv ``ship`` rows follow the rename and are re-pinned to the payload.

  python outputs/toolkit/apply_native_tech_tree_names.py                  # payload/ + recipe.tsv
  python outputs/toolkit/apply_native_tech_tree_names.py --logic <SWBG-Logic or Draft dir>

Then run check_civ_tech_trees.py.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from faction_civs import FACTIONS  # noqa: E402
from remap_reserved_unit_ids import refresh_recipe  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DAT = 'resources/_common/dat'


def dump(obj) -> bytes:
    # Byte format of the generators' Path.write_text(json.dumps(..., indent=2)) on Windows.
    return json.dumps(obj, indent=2).replace('\n', '\r\n').encode('utf-8')


def apply(logic: Path, dry: bool = False) -> list[str]:
    log, trees = [], logic / DAT / 'CivTechTrees'
    for f in FACTIONS:
        old, new = trees / f"{f['legacy_tech_tree']}.json", trees / f"{f['tech_tree']}.json"
        if old.is_file():
            if new.is_file():
                sys.exit(f'both {old.name} and {new.name} exist in {trees}; remove the stale one by hand')
            doc = json.loads(old.read_bytes())
            assert doc.get('civ_id') == f['legacy_tech_tree'], (old, doc.get('civ_id'))
            doc['civ_id'] = f['tech_tree']
            if not dry:
                new.write_bytes(dump(doc))
                old.unlink()
            log.append(f'{old.name} -> {new.name} (civ_id {f["tech_tree"]})')
        elif new.is_file():
            doc = json.loads(new.read_bytes())
            assert doc.get('civ_id') == f['tech_tree'], (new, doc.get('civ_id'))
            log.append(f'{new.name}: already native')
        else:
            sys.exit(f'no tech tree file for {f["internal"]} in {trees}')
    path = logic / DAT / 'civilizations.json'
    civs = json.loads(path.read_bytes())
    names = {f['internal']: f['tech_tree'] for f in FACTIONS}
    changed = 0
    for civ in civs['civilization_list']:
        want = names.get(civ['internal_name'])
        if want and civ['tech_tree_name'] != want:
            civ['tech_tree_name'] = want
            changed += 1
    assert {c['internal_name'] for c in civs['civilization_list']} >= set(names), 'faction missing from civilizations.json'
    if changed and not dry:
        path.write_bytes(dump(civs))
    log.append(f'civilizations.json: {changed} tech_tree_name values changed')
    return log


def rename_recipe(recipe: Path, mod: str, dry: bool) -> str:
    nl, tab = '\n', '\t'
    lines = recipe.read_bytes().decode('ascii').split(nl)
    moves = {f'{DAT}/CivTechTrees/{f["legacy_tech_tree"]}.json': f'{DAT}/CivTechTrees/{f["tech_tree"]}.json' for f in FACTIONS}
    n = 0
    for i, line in enumerate(lines):
        f = line.split(tab)
        if len(f) == 4 and f[0] == 'ship' and f[1] == mod and f[2] in moves:
            lines[i] = tab.join([f[0], f[1], moves[f[2]], f[3]])
            n += 1
    if n and not dry:
        recipe.write_bytes(nl.join(lines).encode('ascii'))
    return f'{recipe.name}: renamed {n} ship rows'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--payload', type=Path, default=ROOT / 'payload')
    ap.add_argument('--logic', type=Path, help='an assembled SWBG-Logic (or SWGB-DE-Factions-Draft) folder')
    ap.add_argument('--recipe', type=Path, default=ROOT / 'outputs/installer/installer/recipe.tsv',
                    help='renamed and re-pinned in payload mode')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    logic = a.logic or a.payload / 'SWBG-Logic'
    log = apply(logic, a.dry_run)
    if not a.logic:
        log.append(rename_recipe(a.recipe, 'SWBG-Logic', a.dry_run))
        log.append(refresh_recipe(a.payload, a.recipe, a.dry_run))
    print('\n'.join(log) + (' [dry run]' if a.dry_run else ''))


if __name__ == '__main__':
    main()
