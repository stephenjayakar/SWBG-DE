"""Place the Classic AI's production buildings inside Power Core range (SWGB power in DE).

SWGB buildings without power work at 25 % speed. The port emulates that with a quarter
work rate on every power-dependent building plus a +300 % work-rate aura (task 155, range
10) on the Power Cores (FACTION-STATUS.md). The source AI never places buildings itself:
SWGB's engine placement put a Troop Center inside the Power Core's radius "nearly always"
when the core came first (airef, SWGB scripting differences, section 6-3), which is why
the source builds its first Power Core before the land Troop Center. DE's placement does
not know about power.

Evidence (2026-10-21 Savannah recordings, BUILD coordinates): in all ten Classic and Land
AI games the first Troop Center stood 12-30 tiles from the Power Core, outside the
10-tile aura. Every AI then trained one Tech Level 1 trooper per 64-73 s, although the
trooper's train time is 16 s: 16 / 0.25 = 64 s, plus the per-difficulty rule delay that
the AIs' workers (25 s train time) show as well (25.5 s Hardest, 26.5 s Hard, 28.5 s
Moderate). Moderate needs 10 troopers for Tech Level 2, so it reached it only at about
20:00.

Fix, without changing the source rules' conditions:
- The XS observer (called at the top of every rule pass) also writes a placement point,
  goals 121/122: the Power Core (finished or under construction) with the fewest
  power-dependent buildings in its radius; the Command Center (or a worker) if there is
  no core yet.
- Every `(build X)` of a building that needs power and stands anywhere on land (Troop
  Center, Mech Factory, Airbase, Heavy Weapons Factory, Jedi/Sith Temple, Shield
  Generator, War Center, Research Center, Spaceport) becomes
  `(up-set-target-point 121) (up-build place-point 0 c: X)`. `build-forward` rules
  (forward bases), Shipyards (shore), Nurseries (food sites), dropsites and the Power
  Cores themselves keep their normal placement. (An earlier version also placed new
  cores at unpowered buildings; in a Moderate test that made the source's once-a-minute
  "too many unpowered buildings" rule succeed every minute, 9 extra cores by 31:00, so it
  was dropped.)
- sn-placement-zone-size 7 (a 4x4 building whose centre is within 7 tiles of the core's
  centre is inside its 10-tile aura), sn-placement-fail-delta 1 so a crowded zone grows
  instead of blocking the build; the zone goes back to 7 whenever nothing is unpowered
  and whenever it has grown past 20.

Unpowered count (goal 101, the source's once-a-minute "too many unpowered buildings" rule,
EMPIRE/REBEL main/502-503 and 1628-1629, threshold goal 100 = 2 / 1 / 0 by Tech Level):
- DE geometry. DE's power aura (task 155, range 10, flags 3: multiply, circular) reaches a
  building when the gap between the two collision boxes is less than the range, not when
  the centres are 10 tiles apart. Evidence from the BUILD coordinates and trooper train
  intervals of the 2026-10-21/22 recordings: Troop Centers at offset (9, 9) from their core
  (centre distance 12.7, box gap 9.9) trained a trooper every 19 s (powered), one at (12, 1)
  (box gap exactly 10.0) every 73 s (unpowered), and every first Troop Center with a larger
  gap at the 25 % rate. The observer used the centre distance, so it counted powered Troop
  Centers as unpowered. Collision half-sizes come from the DAT (HALF_SIZES, compared with the
  DAT by check_classic_power_placement.py).
- Only buildings that a new core can power count. Nurseries and Shipyards stand at food
  sites and on the shore, and new cores keep DE's normal placement, so a core never reaches
  them; counting them bought a core every minute without effect (2026-10-22 Moderate: two
  nurseries 17-23 tiles from the base, 5 extra cores between 22:00 and 33:00). They still
  work at 25 % speed when unpowered, as before.
- A building that was already unpowered when the newest core (finished or not) was placed
  does not count again (unit IDs grow in creation order). The rule then answers each new
  unpowered building once instead of every minute, for example after the zone has grown.

Run from the repository root to apply the same transformation in place (idempotent):
  python outputs/toolkit/classic_ai_power_placement.py --root payload/SWBG-Data
"""
import argparse
import re
from pathlib import Path

PER = 'resources/_common/ai/SWGB Classic AI.per'
XS_COPIES = ('resources/_common/xs/swgb_classic_ai.xs',
             'resources/_common/ai/swgb_classic_ai.xs',
             'resources/_common/ai/SWGB Classic/swgb_classic_ai.xs')
