"""Check source field preservation, not cross-engine behavioral equivalence."""
from pathlib import Path
import csv,json
from faction_aliases import source_aliases
def read(folder,name):
    return list(csv.DictReader((Path(folder)/(name+'.tsv')).open(),delimiter='\t'))
def civ_id(value,kind):
    n=int(value)
    if kind=='unit':return str({0:0,1:1,3:2}[n])
    return str(2 if n==3 else n+10 if n>=2 else n)
mapping={int(r['source']):int(r['target']) for r in read('work','faction-class-mapping')}
assert {k:mapping[k] for k in (58,29,30,31,27,28,50,51,54)}=={58:4,29:32,30:8,31:15,27:7,28:42,50:6,51:43,54:17}
members={}
for row in read('work/faction-source','units'):
    members.setdefault(int(row['class']),set()).add(int(row['id']))
reverse={}
for cl in members:reverse.setdefault(mapping[cl],set()).add(cl)
def selectors(cl):
    if len(reverse.get(mapping[cl],set()))>1:
        return [(-1,unit) for unit in sorted(members.get(cl,set()))]
    return [(mapping[cl],-1)]
resource_map={int(r['source']):int(r['target']) for r in read('work','faction-resource-mapping')}
assert len(set(resource_map.values()))==len(resource_map)
assert [resource_map[x] for x in (59,60,61,63,214,193)]==[58,25,23,24,47,193]
checks={}
for name in ('units','costs','production','techs','requirements','effects'):
    before=source_aliases(read('work/faction-source',name));after=read('work/faction-target',name)
    for row in before:
        if 'civ' in row:row['civ']=civ_id(row['civ'],row.get('kind','unit' if name=='units' else 'tech'))
    if name=='production':
        for row in before:
            if row['kind']=='tech' and row['id'] in ('1','2','3'):
                assert row['button']=='9' and row['location']=='109'
                row['button']='10'
        bindings={(r['kind'],r['civ'],r['id'],r['location'],r['button']):r['hotkey'] for r in read('work','faction-hotkeys')}
        for row in before:
            key=(row['kind'],row['civ'] if row['kind']=='unit' else '-1',row['id'],row['location'],row['button'])
            if key in bindings:row['hotkey']=bindings[key]
    if name=='costs':
        for row in before:row['resource']=str(resource_map[int(row['resource'])])
    if name=='units':
        for row in before:row['class']=str(mapping[int(row['class'])])
    if name=='effects':
        invalid=[r for r in before if r['effect']=='2' and r['type']=='3' and r['a']==r['b']==r['c']=='-1' and float(r['d'])==0]
        assert len(invalid)==3
        before=[r for r in before if r not in invalid]
        expanded=[]
        for row in before:
            if row['type'] in ('1','6') and int(row['a'])>=0:row['a']=str(resource_map[int(row['a'])])
            if row['type'] in ('0','4','5') and int(row['b'])>=0:
                assert row['a']=='-1'
                for cl,unit in selectors(int(row['b'])):
                    expanded.append(dict(row,a=str(unit),b=str(cl)))
            else:expanded.append(row)
        before=expanded
        for rows in (before,after):
            for row in rows:row.pop('command')
    fields=tuple(before[0].keys())
    canonical=lambda rows:sorted(tuple(r[k] for k in fields) for r in rows)
    checks[name+'_exported_field_parity']=canonical(before)==canonical(after)
    assert checks[name+'_exported_field_parity'],name
from collections import defaultdict
before_tasks=defaultdict(list)
for row in source_aliases(read('work/faction-source','runtime-tasks'),'unit'):
    before_tasks[(civ_id(row['civ'],'unit'),row['unit'])].append(row)
after_tasks=defaultdict(list)
power_emitters={(r['civ'],r['unit']) for r in read('work','faction-power-emitters')} if Path('work/faction-power-emitters.tsv').exists() else set()
for row in read('work/faction-target','runtime-tasks'):
    if row['action']=='155':
        assert (row['civ'],row['unit']) in power_emitters
        continue # Independently checked in check_faction_power.py.
    after_tasks[(row['civ'],row['unit'])].append(row)
assert before_tasks.keys()==after_tasks.keys()
for key,rows in before_tasks.items():
    expected=[];default=-1
    for row in rows:
        if row['default_task']!='-1' and row['id']==row['default_task']:default=len(expected)
        targets=selectors(int(row['class'])) if int(row['class'])>=0 else [(-1,int(row['target']))]
        for cl,unit in targets:
            resources=tuple(str(resource_map.get(int(row[k]),int(row[k]))) for k in ('resource_in','resource_out','resource_multiplier','unused_resource'))
            expected.append((row['action'],str(cl),str(unit))+resources)
    actual=after_tasks[key]
    assert expected==[(r['action'],r['class'],r['target'])+tuple(r[k] for k in ('resource_in','resource_out','resource_multiplier','unused_resource')) for r in actual],key
    assert all(int(r['id'])==i and int(r['default_task'])==default for i,r in enumerate(actual)),key
checks['class_task_target_membership_and_defaults']=True
target_resources={(r['civ'],r['id']):r['value'] for r in read('work/faction-target','resources')}
for row in read('work/faction-source','resources'):
    if row['civ'] not in ('0','1','3'):continue
    key=(civ_id(row['civ'],'unit'),str(resource_map[int(row['id'])]))
    assert target_resources[key]==row['value'],key
checks['mapped_resource_initial_values']=True
checks['raw_dat_roundtrip_exact']=Path('work/factions.raw').read_bytes()==Path('work/factions-roundtrip.raw').read_bytes()
assert checks['raw_dat_roundtrip_exact']
checks['status']='Source-rule draft; not engine verified. Installation state is tracked separately.'
checks['limitations']=['Special resources are stored in isolated slots; their behaviors and action IDs still require implementation; native class choices for aircraft and special units are provisional; class mapping alone does not implement flight/shields; the separate power adapter is experimental','Converted art/audio pass static checks; explicit source repairs and one missing Harbor clip remain','Technology applicability for nonselected source civs remapped to unreachable civ IDs; needs engine validation','Terrain, icons and technology panels are translated but engine rendering is unverified','Exported fields are a subset; parity is not full gameplay equivalence']
Path('outputs/faction-parity-report.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
