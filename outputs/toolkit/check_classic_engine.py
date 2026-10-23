"""Differential checks against original executable routines, without a game."""
from pathlib import Path
import hashlib
import json
import random
import subprocess
import time
import unicorn
from classic_engine_oracle import Oracle, SOURCE_SHA
from classic_air_model import (Aircraft, GROUND_CLASSES, AIR_CLASSES, attack_count,
                               source_groups, scaled_air_percent)


def main():
    assert unicorn.__version__ == '2.1.4'
    oracle = Oracle()
    checks = 0
    start = time.monotonic()
    def check(actual, expected, label):
        nonlocal checks
        assert actual == expected, (label, actual, expected)
        checks += 1

    defaults = oracle.defaults()
    for sn, expected in {6: 100, 16: 4, 17: 4, 26: 10, 27: 10, 36: 0, 40: 0,
                         42: 0, 223: 75, 227: 75, 228: 75, 229: 0, 230: 20}.items():
        check(defaults[sn], expected, ('source default', sn))
    for flags in (0, 1, 2, 3):
        for cls in range(128):
            pools = oracle.classification(cls, flags)
            check(0x118 in pools, cls in GROUND_CLASSES, ('ground class', cls, flags))
            check(0x138 in pools, cls in AIR_CLASSES and not flags & 2, ('air class', cls, flags))
    print('PASS source defaults and class dispatch', flush=True)
    for multiplayer in (False, True):
        for no_scaling in (False, True):
            for difficulty in range(5):
                for value in (-1, 0, 1, 2, 3, 5, 25, 50, 75, 99, 100):
                    check(scaled_air_percent(value, difficulty, multiplayer, no_scaling),
                          oracle.scaled_setting(223, value, difficulty, multiplayer, no_scaling),
                          ('air difficulty scaling', value, difficulty, multiplayer, no_scaling))
    for percent in (0, 1, 12, 18, 25, 37, 50, 56, 75, 80, 99, 100):
        for available in list(range(50)) + [75, 99, 100, 101, 199, 200, 500, 999, 1000]:
            result = oracle.attack_counts(available, available, percent, percent)
            expected = attack_count(available, percent)
            check(result.get('ground', 0), expected, ('ground dispatch rounding', available, percent))
            check(result.get('air', 0), expected, ('air dispatch rounding', available, percent))
    print('PASS original difficulty scaling and dispatch rounding', flush=True)
    # Deterministic layouts include ties, chains, isolated units, zone separation,
    # distance boundaries and input sizes beyond the original 40-item window.
    rng = random.Random(549437)
    layouts = [[], [(1, 0, 0, 0)], [(1, 0, 0, 0), (2, 20, 0, 0)],
               [(1, 0, 0, 0), (2, 20.001, 0, 0)],
               [(1, 0, 0, 0), (2, 15, 0, 0), (3, 30, 0, 0), (4, 100, 0, 0)],
               [(i + 1, i * 30, 0, 0) for i in range(45)],
               [(i + 1, i, 0, 0) for i in range(60)]]
    for _ in range(45):
        n = rng.choice((2, 3, 8, 20, 39, 40, 41, 60, 100))
        points = rng.sample([(x, y) for x in range(0, 120, 3) for y in range(0, 120, 3)], n)
        layouts.append([(i + 1, x, y, 0 if x < 60 else 1) for i, (x, y) in enumerate(points)])
    for index, positions in enumerate(layouts):
        for requested in sorted({0, 1, (len(positions) + 1)//2, len(positions)}):
            for distance in (0, 20, 30):
                check(source_groups([Aircraft(*p) for p in positions], requested, distance),
                      oracle.spatial_groups(positions, requested, distance),
                      ('spatial grouping', index, requested, distance))
        if index % 10 == 0:
            print('PASS source grouping layout', index, flush=True)
    report = dict(passed=True, checks=checks, elapsed_seconds=round(time.monotonic()-start, 2),
                  executable_sha256=SOURCE_SHA, emulator='unicorn '+unicorn.__version__,
                  symbols_repository='https://github.com/rva2895/efpatch',
                  symbols_commit=subprocess.check_output(['git', '-C', 'work/efpatch', 'rev-parse', 'HEAD'], text=True).strip(),
                  routines={'classification': '0x0059FA80', 'defaults': '0x00596D10',
                            'difficulty_scaling': '0x005A5730', 'attack_now': '0x005AE520',
                            'spatial_grouping': '0x004506F0'}, defaults=defaults,
                  limitations=['Base executable routines only; injected EF hooks are not executed.',
                               'World fixtures replace position, owner and zone queries.',
                               'Attack rounding fixtures stub collection and spatial grouping.',
                               'Grouping fixtures run original clustering but not subsequent targeting or orders.',
                               'Reference model is not yet wired into the installed DE AI.'],
                  game_launched=False, full_behavior_parity=False)
    report['tool_hashes'] = {name: hashlib.sha256((Path('outputs/toolkit')/name).read_bytes()).hexdigest()
                            for name in ('classic_engine_oracle.py', 'classic_air_model.py', 'check_classic_engine.py')}
    dest = Path('work/classic-engine');dest.mkdir(exist_ok=True)
    (dest/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS', checks, 'original executable differential checks; gameplay not verified')


if __name__ == '__main__':
    main()
