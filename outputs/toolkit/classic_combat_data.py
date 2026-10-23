"""Read-only source/current combat-table audit; never substitute static upgrades."""
from collections import Counter
import csv
import json
from pathlib import Path
import subprocess
import zlib
from classic_unit_identity import CURRENT, SOURCE, PACKAGE, DAT, sha
from classic_combat_attribute import modify

ROOT = Path('work/classic-engine/combat-data')
TOOLKIT = Path('outputs/toolkit')
FIELDS = ('hp', 'base_armor', 'reload', 'max_range', 'min_range', 'defense_terrain', 'attacks', 'armor')


def table(text):
    values = [tuple(map(int, pair.split(':'))) for pair in text.split(',') if pair]
    assert all(-32768 <= value <= 32767 for pair in values for value in pair)
    return values


def read_units(path):
    rows = list(csv.DictReader(path.open(), delimiter='\t'))
    result = {}
    for row in rows:
        key = (int(row['civ']), int(row['slot']))
        assert key not in result and int(row['id']) == key[1] == int(row['copy'])
        for name in ('attacks', 'armor'):
            row[name] = table(row[name])
        result[key] = row
    return result


def audit(source, current):
    differences = []
    for key, row in current.items():
        assert key in source, ('Unmapped combat unit', key)
        old = source[key]
        assert old['type'] == row['type']
        changed = {f: dict(source=old[f], current=row[f]) for f in FIELDS if old[f] != row[f]}
        if changed:
            differences.append(dict(civ=key[0], slot=key[1], fields=changed))
    statistics = {}
    for label, rows in (('source', source), ('current', current)):
        statistics[label] = dict(records=len(rows))
        for name in ('attacks', 'armor'):
            all_entries = [pair for row in rows.values() for pair in row[name]]
            duplicates = [dict(civ=k[0], slot=k[1], entries=r[name]) for k, r in rows.items()
                          if len(set(c for c, _ in r[name])) != len(r[name])]
            statistics[label][name] = dict(entries=len(all_entries),
                classes=sorted(set(c for c, _ in all_entries)),
                duplicate_rows=duplicates, negative_amounts=sum(v < 0 for _, v in all_entries),
                maximum_length=max(len(r[name]) for r in rows.values()))
    return dict(statistics=statistics, differences=differences,
                changed_fields=dict(Counter(f for row in differences for f in row['fields'])),
                source_only_records=[list(k) for k in source.keys() - current.keys()])


def effect_coverage(rows, path):
    """Apply source table semantics independently to each base template.

    These are potential applications, not a reachable research sequence. A
    current-data result means its input was evaluated by the source model;
    it does not establish how DE executes that command.
    """
    by_id, by_class = {}, {}
    for key, row in rows.items():
        by_id.setdefault(key[1], []).append((key, row))
        by_class.setdefault(int(row['class']), []).append((key, row))
    commands = list(csv.DictReader(path.open(), delimiter='\t'))
    noops, unknown = [], []
    affected = Counter()
    for command in commands:
        kind, attr = int(command['type']), int(command['c'])
        if attr not in (8, 9) or kind not in (0, 4, 5, 10, 14, 15):
            continue
        affected[str(kind)] += 1
        if kind not in (0, 4, 5):
            unknown.append(command)
            continue
        value = float(command['d'])
        if not value.is_integer() or abs(value) > 65535:
            unknown.append(command)
            continue
        selector = (int(value) >> 8) & 255
        unit, cls = int(command['a']), int(command['b'])
        if (unit >= 0) == (cls >= 0):
            unknown.append(command)
            continue
        targets = by_id.get(unit, []) if unit >= 0 else by_class.get(cls, [])
        name = 'armor' if attr == 8 else 'attacks'
        missing = [list(key) for key, row in targets if
                   (selector >= len(row[name]) if kind == 0 else selector not in {c for c, _ in row[name]})]
        if missing:
            noops.append(dict(command=command, selector=selector, table=name, units=missing))
        for _, row in targets:
            after = modify(row[name], kind, value)
            assert len(after) == len(row[name]) and [c for c,_ in after] == [c for c,_ in row[name]]
    return dict(command_count=len(commands), attribute_command_types=dict(affected),
                absent_selector_noops=noops, unclassified_commands=unknown,
                limitation='Independent base-template applications using verified source semantics; not DE execution or a reachable research sequence.')


