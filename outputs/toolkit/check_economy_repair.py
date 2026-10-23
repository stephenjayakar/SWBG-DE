"""Validate the isolated economy candidate, then stage its exact patch payload."""
from pathlib import Path
import csv,filecmp,hashlib,json,re,shutil,zlib

work=Path('work/economy-repair');patch=work/'patch'
assert filecmp.cmp(work/'candidate.raw',work/'roundtrip.raw',shallow=False)
assert filecmp.cmp(work/'before.raw',work/'restored.raw',shallow=False), 'Collateral DAT change'
text=(work/'candidate.txt').read_text()
flags={int(t):int(f) for t,f in re.findall(r'TERRAIN (\d+) name=.*? water=(\d+) draw=',text)}
assert flags[29]==flags[30]==flags[31]==32
assert 'Creatable.CreatableType=255' in text.split('UNIT 0 285 ')[1].split('UNIT ')[0]
def rows(path):return list(csv.DictReader(open(path),delimiter='\t'))
mapped={int(r['target']):int(r['source']) for r in rows('work/faction-terrain-map.tsv') if r['canonical']=='1'}
source={(int(r['restriction']),int(r['terrain'])):float(r['value']) for r in rows('work/faction-source/terrain-restrictions.tsv')}
def fallback(t):
    f=flags[t]
    if t in (29,30,31):return 29
    for mask,terrain in ((8,28),(16,2),(7,1),(64,35),(128,32)):
        if f&mask:return terrain
    return 0
target=rows(work/'dependencies/terrain-restrictions.tsv')
for r in target:
    t=int(r['terrain']);restriction=int(r['restriction']);s=mapped.get(t,fallback(t))
    assert float(r['value'])==source[restriction,s],r
grid={(int(r['restriction']),int(r['terrain'])):float(r['value']) for r in target}
assert all(grid[4,t]==1 and grid[7,t]==1 and grid[8,t]==0 for t in (29,30,31))
assert grid[4,1]==0 and grid[4,0]==grid[4,12]==1

bindings=json.loads((work/'bindings.json').read_text())
ids={r['graphic'] for r in bindings['sprites']}
for scale in (1,2):
    log=(work/f'nova-mask-{scale}.log').read_text()
    checked=set(map(int,re.findall(r'swgb_(\d+)\.smx frames=10 neutral-mask=PASS pixels-and-anchors=UNCHANGED',log)))
    assert checked==ids
for r in bindings['sprites']:
    dest=patch/r['path'];dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(work/f"nova-output-{r['scale']}"/f"swgb_{r['graphic']}.smx",dest)
for name in bindings['maps']:
    body=(patch/name).read_text()
    blocks=re.findall(r'create_object SWGB_OBJ-HOLOCRON\s*\{[^{}]*\}',body)
    assert len(blocks)==2
    assert all('set_gaia_object_only' in b and re.search(r'number_of_objects\s+5\b',b) for b in blocks)
    assert body.count('{')==body.count('}')
    if name.endswith(' Savannah.rms'):
        assert all('terrain_to_place_on SWGB_GRASS1' in b and 'min_distance_to_players 18' in b and 'temp_min_distance_group_placement 12' in b for b in blocks)
        assert 'terrain_type SWGB_GRASS2' in body and 'base_size 18' in body
dest=patch/'resources/_common/dat/empires2_x2_p1.dat';dest.parent.mkdir(parents=True,exist_ok=True)
raw=(work/'candidate.raw').read_bytes();compress=zlib.compressobj(9,zlib.DEFLATED,-15)
data=compress.compress(raw)+compress.flush();assert zlib.decompress(data,-15)==raw;dest.write_bytes(data)
files=[dict(path=p.relative_to(patch).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(patch.rglob('*')) if p.is_file()]
assert len(files)==31
report=dict(terrain_cells=len(target),farm_construction_stages=[29,30,31],raw_roundtrip=True,collateral_audit=True,
    maps=len(bindings['maps']),nova_sprites=len(bindings['sprites']),visible_pixels_and_anchors_unchanged=True,
    base_commit='e6cf77a',engine_verified=False,files=files)
Path('outputs/economy-repair-validation.json').write_text(json.dumps(report,indent=2))
print('PASS:',len(target),'terrain cells; exact DAT roundtrip/collateral audit;',len(files),'patch files')
