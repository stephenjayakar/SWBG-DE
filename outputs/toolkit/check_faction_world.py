"""Validate terrain objects/restrictions and UI links in the uninstalled dataset."""
import csv,json
from pathlib import Path
def read(path):return list(csv.DictReader(open(path),delimiter='\t'))
mapping=read('work/faction-terrain-map.tsv');forward={int(x['source']):int(x['target']) for x in mapping}
reverse={int(x['target']):int(x['source']) for x in mapping if x['canonical']=='1'}
target_sources={int(x['native']):int(x['source']) for x in read('work/faction-terrain-targets.tsv')}
assert all(target_sources[t]==s for t,s in reverse.items())
source={(int(x['restriction']),int(x['terrain'])):x['value'] for x in read('work/faction-source/terrain-restrictions.tsv')}
target=read('work/faction-target-dependencies/terrain-restrictions.tsv')
for row in target:assert row['value']==source[(int(row['restriction']),target_sources[int(row['terrain'])])],row
source_spawns={}
for row in read('work/faction-source/terrain-units.tsv'):source_spawns.setdefault(int(row['terrain']),[]).append((row['slot'],row['unit'],row['density']))
target_spawns={}
for row in read('work/faction-target-dependencies/terrain-units.tsv'):target_spawns.setdefault(int(row['terrain']),[]).append((row['slot'],row['unit'],row['density']))
for t in target_sources:assert target_spawns.get(t,[])==(source_spawns.get(reverse[t],[]) if t in reverse else []),t
before=read('work/faction-source/unit-placement.tsv')
after={(r['civ'],r['unit']):r for r in read('work/faction-target-dependencies/unit-placement.tsv')}
for row in before:
    key=(str({0:0,1:1,3:2}[int(row['civ'])]),row['unit']);actual=after[key]
    for field in ('pl1','pl2','side1','side2','foundation'):
        expected=forward.get(int(row[field]),int(row[field]));assert int(actual[field])==expected,(key,field)
    expected=1 if 1901<=int(row['unit'])<=1904 and row['restriction']=='-1' else int(row['restriction'])
    assert int(actual['restriction'])==expected,key
strings={}
for line in Path('work/faction-package/resources/en/strings/key-value/key-value-modded-strings-utf8.txt').read_text(encoding='utf-8').splitlines():
    sid,value=line.split(' ',1);strings[int(sid)]=json.loads(value)
for row in read('work/faction-target-dependencies/language-ids.tsv'):
    for field in ('name','description','help'):
        sid=int(row[field])-(79000 if field=='help' else 0);assert sid in strings,(row['kind'],row['id'],field,sid)
civs=json.loads(Path('work/faction-package/resources/_common/dat/civilizations.json').read_text())['civilization_list']
actual_civs=read('work/faction-target/civs.tsv')
assert len(civs)==len(actual_civs)==3
assert [r['data_name'] for r in civs[1:]]==['BRITON-CIV','FRANKISH-CIV']  # DE DLC gate: native slot data_name
assert [r['tech_tree_name'].replace('_','-') for r in civs[1:]]==[r['name'] for r in actual_civs[1:]]
report={'terrain_restriction_cells':len(target),'terrain_spawn_roles':len(reverse),'placement_fields':True,'ui_string_references':True,'civilization_metadata_alignment':True,
    'limitations':['Unmapped DE terrains use generic land/water passability with no terrain-spawned objects','Four unused lookout records received land restrictions instead of invalid -1','Terrain textures remain native; custom technology-tree panels and icons have static checks but no engine validation','Engine rendering, pathing, resource collection and UI behavior are not established by these checks']}
Path('outputs/faction-world-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
