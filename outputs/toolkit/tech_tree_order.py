"""Order the buildings of the faction tech trees so DE's tree panel shows the important ones.

DE lays the tree out left to right in the order of ``civ_techs_buildings`` and stops scrolling at a
fixed width. With the source order (production, economy, Shipyard, then 17 defense nodes, then
Temple, Fortress and Prefab Shelter) the panel ended at the Shield Generator: the Sith/Jedi Temple
(12 units and technologies), the Fortress (8) and the Prefab Shelter were past the end of the
scroll range in the lobby, for both factions (DE build 185872, 2026-10-22). Each turret and wall
upgrade is drawn in its own column, so the defenses take most of the width.

ORDER puts the production buildings and the Temple and Fortress first, the economy next and the
defenses last (walls at the very end). Upgrade chains keep their parent before the child. Nodes not
in ORDER keep their relative order after it. The node contents are unchanged.

faction_tree_ui.py applies reorder() when it writes the panels. For an assembled SWBG-Logic:
  python outputs/toolkit/tech_tree_order.py                  # payload/ + recipe.tsv re-pin
  python outputs/toolkit/tech_tree_order.py --logic <SWBG-Logic or Draft dir>
It is deterministic and idempotent. check_civ_tech_trees.py checks the order.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[2]
TREES = 'resources/_common/dat/CivTechTrees'
# DE unit IDs of the building nodes (both factions).
ORDER = (
    109,                      # Command Center
    87, 12, 101, 49, 317,     # Troop Center, Power Core, Mech Factory, Heavy Weapons Factory, Airbase
    103, 209, 84,             # War Center, Research Center, Spaceport
    104, 82,                  # Sith/Jedi Temple, Fortress
    68, 50, 562, 323, 584,    # Food Processing Center, Farm, Carbon / Nova / Ore Processing Centers
    319, 70,                  # Animal Nursery, Prefab Shelter
    45, 199, 1576, 7085,      # Shipyard, AquaHarvester, Sensor Buoy, Harbor
    276,                      # Monument
    335, 598,                 # Shield Generator, Sentry Post
    79, 234, 235,             # Light / Medium / Advanced Turret
    236, 196, 1869,           # Anti-Air Turret, Adv Anti-Air Turret, Anti-Air Battery
    5081,                     # Mine
    72, 487, 117, 155, 195,   # Light Wall, Gate, Medium / Heavy / Shield Wall
)
# The panel showed everything up to here in game; the rest may be cut off.
MUST_SHOW = ORDER[:ORDER.index(70) + 1]


def reorder(buildings: list) -> list:
    rank = {uid: i for i, uid in enumerate(ORDER)}
    indexed = list(enumerate(buildings))
    indexed.sort(key=lambda p: (rank.get(p[1]['Node ID'], len(ORDER)), p[0]))
    return [b for _, b in indexed]


def problems(doc: dict) -> list[str]:
    ids = [b['Node ID'] for b in doc['civ_techs_buildings']]
    out = []
    if ids != [b['Node ID'] for b in reorder(doc['civ_techs_buildings'])]:
        out.append(f'{doc.get("civ_id")}: buildings not in tech_tree_order.ORDER')
    pos = {uid: i for i, uid in enumerate(ids)}
    for b in doc['civ_techs_buildings']:
        parent = b.get('Building upgraded from ID', -1)
        if parent in pos and pos[parent] > pos[b['Node ID']]:
            out.append(f'{doc.get("civ_id")}: {b["Name"]} before the building it is upgraded from')
    return out


def dump(obj) -> bytes:
    # Byte format of faction_tree_ui.py (json.dumps(indent=2) written as text on Windows: CRLF).
    return json.dumps(obj, indent=2).replace('\n', '\r\n').encode('utf-8')


def apply(logic: Path, dry: bool = False) -> list[str]:
    log = []
    for path in sorted((logic / TREES).glob('*.json')):
        doc = json.loads(path.read_bytes())
        new = reorder(doc['civ_techs_buildings'])
        if new != doc['civ_techs_buildings']:
            doc['civ_techs_buildings'] = new
            if not dry:
                path.write_bytes(dump(doc))
            log.append(f'{path.name}: buildings reordered')
        else:
            log.append(f'{path.name}: already in order')
    return log


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--payload', type=Path, default=ROOT / 'payload')
    ap.add_argument('--logic', type=Path, help='an assembled SWBG-Logic (or SWGB-DE-Factions-Draft) folder')
    ap.add_argument('--recipe', type=Path, default=ROOT / 'outputs/installer/installer/recipe.tsv')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    log = apply(a.logic or a.payload / 'SWBG-Logic', a.dry_run)
    if not a.logic:
        from remap_reserved_unit_ids import refresh_recipe
        log.append(refresh_recipe(a.payload, a.recipe, a.dry_run))
    print('\n'.join(log))


if __name__ == '__main__':
    main()
