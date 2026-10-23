"""Read back job portraits and explicit melee/conversion data from the built DAT."""
from pathlib import Path
import csv,json,math,subprocess

def read(folder,name):
    return list(csv.DictReader(open(Path(folder)/(name+'.tsv')),delimiter='\t'))
subprocess.run(['work/dat-build/Release/portdat.exe','de-interactions','work/factions.raw','work/faction-interactions'],check=True)
source=read('work/source-interactions','interactions')
target={(int(r['civ']),int(r['id'])):r for r in read('work/faction-interactions','interactions')}
tasks=read('work/faction-interactions','interaction-tasks')
resources={(int(r['civ']),int(r['id'])):float(r['value']) for r in read('work/faction-source','resources')}
worker_count=force_count=ability_count=0
for row in source:
    c=int(row['civ']);civ={0:0,1:1,3:2}[c];uid=int(row['id']);out=target[civ,uid]
    if row['class']=='58' and civ in (1,2):
        assert out['icon']==target[civ,83]['icon'],(civ,uid)
        worker_count+=1
    if row['class']!='50':continue
    force_count+=1
    assert out['class']=='6' and out['reload']==row['reload'],(civ,uid)
    attacks=[t for t in tasks if int(t['civ'])==civ and int(t['unit'])==uid and t['action']=='7']
    assert attacks and all((t['autosearch'],t['enable_targeting'],t['combat_flag'],t['diplomacy'])==('1','1','1','5') for t in attacks),(civ,uid)
    conversion=[t for t in tasks if int(t['civ'])==civ and int(t['unit'])==uid and t['action']=='104' and t['enable_targeting']=='1' and t['combat_flag']=='1' and t['diplomacy']=='2']
    if conversion:
        ability_count+=1
        assert out['charge_type']=='-4' and int(out['charge_event'])==int(resources[c,5]) and out['charge_target']=='38',(civ,uid,out)
        assert math.isclose(float(out['max_charge'])/float(out['recharge']),15,rel_tol=1e-5)
        assert out['button_icon']=='101' and out['button_short']=='898001' and out['button_long']=='898002'
        assert out['displayed_reload']=='1'
    else:assert out['charge_type']=='0',(civ,uid)
assert worker_count==48
assert target[1,44]['charge_type']==target[1,115]['charge_type']=='-4'
assert target[1,180]['charge_type']=='0','Padawan must not gain conversion'
assert target[2,74]['charge_type']==target[2,136]['charge_type']=='-4'
assert target[2,232]['charge_type']=='0'
text=Path('work/faction-package/resources/en/strings/key-value/key-value-modded-strings-utf8.txt').read_text()
assert '898001 "Force Conversion"' in text and '898002 ' in text
report=dict(worker_job_records=worker_count,force_units=force_count,explicit_conversion_units=ability_count,
    melee_reload_preserved=True,conversion_adapter='native Sun Ce, source task times/range',engine_verified=False)
Path('outputs/faction-interaction-validation.json').write_text(json.dumps(report,indent=2))
print(report)
