"""Validate nursery data, source rates, and the narrow follow-up payload.

This does not run DE or simulate its command/pathfinding implementation.
"""
from pathlib import Path
import csv,hashlib,itertools,json,re,subprocess,zlib

work=Path('work/classic-parity');patch=work/'patch'
root=Path('outputs/SWGB-DE-Factions-Draft')
prior=json.loads((work/'faction-package-manifest.before.json').read_text())
old={r['path']:r for r in prior['files']}
checks=[]
def check(ok,message):
    assert ok,message
    checks.append(message)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(base,name):return list(csv.DictReader((Path(base)/(name+'.tsv')).open(),delimiter='\t'))

raw=Path('work/original-ai/current.raw')
check(digest(raw)=='6fe0271101f3a07bc8cf695ad6cbaf8849cde01672aada59ad2f079b8a25e2ff','Current raw checkpoint')
dat='resources/_common/dat/empires2_x2_p1.dat'
check(zlib.decompress((root/dat).read_bytes(),-15)==raw.read_bytes(),'Audit reads the assembled DAT')
subprocess.run(['work/dat-build/Release/portdat.exe','nursery-report',str(raw),str(work/'current-nursery.txt')],check=True)
units={};current=None
nursery_ids={319,320,321,322,3550,3551,3552,3553}
for line in (work/'current-nursery.txt').read_text().splitlines():
    if line.startswith('UNIT '):
        words=line.split();current=(int(words[1]),int(words[2]))
        units[current]=dict(re.findall(r'(\w+)=(-?\d+)',line));units[current]['tasks']=[]
    elif line.startswith('TASK '):units[current]['tasks'].append(dict(re.findall(r'(\w+)=(-?\d+)',line)))
herdables=set()
for (c,uid),u in units.items():
    if u['class']=='58':
        targets=[t for t in u['tasks'] if t['action']=='3' and t['class']=='3' and t['enabled']=='-1']
        check(bool(targets)==(uid!=7959),f'Garrison task exists for herdable {c}/{uid}; egg excluded')
        check(u['size']=='0',f'Native herdable garrison-size semantics {c}/{uid}')
        if targets:herdables.add(uid)
    if uid in nursery_ids:
        check(u['type']=='80' and u['class']=='3' and u['capacity']=='10' and u['accepts']=='16',
              f'Nursery {c}/{uid} accepts ten herdables')
check(len(herdables)==24,'All 24 source garrisonable animal species')
translation=json.loads(Path('work/original-ai/translation.json').read_text())
check(set(translation['herdable_ids'])==herdables,'AI orders every eligible species, never the egg')
classic=json.loads(Path('work/original-ai/validation.json').read_text())
check(classic['passed'] and len(classic['parser_configurations'])==81,'Independent AI configuration matrix passed')
for r in classic['files']:
    check(digest(Path('work/original-ai/patch')/r['path'])==r['sha256'],'Fresh Classic validation: '+r['path'])
script=(patch/'resources/_common/xs/swgb_factions.xs').read_text()
condition=re.search(r'bool swgbIsNursery.*?return\((.*?)\);',script,re.S)[1]
check(set(map(int,re.findall(r'id == (\d+)',condition)))==nursery_ids,'Income covers ages and Rebel Evacuation Protocols variants')
check('float elapsed = now - swgbNurseryLastSecond;' in script and 'swgbNurseryRate(owner) * elapsed' in script,
      'Income uses elapsed game seconds and building owner')
check('if (now <= swgbNurseryLastSecond) return;' in script,'Paused clock cannot add nursery income')
source=rows('work/faction-source','unit-behavior')
rates=[float(r['workrate']) for r in source if r['civ'] in ('1','3') and int(r['unit']) in nursery_ids]
base=float(re.search(r'float swgbNurseryRate.*?float rate = ([\d.]+);',script,re.S)[1])
check(len(rates)==16 and all(rate==base for rate in rates),'Base income matches both factions, ages and Evacuation Protocols')
effects=rows('work/faction-source','effects');techs=rows('work/faction-source','techs')
effects_by_tech={int(t['id']):[e for e in effects if e['effect']==t['effect']] for t in techs if t['id'] in ('82','83','127','571')}
actual={int(t):float(v) for t,v in re.findall(r'if \(xsGetTechState\((\d+), player\) == 3\) rate = rate \* ([\d.]+);',script)}
expected={}
for tid,commands in effects_by_tech.items():
    matches=[r for r in commands if r['type']=='5' and r['c']=='13' and (r['a']=='319' or r['b']=='18')]
    check(len(matches)==1,'One source nursery work multiplier for tech '+str(tid))
    expected[tid]=float(matches[0]['d'])
