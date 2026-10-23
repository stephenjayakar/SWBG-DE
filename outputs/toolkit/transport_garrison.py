"""Make SWGB transports loadable in DE: class-targeted garrison tasks (mandatory DAT step).

Symptom: troops walk up to an Assault Mech, Transport Mech or Air Transport and stop; nothing
boards (Alt+right-click neither), so no Unload button ever appears. Garrisoning buildings works.

Cause: DE matches garrison (action 3) tasks against the target's class only. Every native DE
garrison task is class-targeted (Transport Ship class 20, buildings 3, rams/Siege Tower 13);
none uses UnitID. The C++ builder (faction_classes.h translateTasks) keeps source membership on
DE class collisions by expanding SWGB class-targeted tasks into one task per member unit
(ClassID -1, UnitID n). SWGB transports land in colliding DE classes (naval 17 + air 59 -> 20,
mechs 53 -> 13, gunships/shuttles 48 -> 0, AT-AT swimmer -> 22), so every boarding task became
per-unit and DE ignores all of them (1,150,038 redundant tasks across the three civs in the
1.6/1.7 DAT), most also with SWGB's TargetDiplomacy 0 (DE garrison tasks use 1 or 4). In game (Oct 2026):
diplomacy-only repair still did not load an Air Transport; class-targeted tasks did (load 3/5,
Unload button, unload 0/5). The reserved-ID remap only renumbered those per-unit targets.

Fix, per unit and per civ: all per-unit garrison tasks whose target is a DE-garrisonable unit
(type 70, trait bit 0, capacity > 0) of DE class c collapse into ONE class-c garrison task at the
position of the first, with DE's native diplomacy (4 for class 20 like the Transport Ship, 1
otherwise like rams/Siege Tower); task IDs are renumbered and the default task follows. Classes
20, 0 and 22 contain only transports every such holder could already board, so membership is
exact there. In class 13 the holders' source sets cover every garrisonable unit except
BROADENED below (scenario/hero carriers); they become boardable too. Anything else broadening
membership aborts. Idempotent; independent of the reserved-ID remap (runs before or after).

The builder output (work/factions.raw) keeps source membership for the source-parity checks; this
step runs at the DE boundary next to the reserved-ID remap:
  * package_factions.py and install_parity_dat.py call repair_raw_dat() before compressing;
  * this script applies it to an assembled mod (payload by default, then re-pins recipe.tsv):

  python outputs/toolkit/transport_garrison.py                       # payload/ + recipe.tsv
  python outputs/toolkit/transport_garrison.py --logic <SWBG-Logic or Factions-Draft dir>
  python outputs/toolkit/transport_garrison.py --check               # report only

check_transports.py is the offline guard (every transport can be boarded and can unload).
Needs genieutils-py 0.1.2 (byte-exact round trip checked on every run).
"""
from __future__ import annotations

import argparse
import sys
import zlib
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reserved_unit_ids as R  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
GARRISON = 3
UNLOAD = 12            # "Unload (boat-like)", carried by DE's Transport Ship
TRANSPORT_CLASS = 20   # DE Transport Ship class (SWGB 17 naval + 59 air transports)
DIP_OWN = 1            # DE: rams / Siege Tower (class 13)
DIP_OWN_ALLY = 4       # DE: Transport Ship (class 20), buildings
DE_GARRISON_DIPLOMACY = {DIP_OWN, DIP_OWN_ALLY}


def native_diplomacy(target_class: int) -> int:
    return DIP_OWN_ALLY if target_class == TRANSPORT_CLASS else DIP_OWN


def is_carrier(u) -> bool:
    """DE can garrison into this unit (units only; buildings use GarrisonType)."""
    return u is not None and u.type == 70 and bool(u.trait & 1) and u.garrison_capacity > 0


def _class_members(units):
    members = {}
    for u in units:
        if u is not None:
            members.setdefault(u.class_, []).append(u)
    return members


def garrison_targets(task, units, members):
    """Units a garrison task can target in this civ (unit- or class-selected)."""
    if task.unit_id >= 0:
        u = units[task.unit_id] if task.unit_id < len(units) else None
        return [u] if u is not None and (task.class_id < 0 or u.class_ == task.class_id) else []
    if task.class_id >= 0:
        return members.get(task.class_id, [])
    return []