def expanded_commands(rows, path):
    by_id, by_class = {}, {}
    for key,row in rows.items():
        by_id.setdefault(key[1], []).append(key)
        by_class.setdefault(int(row['class']), []).append(key)
    result, unresolved = {}, []
    for command in csv.DictReader(path.open(), delimiter='\t'):
        mode, attr = int(command['type']), int(command['c'])
        if mode not in (0,4,5) or attr not in (0,8,9,10,12,15,16,19,20,22): continue
        unit,cls = int(command['a']),int(command['b'])
        if (unit >= 0) == (cls >= 0):
            unresolved.append(command)
            continue
        for civ,slot in (by_id.get(unit,[]) if unit >= 0 else by_class.get(cls,[])):
            key = (int(command['effect']),civ,slot)
            result.setdefault(key,[]).append((mode,attr,command['d']))
    return result, unresolved


def compare_effects(source,current):
    before, unresolved_source = expanded_commands(source,ROOT/'source-effects.tsv')
    after, unresolved_current = expanded_commands(current,ROOT/'current-effects.tsv')
    differences = [dict(effect=k[0],civ=k[1],slot=k[2],source=before.get(k,[]),current=after.get(k,[]))
                   for k in sorted(before.keys() | after.keys()) if before.get(k,[]) != after.get(k,[])]
    return dict(source_applications=sum(map(len,before.values())),
                current_applications=sum(map(len,after.values())), differences=differences,
                unresolved_source=unresolved_source,unresolved_current=unresolved_current,
                limitation='Ordered commands after unit/class selector expansion; not native effect execution.')


def main():
    manifest = json.loads(Path('outputs/faction-package-manifest.json').read_text())
    expected = next(x['sha256'] for x in manifest['files'] if x['path'] == DAT)
    assert sha(PACKAGE / DAT) == expected
    assert zlib.decompress((PACKAGE / DAT).read_bytes(), -15) == CURRENT.read_bytes()
    inputs = {str(p): sha(p) for p in (CURRENT, SOURCE, PACKAGE / DAT)}
    subprocess.run(['work/dat-build/Release/portdat.exe', 'classic-combat-report',
                    str(CURRENT), str(ROOT), str(SOURCE)], check=True)
    assert all(sha(Path(p)) == value for p, value in inputs.items())
    source, current = (read_units(ROOT / f'{s}-combat.tsv') for s in ('source', 'current'))
    result = audit(source, current)
    result['effects'] = {s: effect_coverage(rows, ROOT / f'{s}-effects.tsv')
                         for s, rows in (('source', source), ('current', current))}
    result['expanded_effects'] = compare_effects(source,current)
    result.update(inputs=inputs, exporter={name: sha(TOOLKIT / name)
                  for name in ('main.cpp', 'classic_combat_report.h', 'classic_combat_data.py','classic_combat_attribute.py')},
                  exports={p.name: sha(p) for p in sorted(ROOT.glob('*.tsv'))},
                  installed=False, full_behavior_parity=False,
                  limitations=['Base DAT templates, not upgraded live unit attributes.',
                               'Effect rows exported in order but not yet simulated.',
                               'Native getter behavior for absent/duplicate damage classes remains unverified.'])
    (ROOT / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(records=result['statistics']['current']['records'],
                         changed_fields=result['changed_fields'],
                         expanded_effect_differences=len(result['expanded_effects']['differences']),
                         effect_coverage={s: {k: len(v) if isinstance(v, list) else v for k,v in e.items()
                                              if k != 'limitation'} for s,e in result['effects'].items()},
                         duplicate_rows={s: {n: len(result['statistics'][s][n]['duplicate_rows'])
                                             for n in ('attacks', 'armor')} for s in ('source', 'current')}), indent=2))


if __name__ == '__main__':
    main()
