"""Offline guard for the civ technology trees DE shows in the lobby and in game (CivTechTrees).

Why: DE 101.103.54800 (build 185872) resolves civilizations.json ``tech_tree_name`` only against its
native civs. The custom names SWGB_EMPIRE / SWGB_REBELS left both trees empty although their files
were valid; with the native names of the factions' slots (BRITONS, FRANKS) DE loads the data mod's
CivTechTrees/<name>.json. Verified in game on 2026-10-21 (CHANGELOG.md):
  * SWGB_EMPIRE.json with the native Britons content: empty tree, so the content was not the cause;
  * tech_tree_name BRITONS + the mod's BRITONS.json with the SWGB content: full SWGB tree;
  * tech_tree_name FRANKS without a mod FRANKS.json: DE's own Franks tree.

Checks, per non-Gaia civ of SWBG-Logic's civilizations.json:
  1. names: tech_tree_name and data_name are the native names of the civ's slot (pinned below for this
     DE build); CivTechTrees/<tech_tree_name>.json exists with civ_id == tech_tree_name; no other JSON
     in CivTechTrees (a custom name is never loaded, so a stale file there means a wrong name);
  2. schema: top-level keys; node keys among those DE parses; required keys and value types; enum
     values (Node Type, Link Node Type, Draw Node Type, Use Type, Node Status) as in DE's own trees;
     Age ID 1-4; buildings section holds only buildings;
  3. links: a node's Building ID is a building node of the same tree; Link ID is a node of the same
     tree; Building upgraded from ID is -1 or a building node;
  4. icons: Picture Index resolves through widgetui/icons.json (Buildings/Units/Techs by Use Type) to
     a material in materials.json whose atlas or global texture is defined;
  5. DAT: every unit/building node (and each Building ID) is a unit of that civ, every tech node and
     Trigger Tech ID a tech; each node is reachable for that civ (enabled at start, or enabled /
     upgraded to by a tech of that civ or of all civs that the civ's tech tree effect does not
     disable); tech nodes are not restricted to another civ.
With a DE install (--de, default Steam path; skipped when absent, e.g. in CI) it also re-derives the
pinned names, keys and enum values from DE's own civilizations.json and CivTechTrees and fails on any
drift, and runs rules 2-3 on DE's own trees as a self-test of the rules.

  python outputs/toolkit/check_civ_tech_trees.py [--logic payload/SWBG-Logic] [--de DIR] [--no-dat]

The DAT part needs genieutils-py 0.1.2 (pip install genieutils-py==0.1.2).
"""
from __future__ import annotations

import argparse
import json
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[2]
DE_DEFAULT = Path(r'E:\SteamLibrary\steamapps\common\AoE2DE')
DAT = 'resources/_common/dat'

