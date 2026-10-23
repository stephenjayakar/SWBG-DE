"""Check generated army-count bindings against original executable classification."""
from collections import Counter
from functools import lru_cache
from pathlib import Path
import csv
import hashlib
import json
import re
from classic_engine_oracle import Oracle, SOURCE_SHA, TACTICAL
from classic_ai_source import graph, parse, specialize


def main():
    work = Path('work/original-ai')
    patch = work/'patch'
    report = json.loads((work/'translation.json').read_text())
    lines = json.loads((patch/'resources/_common/dat/unitlines.json').read_text())['UnitLines']
    by_id = {line['LineID']: line for line in lines}
    source = list(csv.DictReader(Path('work/faction-source/units.tsv').open(), delimiter='\t'))
    traits = {(int(r['civ']), int(r['unit'])): int(r['trait']) for r in
              csv.DictReader(Path('work/faction-source/compat-units.tsv').open(), delimiter='\t')}
    current = list(csv.DictReader((work/'current-dat/units.tsv').open(), delimiter='\t'))
    oracle = Oracle()
    classify = lru_cache(None)(oracle.classification)
    checks = 0

    def check(condition, label):
        nonlocal checks
        assert condition, label
        checks += 1

    pools = {'source-ground-soldier-line': 0x118, 'source-warboat-line': 0x198}
    # Execute the source getters too: aircraft totals must not enter either fact.
    for ground, boats, aircraft in ((0, 0, 100), (1, 0, 40), (0, 12, 50), (200, 30, 7)):
        oracle.reset()
        oracle.write(TACTICAL + 0x11c, ground)
        oracle.write(TACTICAL + 0x19c, boats)
        oracle.write(TACTICAL + 0x13c, aircraft)
        check(oracle.call(0x5A5560) == ground, 'Source ground getter')
        check(oracle.call(0x5A55C0) == boats, 'Source warboat getter')
    for civ, target in ((1, 1), (3, 2)):
        present = {int(r['id']) for r in current if int(r['civ']) == target}
        records = {int(r['id']): r for r in source if int(r['civ']) == civ}
        for name, offset in pools.items():
            expected = {uid for uid, row in records.items() if uid in present
                        and offset in classify(int(row['class']), traits[civ, uid])}
            actual = set(report['groups'][name]) & present
            check(actual == expected, (civ, name, sorted(actual ^ expected)))
            check(by_id[report['group_ids'][name]]['IDChain'] == report['groups'][name], name)
            for uid in present & records.keys():
                check((uid in actual) == (uid in expected), (civ, name, uid))

    # Aliases may share an ID only if ordered members AND building semantics match.
    signatures = {}
    for name, members in report['groups'].items():
        line = by_id[report['group_ids'][name]]
        signature = (name.startswith('bldg-'), tuple(members))
        check((line['Building'], tuple(line['IDChain'])) == signature, ('alias', name))
        if signature in signatures:
            check(signatures[signature] == line['LineID'], ('duplicate allocation', name))
        signatures[signature] = line['LineID']
    check(len(set(report['group_ids'].values())) == len(signatures), 'No unrelated alias collision')

    nodes, randoms, _ = graph()
    generated = []
    ai = patch/'resources/_common/ai'
    for path in sorted(ai.rglob('*.per')):
        generated += parse(path.read_text())

    def walk(nodes):
        for node in nodes:
            if isinstance(node, list) and node:
                yield node
                yield from walk(node)

    rewritten = {}
    for faction, prefix in (('EMPIRE', 'ce-'), ('REBEL', 'cr-')):
        expected = Counter()
        for node in walk(specialize(nodes, faction) + sum(
                (specialize(part, faction) for part in randoms.values()), [])):
            if node[0] in ('soldier-count', 'warboat-count'):
                name = 'source-ground-soldier-line' if node[0] == 'soldier-count' else 'source-warboat-line'
                expected[(name, node[1], node[2])] += 1
        actual = Counter()
        for node in walk(generated):
            if node[0] == 'unit-type-count' and node[1] in {prefix + name for name in pools}:
                actual[(node[1][len(prefix):], node[2], node[3].removeprefix(prefix))] += 1
        check(actual == expected, ('count predicates preserved', faction, actual - expected, expected - actual))
        rewritten[faction] = sum(actual.values())
    check(not any(n[0] in ('soldier-count', 'warboat-count') for n in walk(generated)), 'No native total-count leftovers')
    # Attack/defend counts need actual tactical group membership; do not silently rewrite them.
    for head in ('attack-soldier-count', 'defend-soldier-count', 'defend-warboat-count'):
        check(any(n[0] == head for n in walk(generated)), ('group-dependent fact retained', head))

    payload = {p.relative_to(patch).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(patch.rglob('*')) if p.is_file()}
    result = dict(passed=True, checks=checks, source_executable_sha256=SOURCE_SHA,
                  rewritten_predicates=rewritten, named_groups=len(report['groups']),
                  distinct_groups=len(signatures), files=payload, engine_verified=False,
                  full_behavior_parity=False,
                  limitations=['DE live count lifecycle is unverified.',
                               'Attack/defend counts and separate aircraft commands remain unported.'])
    result['tool_hashes'] = {name: hashlib.sha256((Path('outputs/toolkit')/name).read_bytes()).hexdigest()
                             for name in ('check_classic_counts.py', 'classic_engine_oracle.py',
                                          'classic_ai_bindings.py', 'port_classic_ai.py')}
    (work/'count-validation.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}, indent=2))


if __name__ == '__main__':
    main()
