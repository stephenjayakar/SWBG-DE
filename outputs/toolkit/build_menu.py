"""Worker build menu for the Empire and Rebels: DE's page model, the construction layouts, analysis.

How DE builds a builder's construction pages (DE's own DAT plus in-game probes, 2026-10-21):
  * Interface kind 2 puts a building on the economic page. Every other kind, including SWGB's
    kind 11 (its third, "defensive" page, which DE does not have), lands on the military page.
  * Train-location ButtonID 1-13 is the grid position (QWERT/ASDFG/ZXC). 14 is DE's next-page
    arrow and 15 the cancel button. ButtonID 0 is never shown (native rotated gate variants).
  * One position shows one building: when two available buildings share it, one covers the other
    (Sentry Post covered Troop Center, Shield Generator the Mech Factory, Trip Mine the Temple).
  * DE researches a technology by itself at game start when it needs no prerequisite and has a
    research time of 0, even with a research location and button. Both layout researches were
    like that, so every game started in the defense layout (researched last) and the Command
    Center never offered the switch. They now take 1 second (LAYOUT_RESEARCH_TIME).
  * DE never shows the native Dock IDs 45, 133, 47 and 51 on these maps, on any page or position,
    whatever their data (a full copy of the Troop Center at ID 45 stayed hidden, while the same
    Shipyard data at a free ID showed). SWGB's Shipyard uses exactly those IDs. Like the Fortress
    (1211 -> 82) and the Command Center (621 -> 109), the worker therefore builds a Shipyard
    foundation, SHIPYARD_FOUNDATION, which becomes unit 45 when it is finished. Unit 45 carries
    the player's current Shipyard upgrades, trains the boats and is what the AI builds directly.

The source has 29 buildings a human can build for 26 visible positions (13 economic, 13 military).
So three advanced defenses share positions with three production buildings and are swapped by the
free, repeatable Command Center research "Advanced defense construction layout" (and back with
"Military construction layout"). The switch moves ButtonIDs with effect attribute 43 (Train
Button): the hidden family sits at ButtonID 0. The earlier switch changed attribute 141 (Interface
Kind) between 10 and 11, but DE shows kind 11 on the military page as well.

Layout, both factions (the C++ builder, faction_build_menu.h, mirrors these tables):
  economic page   unchanged source positions 1-13
  military page   1 Troop Center  2 Shipyard (foundation) 3 Light Wall  4 Medium Wall  5 Mech Factory
                  6 Temple        7 Sentry Post    8 Gate           9 Hvy Weapons  10 Airbase
                  11 Light Turret 12 Fortress      13 Anti-Air Turret
  defense layout  2 Anti-Air Battery (missile turret), 5 Shield Generator, 6 Trip Mine
  never shown     Advanced Infantry Center: only SWGB cheat and hidden AI research enable it;
                  the AI still builds it (AI build commands use unit IDs, not buttons). The
                  Shipyard IDs themselves (45, 133, 47, 51 and the Rebel 3586-3589 variants).

fix_build_menu() applies this to a parsed DAT (idempotent). analyse() reports collisions, unknown
pages, unreachable buildings and hotkey mismatches; check_build_menu.py runs it.
"""
from __future__ import annotations

import copy
from collections import defaultdict

WORKER, TRAWLER = 118, 13
BUILDERS = (WORKER, TRAWLER)
ECONOMIC, MILITARY = 2, 10
PAGES = {ECONOMIC: 'economic', MILITARY: 'military'}
VISIBLE = range(1, 14)          # 14 = next page, 15 = cancel
GRID = 'QWERTASDFGZXCVB'
ATTR_TRAIN_BUTTON = 43          # DE attribute list: string 12243 "Train Button"
ATTR_INTERFACE_KIND = 141       # string 12341 "Interface Kind"
FACTIONS = (1, 2)
LAYOUTS = ('SWGB_MILITARY_LAYOUT', 'SWGB_DEFENSE_LAYOUT')
LAYOUT_RESEARCH_TIME = 1        # 0 makes DE research both at game start

SENTRY_SLOT = 7
SENTRY = (598, 3598)            # Sentry Post and the Rebel upgrade
AI_ONLY = (4908,)               # Advanced Infantry Center
DEFENSE_EXTRAS = {1869: 2, 3604: 2, 213: 5, 215: 5, 5081: 6}
DISPLACED_SLOTS = (2, 5, 6)     # Shipyard, Mech Factory, Temple families
DE_HIDDEN = (45, 133, 47, 51)   # native Dock IDs: DE never shows them in a build menu
SHIPYARD = 45
SHIPYARD_FAMILY = (45, 133, 47, 51, 3586, 3587, 3588, 3589)  # upgrades, Rebel Evac Protocols
SHIPYARD_FOUNDATION = 1696      # first free, unreferenced unit slot after the 900-999 remap block
SHIPYARD_FOUNDATION_NAME = 'BLDG-TRAINBOAT-BUILD'


