from pathlib import Path
import re,json
root=Path('work/extracted/gamedata_x2')
out=Path('outputs/SWGB-DE-Maps/resources/_common/random-map-scripts');out.mkdir(parents=True,exist_ok=True)
maps={54201:'Desert',54202:'WaterMass',54203:'Sea',54204:'Forest',54205:'Shoreline',54206:'LandMass',54207:'Nova Lake',54209:'Nova Assault',54210:'Precipice',54211:'Islands',54212:'Large Sea',54217:'Rivers',54218:'Team Islands',54219:'Tundra',54220:'Flats',54221:'Swamp',54222:'Savannah',54226:'Ice Lake'}
terrain={'GRASS1':0,'GRASS2':12,'GRASS3':9,'DIRT1':6,'DIRT2':11,'LEAVES':5,'SAND1':14,'SAND2':14,'SAND_ROCK':25,'RED_DESERT1':14,'YELLOW_PLAINS1':14,'ROCK2':25,'ROCK_CARBON':10,'SNOW1':32,'SNOW_DIRT':33,'SNOW_ROCK':34,'ICE1':35,'WATER_SHALLOW':1,'WATER_ROUGH':22,'WATER_DEEP':22,'WATER_SWAMP':4,'SHORE':2,'TREE_A':10,'TREE_B':10,'TREE_C':10,'TREE_D':10,'TREE_E':13,'TREE_F':10,'TREE_G':21}
maps.update({54223:'Arena',54225:'Motherlode'})

def special_objects(map_id,source):
    # These standalone blocks preserve defining map features without importing
    # SWGB's incompatible shared economic unit constants.
    symbol,target={54223:('BLDG-BARRIER1',117),54207:('OBJ-NOVA',66),54209:('OBJ-NOVA',66)}.get(map_id,('',0))
    if not symbol:return ''
    blocks=re.findall(r'create_object\s+'+re.escape(symbol)+r'\s*\{[^{}]*\}',source)
    if len(blocks)!=1:raise ValueError(f'{map_id}: expected one defining {symbol} block')
    block=blocks[0].replace(symbol,str(target))
    if target==66:block=block.replace('{','{\n set_gaia_object_only',1)
    return '\n/* Preserved source-specific placement; native DE object substitute. */\n'+block+'\n'
def objects():
    text='<OBJECTS_GENERATION>\ncreate_object 109 { set_place_for_every_player min_distance_to_players 0 max_distance_to_players 0 }\n'
    # Standard DE economy and an immediately usable small troop force.
    for id,count,near,far,extra in [(83,3,3,5,''),(448,1,6,8,''),(4,6,7,10,''),(594,8,5,8,'set_gaia_object_only'),(59,6,10,14,'set_gaia_object_only set_tight_grouping group_placement_radius 3'),(66,7,12,17,'set_gaia_object_only set_tight_grouping group_placement_radius 3'),(102,5,12,17,'set_gaia_object_only set_tight_grouping group_placement_radius 3'),(48,2,14,20,'set_gaia_object_only'),(65,4,14,20,'set_gaia_object_only set_loose_grouping group_placement_radius 4'),(349,12,8,12,'set_gaia_object_only set_loose_grouping group_placement_radius 5')]:
        text+=f'create_object {id} {{ number_of_objects {count} set_place_for_every_player min_distance_to_players {near} max_distance_to_players {far} {extra} }}\n'
    for id,count in [(66,5),(102,4)]:text+=f'create_object {id} {{ number_of_objects {count} number_of_groups 4 set_scaling_to_player_number set_gaia_object_only set_tight_grouping group_placement_radius 3 min_distance_to_players 22 }}\n'
    text+='create_object 285 { number_of_objects 5 set_gaia_object_only min_distance_to_players 20 }\n'
    text+='create_object 53 { number_of_objects 30 set_scaling_to_map_size set_gaia_object_only terrain_to_place_on 1 }\n'
    return text
manifest=[]
terrain.update({'PATH1':24,'PATH2':25,'PATH3':24,'SNOW_GRASS1':32,'SNOW_DIRT':32,'SNOW_ROCK':32,'SAND_ROCK':40,'ROCK2':40,'WATER_ROUGH':23})
for id,name in maps.items():
    source=(root/f'{id}.bin').read_text()
    body=re.sub(r'/\*.*?\*/','',source,flags=re.S)
    body=re.sub(r'#include_drs\s+random_map.def\s+54000','',body)
    parts=re.split(r'(<[A-Z_]+>)',body)
    new=parts[0]
    for i in range(1,len(parts),2):
        tag,content=parts[i:i+2]
        if tag=='<OBJECTS_GENERATION>':new+=objects()+special_objects(id,body)
        else:new+=tag+content
    if '#include' in new:manifest.append(dict(id=id,name=name,status='deferred: external generation include'));continue
    defs=set(re.findall(r'#define\s+(\S+)',new))
    symbols=set(re.findall(r'\b[A-Z][A-Z0-9_-]*\b',re.sub(r'/\*.*?\*/','',new,flags=re.S)))
    unknown=symbols-set(terrain)-defs-{'PLAYER_SETUP','LAND_GENERATION','TERRAIN_GENERATION','ELEVATION_GENERATION','CLIFF_GENERATION','OBJECTS_GENERATION','CONNECTION_GENERATION','TINY_MAP','SMALL_MAP','MEDIUM_MAP','LARGE_MAP','HUGE_MAP','GIGANTIC_MAP','LANDMAP','WATERMAP'}
    if unknown:manifest.append(dict(id=id,name=name,status='deferred: unmapped symbols',symbols=sorted(unknown)));continue
    for key,value in sorted(terrain.items(),key=lambda kv:-len(kv[0])):new=re.sub(r'(?<![\w-])'+re.escape(key)+r'(?![\w-])',str(value),new)
    # RMS object/terrain arguments are identifier tokens, not numeric literals.
    # Numeric amounts/distances stay numeric; only entity arguments are named.
    constants=set()
    def entity(match):
        n=match.group(2);constants.add(int(n));return match.group(1)+'SWGB_ID_'+n
    new=re.sub(r'(\b(?:create_object|create_terrain|base_terrain|terrain_type|terrain_to_place_on|terrain_cost|terrain_size)\s+)(\d+)\b',entity,new)
    def replacement(match):
        a,b=match.group(1),match.group(2);constants.update((int(a),int(b)))
        return 'replace_terrain SWGB_ID_'+a+' SWGB_ID_'+b
    new=re.sub(r'\breplace_terrain\s+(\d+)\s+(\d+)\b',replacement,new)
    new=''.join(f'#const SWGB_ID_{n} {n}\n' for n in sorted(constants))+new
    new='/* SWGB / Expanding Fronts map geometry. Local DE adaptation.\nNative DE terrain substitutes and standard resource/start-object distribution.\nOriginal authors credited in source archive; source DRS entry '+str(id)+'. */\n'+new
    assert new.count('{')==new.count('}')
    (out/f'SWGB {name}.rms').write_text(new,encoding='ascii')
    manifest.append(dict(id=id,name=name,status='built; game verification pending',file=f'SWGB {name}.rms',preserved_special_objects=id in (54223,54207,54209)))
Path('outputs/map-manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
