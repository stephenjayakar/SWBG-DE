"""DE's reserved group-ID range 900-999: the committed SWGB unit-ID remap and its guard.

DE treats object IDs 900-999 as unit-class group IDs (900 + class). Creating a unit whose own ID is
in that range logs "Object Tracker Error: Added object with reserved group id" and corrupts the
object tracker; the result is the intermittent crash at AoE2DE_s.exe+0x1356be0. SWGB used 98 of
those IDs for ordinary units, so every DE-facing file must use the moved IDs instead.

The pipeline keeps working in SWGB (source) IDs: the C++ builder, the source-parity checks and the
work/ intermediates all compare against the SWGB DAT by ID. The move happens at the DE boundary,
with the committed table reserved-unit-id-remap.json (never recomputed implicitly):
  * DAT writers (install_parity_dat.py, package_factions.py) call remap_raw_dat() before compressing;
  * generators that write DE files directly (faction_civs.py, faction_maps.py, faction_astromech.py,
    port_classic_ai.py) call de_unit_id() on unit IDs they emit;
  * remap_reserved_unit_ids.py applies the whole table to an assembled mod pair (idempotent), and
  * check_reserved_unit_ids.py (also run by package_installer.py and CI) fails on any unit or unit
    reference in 900-999.

Values in 900-999 that are DE class groups on purpose (not unit IDs) are listed explicitly in
CLASS_GROUP_* below; the guard accepts nothing else in that range.
"""
from __future__ import annotations

import json
import re
import zlib
from functools import lru_cache
from pathlib import Path

LO, HI = 900, 999
TABLE_PATH = Path(__file__).resolve().with_name('reserved-unit-id-remap.json')
DAT_REL = 'resources/_common/dat/empires2_x2_p1.dat'


def is_reserved(value) -> bool:
    try:
        return LO <= int(value) <= HI
    except (TypeError, ValueError):
        return False


@lru_cache(maxsize=None)
def _load(path: str) -> tuple[tuple[int, int], ...]:
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    pairs = tuple(sorted((int(k), int(v['new'])) for k, v in data['remap'].items()))
    olds = [o for o, _ in pairs]
    news = [n for _, n in pairs]
    assert all(is_reserved(o) for o in olds), 'table keys must be in 900-999'
    assert not any(is_reserved(n) for n in news), 'table targets must be outside 900-999'
    assert len(set(news)) == len(news), 'table targets must be unique'
    assert not set(olds) & set(news)
    return pairs


def load_table(path: Path | str = TABLE_PATH) -> dict[int, int]:
    """{old SWGB unit ID: new DE unit ID} from the committed table."""
    return dict(_load(str(path)))


def de_unit_id(unit_id: int) -> int:
    """SWGB unit ID -> the ID the DE files use. Identity outside the table (idempotent)."""
    return load_table().get(int(unit_id), int(unit_id))


def de_unit_ids(unit_ids) -> list[int]:
    table = load_table()
    return [table.get(int(u), int(u)) for u in unit_ids]


# ---------------------------------------------------------------- DAT model (genieutils-py 0.1.2)
# Effect command types whose A (and B) field is a unit ID. 0/4/5 attribute (B is a class),
# 2 enable/disable, 3 upgrade A->B, 7 spawn A at building B; +10 team and +20 enemy variants.
EFFECT_UNIT_A = {0, 2, 3, 4, 5, 7, 10, 12, 13, 14, 15, 17, 20, 22, 23, 24, 25, 27}
EFFECT_UNIT_B = {3, 7, 13, 17, 23, 27}
EFFECT_ATTRIBUTE = {0, 4, 5, 10, 14, 15, 20, 24, 25}
# Attributes whose value (D) is a unit ID: projectile, train location, trait piece, dead unit,
# secondary projectile, blood unit.
ATTR_UNIT_VALUE = {16, 42, 56, 57, 65, 66}
UNIT_FIELDS = ('id', 'copy_id', 'base_id', 'dead_unit_id', 'blood_unit_id')
BUILDING_FIELDS = ('stack_unit_id', 'head_unit', 'transform_unit', 'pile_unit')
CREATABLE_FIELDS = ('charge_projectile_unit', 'secondary_projectile_unit')


