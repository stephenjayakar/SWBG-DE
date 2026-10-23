"""Check the power adapter's data and math, not native aura runtime behavior."""
from pathlib import Path
import csv,json,math
def read(path):return list(csv.DictReader(open(path),delimiter='\t'))
source={(r['civ'],r['unit']):r for r in read('work/faction-source/unit-behavior.tsv')}
actual={(r['civ'],r['unit']):r for r in read('work/faction-target-dependencies/unit-behavior.tsv')}
targets=read('work/faction-power-targets.tsv');emitters=read('work/faction-power-emitters.tsv')
mapped={}
for r in targets:
    key=(r['civ'],r['unit']);src=source[({'1':'1','2':'3'}[r['civ']],r['unit'])]
    assert math.isclose(float(actual[key]['workrate']),float(src['workrate'])*.25,rel_tol=1e-6),key
    assert math.isclose(float(actual[key]['workrate'])*4,float(src['workrate']),rel_tol=1e-6),key
    mapped.setdefault(r['civ'],set()).add(r['unit'])
    for upgrade in (.5,1,1.25,2):assert math.isclose(float(actual[key]['workrate'])*upgrade*4,float(src['workrate'])*upgrade,rel_tol=1e-6)
for c in ('1','2'):
    assert not mapped[c].intersection({'109','71','141','142','621','82','50','7353'}),'Power-exempt building changed'
auras=read('work/faction-target-dependencies/aura-tasks.tsv');expected_count=0
for e in emitters:
    key=(e['civ'],e['unit']);rows=[r for r in auras if (r['civ'],r['unit'])==key]
    assert {r['target'] for r in rows}==mapped[e['civ']]
    assert len(rows)==len(mapped[e['civ']])==int(e['count'])
    assert int(actual[key]['combat_ability'])&32
    for i,r in enumerate(rows):
        assert int(r['id'])==int(e['first_task'])+i
        assert r['class']=='-1' and r['attribute']=='13' and r['work1']=='3' and r['work2']=='1' and r['flags']==('7' if i==0 else '3') and r['diplomacy']=='1'
        assert r['enabled']=='-1'
        assert .25*(1+float(r['work1']))==1
        assert float(r['range'])==(5 if e['unit'] in ('1009','1013') else 10)
    expected_count+=len(rows)
assert len(auras)==expected_count
for civ in ('1','2'):
    assert {e['unit'] for e in emitters if e['civ']==civ}=={'12','498','132','20','3554','3555','3556','3557','1009','1013'}
report={'power_recipients':len(targets),'emitters':len(emitters),'aura_tasks':len(auras),'source_rate_and_multiplier_upgrade_math':True,'one_visible_radius_per_emitter':True,'work_rate_bonus':3,'engine_power_verified':False,
    'limitations':['DE circular aura uses continuous distance rather than source tile masks','Emitter stacking, construction state, overlap and aura timing need engine checks','Garrisoned Power Droids and self-powered cheat resource are not implemented','Power adapter does not implement shields or the animal nursery resource-production mechanism']}
Path('outputs/faction-power-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