# DE 101.103.54800 (build 185872): (tech_tree_name, data_name) by civ slot, from its civilizations.json.
NATIVE_CIVS = (
    ('GAIA', 'GAIA'), ('BRITONS', 'BRITON-CIV'), ('FRANKS', 'FRANKISH-CIV'), ('GOTHS', 'GOTHIC-CIV'),
    ('TEUTONS', 'TEUTONIC-CIV'), ('JAPANESE', 'JAPANESE-CIV'), ('CHINESE', 'CHINESE-CIV'),
    ('BYZANTINES', 'BYZANTINE-CIV'), ('PERSIANS', 'PERSIAN-CIV'), ('SARACENS', 'SARACEN-CIV'),
    ('TURKS', 'TURKISH-CIV'), ('VIKINGS', 'VIKING-CIV'), ('MONGOLS', 'MONGOL-CIV'), ('CELTS', 'CELTIC-CIV'),
    ('SPANISH', 'SPANISH-CIV'), ('AZTECS', 'AZTEC-CIV'), ('MAYANS', 'MAYAN-CIV'), ('HUNS', 'HUN-CIV'),
    ('KOREANS', 'KOREAN-CIV'), ('ITALIANS', 'ITALIAN-CIV'), ('INDIANS', 'INDIAN-CIV'), ('INCAS', 'INCAN-CIV'),
    ('MAGYAR', 'MAGYAR-CIV'), ('SLAVS', 'SLAVIC-CIV'), ('PORTUGUESE', 'PORTUGUESE-CIV'),
    ('ETHIOPIANS', 'ETHIOPIAN-CIV'), ('MALIANS', 'MALIAN-CIV'), ('BERBERS', 'BERBERS-CIV'),
    ('KHMER', 'KHMER-CIV'), ('MALAY', 'MALAY-CIV'), ('BURMESE', 'BURMESE-CIV'), ('VIETNAMESE', 'VIETNAMESE-CIV'),
    ('BULGARIANS', 'BULGARIANS-CIV'), ('TATARS', 'TATARS-CIV'), ('CUMANS', 'CUMANS-CIV'),
    ('LITHUANIANS', 'LITHUANIANS-CIV'), ('BURGUNDIANS', 'BURGUNDIANS-CIV'), ('SICILIANS', 'SICILIANS-CIV'),
    ('POLES', 'POLES-CIV'), ('BOHEMIANS', 'BOHEMIANS-CIV'), ('DRAVIDIANS', 'DRAVIDIANS-CIV'),
    ('BENGALIS', 'BENGALIS-CIV'), ('GURJARAS', 'GURJARAS-CIV'), ('ROMANS', 'ROMANS-CIV'),
    ('ARMENIANS', 'ARMENIANS-CIV'), ('GEORGIANS', 'GEORGIANS-CIV'), ('ACHAEMENIDS', 'ACHAEMENIDS-CIV'),
    ('ATHENIANS', 'ATHENIANS-CIV'), ('SPARTANS', 'SPARTANS-CIV'), ('SHU', 'SHU-CIV'), ('WU', 'WU-CIV'),
    ('WEI', 'WEI-CIV'), ('JURCHENS', 'JURCHENS-CIV'), ('KHITANS', 'KHITANS-CIV'),
    ('MACEDONIANS', 'MACEDONIANS-CIV'), ('THRACIANS', 'THRACIANS-CIV'), ('PURU', 'PURU-CIV'),
    ('MUISCA', 'MUISCA-CIV'), ('MAPUCHE', 'MAPUCHE-CIV'), ('TUPI', 'TUPI-CIV'), ('SAXONS', 'SAXONS-CIV'),
    ('VARANGIANS', 'VARANGIANS-CIV'), ('DANES', 'DANES-CIV'),
)
TOP_KEYS = ('civ_id', 'civ_techs_buildings', 'civ_techs_units')
# Node keys the DE executable parses (strings next to "CivTechTrees/%s.json") and their JSON types.
NODE_KEYS = {
    'Name': str, 'Node Type': str, 'Link Node Type': str, 'Draw Node Type': str, 'Use Type': str,
    'Node Status': str, 'Picture Node Type': str, 'Name String ID': int, 'Help String ID': int,
    'Age ID': int, 'Building ID': int, 'Building upgraded from ID': int, 'Building in new column': bool,
    'Link ID': int, 'Node ID': int, 'Picture Index': int, 'Trigger Tech ID': int,
    'Prerequisite IDs': list, 'Prerequisite Types': list,
}
# Keys every node of DE's own trees carries.
REQUIRED = ('Name', 'Use Type', 'Node Status', 'Name String ID', 'Help String ID', 'Age ID', 'Building ID',
            'Node ID', 'Picture Index')
# Enum values used by DE's own trees in this build.
ENUMS = {
    'Node Type': {'Unit', 'UnitUpgrade', 'Research', 'BuildingTech', 'BuildingNonTech', 'UniqueUnit',
                  'UniqueTech', 'UniqueBuilding', 'RegionalUnit', 'RegionalTech', 'RegionalBuilding'},
    'Link Node Type': {'Unit', 'UnitUpgrade', 'Research', 'BuildingTech', 'BuildingNonTech', 'UniqueUnit',
                       'UniqueTech', 'RegionalUnit'},
    'Draw Node Type': {'Building', 'UnitTech'},
    'Use Type': {'Unit', 'Tech', 'Building'},
    'Node Status': {'ResearchedCompleted', 'ResearchRequired', 'NotAvailable'},
}
ICON_SET = {'Building': 'Buildings', 'Unit': 'Units', 'Tech': 'Techs'}


