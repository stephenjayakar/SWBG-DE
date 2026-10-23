"""Check commanded aircraft classifications, preserved movement, and sprite coverage.

This is a static regression check, not an in-engine movement/crash test.
"""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def rows(folder, name):
    with (Path('work') / folder / (name + '.tsv')).open() as f:
        return list(csv.DictReader(f, delimiter='\t'))


source = rows('faction-source', 'units')
target = {(r['civ'], r['id']): r for r in rows('faction-target', 'units')}
movement = {(r['civ'], r['unit']): r for r in rows('faction-target-dependencies', 'unit-movement')}
source_movement = {(r['civ'], r['unit']): r for r in rows('faction-source', 'unit-movement')}
placements = {(r['civ'], r['unit']): r for r in rows('faction-target-dependencies', 'unit-placement')}
source_placements = {(r['civ'], r['unit']): r for r in rows('faction-source', 'unit-placement')}
military_classes = {43: 13, 48: 0, 62: 13, 63: 0, 64: 0}
checked = []
for r in source:
    source_class = int(r['class'])
    if source_class not in military_classes:
        continue
    key = (str({0: 0, 1: 1, 3: 2}[int(r['civ'])]), r['id'])
    old_key = (r['civ'], r['id'])
    out = target[key]
    assert int(out['class']) == military_classes[source_class], key
    assert int(out['class']) != 38, ('commanded aircraft must not be ambient birds', key)
    for field in ('type', 'hp', 'speed', 'range', 'reload', 'projectile', 'standing', 'walking', 'attack', 'dying'):
        assert out[field] == r[field], (key, field)
    if int(r['type']) >= 30:
        for field, value in source_movement[old_key].items():
            if field == 'trait':
                value = str(int(value) & 3)  # SWGB-only ability bits have different DE meanings.
            if field != 'civ':
                assert movement[key][field] == value, (key, field)
    assert placements[key]['restriction'] == source_placements[old_key]['restriction'], key
    checked.append(key)
assert ('1', '773') in checked, 'TIE Fighter must be covered'

# Check every artwork dependency of producible aircraft in both resolutions.
roster = json.loads(Path('outputs/faction-roster-report.json').read_text())
unit_art = defaultdict(set)
for r in rows('faction-target-dependencies', 'unit-art'):
    unit_art[(r['civ'], r['unit'])].add(int(r['graphic']))
children = defaultdict(set)
for r in rows('faction-target', 'deltas'):
    if int(r['child']) >= 0:
        children[int(r['parent'])].add(int(r['child']))
art = {int(r['id']): r for r in rows('faction-target', 'art')}
verified = {(r['graphic'], r['scale']): r for r in json.loads(Path('outputs/faction-art-validation.json').read_text())['files']}
graphics = set()
production_count = 0
for source_civ, target_civ in [('1', '1'), ('3', '2')]:
    for unit in roster[source_civ]['production_roster']:
        key = (target_civ, str(unit['id']))
        if key in checked:
            production_count += 1
            graphics.update(unit_art[key])
pending = list(graphics)
while pending:
    for child in children[pending.pop()]:
        if child not in graphics:
            graphics.add(child)
            pending.append(child)
for graphic in graphics:
    if int(art[graphic]['slp']) < 0:
        continue
    for scale, folder in [(1, 'faction-roster-converted'), (2, 'faction-roster-enhanced')]:
        expected = verified[graphic, scale]
        path = Path('work') / folder / f'swgb_{graphic}.smx'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected['sha256'], (graphic, scale)

report = dict(aircraft_records=len(checked), producible_aircraft=production_count,
              graphics=len(graphics), movement_and_combat_fields_preserved_except_trait_adapter=True,
              ambient_bird_class_removed=True, engine_crash_resolution_verified=False)
Path('outputs/faction-aircraft-validation.json').write_text(json.dumps(report, indent=2))
print(report)