POINT = 121
ZONE, FAIL_DELTA, ZONE_CAP = 7, 1, 20
# Building constants (both factions) whose (build X) is placed at goal 121.
PLACED = ('traintrooper', 'trainmech', 'trainair', 'trainheavy', 'trainjedi', 'shldgen',
          'warctr', 'resctr', 'spaceport')
BUILD = re.compile(r'\(build (c[er]-bldg-(' + '|'.join(PLACED) + r'))\)')
PER_BEGIN = '; Power placement (classic_ai_power_placement.py): SWGB engine placement put buildings in Power Core range.'
PER_RULES = (PER_BEGIN + '\n'
             f'(defrule (true) => (set-strategic-number sn-placement-zone-size {ZONE})\n'
             f' (set-strategic-number sn-placement-fail-delta {FAIL_DELTA}) (disable-self))\n'
             f'(defrule (up-compare-goal 101 c:== 0) => (set-strategic-number sn-placement-zone-size {ZONE}))\n'
             f'(defrule (strategic-number sn-placement-zone-size > {ZONE_CAP}) =>\n'
             f' (set-strategic-number sn-placement-zone-size {ZONE}))\n')
OBSERVER_RULE = '(defrule (true) => (up-get-fact player-number 0 104) (xs-script-call "swgbClassicObserve"))\n'
# Power Cores and their Tech Level upgrades (unitlines.json swgb-bldg-powercore); droids move.
CORES = (12, 20, 132, 498, 3554, 3555, 3556, 3557)
MAIN = (109, 71, 141, 142, 3578, 3579, 3580, 3581, 3646, 3647, 3648, 3649, 3650, 3651, 3652,
        3653, 4780, 4781, 4782, 4783)
# Collision half-sizes (DAT collision_size_x == _y, the same in both factions) of the
# observer's power targets (classicPowerTarget) and of the power emitters.
HALF_SIZES = {**{i: 1.5 for i in (10, 14, 30, 31, 45, 47, 51, 87, 104, 133, 335, 336, 337,
                                  3582, 3583, 3584, 3585, 3586, 3587, 3588, 3589, 3593, 3594, 3595)},
              **{i: 2.0 for i in (49, 86, 101, 150, 153, 317, 318, 3342, 3343, 3590, 3591, 3592,
                                  3596, 3597)},
              **{i: 1.0 for i in (319, 320, 321, 322, 3550, 3551, 3552, 3553)}}
EMITTER_HALF_SIZES = {**{i: 0.5 for i in CORES}, 1009: 0.2, 1013: 0.2}
# Shipyards and their upgrades (45/133/47/51, Rebel 3586-3589): shore placement.
SHIPYARDS = (45, 47, 51, 133, 3586, 3587, 3588, 3589)
# The observer's former unpowered test (centre distance), replaced by classicCountsUnpowered.
OLD_COUNT = """                if (classicPowerTarget(id)) {
                    bool powered = false;
                    vector position = xsGetUnitPosition(unit);
                    for (j = 0; < classicEmitterCount) {
                        vector emitter = xsArrayGetVector(classicEmitterPositions, j);
                        float radius = xsArrayGetFloat(classicEmitterRanges, j);
                        float dx = xsVectorGetX(position) - xsVectorGetX(emitter);
                        float dy = xsVectorGetY(position) - xsVectorGetY(emitter);
                        if (dx*dx + dy*dy <= radius*radius) powered = true;
                    }
                    if (powered == false) unpowered++;
                }
"""
NEW_COUNT = """                if (classicPowerTarget(id)) {
                    if (classicCountsUnpowered(unit, id)) unpowered++;
                }
"""
XS_BEGIN = '// Power placement point (goals 121/122); see classic_ai_power_placement.py.'
XS_END = '// End of power placement point.'
XS_CALL = '    classicSetPowerPoint(player);'
XS_AFTER = '    classicAddEmitters(player, classicOtherUnits);\n'
OBSERVE = 'void swgbClassicObserve() {\n'


def _ids(name, ids):
    return (f'bool {name}(int id = -1) {{\n    return(' +
            ' ||\n           '.join(f'id == {i}' for i in ids) + ');\n}')


def _sizes(name, table, default):
    lines = [f'float {name}(int id = -1) {{']
    for size in sorted(set(table.values())):
        ids = sorted(i for i, v in table.items() if v == size)
        lines.append('    if (' + ' ||\n        '.join(f'id == {i}' for i in ids) + f') return({size});')
    lines += [f'    return({default});', '}']
    return '\n'.join(lines)