# Garrisonable class-13 units no holder could board as a whole set in SWGB (FLAKB: nobody; the
# three cruisers: only the hero/officer holders). A class-13 task makes them boardable too.
BROADENED = {'UNIT-FLAKB', 'UNIT-GUBLCE', 'Super Star Destroyer', 'Resurgent Star Destroyer'}


def repair_dat(dat) -> dict:
    """Collapse per-unit garrison tasks into carriers to one class task per carrier class."""
    stats = Counter()
    for civ in dat.civs:
        units = civ.units
        carriers = {}
        for x in units:
            if is_carrier(x):
                carriers.setdefault(x.class_, set()).add(x.id)
        for u in units:
            if u is None or u.bird is None or not u.bird.tasks:
                continue
            tasks, out, first, covered = u.bird.tasks, [], {}, {}
            default = u.bird.default_task_id
            new_default = -1
            for t in tasks:
                target = units[t.unit_id] if t.action_type == GARRISON and 0 <= t.unit_id < len(units) else None
                if is_carrier(target) and t.class_id in (-1, target.class_):
                    c = target.class_
                    covered.setdefault(c, set()).add(target.id)
                    if c in first:
                        if t.id == default:
                            new_default = first[c]
                        stats['removed'] += 1
                        continue
                    t.class_id, t.unit_id, t.target_diplomacy = c, -1, native_diplomacy(c)
                    first[c] = len(out)
                    stats[f'class_{c}'] += 1
                elif t.action_type == GARRISON and t.unit_id < 0 and t.class_id in carriers                         and t.target_diplomacy not in DE_GARRISON_DIPLOMACY:
                    t.target_diplomacy = native_diplomacy(t.class_id)
                    stats['diplomacy'] += 1
                if t.id == default:
                    new_default = len(out)
                out.append(t)
            for c, ids in covered.items():
                extra = {units[i].name for i in carriers[c] - ids}
                if extra - BROADENED:
                    raise SystemExit(f'unit {u.id} {u.name}: a class-{c} garrison task would also board '
                                     f'{sorted(extra - BROADENED)}; extend BROADENED only after review')
                stats['broadened'] += len(extra)
            if len(out) != len(tasks):
                for i, t in enumerate(out):
                    t.id = i
                u.bird.tasks = out
                if default >= 0:
                    assert new_default >= 0, (u.id, default)
                    u.bird.default_task_id = new_default
                stats['units'] += 1
    return dict(stats)


def repair_raw_dat(raw: bytes) -> tuple[bytes, dict]:
    """Apply repair_dat to an uncompressed DAT, refusing if genieutils-py is not byte-exact."""
    dat = R.parse_raw(raw)
    if dat.to_bytes() != raw:
        raise SystemExit('genieutils-py does not round-trip this DAT byte-exactly; refusing to rewrite it')
    stats = repair_dat(dat)
    out = dat.to_bytes()
    if out != raw:
        check = R.parse_raw(out)
        if check.to_bytes() != out:
            raise SystemExit('repaired DAT does not round-trip')
    return out, stats


# ------------------------------------------------------------------------------------- guard
# Transport lines every playable civ must be able to load and unload (SWGB internal names).
CORE_LINES = {'UNIT-M3TR': 'Assault Mech', 'UNIT-MH3T': 'Hvy Assault Mech', 'UNIT-M4TR': 'Transport Mech',
              'UNIT-AATR': 'Air Transport', 'BOAT-STRN': 'Transport Ship'}
WORKER_CLASS = 4       # DE Civilian (SWGB 58 Workers)


