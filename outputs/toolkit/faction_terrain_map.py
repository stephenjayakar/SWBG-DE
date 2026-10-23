"""Derive the dataset terrain mapping from the existing map port without running it."""
import ast,csv,re
from pathlib import Path
mapping={}
for node in ast.parse(Path('work/build_maps.py').read_text()).body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='terrain' for t in node.targets):mapping.update(ast.literal_eval(node.value))
    if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and isinstance(node.value.func.value,ast.Name) and node.value.func.value.id=='terrain' and node.value.func.attr=='update':mapping.update(ast.literal_eval(node.value.args[0]))
constants={k:int(v) for k,v in re.findall(r'#const\s+(\S+)\s+(-?\d+)',Path('work/extracted/gamedata_x2/54000.bin').read_text())}
mapping.update(FARM=7,FARM_DEAD=8,FOUNDATION=27,WALKABLE_WATER=28,VOLCANIC_ROCK1=40,SHORE_BEACH=2)
# Keep source forest identities distinct: RMS replacement rules depend on them.
mapping.update(TREE_A=10,TREE_B=17,TREE_C=20,TREE_D=19,TREE_E=13,TREE_F=18,TREE_G=56)
assert len({mapping['TREE_'+c] for c in 'ABCDEFG'})==7
# Distinct DE slots (< dataset TerrainsUsed1=131) for SWGB terrains that were previously collapsed,
# so RMS patches/replace rules and carbon-rock spawns survive (faction_parity_patch.cpp mirrors this).
# TREE_G redwood uses Rainforest ground instead of DE Snow Forest.
mapping.update(SAND2=45,RED_DESERT1=42,YELLOW_PLAINS1=100,ROCK2=70,ROCK_CARBON=48,
               SNOW_DIRT=125,SNOW_ROCK=124,SNOW_GRASS1=72,PATH3=78)
rows=[(name,constants[name],target) for name,target in mapping.items()]
canonical={}
for name,source,target in rows:canonical.setdefault(target,source)
canonical[10]=constants['TREE_A']
with open('work/faction-terrain-map.tsv','w',newline='') as f:
    writer=csv.writer(f,delimiter='\t');writer.writerow(('symbol','source','target','canonical'))
    for name,source,target in rows:writer.writerow((name,source,target,int(canonical[target]==source)))
print(len(rows),'source terrain aliases;',len(canonical),'native terrain roles')