def _worker_location(u):
    locs = [t for t in u.creatable.train_locations if t.unit_id == WORKER]
    if u.type != 80 or len(u.creatable.train_locations) != 1 or len(locs) != 1:
        raise SystemExit(f'unit {u.id} {u.name}: expected a building with one worker train location')
    return locs[0]


def displaced_units(dat) -> dict[int, int]:
    """{unit: military slot} of every worker building family the defense layout hides."""
    out = {}
    for c in FACTIONS:
        for u in dat.civs[c].units:
            if u is None or u.type != 80 or u.creatable is None or u.id in DEFENSE_EXTRAS:
                continue
            if u.interface_kind != MILITARY:
                continue
            for t in u.creatable.train_locations:
                if t.unit_id == WORKER and t.button_id in DISPLACED_SLOTS:
                    _worker_location(u)
                    if out.setdefault(u.id, t.button_id) != t.button_id:
                        raise SystemExit(f'unit {u.id}: different military slots per faction')
    return out


def layout_commands(displaced: dict[int, int], defense: bool):
    from genieutils.effect import EffectCommand
    cmds = [(uid, 0 if defense else slot) for uid, slot in sorted(displaced.items())]
    cmds += [(uid, slot if defense else 0) for uid, slot in sorted(DEFENSE_EXTRAS.items())]
    return [EffectCommand(type=0, a=uid, b=-1, c=ATTR_TRAIN_BUTTON, d=float(button)) for uid, button in cmds]


def _enabling_effect(dat, uid):
    """The single effect that enables `uid` (type 2) and the command index."""
    hits = [(e, i) for e in dat.effects for i, c in enumerate(e.effect_commands)
            if c.type == 2 and c.a == uid and c.b == 1]
    if len(hits) != 1:
        raise SystemExit(f'unit {uid}: expected exactly one enabling effect command, found {len(hits)}')
    return hits[0]


def add_shipyard_foundation(dat, stats) -> None:
    """Unit SHIPYARD_FOUNDATION in every civ: a copy of that civ's Shipyard that becomes unit 45."""
    from genieutils.effect import EffectCommand
    fid = SHIPYARD_FOUNDATION
    for c, civ in enumerate(dat.civs):
        existing = civ.units[fid]
        if existing is not None:
            if existing.name != SHIPYARD_FOUNDATION_NAME or existing.building.stack_unit_id != SHIPYARD:
                raise SystemExit(f'civ {c}: unit {fid} is {existing.name}, not the Shipyard foundation')
            continue
        src = civ.units[SHIPYARD]
        if src is None or src.type != 80:
            raise SystemExit(f'civ {c}: no Shipyard building {SHIPYARD}')
        u = copy.deepcopy(src)
        u.id = u.copy_id = u.base_id = fid
        u.name = SHIPYARD_FOUNDATION_NAME
        u.enabled = 0
        u.hide_in_editor = 1
        u.building.disappears_when_built = 1
        u.building.stack_unit_id = SHIPYARD
        u.building.head_unit = -1
        civ.units[fid] = u
        stats['changed'] += 1
    effect, i = _enabling_effect(dat, SHIPYARD)
    if not any(c.type == 2 and c.a == fid and c.b == 1 for c in effect.effect_commands):
        effect.effect_commands.insert(i + 1, EffectCommand(type=2, a=fid, b=1, c=-1, d=0.0))
        stats['changed'] += 1


