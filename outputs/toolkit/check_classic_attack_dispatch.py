"""End-to-end source ground/naval/air dispatch through actual group creation."""
from pathlib import Path
import hashlib
import json
import random
from classic_group_state import GroupState
from classic_attack_dispatch import dispatch
from classic_attack_dispatch_oracle import DispatchOracle
from classic_engine_oracle import SOURCE_SHA


def fixtures():
    rng = random.Random(549437)
    for n in (0, 1, 2, 5, 39, 40, 41, 65):
        classes, positions = {}, {}
        ground, air = list(range(1,n+1)), list(range(1001,1001+n))
        for i, uid in enumerate(ground + air):
            classes[uid] = rng.choice((32, 50, 51)) if uid < 1000 else rng.choice((48, 59, 63))
            positions[uid] = (i * 3, (i % 5) * 7, int(i * 3 >= 120))
        for difficulty in (0, 2, 3, 4):
            for gp, ap in ((0, 100), (100, 0), (75, 50), (100, 100), (1, 1)):
                for fail_after in (None, 0, 1):
                    yield dict(ground=ground, air=air, classes=classes, positions=positions,
                               ground_percent=gp, air_percent=ap, difficulty=difficulty,
                               radius=20, now=8765, fail_after=fail_after)

    # Naval admission deliberately retains stale IDs. Missing objects consume
    # first-40 slots, and a missing first ID cancels this domain entirely.
    for n in (1, 5, 39, 40, 41, 65):
        for missing in ((), (0,), (1,), tuple(range(1, 40))):
            for duplicate in (False, True):
                boats = list(range(2001, 2001+n))
                classes = {uid: 20 for i, uid in enumerate(boats) if i not in missing}
                positions = {uid: (i * 3, (i % 5) * 7, int(i >= 20)) for i, uid in enumerate(boats)}
                classes.update({1: 32, 2: 32, 1001: 48, 1002: 48})
                positions.update({1: (500, 0, 0), 2: (503, 0, 0), 1001: (600, 0, 0), 1002: (603, 0, 0)})
                if duplicate:
                    boats = [uid for uid in boats for _ in range(2)]
                # ID 1 is pre-grouped by the test; naval admission must skip it.
                boats = [1] + boats
                for difficulty in (0, 3, 4):
                    for bp in (1, 50, 100):
                        for fail_after in (None, 1, 2):
                            yield dict(ground=[1, 2], air=[1001, 1002], boats=boats,
                                       classes=classes, positions=positions, ground_percent=100,
                                       air_percent=100, boat_percent=bp, difficulty=difficulty,
                                       radius=20, now=8765, fail_after=fail_after)


def main():
    oracle = DispatchOracle()
    cases = 0
    for fixture in fixtures():
        model = GroupState(7)
        oracle.begin(7)
        # Existing groups must retain their members and insertion order.
        if fixture['ground']:
            m, o = model.create(), oracle.create()
            model.groups[m].kind = 101
            oracle.set_kind(o, 101)
            model.add(m, fixture['ground'][0], 123)
            oracle.add(o, fixture['ground'][0], 123)
        for repeat in range(2):
            expected_stops = dispatch(model, **fixture)
            actual_stops = oracle.dispatch(**fixture)
            assert actual_stops == expected_stops, (cases, repeat, fixture, actual_stops, expected_stops)
            assert oracle.snapshot() == model.snapshot(), (cases, repeat, fixture, oracle.snapshot(), model.snapshot())
            cases += 1
        if cases % 60 == 0:
            print('PASS dispatch fixtures', cases, flush=True)
    names = ('classic_attack_dispatch.py', 'classic_attack_dispatch_oracle.py', 'check_classic_attack_dispatch.py',
             'classic_group_state.py', 'classic_group_state_oracle.py', 'classic_air_model.py', 'classic_army_pool.py')
    report = dict(passed=True, cases=cases, source_executable_sha256=SOURCE_SHA,
                  tool_hashes={n: hashlib.sha256((Path('outputs/toolkit')/n).read_bytes()).hexdigest() for n in names},
                  installed=False, full_behavior_parity=False,
                  limitations=['World lookup, geometry queries and stop delivery are explicit fixtures.',
                               'Object ownership is fixed to the issuing player; null-owner objects are not tested.',
                               'Targeting and live commands after group creation are not tested.'])
    Path('work/classic-engine/dispatch-validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS', cases, 'source end-to-end dispatch fixtures; not installed')


if __name__ == '__main__':
    main()