def xs_block():
    return '\n'.join([
        XS_BEGIN,
        '// The Power Core (finished or not) with the fewest power-dependent buildings in range,',
        '// else the Command Center, else a worker; -1 if the player has none of these.',
        '// It also collects the power emitters for the unpowered count (goal 101): DE powers a',
        '// building when the gap between the two collision boxes is less than the aura range.',
        'int classicAuraPositions = -1;',
        'int classicAuraHalves = -1;',
        'int classicAuraRanges = -1;',
        'int classicAuraCount = 0;',
        'int classicNewestCore = -1;',
        _ids('classicPowerCore', CORES),
        _ids('classicMainBuilding', MAIN),
        _ids('classicShipyard', SHIPYARDS),
        _sizes('classicHalfSize', HALF_SIZES, 1.5),
        _sizes('classicEmitterHalfSize', EMITTER_HALF_SIZES, 0.5),
        'float classicGap(float d = 0.0, float halves = 0.0) {',
        '    if (d < 0.0) d = 0.0 - d;',
        '    d = d - halves;',
        '    if (d < 0.0) return(0.0);',
        '    return(d);',
        '}',
        'bool classicInAura(vector a = vector(0,0,0), float ha = 0.0, vector b = vector(0,0,0), float hb = 0.0, float range = 10.0) {',
        '    float gx = classicGap(xsVectorGetX(a) - xsVectorGetX(b), ha + hb);',
        '    float gy = classicGap(xsVectorGetY(a) - xsVectorGetY(b), ha + hb);',
        '    return(gx*gx + gy*gy < range*range);',
        '}',
        'void classicAddAuras(int player = 1, int array = -1) {',
        '    if (array < 0) return;',
        '    for (i = 0; < xsArrayGetSize(array)) {',
        '        int unit = xsArrayGetInt(array, i);',
        '        if (xsDoesUnitExist(unit)) {',
        '            int id = xsGetUnitCopyId(unit);',
        '            float range = classicEmitterRange(player, id);',
        '            if (range > 0.0) {',
        '                bool ready = true;',
        '                if (xsGetUnitType(unit) == 80) ready = classicFinished(unit);',
        '                if (ready) {',
        '                    if (classicAuraCount >= xsArrayGetSize(classicAuraPositions)) {',
        '                        xsArrayResizeVector(classicAuraPositions, classicAuraCount + 1);',
        '                        xsArrayResizeFloat(classicAuraHalves, classicAuraCount + 1);',
        '                        xsArrayResizeFloat(classicAuraRanges, classicAuraCount + 1);',
        '                    }',
        '                    xsArraySetVector(classicAuraPositions, classicAuraCount, xsGetUnitPosition(unit));',
        '                    xsArraySetFloat(classicAuraHalves, classicAuraCount, classicEmitterHalfSize(id));',
        '                    xsArraySetFloat(classicAuraRanges, classicAuraCount, range);',
        '                    classicAuraCount++;',
        '                }',
        '            }',
        '        }',
        '    }',
        '}',
        '// Goal 101 counts a finished power target unless a core reaches it, it is a Nursery or a',
        '// Shipyard (placed away from the cores, so a new core cannot reach it), or it was already',
        '// there when the newest core was placed (one core per unpowered building, not one a minute).',
        'bool classicCountsUnpowered(int unit = -1, int id = -1) {',
        '    if (classicNursery(id) || classicShipyard(id)) return(false);',
        '    if (unit <= classicNewestCore) return(false);',
        '    vector at = xsGetUnitPosition(unit);',
        '    float half = classicHalfSize(id);',
        '    for (j = 0; < classicAuraCount) {',
        '        if (classicInAura(at, half, xsArrayGetVector(classicAuraPositions, j),',
        '                          xsArrayGetFloat(classicAuraHalves, j), xsArrayGetFloat(classicAuraRanges, j)))',
        '            return(false);',
        '    }',
        '    return(true);',
        '}',
        'void classicSetPowerPoint(int player = 1) {',
        '    vector home = vector(-1,-1,-1);',
        '    vector core = vector(-1,-1,-1);',
        '    int fewest = 1000000;',
        '    if (classicAuraPositions < 0) {',
        '        classicAuraPositions = xsArrayCreateVector(1, vector(0,0,0), "classic aura positions");',
        '        classicAuraHalves = xsArrayCreateFloat(1, 0.0, "classic aura half sizes");',
        '        classicAuraRanges = xsArrayCreateFloat(1, 0.0, "classic aura ranges");',
        '    }',
        '    classicAuraCount = 0;',
        '    classicAddAuras(player, classicBuildings);',
        '    classicAddAuras(player, classicOtherUnits);',
        '    classicNewestCore = -1;',
        '    if (classicWorkers >= 0) {',
        '        if (xsArrayGetSize(classicWorkers) > 0) home = xsGetUnitPosition(xsArrayGetInt(classicWorkers, 0));',
        '    }',
        '    if (classicBuildings >= 0) {',
        '        int n = xsArrayGetSize(classicBuildings);',
        '        for (i = 0; < n) {',
        '            int unit = xsArrayGetInt(classicBuildings, i);',
        '            if (xsDoesUnitExist(unit)) {',
        '                int id = xsGetUnitCopyId(unit);',
        '                vector at = xsGetUnitPosition(unit);',
        '                if (classicMainBuilding(id)) home = at;',
        '                if (classicPowerCore(id)) {',
        '                    if (unit > classicNewestCore) classicNewestCore = unit;',
        '                    int load = 0;',
        '                    for (j = 0; < n) {',
        '                        int other = xsArrayGetInt(classicBuildings, j);',
        '                        if (xsDoesUnitExist(other)) {',
        '                            int otherId = xsGetUnitCopyId(other);',
        '                            if (classicPowerTarget(otherId) && classicNursery(otherId) == false) {',
        '                                if (classicInAura(xsGetUnitPosition(other), classicHalfSize(otherId), at,',
        '                                                  classicEmitterHalfSize(id), 10.0)) load++;',
        '                            }',
        '                        }',
        '                    }',
        '                    if (load <= fewest) {',
        '                        fewest = load;',
        '                        core = at;',
        '                    }',
        '                }',
        '            }',
        '        }',
        '    }',
        '    if (xsVectorGetX(core) < 0.0) core = home;',
        '    if (xsVectorGetX(core) < 0.0) {',
        f'        xsSetGoal({POINT}, -1);',
        f'        xsSetGoal({POINT + 1}, -1);',
        '        return;',
        '    }',
        f'    xsSetGoal({POINT}, xsCeilToInt(xsVectorGetX(core) - 0.5));',
        f'    xsSetGoal({POINT + 1}, xsCeilToInt(xsVectorGetY(core) - 0.5));',
        '}',
        XS_END, ''])


