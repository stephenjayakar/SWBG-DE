"""Check the Classic AI's Power Core placement (classic_ai_power_placement.py).

- the placement settings come right after the XS observer call, once;
- no plain (build X) is left for a building that needs power, and every placed build
  sets the Power Core point (goals 121/122) first;
- Power Cores, build-forward rules, Shipyards, Nurseries and dropsites keep their normal
  placement;
- every copy of swgb_classic_ai.xs carries the placement block, calls it after the emitter
  scan, writes only goals 121/122, and passes xs-check when work/xs-check is present;
- the unpowered count (goal 101) uses DE's aura geometry (collision-box gap < range), skips
  Nurseries, Shipyards and buildings older than the newest core, and its half-sizes match
  the DAT (--logic); a model of it reproduces the in-game evidence;
- the transformation is idempotent.

  python outputs/toolkit/check_classic_power_placement.py [--root payload/SWBG-Data]
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import classic_ai_power_placement as P  # noqa: E402

cli = argparse.ArgumentParser()
cli.add_argument('--root', type=Path, default=Path('payload/SWBG-Data'))
cli.add_argument('--logic', type=Path, default=Path('payload/SWBG-Logic'),
                 help='SWBG-Logic for the collision half-sizes (skipped if it has no DAT)')
args = cli.parse_args()
checks = 0


def check(condition, message):
    global checks
    assert condition, message
    checks += 1


per = (args.root / P.PER).read_text()
per_lf = per.replace('\r\n', '\n')
check(per_lf.count(P.PER_BEGIN) == 1, 'placement settings present once')
check(P.OBSERVER_RULE + P.PER_RULES in per_lf, 'placement settings follow the observer call (goals are fresh)')
check(f'(set-strategic-number sn-placement-zone-size {P.ZONE})' in per_lf, 'zone size set')
check(f'(strategic-number sn-placement-zone-size > {P.ZONE_CAP})' in per_lf, 'grown zone is reset')
check(not P.BUILD.search(per_lf), 'no plain (build X) left for a building that needs power')
check('(build ce-bldg-powercore)' in per_lf and '(build cr-bldg-powercore)' in per_lf
      and 'place-point 0 c: ce-bldg-powercore' not in per_lf, 'Power Cores keep normal placement')
placed = re.findall(r'\(up-set-target-point (\d+)\) \(up-build place-point 0 c: (c[er]-bldg-[a-z]+)\)', per_lf)
check(len(placed) == per_lf.count('(up-build place-point'), 'every placed build sets its point immediately before')
for goal, building in placed:
    kind = building.split('-', 2)[2]
    check(kind in P.PLACED and goal == str(P.POINT), f'{building}: placed at a Power Core')
kinds = {b.split('-', 2)[2] for _, b in placed}
check({'traintrooper', 'trainmech', 'trainair', 'trainheavy', 'trainjedi'} <= kinds,
      'Troop Center, Mech Factory, Airbase, Heavy Weapons Factory and Temple placed')
for keep in ('powercore', 'trainboat', 'dropanim', 'dropcarbon', 'dropchow', 'dropnova', 'dropmetal', 'prefab', 'farm'):
    check(f'c: ce-bldg-{keep})' not in per_lf and f'c: cr-bldg-{keep})' not in per_lf, f'{keep}: normal placement kept')
check('(build-forward ce-bldg-powercore)' in per_lf and '(build-forward ce-bldg-traintrooper)' in per_lf,
      'build-forward rules keep their forward placement')
# The land Troop Center (source main/1742) is placed at the Power Core it waits for.
land = [b for b in re.findall(r'\(defrule\n(?:  .*\n)*?  =>\n(?:  .*\n)*?\)', per_lf)
        if '(not (goal ce-special-map ce-WATER))' in b and '(building-type-count-total ce-bldg-powercore > 0)' in b
        and 'bldg-traintrooper' in b]
check(land and all(f'(up-set-target-point {P.POINT}) (up-build place-point 0 c: ce-bldg-traintrooper)' in b for b in land),
      'Empire land Troop Center placed at its Power Core')
again, builds = P.rewrite_per(per)
check(again == per and builds == 0, 'PER transformation is idempotent')

goal_writes = set()
xs_files = [args.root / rel for rel in P.XS_COPIES if (args.root / rel).is_file()]
check(len(xs_files) == 3, 'three copies of swgb_classic_ai.xs')
texts = {p.read_text().replace('\r\n', '\n') for p in xs_files}
check(len(texts) == 1, 'XS copies identical')
xs = texts.pop()
check(xs.count(P.XS_BEGIN) == 1 and xs.count(P.XS_END) == 1, 'XS placement block present once')
observer = xs.split(P.OBSERVE)[1].split('\n}\n')[0]
check(observer.count(P.XS_CALL) == 1 and observer.index(P.XS_AFTER) < observer.index(P.XS_CALL),
      'placement points computed after the emitter scan, every observer pass')
block = xs[xs.index(P.XS_BEGIN):xs.index(P.XS_END)]
goal_writes = {int(g) for g in re.findall(r'xsSetGoal\((\d+),', block)}
check(goal_writes == {P.POINT, P.POINT + 1}, 'block writes goals 121/122 only')
check(all(f'id == {c}' in block for c in P.CORES), 'all Power Core upgrades count as cores')
check(P.rewrite_xs(xs) == (xs, False), 'XS transformation is idempotent')

# Unpowered count (goal 101).
check(P.OLD_COUNT not in xs and observer.count(P.NEW_COUNT) == 1,
      'observer counts unpowered buildings with classicCountsUnpowered (no centre-distance test)')
check('return(gx*gx + gy*gy < range*range);' in block and 'ha + hb' in block,
      'aura test uses the gap between collision boxes')
counts = block[block.index('bool classicCountsUnpowered'):block.index('void classicSetPowerPoint')]
check('classicNursery(id) || classicShipyard(id)' in counts and 'unit <= classicNewestCore' in counts,
      'Nurseries, Shipyards and buildings older than the newest core are not counted')
check('if (unit > classicNewestCore) classicNewestCore = unit;' in block, 'newest core tracked (finished or not)')


def xs_ids(name):
    body = re.search(r'bool %s\(int id = -1\) \{\n    return\((.*?)\);' % name, xs, re.S).group(1)
    return {int(i) for i in re.findall(r'id == (\d+)', body)}


targets = xs_ids('classicPowerTarget')
check(set(P.HALF_SIZES) == targets, f'half-size for every power target: {sorted(targets ^ set(P.HALF_SIZES))}')
emitters = {int(i) for i in re.findall(r'if \(id == (\d+)\) return\(\d', xs.split('float classicEmitterRange')[1].split('\n}\n')[0])}
check(set(P.EMITTER_HALF_SIZES) == emitters, f'half-size for every emitter: {sorted(emitters ^ set(P.EMITTER_HALF_SIZES))}')
check(set(P.SHIPYARDS) <= targets and not set(P.SHIPYARDS) & xs_ids('classicNursery'), 'Shipyard IDs are power targets')
dat_path = args.logic / 'resources/_common/dat/empires2_x2_p1.dat'
if dat_path.is_file():
    import zlib
    import reserved_unit_ids as R
    dat = R.parse_raw(zlib.decompress(dat_path.read_bytes(), -15))
    for table in (P.HALF_SIZES, P.EMITTER_HALF_SIZES):
        for uid, half in sorted(table.items()):
            sizes = {(round(u.collision_size_x, 3), round(u.collision_size_y, 3))
                     for u in (dat.civs[1].units[uid], dat.civs[2].units[uid]) if u is not None}
            check(sizes == {(half, half)}, f'unit {uid}: DAT collision half-size {sizes} != {half}')


def in_aura(dx, dy, half, core_half=0.5, rng=10.0):
    gx, gy = (max(0.0, abs(d) - half - core_half) for d in (dx, dy))
    return gx * gx + gy * gy < rng * rng


# In-game evidence (Troop Center 87, half-size 1.5, at these offsets from a Power Core):
# (9, 9) trained a trooper every 19 s (powered), (12, 1) every 73 s and (15, 7), (16, 2),
# (13, 7), (0, 13) every 64-86 s (unpowered).
check(in_aura(9, 9, 1.5) and in_aura(9, 1, 1.5) and in_aura(5, 9, 1.5), 'powered Troop Centers are in the aura')
check(not any(in_aura(dx, dy, 1.5) for dx, dy in ((12, 1), (15, 7), (16, 2), (13, 7), (0, 13))),
      'unpowered Troop Centers are outside the aura')
check(not (9 * 9 + 9 * 9 <= 10 * 10), 'self-test: the former centre-distance test missed the (9, 9) Troop Center')
checker = Path('work/xs-check/xs-check.exe')
if checker.exists():
    result = subprocess.run([str(checker.resolve()), str(xs_files[0].resolve())], capture_output=True, text=True)
    check(result.returncode == 0 and 'No errors found' in result.stdout, 'xs-check: ' + result.stdout + result.stderr)
print('PASS', checks, 'checks;', len(placed), 'placed builds; runtime verification pending')