def check_tree(name: str, doc, problems: list, strict: bool = True) -> dict:
    """Rules 2-3 on one tree document (problems appended); returns {(Node Type, Node ID): node}."""
    def bad(msg):
        problems.append(f'{name}: {msg}')
    if not isinstance(doc, dict) or tuple(doc) != TOP_KEYS:
        bad(f'top-level keys {list(doc) if isinstance(doc, dict) else type(doc).__name__}, want {list(TOP_KEYS)}')
        return {}
    nodes, index = [], {}
    for section in TOP_KEYS[1:]:
        for n in doc[section]:
            label = f'{section} {n.get("Name")!r} ({n.get("Node ID")})'
            for k, v in n.items():
                if k not in NODE_KEYS:
                    bad(f'{label}: unknown key {k!r}')
                elif type(v) is not NODE_KEYS[k]:
                    bad(f'{label}: {k} is {type(v).__name__}, want {NODE_KEYS[k].__name__}')
            for k in REQUIRED:
                if k not in n:
                    bad(f'{label}: missing {k!r}')
            for k, allowed in ENUMS.items():
                if k in n and n[k] not in allowed:
                    bad(f'{label}: {k} {n[k]!r} not used by DE')
            if not 1 <= n.get('Age ID', 0) <= 4:
                bad(f'{label}: Age ID {n.get("Age ID")}')
            if section == 'civ_techs_buildings' and n.get('Use Type') != 'Building':
                bad(f'{label}: Use Type {n.get("Use Type")!r} in the buildings section')
            for k in ('Prerequisite IDs', 'Prerequisite Types'):
                if k in n and len(n[k]) != 5:
                    bad(f'{label}: {k} has {len(n[k])} entries, want 5')
            nodes.append((label, n))
            index[(n.get('Node Type'), n.get('Node ID'))] = n
    buildings = {n.get('Node ID') for _, n in nodes if n.get('Use Type') == 'Building'
                 and n.get('Node Type') in ('BuildingTech', 'BuildingNonTech', 'UniqueBuilding', 'RegionalBuilding')}
    ids = {n.get('Node ID') for _, n in nodes}
    for label, n in nodes:
        # Strict: a building node. DE's own trees break that only with six Fish Trap nodes (Building ID
        # 13, the Fishing Ship) of Chronicles civs, so the self-test accepts any node of the tree there.
        if n.get('Building ID') not in (buildings if strict else ids):
            bad(f'{label}: Building ID {n.get("Building ID")} is no {"building " if strict else ""}node of this tree')
        # DE's own trees link by ID; their Link Node Type does not always match the target's type.
        if 'Link ID' in n and n['Link ID'] not in ids:
            bad(f'{label}: Link ID {n["Link ID"]} is no node of this tree')
        up = n.get('Building upgraded from ID', -1)
        if up != -1 and up not in buildings:
            bad(f'{label}: Building upgraded from ID {up} is no building node of this tree')
    return index


def check_icons(name: str, doc, icons: dict, materials: dict, problems: list) -> None:
    mats = {m['MaterialDef']['Name']: m['MaterialDef'] for m in materials.get('Materials', [])}
    atlas = {a['AtlasDef']['Name']: {t['RefName'] for t in a['AtlasDef'].get('Textures', [])}
             for a in materials.get('AtlasTextures', [])}
    textures = {t['TextureDef']['Name'] for t in materials.get('GlobalTextures', [])}
    for section in TOP_KEYS[1:]:
        for n in doc[section]:
            label = f'{name}: {section} {n["Name"]!r} ({n["Node ID"]})'
            group = icons.get(ICON_SET.get(n['Use Type'], ''), {})
            ref = group.get(f'{n["Picture Index"]:03d}')
            if ref in (None, '', 'None'):
                problems.append(f'{label}: Picture Index {n["Picture Index"]} has no {ICON_SET.get(n["Use Type"])} icon')
                continue
            m = mats.get(ref)
            if m is None:
                problems.append(f'{label}: icon material {ref!r} not in materials.json')
            elif m.get('Type') == 'Atlas' and m.get('TextureRef') not in atlas.get(m.get('AtlasRef'), ()):
                problems.append(f'{label}: {ref!r} texture {m.get("TextureRef")!r} not in atlas {m.get("AtlasRef")!r}')
            elif m.get('Type') == 'Texture' and m.get('TextureRef') not in textures:
                problems.append(f'{label}: {ref!r} texture {m.get("TextureRef")!r} not defined')


