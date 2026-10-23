"""Compare source post-ranking control flow, not source path geometry."""
from pathlib import Path
import hashlib
import itertools
import json
import math
import random
import struct
from classic_engine_oracle import SOURCE_SHA
from classic_path_model import PathTarget, choose_path
from classic_path_oracle import PathOracle


def fixtures():
    yield [], {}
    for zone, direct, transport, obstruction, use_transport, sn241 in itertools.product(
            (0, 1, 2), (0, 1, 2), (0, 1, 2), (0, 1, 2), (0, 1, 2), (0, 1)):
        yield [PathTarget(1, zone, direct=direct, transport=transport, obstruction=obstruction,
                          blockers=(3, 4)), PathTarget(2, direct=1)], dict(can_transport=use_transport, sn241=sn241)
    for size in (0, 1, 2, 18, 19, 20, 21, 40):
        blockers = tuple(range(100, 100 + size))
        for missing in ((), blockers[:2], blockers):
            yield [PathTarget(1, obstruction=1, blockers=blockers, missing_blockers=missing)], {}
    yield [PathTarget(1, obstruction=1, blockers=(3, 3, 4, 3))], {}
    for exception in ((), (1,), (22,), (23,), (16,), (15,), (22, 23), (99,)):
        for retry in (0, 1, 2, -1):
            for zone in (0, 1):
                yield [PathTarget(1, zone, transport=1, exception_terrains=exception, plain_retry=retry)], dict(can_transport=1)
    for ranges in ((), (None,), (1,), (30,), (20, 30), (1, 4, 8), (8, None, 2.5),
                   (-1, 2), (float('nan'),), (float('nan'), 8), (8, float('nan')), (0,)):
        yield [PathTarget(1, direct=1)], dict(ranges=ranges)
    for size in (0, 1, 2, 5):
        targets = [PathTarget(i + 1, exists=i % 2 == 0) for i in range(size)]
        for resume in (None, 0, 1, size, size + 1):
            for ticks in ((0,) * size, (99,) * size, (100,) * size):
                yield targets, dict(resume=resume, ticks=ticks)
    for start, ticks, budget in ((1000, (1099, 1100), 100), (1000, (999,), 100),
                                (0xFFFFFFF0, (0x10,), 32), (0xFFFFFFF0, (0xF,), 32),
                                (0, (0,), 0)):
        yield [PathTarget(1), PathTarget(2), PathTarget(3, direct=1)], dict(start_time=start, ticks=ticks, time_budget=budget)
    rng = random.Random(593938)
    for _ in range(240):
        targets = [PathTarget(i + 1, rng.randrange(2), rng.randrange(5) != 0,
                              rng.randrange(2), rng.randrange(2), rng.randrange(2),
                              tuple(range(100 + i * 3, 103 + i * 3))) for i in range(rng.randrange(1, 12))]
        yield targets, dict(can_transport=rng.randrange(2), sn241=rng.randrange(2),
                            resume=rng.choice((None, 0, 1)), ticks=(rng.randrange(150),) * len(targets))


def main():
    oracle = PathOracle()
    count = 0
    for targets, options in fixtures():
        got, want = oracle.choose(targets, **options), choose_path(targets, **options)
        gr, wr = got.pop('radius'), want.pop('radius')
        assert got == want, (count, targets, options, got, want)
        assert (math.isnan(gr) and math.isnan(wr)) or struct.pack('<f', gr) == struct.pack('<f', wr), (count, gr, wr)
        count += 1
    names = ('classic_path_model.py', 'classic_path_oracle.py', 'check_classic_paths.py',
             'classic_admission_oracle.py', 'classic_engine_oracle.py', 'classic_air_model.py')
    report = dict(passed=True, cases=count, source_sha256=SOURCE_SHA,
                  routine_slice='0x00593938..0x005940C1',
                  coverage=['minimum weapon-range cap and missing members', 'strict path-result comparisons',
                            'transport eligibility and strategic number 241', 'exception terrain checks and plain retry',
                            'obstruction target queue including duplicates and 19-entry limit',
                            'memory attack-attempt updates', 'rank continuation and unsigned clock wrap'],
                  limitations=['Explicit geometry/path answers; actual source pathfinding is not executed.',
                               'Source blocker memory refresh and scratch path construction/destruction are stubs.',
                               'Target admission, scoring, previous-priority processing and live DE orders are outside this slice.',
                               'No native DE XS/PER runtime, saved game or multiplayer validation.'],
                  installed=False, full_behavior_parity=False,
                  tool_hashes={n: hashlib.sha256((Path('outputs/toolkit') / n).read_bytes()).hexdigest() for n in names})
    Path('work/classic-engine/path-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS {count} source post-ranking path-choice cases; geometry is fixture-supplied; not installed')


if __name__ == '__main__':
    main()