def unit_references(dat):
    """Yield (owner, field, getter, setter) for every DAT field that holds a unit ID.

    One list drives the remap, the reference scan and the guard, so they cannot drift apart.
    Task targets are included: the builder expands SWGB class targets into explicit per-unit tasks
    (faction_classes.h: ClassID=-1, UnitID=member), so a task UnitID is always a unit, never a
    class; DE class targets live in Task.class_id and are never touched.
    """
    def attr(obj, name, where):
        return (where, name, lambda: getattr(obj, name), lambda v: setattr(obj, name, v))

    def item(seq_owner, name, index, where):
        def get():
            return getattr(seq_owner, name)[index]

        def put(v):
            seq = list(getattr(seq_owner, name))
            seq[index] = v
            old = getattr(seq_owner, name)
            setattr(seq_owner, name, tuple(seq) if isinstance(old, tuple) else seq)
        return (where, f'{name}[{index}]', get, put)

    for ci, civ in enumerate(dat.civs):
        for u in civ.units:
            if u is None:
                continue
            w = f'civ{ci}/unit{u.id}'
            for f in UNIT_FIELDS:
                yield attr(u, f, w)
            if u.dead_fish:
                yield attr(u.dead_fish, 'tracking_unit', w)
            if u.bird:
                for i in range(len(u.bird.drop_sites)):
                    yield item(u.bird, 'drop_sites', i, w)
                for t in u.bird.tasks:
                    yield attr(t, 'unit_id', w + '/task')
            if u.type_50:
                yield attr(u.type_50, 'projectile_unit_id', w)
            if u.creatable:
                for tl in u.creatable.train_locations:
                    yield attr(tl, 'unit_id', w + '/train_location')
                for f in CREATABLE_FIELDS:
                    yield attr(u.creatable, f, w)
            if u.building:
                for f in BUILDING_FIELDS:
                    yield attr(u.building, f, w)
                for an in u.building.annexes:
                    yield attr(an, 'unit_id', w + '/annex')
    for hi, h in enumerate(dat.unit_headers):
        if h.exists and h.task_list:
            for t in h.task_list:
                yield attr(t, 'unit_id', f'unit_header{hi}/task')
    for ti, tech in enumerate(dat.techs):
        for rl in tech.research_locations:
            yield attr(rl, 'location_id', f'tech{ti}')
    for ei, eff in enumerate(dat.effects):
        for cmd in eff.effect_commands:
            w = f'effect{ei}/type{cmd.type}'
            if cmd.type in EFFECT_UNIT_A:
                yield attr(cmd, 'a', w)
            if cmd.type in EFFECT_UNIT_B:
                yield attr(cmd, 'b', w)
            if cmd.type in EFFECT_ATTRIBUTE and cmd.c in ATTR_UNIT_VALUE and float(cmd.d).is_integer():
                yield (w, f'd(attr {cmd.c})', lambda cmd=cmd: int(cmd.d),
                       lambda v, cmd=cmd: setattr(cmd, 'd', float(v)))
    tt = dat.tech_tree
    if tt is not None:
        groups = [('age', age, ('buildings', 'units')) for age in tt.tech_tree_ages]
        groups += [('building', bc, ('buildings', 'units')) for bc in tt.building_connections]
        groups += [('unit', uc, ('units',)) for uc in tt.unit_connections]
        groups += [('research', rc, ('buildings', 'units')) for rc in tt.research_connections]
        for kind, node, lists in groups:
            w = f'tech_tree/{kind}'
            if kind in ('building', 'unit'):
                yield attr(node, 'id', w)
            if kind in ('unit', 'research'):
                yield attr(node, 'upper_building', w)
            for name in lists:
                for i in range(len(getattr(node, name))):
                    yield item(node, name, i, w)
            c = node.common
            for i, mode in enumerate(c.mode):
                if mode in (1, 2):  # 1 building, 2 unit (0 age, 3 research)
                    yield item(c, 'unit_research', i, w + '/common')
    for mi in list(dat.random_maps.map_info_1) + list(dat.random_maps.map_info_2):
        for mu in mi.map_units:
            yield attr(mu, 'unit', 'random_maps')
    for ti, terr in enumerate(dat.terrain_block.terrains):
        for i in range(len(terr.terrain_unit_id)):
            yield item(terr, 'terrain_unit_id', i, f'terrain{ti}')


