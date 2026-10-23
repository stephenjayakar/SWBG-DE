"""Stateful differential tests of source tactical-group container operations."""
from pathlib import Path
import hashlib
import json
import random
from classic_group_state import GroupState
from classic_group_state_oracle import GroupStateOracle
from classic_engine_oracle import SOURCE_SHA


def main():
    oracle = GroupStateOracle()
    cases = 0
    sequences = []
    for seed in range(16):
        rng = random.Random(549437 + seed)
        model = GroupState(1 + seed*100)
        oracle.begin(model.next_id)
        sequence = []
        def execute(name, *args):
            nonlocal cases
            actual = getattr(oracle, name)(*args)
            expected = getattr(model, name)(*args)
            assert actual == expected, (seed, len(sequence), name, args, actual, expected)
            assert oracle.snapshot() == model.snapshot(), (seed, len(sequence), name, oracle.snapshot(), model.snapshot())
            sequence.append([name, *args])
            cases += 1
            return expected

        # Saturation, duplicate removal, allocation failure, and zero-init IDs.
        first = execute('create', 1, False)
        execute('create', 1, True)
        for uid in [7, 7] + list(range(39)):
            execute('add', first, uid, 120 + uid)
        execute('remove', first, 7)
        execute('remove', first, -1)
        execute('add', first, 100, 900)
        execute('create', 0, False)
        execute('create', 2, False)
        execute('delete', -1)
        for i in range(180):
            op = rng.choice(('create', 'add', 'remove', 'delete', 'delete_kind', 'containing'))
            handles = list(model.groups)
            if not handles:
                op = 'create'
            if op == 'create':
                handle = execute(op, 1, rng.randrange(8) == 0)
                if handle:
                    kind = rng.choice((100, 102, 108, 999))
                    model.groups[handle].kind = kind
                    oracle.set_kind(handle, kind)
                    sequence.append(['kind', handle, kind])
            elif op == 'add':
                execute(op, rng.choice(handles), rng.randrange(30), i*100)
            elif op == 'remove':
                execute(op, rng.choice(handles), rng.randrange(30))
            elif op == 'delete':
                execute(op, rng.choice([g.id for g in model.groups.values()] + [999999]))
            elif op == 'delete_kind':
                execute(op, rng.choice((-1, 100, 102, 108, 999)))
            else:
                execute(op, rng.randrange(30))
        execute('delete_kind', -1)
        sequences.append(dict(next_id=1 + seed*100, operations=sequence))
    toolkit = Path('outputs/toolkit')
    names = ('classic_group_state.py', 'classic_group_state_oracle.py', 'check_classic_group_state.py')
    report = dict(passed=True, cases=cases, sequences=sequences, source_executable_sha256=SOURCE_SHA,
                  tool_hashes={name: hashlib.sha256((toolkit/name).read_bytes()).hexdigest() for name in names},
                  installed=False, full_behavior_parity=False,
                  limitations=['Allocation is an explicit arena fixture, including failed malloc.',
                               'Path objects stay constructor-empty; populated path teardown is not tested.',
                               'Container state only; live order scheduling and save/load are not implemented.'])
    Path('work/classic-engine/group-state-validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS', cases, 'source group lifecycle mutations; not installed')


if __name__ == '__main__':
    main()
