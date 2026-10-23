"""Validate the serialized aircraft, auto-scout and garrison compatibility edits."""
import csv,hashlib,json
from pathlib import Path
def rows(folder,name):
    return list(csv.DictReader((Path('work')/folder/(name+'.tsv')).open(),delimiter='\t'))
source=rows('faction-source','compat-units')
target={(r['civ'],r['unit']):r for r in rows('faction-target','compat-units')}
movement={(r['civ'],r['unit']):r for r in rows('faction-source','unit-movement')}
air={43,48,62,63,64}
counts=dict(aircraft=0,scouts=0,workers=0,troopers=0,traits=0)
for r in source:
    key=(str({0:0,1:1,3:2}[int(r['civ'])]),r['unit']);out=target[key]
    cl,typ=int(r['class']),int(r['type'])
    expected_trait=(int(r['trait'])&3)|(16 if typ==70 and cl==47 else 0)
    assert int(out['trait'])==expected_trait,(key,'trait')
    counts['traits']+=out['trait']!=r['trait']
    counts['scouts']+=bool(expected_trait&16)
    expected_fire=0
    if typ==70 and cl==58:expected_fire=-2.5;counts['workers']+=1
    if typ==70 and cl in (52,55):expected_fire=1;counts['troopers']+=1
    assert float(out['firepower'])==expected_fire,(key,'firepower')
    flying=typ>=70 and cl in air and movement[(r['civ'],r['unit'])]['fly']=='1'
    for field in ('x','y','z'):
        assert float(out[field])==(0 if flying else float(r[field])),(key,field)
    counts['aircraft']+=flying
    for field in ('projectiles','max_projectiles','secondary','can_burn'):
        assert out[field]==r[field],(key,field)
assert int(target['1','550']['trait'])&16 and int(target['2','556']['trait'])&16
assert int(target['1','83']['trait'])&16==0
assert target['1','773']['x']=='0'
graphics={int(r['graphic']):r for r in rows('faction-target','compat-graphics')}
source_graphics={int(r['graphic']):r for r in rows('faction-source','compat-graphics')}
for gid in (5548,5549,5550,5551,5552):
    assert int(graphics[gid]['sequence'])&2,(gid,'directional')
    for field in ('frames','angles','mirror'):
        assert graphics[gid][field]==source_graphics[gid][field]
# Restore exactly the four edited field families; everything else must be identical.
before=Path('work/behavior-before/factions.raw').read_bytes()
assert Path('work/behavior-restored.raw').read_bytes()==before,'Unexpected collateral DAT changes'
assert Path('work/factions.raw').read_bytes()==Path('work/factions-roundtrip.raw').read_bytes()
report=dict(counts=counts,collateral_restore_sha256=hashlib.sha256(before).hexdigest(),
            tie_static_flight_directional=True,engine_verified=False,
            caveats=['Flight uses zero collision: aircraft can overlap; air/ground targeting remains experimental.',
                     'Garrison contribution uses native DE worker and archer values; exact SWGB balance remains unverified.'])
Path('outputs/faction-behavior-validation.json').write_text(json.dumps(report,indent=2));print(report)