def unit_slots_in_range(dat) -> list[tuple[int, int, str]]:
    return [(ci, u.id, u.name) for ci, c in enumerate(dat.civs) for u in c.units
            if u is not None and is_reserved(u.id)]


def remap_dat(dat, table: dict[int, int]) -> dict:
    """Move unit slots and rewrite every unit reference with the committed table. Idempotent."""
    stats = {'slots': 0, 'refs': 0}
    moving = {old: new for old, new in table.items() if any(c.units[old] is not None for c in dat.civs)}
    if moving:
        # A reference that already points at a target slot would silently start naming the moved
        # unit (this is why 1621 is skipped: unit 5012 has a dangling task reference to it).
        targets = set(moving.values())
        for where, field, get, _ in unit_references(dat):
            if get() in targets:
                raise SystemExit(f'{where}.{field} already references target slot {get()}; fix the table')
    for ci, civ in enumerate(dat.civs):
        units = list(civ.units)
        for old, new in table.items():
            if units[old] is None:
                continue
            if units[new] is not None:
                raise SystemExit(f'civ{ci}: target slot {new} for {old} is already used by {units[new].name}')
            units[new], units[old] = units[old], None
            stats['slots'] += 1
        civ.units = units
    # Unit headers are indexed by unit ID too and move with their unit. The header at the target
    # index belongs to an SWGB unit of a civ this dataset does not carry; it is swapped into the
    # vacated index so the file keeps every record (and its size).
    uh = list(dat.unit_headers)
    for old, new in moving.items():
        uh[new], uh[old] = uh[old], uh[new]
    dat.unit_headers = uh
    for where, field, get, put in unit_references(dat):
        v = get()
        if v in table:
            put(table[v])
            stats['refs'] += 1
    return stats


def parse_raw(raw: bytes):
    from genieutils.common import ByteHandler
    from genieutils.datfile import DatFile
    return DatFile.from_bytes(ByteHandler(memoryview(raw)))


def compress_dat(raw: bytes) -> bytes:
    """Same raw-deflate settings as package_factions.py / install_parity_dat.py."""
    c = zlib.compressobj(9, zlib.DEFLATED, -15)
    data = c.compress(raw) + c.flush()
    assert zlib.decompress(data, -15) == raw
    return data


def remap_raw_dat(raw: bytes, table: dict[int, int] | None = None) -> tuple[bytes, dict]:
    """Apply the committed table to an uncompressed DAT. Returns (raw, stats).

    The genieutils-py serializer is checked byte-exact on the input first, so nothing but the
    remapped fields can change.
    """
    table = load_table() if table is None else table
    dat = parse_raw(raw)
    if dat.to_bytes() != raw:
        raise SystemExit('genieutils-py does not round-trip this DAT byte-exactly; refusing to rewrite it')
    unknown = sorted({uid for _, uid, _ in unit_slots_in_range(dat)} - set(table))
    if unknown:
        raise SystemExit(f'units {unknown} are in the reserved range 900-999 but not in {TABLE_PATH.name}; '
                         'extend the table (remap_reserved_unit_ids.py --extend-table) and commit it')
    stats = remap_dat(dat, table)
    out = dat.to_bytes()
    assert len(out) == len(raw), 'remap must not change the DAT size'
    return out, stats


# ---------------------------------------------------------------------- text and JSON files
RMS_CONST = re.compile(r'^(\s*#const\s+\S+\s+)(-?\d+)(.*)$')
PER_CONST = re.compile(r'^(\s*\(defconst\s+(\S+)\s+)(-?\d+)(\).*)$')
XS_ID_COMPARE = re.compile(r'((?:objectId|id|unitType|headType|copyId|protoId)\s*[!=]=\s*)(\d+)')
# Classic AI constants are "<ce-|cr-><symbol>"; these symbol prefixes name units or buildings.
PER_UNIT_PREFIXES = ('unit-', 'boat-', 'bldg-', 'siege-', 'gaia-', 'uu-', 'sub-', 'troop-')
# Plain numbers that merely share a unit-like prefix.
PER_NOT_UNITS = {'boat-strategy', 'siege-available', 'siege-rating', 'troop-upgrades'}
TECH_NODE_TYPES = ('Research', 'Tech', 'Age', 'ResearchTech')

