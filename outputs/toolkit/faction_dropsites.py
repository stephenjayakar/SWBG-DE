"""Adapt DE's economic helper rules to the source processing-center IDs."""
from pathlib import Path
from collections import defaultdict
import csv,json,copy
native=json.loads(Path(r'E:\SteamLibrary\steamapps\common\AoE2DE\resources\_common\dat\dropsites.json').read_text())['drop_site_list']
units={int(r['id']):r for r in csv.DictReader(open('work/faction-source/units.tsv'),delimiter='\t') if r['civ']=='1'}
links=defaultdict(set)
for r in csv.DictReader(open('work/faction-source/unit-links.tsv'),delimiter='\t'):
    a,b=int(r['unit']),int(r['target'])
    if r['civ']=='1' and r['field'] in ('head','stack') and units[a]['type']=='80' and b in units and units[b]['type']=='80':links[a].add(b);links[b].add(a)
def family(root):
    found={root};todo=[root]
    while todo:
        for u in links[todo.pop()]:
            if u not in found:found.add(u);todo.append(u)
    return found
def prototype(name):return copy.deepcopy(next(r for r in native if r['name']==name))
result=[];roles={}
for root,name,prototype_name,groups,resources in [(109,'Command Center','Town Center',{9,10,58,7,49,33,5,15,8,32},[0,1,2,3]),(68,'Food Processing Center','Mill',{9,10,58,7,49,33,5},[0]),(562,'Carbon Processing Center','Saw Mill',{15},[1]),(584,'Ore Processing Center','Mining Camp',{8},[2]),(323,'Nova Crystal Processing Center','Mining Camp',{32},[3]),(50,'Farm','Farm',{49},[0])]:
    p=prototype(prototype_name)
    p['target_list']=[r for r in p['target_list'] if r['object_group'] in groups]
    assert {r['object_group'] for r in p['target_list']}==groups,(name,'native rule shape changed')
    p['update_ai_resource_types']=[dict(resource_type=r) for r in resources]
    p['worker_object_group']=4;p.pop('worker_object_list',None)
    for u in sorted(family(root)):
        assert u not in roles,(u,roles.get(u),name)
        roles[u]=name;result.append(dict(copy.deepcopy(p),name=name,building_id=u))
ship=next(r for r in native if r['building_id']==45 and r.get('worker_object_group')==21)
for root in (45,7353):
    for u in sorted(family(root)):
        p=copy.deepcopy(ship);p['name']='Shipyard' if root==45 else 'Harbor';p['building_id']=u
        result.append(p)
# EF harbor accepts ordinary workers as well as utility trawlers.
harbor=prototype('Town Center');harbor['target_list']=[r for r in harbor['target_list'] if r['object_group']!=63]
for u in sorted(family(7353)):result.append(dict(copy.deepcopy(harbor),name='Harbor worker drop-off',building_id=u))
dest=Path('work/faction-package/resources/_common/dat/dropsites.json');dest.write_text(json.dumps({'drop_site_list':result},indent=2))
report={'rules':len(result),'building_ids':sorted({r['building_id'] for r in result}),'dedicated_ore_and_nova_centers':True,'engine_dropoff_verified':False,'limitations':['Rules adapt DE economic helper behavior; source per-unit drop-site lists and gather tasks remain authoritative','Animal nursery garrison-food production is a separate unfinished mechanic']}
Path('outputs/faction-dropsites-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