def check_dat(trees: dict, logic: Path, problems: list) -> dict:
    """Rule 5. trees: {civ slot: (file name, doc)}."""
    import reserved_unit_ids as R
    dat = R.parse_raw(zlib.decompress((logic / R.DAT_REL).read_bytes(), -15))
    techs, effects = dat.techs, dat.effects
    gives = {}  # unit id -> [(tech id, tech civ)] that enable it or upgrade a unit to it
    for tid, t in enumerate(techs):
        if 0 <= t.effect_id < len(effects):
            for c in effects[t.effect_id].effect_commands:
                if (c.type == 2 and c.b == 1) or c.type == 3:
                    gives.setdefault(c.a if c.type == 2 else c.b, []).append((tid, t.civ))
    info = {}
    for slot, (name, doc) in trees.items():
        if slot >= len(dat.civs):
            problems.append(f'{name}: civ slot {slot} not in the DAT ({len(dat.civs)} civs)')
            continue
        civ = dat.civs[slot]
        off_units, off_techs = set(), set()
        if 0 <= civ.tech_tree_id < len(effects):
            for c in effects[civ.tech_tree_id].effect_commands:
                if c.type == 2 and c.b == 0:
                    off_units.add(c.a)
                elif c.type == 102:
                    off_techs.add(int(c.d))

        def tech_ok(tid):
            return 0 <= tid < len(techs) and techs[tid].civ in (-1, slot) and tid not in off_techs

        def unit(uid):
            return civ.units[uid] if 0 <= uid < len(civ.units) else None
        count = 0
        for section in TOP_KEYS[1:]:
            for n in doc[section]:
                label = f'{name}: {n["Name"]!r} ({n["Node ID"]})'
                count += 1
                if unit(n['Building ID']) is None:
                    problems.append(f'{label}: Building ID {n["Building ID"]} is no unit of civ {slot}')
                if 'Trigger Tech ID' in n and not tech_ok(n['Trigger Tech ID']):
                    problems.append(f'{label}: Trigger Tech ID {n["Trigger Tech ID"]} not available to civ {slot}')
                nid = n['Node ID']
                if n['Use Type'] == 'Tech':
                    if not (0 <= nid < len(techs)) or not techs[nid].name:
                        problems.append(f'{label}: no such tech in the DAT')
                    elif not tech_ok(nid):
                        problems.append(f'{label}: tech not available to civ {slot} (civ {techs[nid].civ})')
                    continue
                u = unit(nid)
                if u is None:
                    problems.append(f'{label}: no such unit for civ {slot}')
                elif nid in off_units or not (u.enabled or any(tech_ok(t) for t, _ in gives.get(nid, ()))):
                    problems.append(f'{label}: unit never becomes available to civ {slot}')
        info[name] = count
    return info


def check_de(de: Path, problems: list) -> dict:
    """Drift guard against the installed DE and self-test of rules 2-3 on DE's own trees."""
    civs = json.loads((de / DAT / 'civilizations.json').read_text(encoding='utf-8'))['civilization_list']
    native = tuple((c['tech_tree_name'], c['data_name']) for c in civs)
    if native != NATIVE_CIVS:
        problems.append(f'DE civilizations.json differs from NATIVE_CIVS (DE update?): {native}')
    seen = {k: set() for k in ENUMS}
    keys, own = set(), []
    for name, _ in native[1:]:
        p = de / DAT / 'CivTechTrees' / f'{name}.json'
        if not p.is_file():
            problems.append(f'DE has no CivTechTrees/{name}.json')
            continue
        doc = json.loads(p.read_text(encoding='utf-8'))
        for section in TOP_KEYS[1:]:
            for n in doc.get(section, []):
                keys |= set(n)
                for k in ENUMS:
                    if k in n:
                        seen[k].add(n[k])
        check_tree(p.name, doc, own, strict=False)
    if not keys <= set(NODE_KEYS):
        problems.append(f'DE trees use node keys this check does not know: {sorted(keys - set(NODE_KEYS))}')
    for k, values in seen.items():
        if values != ENUMS[k]:
            problems.append(f'DE trees use {k} values {sorted(values)}, pinned {sorted(ENUMS[k])}')
    # DE's own data is the reference: any rule it breaks is too strict (or DE changed).
    problems += [f'self-test on DE data: {p}' for p in own[:20]]
    return {'de_trees': len(native) - 1, 'de_self_test_problems': len(own)}


