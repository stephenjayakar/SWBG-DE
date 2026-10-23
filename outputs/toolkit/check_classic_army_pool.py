"""Differential checks for source group membership and attack-pool admission."""
from pathlib import Path
import hashlib
import json
import random
from classic_army_pool import TacticalGroup, first_group, attack_totals, available
from classic_army_pool_oracle import PoolOracle
from classic_engine_oracle import SOURCE_SHA


def fixtures():
    yield [], {}, []
    yield [1, 2, 1, 3, 4], {1: 48, 2: 59, 3: 51, 4: 50}, []
    yield [1, 2, 3], {1: 48, 2: 32, 3: 50}, [TacticalGroup(999, (1,))]
    yield [1, 2, 3], {1: 48, 2: 32, 3: 50}, [TacticalGroup(108, (2, 3)), TacticalGroup(100, (1, 2))]
    rng = random.Random(549437)
    for size in (1, 2, 10, 39, 40, 41, 100, 500, 1000):
        for iteration in range(8):
            pool = list(range(1, size+1))
            rng.shuffle(pool)
            if iteration % 2:
                pool += pool[:min(20, 1024-size)]
            classes = {uid: rng.choice((32, 48, 50, 51, 59, 63)) for uid in set(pool)
                       if rng.randrange(5)}
            groups = [TacticalGroup(rng.choice((100, 101, 102, 108, 109, 999)),
                                   tuple(rng.choices(pool, k=rng.randrange(min(size, 40)+1))))
                      for _ in range(iteration)]
            yield pool, classes, groups


def main():
    oracle = PoolOracle()
    cases = 0
    for index, (pool, classes, groups) in enumerate(fixtures()):
        expected = attack_totals(groups)
        assert oracle.totals(groups) == expected, ('totals', index)
        cases += 1
        for uid in list(dict.fromkeys(pool))[:10] + [-1, 99999]:
            assert oracle.membership(uid, groups) == first_group(uid, groups), ('membership', index, uid)
            cases += 1
        for aircraft in (False, True):
            for difficulty in range(5):
                actual = oracle.available(pool, classes, groups, aircraft, difficulty)
                expected = available(pool, classes, groups, aircraft, difficulty)
                assert actual == expected, (index, aircraft, difficulty, actual, expected)
                cases += 1
    names = ('classic_army_pool.py', 'classic_army_pool_oracle.py', 'check_classic_army_pool.py')
    result = dict(passed=True, cases=cases, source_executable_sha256=SOURCE_SHA,
                  routines=['0x5AD410', '0x59AFE0', '0x5AE490', '0x5AE4C0', '0x5AE4F0', '0x5AB350', '0x5ABF80'],
                  tool_hashes={n: hashlib.sha256((Path('outputs/toolkit')/n).read_bytes()).hexdigest() for n in names},
                  installed=False, full_behavior_parity=False,
                  limitations=['World lookup and difficulty are supplied fixtures.',
                               'Preallocated arrays; source allocation failure is not reproduced.',
                               'DE group ownership, timing and native orders remain unconnected.'])
    Path('work/classic-engine/army-pool-validation.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS', cases, 'source army-pool cases; controller component not installed')


if __name__ == '__main__':
    main()