check(actual==expected,'Every nursery upgrade multiplier matches source')
income=[]
for choices in itertools.product((False,True),repeat=4):
    chosen=[t for t,on in zip(sorted(expected),choices) if on]
    source_rate=base;script_rate=base
    for t in chosen:source_rate*=expected[t];script_rate*=actual[t]
    check(abs(source_rate-script_rate)<1e-12,'Source rate combination '+str(chosen))
    income.append(dict(techs=chosen,food_per_animal_per_game_second=source_rate,food_per_full_nursery_per_game_minute=source_rate*600))
resources=rows('work/original-ai/current-dat','resources')
check(all(float(r['value'])==0 for r in resources if r['id']=='254'),'Native Gurjara trickle is disabled; no double income')
check(not any(r['type'] in ('1','6') and r['a']=='254' for r in rows('work/original-ai/current-dat','effects')),
      'Research cannot enable an additional native herdable trickle')
eligible=set(json.loads(Path('outputs/faction-astromech-report.json').read_text())['eligible_unit_ids'])
current_units=rows('work/original-ai/current-dat','units')
for c in ('1','2'):
    for r in current_units:
        if r['civ']==c and int(r['id']) in eligible:
            check(int(r['class']) in (0,13,20),'Astromech query reaches current aircraft '+c+'/'+r['id'])
check('int category = 913;' in script and 'category = 900;' in script and 'category = 920;' in script
      and 'category = 938;' not in script,'Astromech lookup matches military aircraft classes')
result=subprocess.run(['work/xs-check/xs-check.exe',str(patch/'resources/_common/xs/swgb_factions.xs')],capture_output=True,text=True)
check(result.returncode==0 and 'Warning:' not in result.stdout and 'Error:' not in result.stdout,'Global XS checker passes without warnings')
strings='resources/en/strings/key-value/key-value-modded-strings-utf8.txt'
def texts(path):return {int(k):json.loads(v) for k,v in re.findall(r'^(\d+) (".*")$',path.read_text(),re.M)}
before=texts(root/strings);after=texts(patch/strings)
check(before.keys()==after.keys(),'No string IDs added or lost')
changed={k for k in before if before[k]!=after[k]}
help_rows=[r for r in rows('work/economy-repair/dependencies','language-ids') if r['kind']=='unit'
           and r['civ'] in ('0','1','2') and int(r['id']) in nursery_ids]
check(len(help_rows)==24 and changed=={int(r['help'])-79000 for r in help_rows},
      'All eight nursery tooltips in each of the three DAT faction banks changed')
check(all('Alt + right-click' in after[k] and after[k].startswith(before[k]) for k in changed),'Nursery help preserves existing information')
maps=list((patch/'resources/_common/random-map-scripts').glob('*.rms'))
check(len(maps)==20,'All faction maps covered')
for p in maps:
    name=p.relative_to(patch).as_posix()
    check(p.read_bytes()==(root/name).read_bytes() and p.read_text().count('#includeXS swgb_factions.xs')==1,
          'Map unchanged and loads global economy: '+p.name)
allowed={'resources/_common/xs/swgb_factions.xs',strings,'resources/_common/ai/SWGB Classic AI.per',
         'resources/_common/ai/SWGB Classic/swgb_classic_ai.xs'}
allowed|={f'resources/_common/ai/SWGB Classic/ce-dip-{p}.per' for p in ('bully','boomer','feeder')}
files=[]
for p in sorted(patch.rglob('*')):
    if not p.is_file():continue
    name=p.relative_to(patch).as_posix();check(name in old,'No unexpected added payload: '+name)
    sha=digest(p)
    if sha!=old[name]['sha256']:
        check(name in allowed,'Change is within reviewed scope: '+name)
        files.append(dict(path=name,sha256=sha,bytes=p.stat().st_size,before_sha256=old[name]['sha256']))
check({r['path'] for r in files}==allowed,'Exact seven-file follow-up')
out=dict(passed=True,checks=len(checks),assertions=checks,files=files,source_income=income,
         classic_checks=classic['checks'],parser_configurations=81,binary_dat_unchanged=True,
         classic_validation=classic,default_ai_unchanged=True,engine_verified=False,full_behavior_parity=False)
(work/'validation.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS',len(checks),'checks; seven changed files; runtime verification pending')
