"""Validate read-only combat export and ordered source/current command mapping."""
from copy import deepcopy
import json
from pathlib import Path
from classic_combat_data import ROOT, FIELDS, audit, read_units, table
from classic_unit_identity import sha


def main():
    report = json.loads((ROOT/'audit.json').read_text())
    for name,digest in report['inputs'].items(): assert sha(Path(name)) == digest
    for name,digest in report['exporter'].items(): assert sha(Path('outputs/toolkit')/name) == digest
    for name,digest in report['exports'].items(): assert sha(ROOT/name) == digest
    assert not report['differences'] and not report['source_only_records']
    fx = report['expanded_effects']
    assert not fx['differences'] and fx['source_applications'] == fx['current_applications']
    # One source command has neither a unit nor a class selector. Its semantics
    # are intentionally unresolved, but its full input must survive unchanged.
    assert fx['unresolved_source'] == fx['unresolved_current']
    assert fx['unresolved_source'] == [dict(effect='48',ordinal='3',type='5',a='-1',b='-1',c='0',d='1.10000002')]
    for value in report['effects'].values(): assert not value['unclassified_commands']
    source = read_units(ROOT/'source-combat.tsv')
    current = read_units(ROOT/'current-combat.tsv')
    assert audit(source,current)['differences'] == []
    # Detect collapsed/reordered duplicates, amount and combat attribute drift.
    key = next(k for k,row in source.items() if len(set(c for c,_ in row['attacks'])) < len(row['attacks'])
               and len(set(row['attacks'])) > 1)
    baseline = {key:source[key]}
    mutation_cases = 0
    for field in FIELDS:
        changed = deepcopy(baseline)
        if field in ('attacks','armor'):
            changed[key][field] = [(3,-32768),(3,32767)]
        else: changed[key][field] = '123456'
        assert set(audit(baseline,changed)['differences'][0]['fields']) == {field}
        mutation_cases += 1
    for entries in (list(reversed(baseline[key]['attacks'])),list(dict(baseline[key]['attacks']).items())):
        changed = deepcopy(baseline); changed[key]['attacks'] = entries
        assert audit(baseline,changed)['differences'][0]['fields']['attacks']
        mutation_cases += 1
    assert table('-1:-32768,3:32767,3:0') == [(-1,-32768),(3,32767),(3,0)]
    validation = dict(passed=True,records=len(current),ordered_effect_applications=fx['current_applications'],
                      unresolved_identical_selector_commands=len(fx['unresolved_source']),
                      negative_control_cases=mutation_cases,audit_sha256=sha(ROOT/'audit.json'),
                      checker_sha256=sha(Path(__file__)),installed=False,full_behavior_parity=False)
    (ROOT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    print(f'PASS {len(current)} combat records / {fx["current_applications"]} ordered effect applications; {mutation_cases} drift controls')


if __name__ == '__main__': main()