def scan_dat(dat) -> tuple[list[str], dict]:
    """Guard for check_transports.py. A transport is a DE-garrisonable unit (type 70, trait bit 0,
    capacity > 0) that some garrison task targets (the source's intended boarders). Each must
    have boarders through a class-targeted garrison task with a DE target diplomacy (1 or 4), no
    per-unit garrison task (DE ignores them) and no other diplomacy, and must be able to unload
    (trait bit + ungarrison-capable interface; class-20 transports also carry DE's Unload task). In each playable civ the core lines (Assault Mech,
    Hvy Assault Mech, Transport Mech, Air Transport, Transport Ship) must exist as transports and
    be boardable by a worker and by the civ's other trained units.
    """
    problems, info = [], Counter()
    for ci, civ in enumerate(dat.civs):
        units = civ.units
        members = _class_members(units)
        good, bad, per_unit = {}, Counter(), Counter()
        for u in units:
            if u is None or u.bird is None:
                continue
            for t in u.bird.tasks:
                if t.action_type != GARRISON:
                    continue
                for x in garrison_targets(t, units, members):
                    if not is_carrier(x):
                        continue
                    if t.unit_id >= 0:
                        per_unit[x.id] += 1   # DE ignores UnitID on garrison tasks
                    elif t.target_diplomacy in DE_GARRISON_DIPLOMACY:
                        good.setdefault(x.id, set()).add(u.id)
                    else:
                        bad[x.id] += 1
        targeted = set(good) | set(bad) | set(per_unit)
        for x in (u for u in units if is_carrier(u) and u.id in targeted):
            info['transports'] += 1
            where = f'civ {ci} unit {x.id} {x.name}'
            if per_unit[x.id]:
                problems.append(f'{where}: {per_unit[x.id]} per-unit garrison tasks (DE matches the class only)')
            if bad[x.id]:
                problems.append(f'{where}: {bad[x.id]} garrison tasks use target diplomacy outside DE 1/4')
            if not good.get(x.id):
                problems.append(f'{where}: no unit can board it')
            if x.class_ == TRANSPORT_CLASS and not any(t.action_type == UNLOAD for t in x.bird.tasks):
                problems.append(f'{where}: class-20 transport without the Unload task')
            if x.interface_kind not in (4, 7, 12):
                problems.append(f'{where}: interface kind {x.interface_kind} has no ungarrison command')
        if ci == 0:
            continue
        trained = {u.id for u in units if u is not None and u.type == 70 and u.creatable is not None
                   and any(l.unit_id >= 0 for l in u.creatable.train_locations)}
        workers = {u.id for u in units if u is not None and u.id in trained and u.class_ == WORKER_CLASS}
        for prefix, label in CORE_LINES.items():
            line = [u for u in units if u is not None and u.type == 70 and u.name.startswith(prefix)]
            if not line:
                problems.append(f'civ {ci}: no {label} ({prefix}*) units')
            for x in line:
                where = f'civ {ci} {label} {x.id} {x.name}'
                if not is_carrier(x):
                    problems.append(f'{where}: not garrisonable (trait {x.trait}, capacity {x.garrison_capacity})')
                    continue
                b = good.get(x.id, set())
                if not b & workers:
                    problems.append(f'{where}: workers cannot board it')
                if len(b & trained) < 10:
                    problems.append(f'{where}: only {len(b & trained)} trained unit types can board it')
                info[f'core_{prefix}'] += 1
    return problems, dict(info)


def _payload_logic(a):
    return a.logic or a.payload / 'SWBG-Logic'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--payload', type=Path, default=ROOT / 'payload')
    ap.add_argument('--logic', type=Path, help='SWBG-Logic (or SWGB-DE-Factions-Draft) folder')
    ap.add_argument('--recipe', type=Path, default=ROOT / 'outputs/installer/installer/recipe.tsv')
    ap.add_argument('--check', action='store_true', help='report what would change; write nothing')
    a = ap.parse_args()
    path = _payload_logic(a) / R.DAT_REL
    compressed = path.read_bytes()
    raw = zlib.decompress(compressed, -15)
    new_raw, stats = repair_raw_dat(raw)
    print(f'{path}: transport garrison tasks', stats)
    if a.check or new_raw == raw:
        return
    path.write_bytes(R.compress_dat(new_raw))
    if not a.logic:
        from remap_reserved_unit_ids import refresh_recipe
        print(refresh_recipe(a.payload, a.recipe, False))


if __name__ == '__main__':
    main()
