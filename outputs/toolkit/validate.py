from pathlib import Path
import csv,json,re,struct,zlib,hashlib
root=Path.cwd();out=root/'outputs';checks={}
native=root/'work/de.raw';roundtrip=root/'work/de-roundtrip.raw'
checks['native_dat_byte_exact_roundtrip']=native.read_bytes()==roundtrip.read_bytes()
mod=out/'SWGB-DE-Trooper-MVP'
dat=mod/'resources/_common/dat/empires2_x2_p1.dat'
raw=zlib.decompress(dat.read_bytes(),-15)
checks['mod_dat_raw_matches_build']=raw==(root/'work/next-mod.raw').read_bytes()
checks['only_intended_native_dat_changes']=native.read_bytes()==(root/'work/audited-native.raw').read_bytes()
checks['mod_dat_version_8_9']=raw[:8]==b'VER 8.9\0'
graphics={r['id']:r for r in csv.DictReader(open(out/'ef-graphics.tsv'),delimiter='\t')}
count=0
mapping=list(csv.DictReader(open(out/'graphic-mapping.tsv'),delimiter='\t'))
for m in mapping:
    for suffix in ('_x1','_x2'):
        p=out/'SWGB-DE-Assets/resources/_common/drs/graphics'/(m['filename'].replace('_x1',suffix)+'.smx')
        b=p.read_bytes();assert b[:4]==b'SMPX'
        frames=struct.unpack_from('<H',b,6)[0];g=graphics[m['source']]
        assert frames==int(g['frames'])*int(g['angles'])
        count+=1
checks['referenced_sprite_variants_present']=count==2*len(mapping)==36
checks['dataset_contains_no_sprite_files']=not list(mod.rglob('*.smx'))
checks['assets_contains_no_dat']=not list((out/'SWGB-DE-Assets').rglob('*.dat'))
maps=list((out/'SWGB-DE-Maps/resources/_common/random-map-scripts').glob('*.rms'))
unit={r['id']:r['name'] for r in csv.DictReader(open(out/'de-units.tsv'),delimiter='\t') if r['civ']=='0'}
def resolve_rms(s):
    declarations=dict(re.findall(r'#const\s+(SWGB_ID_\d+)\s+(\d+)',s))
    entity_commands=r'(?:create_object|create_terrain|base_terrain|terrain_type|terrain_to_place_on|terrain_cost|terrain_size|replace_terrain)'
    assert not re.search(r'\b'+entity_commands+r'\s+\d',s),'Raw numeric entity argument'
    references=set(re.findall(r'\bSWGB_ID_\d+\b',s))
    assert references<=declarations.keys(),'Undeclared entity constant'
    return re.sub(r'\bSWGB_ID_\d+\b',lambda m:declarations[m.group()],s)
assert unit['66']=='GOLDM' and unit['102']=='STONM' and unit['65']=='DEERX' and unit['349']=='FOAK'
for p in maps:
    s=re.sub(r'/\*.*?\*/','',p.read_text(),flags=re.S)
    s=resolve_rms(s)
    assert '#include' not in s and s.count('{')==s.count('}')
    ids=set(re.findall(r'create_object\s+(\d+)',s))
    assert {'109','83','4','59','66','102','349'}<=ids
    assert all(i in unit for i in ids)
checks['map_count']=len(maps)
manifest=json.loads((out/'map-manifest.json').read_text())
checks['all_maps_have_core_start_and_resource_ids']=len(maps)==len(manifest)==20 and all(r['status'].startswith('built;') for r in manifest)
for name,terrain,groups in [('Nova Lake',0,6),('Nova Assault',6,10)]:
    s=resolve_rms((out/'SWGB-DE-Maps/resources/_common/random-map-scripts'/f'SWGB {name}.rms').read_text())
    blocks=re.findall(r'create_object 66\s*\{[^{}]*\}',s)
    assert any(re.search(r'terrain_to_place_on\s+'+str(terrain)+r'\b',b) and re.search(r'number_of_groups\s+'+str(groups)+r'\b',b) for b in blocks)
arena=resolve_rms((out/'SWGB-DE-Maps/resources/_common/random-map-scripts/SWGB Arena.rms').read_text())
assert re.search(r'create_object 117\s*\{[^{}]*number_of_objects\s+9999\b',arena)
checks['nova_deposits_and_arena_wall_blocks_present']=True
for name in ('SWGB-DE-Trooper-MVP','SWGB-DE-Maps','SWGB-DE-Assets'):
    info=json.loads((out/name/'info.json').read_text());assert info['Title']==name and info['CacheStatus']==0
    dest=Path.home()/'Games/Age of Empires 2 DE/76561198022514833/mods/local'/name
    for p in (out/name).rglob('*'):
        if p.is_file():
            installed=dest/p.relative_to(out/name)
            if p.name=='info.json':
                # DE rewrites formatting and its own CacheStatus after discovery.
                actual=json.loads(installed.read_text())
                assert all(actual.get(k)==v for k,v in info.items() if k!='CacheStatus')
            else:assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(installed.read_bytes()).digest(),str(p)
checks['installed_files_match_packages']=True
checks['in_game_verified']=False
checks['engine_validation_note']='User confirmed working Savannah and improved trooper rendering. Release 0.0.1 enlarges laser projectiles threefold; visibility and complete combat verification pending.'
(out/'validation-report.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
assert all(v for k,v in checks.items() if isinstance(v,bool) and k!='in_game_verified')