# Deliberate DE class groups (900 + class) in the shipped files. Nothing else in 900-999 passes.
CLASS_GROUP_PER = {'unit-worker-count-line': 904}  # classic_ai_de_lines.VILLAGER_CLASS
CLASS_GROUP_XS_CALL = re.compile(r'xsGetPlayerUnitIds\(\s*\w+\s*,\s*(\d+)\s*,')
CLASS_GROUP_XS_ASSIGN = re.compile(r'\bcategory\s*=\s*(\d+)\s*;')  # swgb_factions.xs aircraft classes


def per_symbol(name: str) -> str:
    low = name.lower()
    for prefix in ('ce-', 'cr-'):
        if low.startswith(prefix):
            return low[len(prefix):]
    return low


def per_is_unit_const(name: str) -> bool:
    sym = per_symbol(name)
    if sym in CLASS_GROUP_PER or sym in PER_NOT_UNITS:
        return False
    return sym.startswith(PER_UNIT_PREFIXES) and not sym.endswith(('-line', '-max', '-count'))


def _lines(text):
    return text.split('\n')


def remap_rms(text: str, table: dict[int, int]) -> tuple[str, int]:
    """#const values are object IDs once faction_maps.py has translated the terrain constants."""
    out, n = [], 0
    for line in _lines(text):
        body, cr = (line[:-1], '\r') if line.endswith('\r') else (line, '')
        m = RMS_CONST.match(body)
        if m and int(m.group(2)) in table:
            body = m.group(1) + str(table[int(m.group(2))]) + m.group(3)
            n += 1
        out.append(body + cr)
    return '\n'.join(out), n


def remap_per(text: str, table: dict[int, int]) -> tuple[str, int]:
    out, n = [], 0
    for line in _lines(text):
        m = PER_CONST.match(line)
        if m and per_is_unit_const(m.group(2)) and int(m.group(3)) in table:
            line = m.group(1) + str(table[int(m.group(3))]) + m.group(4)
            n += 1
        out.append(line)
    return '\n'.join(out), n


def remap_xs(text: str, table: dict[int, int]) -> tuple[str, int]:
    n = 0

    def sub(mo):
        nonlocal n
        v = int(mo.group(2))
        if v in table:
            n += 1
            return mo.group(1) + str(table[v])
        return mo.group(0)
    return XS_ID_COMPARE.sub(sub, text), n


def remap_unitlines(obj, table) -> int:
    n = 0
    for line in obj['UnitLines']:
        chain = line.get('IDChain', [])
        new = [table.get(v, v) for v in chain]
        n += sum(a != b for a, b in zip(chain, new))
        line['IDChain'] = new
    return n


def remap_civilizations(obj, table) -> int:
    n = 0
    for civ in obj['civilization_list']:
        for k in ('unique_unit_id', 'elite_unique_unit_id'):
            if civ.get(k) in table:
                civ[k] = table[civ[k]]
                n += 1
    return n


def remap_civtechtree(obj, table) -> int:
    n = 0
    for nodes in obj.values():
        if not isinstance(nodes, list):
            continue
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get('Node Type') not in TECH_NODE_TYPES and node.get('Node ID') in table:
                node['Node ID'] = table[node['Node ID']]
                n += 1
            if node.get('Link Node Type') not in TECH_NODE_TYPES + (None,) and node.get('Link ID') in table:
                node['Link ID'] = table[node['Link ID']]
                n += 1
            for k in ('Building ID', 'Building upgraded from ID'):
                if node.get(k) in table:
                    node[k] = table[node[k]]
                    n += 1
    return n


def dump_json_like(raw: str, obj) -> str:
    """Re-serialise with the file's own indent and newline style."""
    indent = 2
    m = re.search(r'\n( +)\S', raw)
    if m:
        indent = len(m.group(1))
    text = json.dumps(obj, indent=indent, ensure_ascii=False)
    if raw.endswith('\n'):
        text += '\n'
    if '\r\n' in raw:
        text = text.replace('\n', '\r\n')
    return text


