"""Check filtered legacy tree records and generated faction panel references."""
from pathlib import Path
import csv,json
from reserved_unit_ids import load_table
from faction_civs import FACTIONS
# Panels carry DE unit IDs; the target exports are keyed by SWGB IDs (reserved_unit_ids).
swgb_id={new:old for old,new in load_table().items()}
def read(folder,name):return list(csv.DictReader(open('work/'+folder+'/'+name+'.tsv'),delimiter='\t'))
allowed=set(map(int,Path('work/faction-tree-units.txt').read_text().split()))
for name in ('tree-nodes','tree-edges'):
    source=[r for r in read('faction-source',name) if r['kind']!='unit' or int(r['id']) in allowed]
    assert source==read('faction-target-dependencies',name),name
assert Path('work/factions.raw').read_bytes()==Path('work/factions-roundtrip.raw').read_bytes()
target={(r['kind'],int(r['civ']) if r['kind']=='unit' else -1,int(r['id'])):r for r in read('faction-target-dependencies','language-ids')}
counts={}
for c,name in ((f['slot'],f['tech_tree']) for f in FACTIONS):
    panel=json.loads(Path(f'work/faction-package/resources/_common/dat/CivTechTrees/{name}.json').read_text())
    nodes=panel['civ_techs_buildings']+panel['civ_techs_units']
    keys={(r['Node Type'],r['Node ID']) for r in nodes}
    for row in nodes:
        key=('tech',-1,row['Node ID']) if row['Use Type']=='Tech' else ('unit',c,swgb_id.get(row['Node ID'],row['Node ID']))
        assert row['Name String ID']==int(target[key]['name']) and row['Help String ID']==int(target[key]['help'])
        assert row['Picture Index']==int(target[key]['icon'])
        if 'Link ID' in row:assert (row['Link Node Type'],row['Link ID']) in keys,row
    counts[name]=len(nodes)
Path('outputs/faction-tree-validation.json').write_text(json.dumps({'legacy_tree_records':True,'raw_roundtrip_exact':True,'panel_nodes':counts,'engine_rendering_verified':False},indent=2))
print('Source legacy tree, panel references and DAT roundtrip validated:',counts)