def fix_build_menu(dat) -> dict:
    """Give every buildable building its own position; the default state is the military layout."""
    stats = defaultdict(int)
    add_shipyard_foundation(dat, stats)
    for c in FACTIONS:
        units = dat.civs[c].units
        for uid in SHIPYARD_FAMILY:
            loc = _worker_location(units[uid])
            stats['changed'] += loc.button_id != 0
            loc.button_id = 0
    displaced = displaced_units(dat)
    if sorted(set(displaced.values())) != list(DISPLACED_SLOTS):
        raise SystemExit(f'unexpected displaced families: {displaced}')
    for c in FACTIONS:
        units = dat.civs[c].units
        for uid in SENTRY:
            loc = _worker_location(units[uid])
            stats['changed'] += (units[uid].interface_kind, loc.button_id) != (MILITARY, SENTRY_SLOT)
            units[uid].interface_kind, loc.button_id = MILITARY, SENTRY_SLOT
        for uid in AI_ONLY:
            loc = _worker_location(units[uid])
            stats['changed'] += loc.button_id != 0
            loc.button_id = 0
        for uid in DEFENSE_EXTRAS:
            loc = _worker_location(units[uid])
            stats['changed'] += (units[uid].interface_kind, loc.button_id) != (MILITARY, 0)
            units[uid].interface_kind, loc.button_id = MILITARY, 0
    by_name = {t.name: t for t in dat.techs}
    for mode, name in enumerate(LAYOUTS):
        tech = by_name[name]
        effect = dat.effects[tech.effect_id]
        if effect.name != name:
            raise SystemExit(f'{name}: effect {tech.effect_id} is {effect.name}')
        new = layout_commands(displaced, bool(mode))
        stats['changed'] += effect.effect_commands != new
        effect.effect_commands = new
        if len(tech.research_locations) != 1:
            raise SystemExit(f'{name}: expected one research location')
        stats['changed'] += tech.research_locations[0].research_time != LAYOUT_RESEARCH_TIME
        tech.research_locations[0].research_time = LAYOUT_RESEARCH_TIME
    stats['displaced'] = len(displaced)
    return dict(stats)


# ------------------------------------------------------------------------------------- analysis

def _disabled_techs(dat, civ):
    c = dat.civs[civ]
    if c.tech_tree_id < 0:
        return set()
    return {int(e.d) for e in dat.effects[c.tech_tree_id].effect_commands if e.type == 102}


def _tech_ok(dat, ti, civ, disabled):
    return dat.techs[ti].civ in (-1, civ) and ti not in disabled


def _effects(dat, ti):
    eid = dat.techs[ti].effect_id
    return dat.effects[eid].effect_commands if 0 <= eid < len(dat.effects) else []


def _families(dat):
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for e in dat.effects:
        for cmd in e.effect_commands:
            if cmd.type == 3 and cmd.a >= 0 and cmd.b >= 0:
                parent[find(cmd.a)] = find(cmd.b)
    return find


def availability(dat, civ):
    """(potential, human, reached): units the civ can ever get, units and techs a human can reach."""
    disabled = _disabled_techs(dat, civ)
    units = dat.civs[civ].units
    ok = [ti for ti in range(len(dat.techs)) if _tech_ok(dat, ti, civ, disabled)]
    potential = {u.id for u in units if u is not None and u.enabled}
    for ti in ok:
        for cmd in _effects(dat, ti):
            if cmd.type == 2 and cmd.b == 1:
                potential.add(cmd.a)
    changed = True
    while changed:
        changed = False
        for ti in ok:
            for cmd in _effects(dat, ti):
                if cmd.type == 3 and cmd.a in potential and cmd.b not in potential:
                    potential.add(cmd.b)
                    changed = True
    # Human reachability: research needs a visible button (255 = hidden AI research); a tech
    # without any location is researched automatically once its requirements are met, or when a
    # building naming it is completed.
    reached, human = set(), {u.id for u in units if u is not None and u.enabled}
    on_completion = defaultdict(list)  # a building researches its tech_id when it is completed
    for u in units:
        if u is not None and u.type == 80 and u.building is not None and u.building.tech_id >= 0:
            on_completion[u.building.tech_id].append(u.id)
    changed = True
    while changed:
        changed = False
        for ti in ok:
            if ti in reached:
                continue
            t = dat.techs[ti]
            reqs = [r for r in t.required_techs if r >= 0]
            built = any(b in human for b in on_completion.get(ti, ()))  # e.g. MADE-BLDG-* techs
            if not built and sum(r in reached for r in reqs) < t.required_tech_count:
                continue
            locs = [loc for loc in t.research_locations if loc.location_id >= 0]
            if locs and not any(loc.button_id not in (0, 255) for loc in locs):
                continue
            reached.add(ti)
            changed = True
            for cmd in _effects(dat, ti):
                if cmd.type == 2 and cmd.b == 1:
                    human.add(cmd.a)
                elif cmd.type == 3 and cmd.a in human:
                    human.add(cmd.b)
    return potential, human, reached