def rewrite_xs(text):
    """Insert or refresh the placement block and its call; returns (text, changed)."""
    original = text
    block = xs_block()
    if XS_BEGIN in text:
        start = text.index(XS_BEGIN)
        end = text.index(XS_END, start) + len(XS_END) + 1
        text = text[:start] + block + text[end:]
    else:
        assert text.count(OBSERVE) == 1, 'observer entry point not found'
        text = text.replace(OBSERVE, block + '\n' + OBSERVE)
    if OLD_COUNT in text:
        assert text.count(OLD_COUNT) == 1, 'observer unpowered count found twice'
        text = text.replace(OLD_COUNT, NEW_COUNT)
    assert text.count(NEW_COUNT) == 1, 'observer unpowered count not found'
    head, body = text.split(OBSERVE)
    observer = body.split('\n}\n')[0]
    if XS_CALL not in observer:
        assert observer.count(XS_AFTER) == 1, 'emitter scan not found in the observer'
        body = body.replace(XS_AFTER, XS_AFTER + XS_CALL + '\n', 1)
    text = head + OBSERVE + body
    return text, text != original


def rewrite_per(text):
    """Returns (text, newly placed builds). Idempotent."""
    newline = '\r\n' if '\r\n' in text else '\n'
    text = text.replace('\r\n', '\n')
    if PER_BEGIN not in text:
        assert text.count(OBSERVER_RULE) == 1, 'observer rule not found'
        text = text.replace(OBSERVER_RULE, OBSERVER_RULE + PER_RULES, 1)
    text, builds = BUILD.subn(lambda m: f'(up-set-target-point {POINT}) (up-build place-point 0 c: {m.group(1)})', text)
    return text.replace('\n', newline), builds


def apply(root):
    root = Path(root)
    report = []
    for rel in XS_COPIES:
        path = root / rel
        if not path.is_file():
            continue
        with path.open(encoding='utf-8', newline='') as handle:
            raw = handle.read()
        newline = '\r\n' if '\r\n' in raw else '\n'
        text, changed = rewrite_xs(raw.replace('\r\n', '\n'))
        if changed:
            with path.open('w', encoding='utf-8', newline='') as handle:
                handle.write(text.replace('\n', newline))
        report.append(f'{rel} {"changed" if changed else "unchanged"}')
    assert report, 'no swgb_classic_ai.xs found under ' + str(root)
    path = root / PER
    with path.open(encoding='utf-8', newline='') as handle:
        raw = handle.read()
    text, builds = rewrite_per(raw)
    if text != raw:
        with path.open('w', encoding='utf-8', newline='') as handle:
            handle.write(text)
    report.append(f'{PER} newly placed at a Power Core: {builds} builds')
    return report


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--root', type=Path, default=Path('payload/SWBG-Data'))
    args = cli.parse_args()
    for line in apply(args.root):
        print(line)


if __name__ == '__main__':
    main()
