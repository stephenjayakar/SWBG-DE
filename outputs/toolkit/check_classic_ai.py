"""Independent parser matrix and semantic checks for the Classic AI port.

These are offline checks. They do not establish DE engine or gameplay parity.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from reserved_unit_ids import de_unit_id, load_table, remap_rms
from classic_ai_extreme import untwin
from ai_difficulty_source import preprocess, constants
from classic_ai_source import parse,graph
from classic_ai_config import resolve_configuration

work=Path('work/original-ai')
# Default: the generator's staging tree. The shipped payload splits it into two mods:
#   --root payload/SWBG-Data --logic payload/SWBG-Logic
cli=argparse.ArgumentParser()
cli.add_argument('--root',type=Path,default=work/'patch',help='scripts, maps and XS (SWBG-Data)')
cli.add_argument('--logic',type=Path,default=None,help='unitlines.json (SWBG-Logic); defaults to --root')
args=cli.parse_args()
root=args.root
logic=args.logic or root
ai=root/'resources/_common/ai'
report=json.loads((work/'translation.json').read_text())
parser=Path('work/ai-parser')
revision=subprocess.check_output(['git','-C',str(parser),'rev-parse','HEAD'],text=True).strip()
assert revision=='3dfa2583b7c2ec36b85ccb421ebd0abe9ff276ba'
env=dict(os.environ,PYTHONPATH=str((parser/'src').resolve()))
# Logical single-copy view of the Hardest/Extreme twins (classic_ai_extreme.untwin).
script=untwin((ai/'SWGB Classic AI.per').read_text())
checks=0

def check(condition,message):
    global checks
    assert condition,message
    checks+=1

check(len(report['source_files'])==44,'Complete source graph, including randomized diplomacy')
check(len(report['rules'])==4522,'All source rules retained in the two faction variants')
source_nodes,source_randoms,_=graph()
all_source=source_nodes+sum(source_randoms.values(),[])
definitions={}
for n in all_source:
    if isinstance(n,list) and n[0]=='defconst' and re.fullmatch(r'-?\d+',n[2]):
        definitions.setdefault(n[1],set()).add(int(n[2]))
def goal_slots(nodes):
    result=set()
    for n in nodes:
        if not isinstance(n,list):continue
        if n and n[0] in ('goal','set-goal'):
            result.update({int(n[1])} if n[1].isdigit() else definitions[n[1]])
        result.update(goal_slots(n))
    return result
check(not (goal_slots(all_source)&(set(range(100,117))|set(range(120,125)))),'Observer/command/age-clock/placement goal slots do not collide with source goals')
check(script.count('(defrule')+sum(p.read_text().count('(defrule') for p in (ai/'SWGB Classic').glob('*.per'))==4540,
      'No dropped rules; observer/bootstrap/nursery/air-dispatch/age-clock/power-placement rules added')
check('or-list' not in script,'SWGB or-list converted to DE nested or')
check('(current-age-time' not in script,'DE current-age-time ignores SWGB Tech Levels; emulated clock used')
check(max(map(len,script.splitlines()))<255,'Legacy PER line limit')
check(len({r['identity'] for r in report['map_patches']})==20,'Map identities cannot alias one another')
for row in report['map_patches']:
    text=(root/row['file']).read_text()
    # The development install keeps SWGB unit IDs; the shipped maps use the DE IDs of the
    # reserved-range table (reserved_unit_ids), so compare against the remapped original.
    original,_=remap_rms((Path('outputs/SWGB-DE-Factions-Draft')/row['file']).read_text(),load_table())
    pattern=r'\n/\* Classic AI map identity[^\n]*\*/\neffect_amount[^\n]*\n'
    check(re.sub(pattern,'',text)==re.sub(pattern,'',original),'Map terrain/object content unchanged: '+row['file'])
resources=list(csv.DictReader((work/'current-dat/resources.tsv').open(),delimiter='\t'))
check([float(r['value']) for r in resources if r['id']=='1997']==[0,0,0],'Reserved map resource exists and starts zero')
effects=list(csv.DictReader((work/'current-dat/effects.tsv').open(),delimiter='\t'))
check(not any(r['type'] in ('1','6') and r['a']=='1997' for r in effects),'Map identity has no DAT effect writers')
lines=json.loads((logic/'resources/_common/dat/unitlines.json').read_text())['UnitLines']
check(len({r['LineID'] for r in lines})==len(lines),'Unit group IDs unique')
check(all(-400<r['LineID']<-199 for r in lines),'Unit group IDs in DE supported range')
# Since 104f8cb (2026-09-29) the mod's unitlines.json replaces DE's on purpose: DE's native
# lines and counting groups made (can-train 83) resolve to another unit, and they name AoE2
# units this dataset does not have. Neither shipped AI uses a native line, so require the
# opposite of the old "native groups preserved" check: SWGB lines only, and every line
# constant the scripts use resolves in this file.
native=json.loads(Path('E:/SteamLibrary/steamapps/common/AoE2DE/resources/_common/dat/unitlines.json').read_text())['UnitLines']
check(all(r['Identifier'].startswith('swgb-') for r in lines),'SWGB unit groups only; DE native groups removed')
native_names={n for r in native for n in ([r['Identifier']] if isinstance(r['Identifier'],str) else r['Identifier'])}
line_ids={r['LineID'] for r in lines}
for per in sorted((root/'resources/_common/ai').rglob('*.per')):
    text=per.read_text(encoding='utf-8')
    check(not set(re.findall(r'[A-Za-z][\w-]*',text))&native_names,per.name+': no DE native unit-line names')
    used={int(v) for v in re.findall(r'\(defconst \S+ (-[23]\d\d)\)',text)}
    check(used<=line_ids,per.name+': every unit-line constant resolves '+str(sorted(used-line_ids)))
# work/ keeps SWGB IDs; unitlines.json names the DE IDs (reserved range 900-999 moved).
unit_ids={de_unit_id(int(r['id'])) for r in csv.DictReader((work/'current-dat/units.tsv').open(),delimiter='\t')}
for line in lines:
    check(set(line['IDChain'])<=unit_ids,'No dangling group members: '+line['Name'])
for faction,prefix in [('EMPIRE','ce-'),('REBEL','cr-')]:
    b=report['bindings'][faction]
    # Independent expected source research identities, not DE's Archer upgrades.
    expected={'ut-laser-2':261 if prefix=='ce-' else 264,
              'ut-laser-3':251 if prefix=='ce-' else 254,
              'ut-laser-4':256 if prefix=='ce-' else 259,
              'ut-fighter-2':381 if prefix=='ce-' else 384,
              'ut-bomber-2':376 if prefix=='ce-' else 379,
              'ut-boat-grenade-2':704 if prefix=='ce-' else 706}
    for name,value in expected.items():check(b[prefix+name]==value,faction+' '+name)
    check(report['groups']['bldg-aabattery'][0]==1869 and b[prefix+'bldg-aabattery']==report['group_ids']['bldg-aabattery'],'Anti-Air Battery uses the unit enabled by source research 731')
    check(f'(defconst {prefix}FOOD 2)' in script,'Source goal category FOOD preserved')
    check(f'(release-escrow {prefix}FOOD)' not in script,'Food resources cannot alias the FOOD goal category')
    check(f'(release-escrow {prefix}NOVA)' not in script,'Gold resources cannot alias the NOVA goal category')
check('(release-escrow food)' in script and '(release-escrow gold)' in script,'Native resource identifiers used')
check('(defconst ce-ut-laser-2 261)' in script and '(defconst cr-ut-laser-2 264)' in script,'Distinct faction research bindings')

lintroot=work/'matrix/resources/_common/ai'
lintroot.mkdir(parents=True,exist_ok=True)
(lintroot/'SWGB Classic').mkdir(exist_ok=True)
shutil.copy2(ai/'SWGB Classic/swgb_classic_ai.xs',lintroot/'SWGB Classic/swgb_classic_ai.xs')
# DE resolves (include "swgb_classic_ai.xs") from resources/_common/xs; the parser looks beside the script.
shutil.copy2(root/'resources/_common/xs/swgb_classic_ai.xs',lintroot/'swgb_classic_ai.xs')
# This is generated scratch only; resolve and check containment before cleanup.
for p in (lintroot/'SWGB Classic').glob('*.per'):
    assert p.resolve().is_relative_to((work/'matrix').resolve())
    p.unlink()
(lintroot/'SWGB Classic AI.ai').write_bytes(b'')
results=[]
levels=('easiest','easy','moderate','hard','hardest','extreme')
configs=[(level,mode,200,'TINY-MAP') for level in levels
         for mode in ('random-map','DEATH-MATCH','WONDER-RACE','DEFEND-WONDER')]
configs += [('hard','random-map',cap,size) for cap,size in [(25,'SMALL-MAP'),(500,'LARGE-MAP'),(1000,'GIANT-MAP')]]
configs=[(*config,personality) for config in configs for personality in ('bully','boomer','feeder')]
for level,mode,cap,size,personality in configs:
    symbols={'DIFFICULTY-'+level.upper(),f'POPULATION-CAP-{cap}',size,'VICTORY-CONQUEST','TEAMS-LOCKED'}
    if mode!='random-map':symbols.add(mode)
    loaded,loader=resolve_configuration(ai,symbols,personality)
    check(len(loader['draws'])<=1,'At most one source personality draw')
    if loader['draws']:
        selected=loader['draws'][0]['selected'].split('ce-',1)[1]
        check('SWGB Classic/cr-'+selected+'.per' in loader['loaded'],'Both factions reuse the same personality')
        weights=[w for w,_ in loader['draws'][0]['options']]
        expected=([25] if mode=='WONDER-RACE' else [15] if mode=='DEFEND-WONDER'
                  else [20,5,5] if level=='moderate' else [10,10,10])
        check(weights==expected,'Original personality weights')
    # constants() rejects conflicting declarations even if the parser would miss them.
    constants(loaded)
    (lintroot/'SWGB Classic AI.per').write_text(loaded)
    name=f'{level}-{mode}-{cap}-{size}-{personality}'
    dest=work/'matrix'/(name+'.json')
    result=subprocess.run([sys.executable,'-m','aoe2_ai_lab','lint-package',str(lintroot),
        '--output',str(dest),'--fail-confidence','conditional','--fail-level','info'],
        capture_output=True,text=True,env=env)
    details=json.loads(dest.read_text())
    check(result.returncode==0 and not details['finding_groups'],name+': '+str(details.get('finding_groups'))[:2000])
    results.append(dict(difficulty=level,mode=mode,population=cap,map_size=size,personality=personality,
                        loader=loader,rules=loaded.count('(defrule'),findings=0))
    print('PASS',name,flush=True)

# Source cap tables must load on every supported increment, including easy levels.
for cap in range(25,1001,25):
    for level in levels:
        loaded=preprocess(script,{'DIFFICULTY-'+level.upper(),f'POPULATION-CAP-{cap}','TINY-MAP'})
        values=constants(loaded)
        check(values.get('ce-pop-cap')==cap and values.get('cr-pop-cap')==cap
              and 0<values.get('ce-unit-max',0)<=cap and values.get('ce-unit-max')==values.get('cr-unit-max'),
              'Population '+str((cap,level)))

xs=ai/'SWGB Classic/swgb_classic_ai.xs'
# Absolute: Windows CreateProcess does not resolve a relative path with forward slashes.
result=subprocess.run([str(Path('work/xs-check/xs-check.exe').resolve()),str(xs)],capture_output=True,text=True)
xs_output=re.sub(r'\x1b\[[0-9;]*m','',result.stdout+'\n'+result.stderr)
check(result.returncode==0 and 'No errors found' in xs_output
      and not re.search(r'\b(?:Warning|Error):',xs_output),'XS observer: '+xs_output[-1200:])
payload=[dict(path=p.relative_to(root).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
         for p in sorted(root.rglob('*')) if p.is_file()]
result=dict(passed=True,checks=checks,parser_commit=revision,parser_configurations=results,files=payload,
            engine_verified=False,gameplay_verified=False,full_behavior_parity=False)
(work/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS',checks,'checks;',len(results),'parser configurations; runtime verification pending')
