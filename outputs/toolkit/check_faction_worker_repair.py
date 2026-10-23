"""Assert explicit worker task art, temple variants and Savannah start limits."""
import csv,json,re
from pathlib import Path
read=lambda folder,name:list(csv.DictReader(open(folder+'/'+name+'.tsv'),delimiter='\t'))
source={int(r['id']):r for r in read('work/faction-source','art')}
audit=read('work','faction-task-graphics')
assert len(audit)>0
production=read('work/faction-target','production')
ages=[r for r in production if r['kind']=='tech' and r['id'] in ('1','2','3')]
assert len(ages)==3 and all(r['location']=='109' and r['button']=='10' for r in ages)
assert not [r for r in production if r['location']=='109' and r['button']=='10' and not (r['kind']=='tech' and r['id'] in ('1','2','3'))]
for r in audit:
    civ=3 if r['civ']=='2' else 1
    assert source[int(r['graphic'])]['name']==source[int(r['selector'])]['name']+'-C'+str(civ)
    assert int(source[int(r['graphic'])]['slp'])>=6
art=read('work/faction-target-dependencies','unit-art')
for civ,variant in ((1,16851),(2,16853)):
    for unit in (118,212):
        rows=[r for r in art if int(r['civ'])==civ and int(r['unit'])==unit]
        assert any(r['field']=='task-working' and int(r['graphic'])==variant for r in rows)
        assert not any(r['field'].startswith('task-') and int(r['graphic']) in (16790,16850) for r in rows)
strings={}
for line in Path('work/faction-package/resources/en/strings/key-value/key-value-modded-strings-utf8.txt').read_text(encoding='utf-8').splitlines():
    sid,value=line.split(' ',1);strings[int(sid)]=json.loads(value)
from faction_language_ids import text_ids
for unit in (30,31,104,3593,3594,3595):
    assert strings[text_ids('unit',1,unit)[0]]=='Sith Temple'
    assert strings[text_ids('unit',2,unit)[0]]=='Jedi Temple'
maptext=Path('work/faction-package/resources/_common/random-map-scripts/SWGB Factions Savannah.rms').read_text()
land=re.search(r'create_player_lands\s*\{[^{}]*\}',maptext)[0]
assert 'terrain_type SWGB_GRASS2' in land and 'base_size 18' in land and 'land_percent 0' in land
assert 'land_id' not in land
cc=re.search(r'create_object\s+SWGB_BLDG-MAIN1\s*\{[^{}]*\}',maptext)[0]
assert 'terrain_to_place_on SWGB_GRASS2' in cc
placement=read('work/faction-target-dependencies','unit-placement')
restrictions={(r['restriction'],r['terrain']):float(r['value']) for r in read('work/faction-target-dependencies','terrain-restrictions')}
for civ in ('1','2'):
    center=next(r for r in placement if r['civ']==civ and r['unit']=='109')
    assert restrictions[center['restriction'],'12']>0
assert not [r for r in read('work/faction-target-dependencies','terrain-units') if r['terrain']=='12']
for terrain in re.findall(r'create_terrain\s+\S+\s*\{[^{}]*\}',maptext):
    assert not re.search(r'base_terrain\s+SWGB_GRASS2\b',terrain),'Protected terrain overwritten'
assert re.findall(r'set_avoid_player_start_areas\s+(\d+)',maptext)==['18']*6
for tree in 'BCG':
    block=re.search(r'create_object\s+SWGB_OBJ-TREE_'+tree+r'\s*\{[^{}]*\}',maptext)[0]
    assert 'min_distance_to_players 18' in block
    assert 'terrain_to_place_on SWGB_GRASS1' in block
stragglers=re.findall(r'create_object\s+SWGB_OBJ-TREE_F\s+endif\s*\{[^{}]*\}',maptext)
assert len(stragglers)==2
assert all('min_distance_to_players 20' in b and 'max_distance_to_players 23' in b and 'terrain_to_place_on SWGB_GRASS1' in b for b in stragglers)
print('PASS: faction-resolved builder tasks, six temple variants per faction, explicit Savannah clearings')
