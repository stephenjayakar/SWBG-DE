"""Stage a small repair against installed e6cf77a, leaving expansion caches alone."""
from pathlib import Path
import csv,hashlib,json,shutil,zlib
from faction_relic_maps import repair_relics

work=Path('work/economy-repair');patch=work/'patch';patch.mkdir(exist_ok=True)
for name in ('faction-install-report.json','faction-package-manifest.json'):
    saved=work/name
    if not saved.exists():shutil.copy2(Path('outputs')/name,saved)
report=json.loads((work/'faction-install-report.json').read_text())
local=Path(report['asset_mod']).parent
records={r['path']:r for r in report['installed_files']}
def original(name):
    r=records[name];p=local/r['mod']/name
    data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==r['sha256'],name
    return data
maps=[]
for name in records:
    if name.endswith('.rms') and '/random-map-scripts/' in name:
        before=original(name).decode('ascii')
        after=repair_relics(before,name.endswith(' Savannah.rms'))
        dest=patch/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(after,encoding='ascii',newline='')
        maps.append(name)
assert len(maps)==20

def rows(name):return list(csv.DictReader(open('work/faction-source/'+name+'.tsv'),delimiter='\t'))
nova={r['id'] for r in rows('units') if r['civ']=='0' and r['class']=='29'}
roots={int(r['graphic']) for r in rows('unit-art') if r['civ']=='0' and r['unit'] in nova}
children={}
for r in rows('deltas'):children.setdefault(int(r['parent']),set()).add(int(r['child']))
graphics=set();pending=list(roots)
while pending:
    gid=pending.pop()
    if gid<0 or gid in graphics:continue
    graphics.add(gid);pending.extend(children.get(gid,()))
selected=[];bindings=[]
for gid in sorted(graphics):
    paths=[f'resources/_common/drs/graphics/swgb_{gid}_x{s}.smx' for s in (1,2)]
    if not any(p in records for p in paths):continue
    assert all(p in records for p in paths)
    selected.append(gid)
    for scale,name in zip((1,2),paths):
        dest=work/f'nova-input-{scale}'/f'swgb_{gid}.smx';dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(original(name));bindings.append(dict(graphic=gid,scale=scale,path=name))
assert 5136 in selected
(work/'nova-graphics.txt').write_text(''.join(f'{g}\n' for g in selected))
(work/'bindings.json').write_text(json.dumps(dict(maps=maps,sprites=bindings),indent=2))
print('Staged',len(maps),'maps and',len(selected),'Nova sprites per resolution')