def layout_states(dat, civ, reached):
    """{state name: {unit: (kind, button)}} for the default state and each layout research."""
    units = dat.civs[civ].units
    base = {}
    for u in units:
        if u is not None and u.type == 80 and u.creatable is not None:
            for t in u.creatable.train_locations:
                if t.unit_id in BUILDERS:
                    base[(u.id, t.unit_id)] = (u.interface_kind, t.button_id, t.hot_key_id)
    states = {'default': base}
    for ti in sorted(reached):
        cmds = [c for c in _effects(dat, ti) if c.type == 0 and c.c in (ATTR_TRAIN_BUTTON, ATTR_INTERFACE_KIND)]
        if not cmds:
            continue
        state = dict(base)
        for cmd in cmds:
            for key, (kind, button, hotkey) in list(state.items()):
                if key[0] == cmd.a:
                    if cmd.c == ATTR_TRAIN_BUTTON:
                        button = int(cmd.d)
                    else:
                        kind = int(cmd.d)
                    state[key] = (kind, button, hotkey)
        states[dat.techs[ti].name] = state
    return states


def page_of(kind):
    return ECONOMIC if kind == ECONOMIC else MILITARY


def analyse(dat, hotkeys: dict | None = None) -> tuple[list[str], dict]:
    problems, report = [], {}
    for ti, t in enumerate(dat.techs):
        if t.required_tech_count == 0 and any(loc.location_id >= 0 and loc.research_time == 0
                                              for loc in t.research_locations):
            problems.append(f'tech {ti} {t.name}: no prerequisite and research time 0, so DE researches it '
                            'at game start instead of offering it')
    family = _families(dat)
    keys = {}
    if hotkeys is not None:
        for group in hotkeys['hotkey_group_list']:
            for entry in group['hotkey_list']:
                for sid in entry.get('string_index_list', []):
                    keys.setdefault(sid, []).append({d['key'] for d in entry.get('defaults_list', [])})
    for civ in FACTIONS:
        cname = dat.civs[civ].name
        units = dat.civs[civ].units
        potential, human, reached = availability(dat, civ)
        states = layout_states(dat, civ, reached)
        shown_any = set()
        civ_report = {}
        for state_name, state in states.items():
            slots = defaultdict(list)
            for (uid, builder), (kind, button, hotkey) in state.items():
                if uid not in potential or button == 0:
                    continue
                name = f'{uid} {units[uid].name}'
                if button not in VISIBLE:
                    problems.append(f'{cname} [{state_name}] {name}: button {button} is not a build position '
                                    '(1-13; 14 = next page, 15 = cancel)')
                    continue
                if kind not in PAGES:
                    problems.append(f'{cname} [{state_name}] {name}: interface kind {kind} has no DE page '
                                    '(DE shows it on the military page)')
                if uid in DE_HIDDEN:
                    problems.append(f'{cname} [{state_name}] {name}: DE never shows native Dock IDs '
                                    f'{DE_HIDDEN}; build it through a foundation')
                slots[(builder, page_of(kind), button)].append(uid)
            menu = {}
            for (builder, page, button), uids in sorted(slots.items()):
                fams = {family(u) for u in uids}
                label = f'{builder}/{PAGES[page]}/{button}'
                if len(fams) > 1:
                    problems.append(f'{cname} [{state_name}] {label}: shared by '
                                    + ', '.join(f'{u} {units[u].name}' for u in sorted(uids)))
                vis = sorted(u for u in uids if u in human)
                shown_any.update((u, builder) for u in vis)
                menu[label] = [f'{u} {units[u].name}' for u in vis]
                for u in vis:
                    hk = state[(u, builder)][2]
                    if hotkeys is None:
                        continue
                    want = GRID[button - 1]
                    found = keys.get(hk)
                    if not found:
                        problems.append(f'{cname} [{state_name}] {u} {units[u].name}: hotkey {hk} not in hotkeys.json')
                    elif any(k != {want} for k in found):
                        problems.append(f'{cname} [{state_name}] {u} {units[u].name}: hotkey {hk} defaults '
                                        f'{sorted(set().union(*found))}, position {button} needs {want}')
            civ_report[state_name] = menu
        # A shown foundation (Shipyard, Fortress, Command Center) provides the building it turns
        # into; a shown upgrade provides its line.
        provided = set()
        for u, builder in shown_any:
            provided.add((family(u), builder))
            stack = units[u].building.stack_unit_id if units[u].building is not None else -1
            if stack >= 0:
                provided.add((family(stack), builder))
        for (uid, builder) in sorted(states['default']):
            if uid in human and (family(uid), builder) not in provided:
                problems.append(f'{cname}: {uid} {units[uid].name} (builder {builder}) can be built by a human '
                                'but is on no build page in any layout')
        if LAYOUTS[0] in states and states[LAYOUTS[0]] != states['default']:
            problems.append(f'{cname}: {LAYOUTS[0]} does not restore the default layout')
        report[cname] = civ_report
    return problems, report