def check(logic: Path, de: Path | None, dat: bool = True) -> tuple[list[str], dict]:
    problems, info = [], {}
    civs = json.loads((logic / DAT / 'civilizations.json').read_text(encoding='utf-8'))['civilization_list']
    folder = logic / DAT / 'CivTechTrees'
    icons = json.loads((logic / 'widgetui/icons.json').read_text(encoding='utf-8'))
    materials = json.loads((logic / 'widgetui/materials.json').read_text(encoding='utf-8'))
    trees, wanted = {}, set()
    for slot, civ in enumerate(civs):
        tree, data_name = civ.get('tech_tree_name'), civ.get('data_name')
        if slot == 0:
            continue  # Gaia has no tree (DE ships no GAIA.json either)
        if slot >= len(NATIVE_CIVS):
            problems.append(f'civ slot {slot} ({civ["internal_name"]}) has no native DE civ to borrow names from')
            continue
        native_tree, native_data = NATIVE_CIVS[slot]
        if tree != native_tree:
            problems.append(f'{civ["internal_name"]}: tech_tree_name {tree!r} is not DE\'s native {native_tree!r} '
                            f'for slot {slot}; DE renders an empty tree for unknown names')
        if data_name != native_data:
            problems.append(f'{civ["internal_name"]}: data_name {data_name!r} is not DE\'s native {native_data!r}')
        wanted.add(f'{tree}.json')
        p = folder / f'{tree}.json'
        if not p.is_file():
            problems.append(f'{civ["internal_name"]}: CivTechTrees/{tree}.json missing')
            continue
        doc = json.loads(p.read_text(encoding='utf-8'))
        if doc.get('civ_id') != tree:
            problems.append(f'{p.name}: civ_id {doc.get("civ_id")!r}, want {tree!r}')
        before = len(problems)
        check_tree(p.name, doc, problems)
        if len(problems) == before:  # icon and DAT rules need a well-formed tree
            check_icons(p.name, doc, icons, materials, problems)
            trees[slot] = (p.name, doc)
            # DE's panel stops scrolling at a fixed width: important buildings first (tech_tree_order.py).
            import tech_tree_order
            problems.extend(tech_tree_order.problems(doc))
            ids = [b['Node ID'] for b in doc['civ_techs_buildings']]
            missing = [u for u in tech_tree_order.MUST_SHOW if u in ids and ids.index(u) >= len(tech_tree_order.MUST_SHOW)]
            if missing:
                problems.append(f'{p.name}: buildings {missing} may be past the end of the panel')
    stale = sorted(p.name for p in folder.glob('*.json') if p.name not in wanted)
    if stale:
        problems.append(f'CivTechTrees files no civ uses (never loaded by DE): {stale}')
    info['trees'] = {name: len(doc['civ_techs_buildings']) + len(doc['civ_techs_units']) for name, doc in trees.values()}
    if dat:
        check_dat(trees, logic, problems)
        info['dat'] = 'checked'
    if de is not None:
        info.update(check_de(de, problems))
    return problems, info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--logic', type=Path, default=ROOT / 'payload/SWBG-Logic',
                    help='SWBG-Logic (or SWGB-DE-Factions-Draft) folder; default payload/SWBG-Logic')
    ap.add_argument('--de', type=Path, help=f'AoE2 DE install for the drift guard (default {DE_DEFAULT} if present)')
    ap.add_argument('--no-dat', action='store_true', help='skip the DAT part (no genieutils-py)')
    a = ap.parse_args()
    de = a.de or (DE_DEFAULT if (DE_DEFAULT / DAT / 'civilizations.json').is_file() else None)
    problems, info = check(a.logic, de, dat=not a.no_dat)
    for p in problems[:80]:
        print('FAIL', p)
    if len(problems) > 80:
        print(f'... {len(problems) - 80} more')
    if problems:
        sys.exit(f'{len(problems)} tech tree problems')
    print('civ tech trees: OK', json.dumps(info), '' if de else '(no DE install: drift guard skipped)')


if __name__ == '__main__':
    main()
