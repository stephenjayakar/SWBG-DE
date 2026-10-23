"""Differential checks for the source candidate gate and group validation."""
from dataclasses import replace
from pathlib import Path
import hashlib
import itertools
import json
import math
import random
import struct
from classic_engine_oracle import SOURCE_SHA
from classic_admission_model import Candidate, SelectionContext, GroupMember, candidate_admitted, group_validity
from classic_admission_oracle import AdmissionOracle


def fixtures():
    target, context = Candidate(), SelectionContext()
    yield target, context, ()
    for field, values in {
        'uid': (-1, 0, 100), 'memory_owner': (0, 1, 2, 8, 255),
        'exists': (False, True), 'owner_status': (0, 1, 2, 3, 255),
        'relation': (-1, 0, 1, 2, 3), 'state': (0, 1, 2, 3, 4, 255),
        'hp': (-100, -0.00001, -0.0, 0, 0.00001, 100, float('nan')),
    }.items():
        for value in values:
            for player in (-1, 1, 2):
                yield replace(target, **{field: value}), replace(context, player=player), ()
    for master, visible, fog, moving in itertools.product((45, 70, 80), (0, 1, 128, 255), (0, 1, 255), (0, 1, 2)):
        yield replace(target, master_type=master, visibility=visible, fog_flag=fog, moving=moving), context, ()
    for land, flags, master, cls, uid in itertools.product((0, 1), (0, 1, 2, 3, 4), (45, 70, 80), (6, 8, 32), (4, 45)):
        for tiles in ((), ((20, 20),)):
            yield replace(target, object_flags=flags, master_type=master, source_class=cls, source_id=uid), replace(context, land_group=land), tiles
    for land, force, zone, group in itertools.product((0, 1), (0, 1, 2), (0, 1, 2, 255, 257), (0, 1, 2, 255)):
        yield replace(target, object_flags=2 if land == 0 else 0, zone=zone), replace(context, land_group=land, force_different_zone=force, group_zone=group), ()
    for all_monks, reference, unit_ai, convertible in itertools.product((0, 1, 2), (False, True), (False, True), (0, 1, 2)):
        yield replace(target, convertible=convertible), replace(context, all_monks=all_monks, reference_monk=reference, monk_unit_ai=unit_ai), ()
    for cls, difficulty in itertools.product(range(70), range(5)):
        yield replace(target, source_class=cls), replace(context, difficulty=difficulty), ()
    # Source truncates float32 world coordinates toward zero, then clamps each
    # inspected tile against map bounds. Check radius edges and clipped corners.
    for x, y, width, height in ((20, 20, 100, 100), (20.99, 20.01, 100, 100),
                                (0, 0, 100, 100), (-0.9, -0.1, 100, 100),
                                (99.99, 99.99, 100, 100), (3, 8, 4, 9)):
        for tx in range(int(x) - 4, int(x) + 5):
            for ty in range(int(y) - 4, int(y) + 5):
                yield replace(target, source_class=6, master_type=80, x=x, y=y), replace(context, land_group=0, width=width, height=height), ((tx, ty),)
    rng = random.Random(549437)
    for _ in range(600):
        yield replace(target, source_class=rng.choice((6, 8, 32, 50, 58)),
                      object_flags=rng.randrange(4), master_type=rng.choice((45, 70, 80)),
                      visibility=rng.choice((0, 1, 128)), fog_flag=rng.randrange(2),
                      moving=rng.randrange(2), owner_status=rng.randrange(3),
                      state=rng.randrange(4), relation=rng.randrange(4)), replace(
                          context, difficulty=rng.randrange(5), land_group=rng.randrange(2)), ()


def group_fixtures():
    yield []
    for flags, zone, cls, exists in itertools.product((0, 1, 2, 3, 4), (0, 1, 255, 257), (32, 50, 51), (False, True)):
        yield [GroupMember(1, cls, flags, zone, (1.25, 2.5, -1.5), exists)]
    for flags1, flags2, zone1, zone2, cls1, cls2 in itertools.product((0, 2), (0, 2), (0, 1), (0, 1), (32, 50), (32, 50)):
        yield [GroupMember(1, cls1, flags1, zone1, (4, 8, 1)), GroupMember(2, cls2, flags2, zone2, (8, 2, 3))]
    for missing in range(4):
        yield [GroupMember(i + 1, 50 if i % 2 == 0 else 32, position=(i, i * 2, i * 3), exists=i != missing) for i in range(4)]
    rng = random.Random(565433)
    for _ in range(300):
        size = rng.choice((1, 2, 3, 10, 40, 128))
        flags, zone = rng.choice((0, 2)), rng.randrange(4)
        yield [GroupMember(i + 1, rng.choice((32, 50)), flags, zone,
                           tuple(rng.uniform(-100, 100) for _ in range(3))) for i in range(size)]


def main():
    oracle = AdmissionOracle()
    count = groups = 0
    for target, context, tiles in fixtures():
        got, want = oracle.candidate(target, context, tiles), candidate_admitted(target, context, tiles)
        assert got == want, (count, target, context, tiles, got, want)
        count += 1
    for members in group_fixtures():
        got, want = oracle.group(members), group_validity(members)
        assert got[:3] == want[:3] and got[4:] == want[4:], (members, got, want)
        for actual, expected in zip(got[3], want[3]):
            assert (math.isnan(actual) and math.isnan(expected)) or struct.pack('<f', actual) == struct.pack('<f', expected), (members, got, want)
        groups += 1
    names = ('classic_admission_model.py', 'classic_admission_oracle.py', 'check_classic_admission.py', 'classic_engine_oracle.py')
    report = dict(passed=True, candidate_cases=count, group_cases=groups, source_sha256=SOURCE_SHA,
                  routines={'candidate_slice': '0x005934A9..0x00593796/0x0059382E', 'group': '0x005941A0'},
                  coverage=['memory-owner filter', 'live existence/status/relation/state/HP',
                            'building visibility bypass', 'moving-unit exclusion', 'boat object flag',
                            'naval dock/wall exceptions', 'bounded seven-by-seven wall-zone scan',
                            'forced different zone', 'monk eligibility gate', 'Easy/Easiest worker exemption',
                            'mixed/missing group validation', 'float32 centroid', 'reference monk selection'],
                  limitations=['Explicit world, visibility, movement, conversion and zone fixtures; not a live observation adapter.',
                               'Candidate slice only: memory updates, retained targets, score/path selection and commands are outside these tests.',
                               'Base executable bytes; injected Expanded Fronts hooks are not executed.',
                               'No native DE match, XS/PER runtime, save/load or multiplayer validation.'],
                  installed=False, full_behavior_parity=False,
                  tool_hashes={n: hashlib.sha256((Path('outputs/toolkit') / n).read_bytes()).hexdigest() for n in names})
    Path('work/classic-engine/admission-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS {count} candidate gates and {groups} group-validation cases; not installed')


if __name__ == '__main__':
    main()
