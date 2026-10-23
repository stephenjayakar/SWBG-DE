"""Verify explicit splash multipliers and exact absence of collateral DAT edits."""
from pathlib import Path
import csv,json,hashlib

def read(path):
    return list(csv.DictReader(open(path),delimiter='\t'))
units={(r['civ'],r['id']):r for r in read('work/faction-source/units.tsv')}
target=read('work/faction-target-dependencies/unit-mechanics.tsv')
checked=0;splash=[]
for r in target:
    source=units[({'0':'0','1':'1','2':'3'}[r['civ']],r['unit'])]
    if int(source['type'])>=50:
        assert float(r['blast_damage'])==1,(r['civ'],r['unit'])
        checked+=1
        if float(r['blast_width'])>0:
            splash.append(dict(civ=int(r['civ']),unit=int(r['unit']),name=source['name'],
                               radius=float(r['blast_width']),level=int(r['blast_attack'])))
def digest(name):return hashlib.sha256(Path('work/'+name).read_bytes()).hexdigest()
assert digest('factions-combat-collateral.raw')==digest('factions-pre-combat.raw')
assert digest('factions-combat.raw')==digest('factions-combat-roundtrip.raw')
report=dict(combat_records_checked=checked,splash_records=splash,
            exact_collateral_audit=True,exact_roundtrip=True,engine_damage_verified=False,
            limitations=['Blast target levels, friendly fire and aircraft require engine-semantic validation',
                         'Source attack/armor and terrain modifiers remain separate from this multiplier'])
Path('outputs/faction-blast-validation.json').write_text(json.dumps(report,indent=2))
print(checked,'combat records; exact collateral audit and roundtrip PASS;',len(splash),'splash records')