# ------------------------------------------------------------------------------- mod layout
LOGIC_JSON = {
    'resources/_common/dat/unitlines.json': remap_unitlines,
    'resources/_common/dat/civilizations.json': remap_civilizations,
    'resources/_common/dat/CivTechTrees/*.json': remap_civtechtree,
}


def data_text_files(data_root: Path):
    common = data_root / 'resources/_common'
    files = [(p, 'rms') for p in sorted((common / 'random-map-scripts').glob('*.rms'))]
    files += [(p, 'per') for p in sorted((common / 'ai').rglob('*.per'))]
    files += [(p, 'per') for p in sorted(common.rglob('*.per2'))]
    files += [(p, 'xs') for p in sorted(common.rglob('*.xs'))]
    return files


TEXT_REMAP = {'rms': remap_rms, 'per': remap_per, 'xs': remap_xs}


def remap_mod_pair(logic: Path, data: Path, table=None, dry_run=False, dat=True) -> list[str]:
    """Apply the table to an assembled SWBG-Logic/SWBG-Data pair (payload, package or install)."""
    table = load_table() if table is None else table
    log = []
    if dat:
        path = logic / DAT_REL
        compressed = path.read_bytes()
        raw = zlib.decompress(compressed, -15)
        new_raw, stats = remap_raw_dat(raw, table)
        log.append(f'{path.name}: moved {stats["slots"]} unit slots, rewrote {stats["refs"]} references')
        if not dry_run and (new_raw != raw or compressed != compress_dat(raw)):
            path.write_bytes(compress_dat(new_raw))
    for pattern, fn in LOGIC_JSON.items():
        for p in sorted(logic.glob(pattern)):
            raw = p.read_bytes().decode('utf-8')
            obj = json.loads(raw)
            n = fn(obj, table)
            log.append(f'{p.relative_to(logic).as_posix()}: {n} refs')
            if n and not dry_run:
                p.write_bytes(dump_json_like(raw, obj).encode('utf-8'))
    total = 0
    for p, kind in data_text_files(data):
        raw = p.read_bytes().decode('latin-1')
        text, n = TEXT_REMAP[kind](raw, table)
        if n:
            total += n
            log.append(f'{p.relative_to(data).as_posix()}: {n} refs')
            if not dry_run:
                p.write_bytes(text.encode('latin-1'))
    log.append(f'text files: {total} refs')
    return log


# ------------------------------------------------------------------------------------- guard
def scan_dat(dat) -> tuple[list[str], set[int]]:
    """Violations in a parsed DAT, plus the set of unit IDs present in any civ."""
    problems = [f'civ{ci}: unit {uid} {name} occupies reserved slot'
                for ci, uid, name in unit_slots_in_range(dat)]
    seen = {}
    for where, field, get, _ in unit_references(dat):
        v = get()
        if is_reserved(v):
            key = (re.sub(r'\d+', 'N', where), field, v)
            seen.setdefault(key, f'{where}.{field} = {v}')
    problems += [f'{example} (reserved group ID used as unit reference)' for example in seen.values()]
    present = {u.id for c in dat.civs for u in c.units if u is not None}
    return problems, present


