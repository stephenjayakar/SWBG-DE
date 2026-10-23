"""Create DE faction tree panels from source tree nodes, filtered by reachability."""
from pathlib import Path
from collections import defaultdict
import csv,json
from reserved_unit_ids import de_unit_id
from faction_civs import FACTIONS
from tech_tree_order import reorder  # DE's panel stops at a fixed width: important buildings first
# DE resolves civilizations.json tech_tree_name only against its native civs (see faction_civs), so the
# panels are written as CivTechTrees/<native name>.json; SOURCE_CIV maps a DE slot to its SWGB civ.
SOURCE_CIV={1:'1',2:'3'}
def read(name):return list(csv.DictReader(open('work/faction-source/'+name+'.tsv'),delimiter='\t'))
roster=json.loads(Path('outputs/faction-roster-report.json').read_text())
nodes=read('tree-nodes');edges=defaultdict(list)
for r in read('tree-edges'):edges[(r['kind'],int(r['id']))].append((int(r['mode']),int(r['target'])))
units={(r['civ'],int(r['id'])):r for r in read('units')}
target={(r['kind'],int(r['civ']) if r['kind']=='unit' else -1,int(r['id'])):r for r in csv.DictReader(open('work/faction-target-dependencies/language-ids.tsv'),delimiter='\t')}
strings={int(line.split(' ',1)[0]):json.loads(line.split(' ',1)[1]) for line in Path('work/faction-package/resources/en/strings/key-value/key-value-modded-strings-utf8.txt').read_text().splitlines()}
out=Path('work/faction-package/resources/_common/dat/CivTechTrees');out.mkdir(parents=True,exist_ok=True)
for f in FACTIONS:(out/(f['legacy_tech_tree']+'.json')).unlink(missing_ok=True)  # unreachable custom names
reports={};all_units=set()
for source_civ,civ,name in [(SOURCE_CIV[f['slot']],f['slot'],f['tech_tree']) for f in FACTIONS]:
    available={r['id'] for r in roster[source_civ]['production_roster']};techs=set(roster[source_civ]['technologies']);all_units.update(available)
    selected=[r for r in nodes if r['kind']!='age' and int(r['id']) in (techs if r['kind']=='tech' else available) and not (r['kind']=='tech' and r['location']=='0')]
    selected_keys={(r['kind'],int(r['id'])) for r in selected};built=[];items=[];omitted_links=[]
    node_types={}
    for r in selected:
        key=(r['kind'],int(r['id']))
        node_types[key]='Research' if r['kind']=='tech' else 'BuildingTech' if r['kind']=='building' else 'UnitUpgrade' if int(r['required'])>=0 else 'Unit'
    for r in selected:
        kind=r['kind'];u=int(r['id']);key=(kind,u);is_tech=kind=='tech';is_building=kind=='building'
        data=target[('tech' if is_tech else 'unit',-1 if is_tech else civ,u)]
        age=next((v for mode,v in edges[key] if mode==0),1)
        assert 1<=age<=4,(key,age)
        upper=u if is_building else int(r['upper'])
        if not is_building:assert ('building',upper) in selected_keys,(key,'missing production building',upper)
        item={'Name':strings[int(data['name'])],'Node Type':node_types[key],'Link Node Type':'BuildingTech','Draw Node Type':'Building' if is_building else 'UnitTech','Use Type':'Tech' if is_tech else 'Building' if is_building else 'Unit','Node Status':'ResearchRequired' if is_building and int(r['enabling'])>=0 else 'ResearchedCompleted','Name String ID':int(data['name']),'Age ID':age,'Building ID':de_unit_id(upper),'Help String ID':int(data['help']),'Node ID':u if is_tech else de_unit_id(u),'Picture Index':int(data['icon'])}
        # Unit/building IDs in the panel are DE IDs (SWGB 900-999 moved, see reserved_unit_ids);
        # u, upper and v stay SWGB IDs for the source lookups.
        if is_building:item['Building upgraded from ID']=-1
        # Prefer a same-type upgrade predecessor over the enclosing building.
        candidates=sorted([(mode,v) for mode,v in edges[key] if mode in (1,2,3)],key=lambda x:x[0]!=({'building':1,'unit':2,'tech':3}[kind]))
        for mode,v in candidates:
            parent=({1:'building',2:'unit',3:'tech'}[mode],v)
            if parent not in selected_keys:omitted_links.append(dict(node=key,parent=parent));continue
            item['Link ID']=v if mode==3 else de_unit_id(v);item['Link Node Type']=node_types[parent]
            if is_building and mode==1:item['Building upgraded from ID']=de_unit_id(v)
            break
        if kind=='unit' and int(r['required'])>=0:item['Trigger Tech ID']=int(r['required'])
        (built if is_building else items).append(item)
    document={'civ_id':name,'civ_techs_buildings':reorder(built),'civ_techs_units':items}
    (out/(name+'.json')).write_text(json.dumps(document,indent=2))
    reports[name]={'buildings':len(built),'units_and_technologies':len(items),'omitted_cross_faction_links':omitted_links}
Path('work/faction-tree-units.txt').write_text('\n'.join(map(str,sorted(all_units))))
reports['limitations']=['Panels follow source display nodes, not every internal production-stage record','Native frontend rendering and layout are unverified','Source source-rules availability still needs engine validation']
Path('outputs/faction-tree-ui-report.json').write_text(json.dumps(reports,indent=2))
print(json.dumps(reports,indent=2))