def scan_mod_pair(logic: Path, data: Path, present: set[int] | None = None) -> list[str]:
    """Violations in the JSON/AI/RMS/XS files. With `present`, also flag dangling unit IDs."""
    problems = []

    def bad(v):
        return is_reserved(v) or (present is not None and isinstance(v, int) and v >= 0 and v not in present)

    def why(v):
        return 'reserved 900-999' if is_reserved(v) else 'no such unit in the DAT'

    def j(rel):
        p = logic / rel
        return json.loads(p.read_text(encoding='utf-8')) if p.is_file() else None

    lines = j('resources/_common/dat/unitlines.json')
    for line in (lines or {}).get('UnitLines', []):
        for v in line.get('IDChain', []):
            if bad(v):
                problems.append(f'unitlines.json {line.get("Identifier")}: {v} ({why(v)})')
    civs = j('resources/_common/dat/civilizations.json')
    for civ in (civs or {}).get('civilization_list', []):
        for k in ('unique_unit_id', 'elite_unique_unit_id'):
            if k in civ and civ[k] != -1 and bad(civ[k]):
                problems.append(f'civilizations.json {civ["internal_name"]}.{k}: {civ[k]} ({why(civ[k])})')
    for p in sorted((logic / 'resources/_common/dat/CivTechTrees').glob('*.json')):
        obj = json.loads(p.read_text(encoding='utf-8'))
        for nodes in obj.values():
            for node in nodes if isinstance(nodes, list) else []:
                if not isinstance(node, dict):
                    continue
                checks = [(k, node.get(k)) for k in ('Building ID', 'Building upgraded from ID')]
                if node.get('Node Type') not in TECH_NODE_TYPES:
                    checks.append(('Node ID', node.get('Node ID')))
                if node.get('Link Node Type') not in TECH_NODE_TYPES + (None,):
                    checks.append(('Link ID', node.get('Link ID')))
                for k, v in checks:
                    if isinstance(v, int) and v != -1 and bad(v):
                        problems.append(f'{p.name} {node.get("Name")}: {k} {v} ({why(v)})')
    drops = j('resources/_common/dat/dropsites.json')
    for site in (drops or {}).get('drop_site_list', []):
        if bad(site['building_id']):
            problems.append(f'dropsites.json {site["name"]}: {site["building_id"]} ({why(site["building_id"])})')
    res = j('resources/_common/dat/airesourcetypes.json')
    for group in (res or {}).get('ResourceTypes', []):
        for t in group['Types']:
            if is_reserved(t['ID']):
                problems.append(f'airesourcetypes.json {t["Name"]}: {t["ID"]} (reserved 900-999)')
    for p, kind in data_text_files(data):
        text = p.read_bytes().decode('latin-1')
        rel = p.relative_to(data).as_posix()
        for no, line in enumerate(_lines(text), 1):
            if kind == 'rms':
                code = re.sub(r'/\*.*?\*/', '', line)
                m = RMS_CONST.match(code.rstrip('\r'))
                if m and is_reserved(m.group(2)):
                    problems.append(f'{rel}:{no}: {code.strip()} (reserved 900-999)')
                for v in re.findall(r'\bcreate_object\s+(\d+)', code):
                    if is_reserved(v):
                        problems.append(f'{rel}:{no}: create_object {v} (reserved 900-999)')
            elif kind == 'per':
                code = line.split(';', 1)[0]
                m = PER_CONST.match(code)
                if m:
                    name, v = m.group(2), int(m.group(3))
                    sym = per_symbol(name)
                    if sym in CLASS_GROUP_PER:
                        if v != CLASS_GROUP_PER[sym] and bad(v):
                            problems.append(f'{rel}:{no}: {name} {v} ({why(v)})')
                    elif per_is_unit_const(name) and v >= 0 and bad(v):
                        problems.append(f'{rel}:{no}: {name} {v} ({why(v)})')
                    continue
                for v in re.findall(r'\((?:train|can-train|build|can-build|build-forward|can-build-gate|'
                                    r'can-train-with-escrow|can-build-with-escrow|unit-type-count|'
                                    r'unit-type-count-total|building-type-count|building-type-count-total|'
                                    r'unit-available|building-available)\s+(\d+)', code):
                    if is_reserved(v):
                        problems.append(f'{rel}:{no}: literal unit {v} (reserved 900-999)')
                for v in re.findall(r'\(up-[\w-]+\s+c:\s+(\d+)', code):
                    if is_reserved(v):
                        problems.append(f'{rel}:{no}: literal object/class {v} in an up- command (review)')
            else:
                code = line.split('//', 1)[0]
                allowed = {m.start(1) for m in CLASS_GROUP_XS_CALL.finditer(code)}
                allowed |= {m.start(1) for m in CLASS_GROUP_XS_ASSIGN.finditer(code)}
                for m in re.finditer(r'(?<![\w.])(\d{3})(?![\w.])', code):
                    if is_reserved(m.group(1)) and m.start(1) not in allowed:
                        problems.append(f'{rel}:{no}: literal {m.group(1)} ({code.strip()[:80]})')
    return problems
