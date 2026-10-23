"""Stage Ore/AI repairs against the verified two-faction installed payload."""
from pathlib import Path
import csv, hashlib, json, shutil, subprocess

work=Path('work/worker-ui-repair');patch=work/'patch';patch.mkdir(exist_ok=True)
for name in ('faction-install-report.json','faction-package-manifest.json'):
    if not (work/name).exists():shutil.copy2(Path('outputs')/name,work/name)
report=json.loads((work/'faction-install-report.json').read_text())
local=Path(report['asset_mod']).parent
records={r['path']:r for r in report['installed_files']}
def original(name):
    r=records[name];data=(local/r['mod']/name).read_bytes()
    assert hashlib.sha256(data).hexdigest()==r['sha256'],name
    return data
def rows(name):return list(csv.DictReader(open('work/faction-source/'+name+'.tsv'),delimiter='\t'))
ore={r['id'] for r in rows('units') if r['civ']=='0' and r['class']=='30'}
pending=[int(r['graphic']) for r in rows('unit-art') if r['civ']=='0' and r['unit'] in ore]
children={}
for r in rows('deltas'):children.setdefault(int(r['parent']),set()).add(int(r['child']))
graphics=set()
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
        dest=work/f'ore-input-{scale}'/f'swgb_{gid}.smx';dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(original(name));bindings.append(dict(graphic=gid,scale=scale,path=name))
assert 5234 in selected
(work/'ore-graphics.txt').write_text(''.join(f'{g}\n' for g in selected))
for scale in (1,2):
    # Run in the workshop directory so its palette configuration resolves.
    result=subprocess.run(['java','-cp','Export/SMX Workshop.jar;.', 'NeutralBuildingMasks',
        str((work/'ore-graphics.txt').resolve()),str((work/f'ore-input-{scale}').resolve()),
        str((work/f'ore-output-{scale}').resolve())],cwd='work/smx-workshop',capture_output=True,text=True,check=True)
    (work/f'ore-mask-{scale}.log').write_text(result.stdout)
for b in bindings:
    dest=patch/b['path'];dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(work/f'ore-output-{b["scale"]}'/f'swgb_{b["graphic"]}.smx',dest)

# Read the *installed DAT's* exported Gaia storage/class fields, not the paused
# expansion cache. Exclude civilization bonuses/cost refunds (nonzero flag).
# Native airesourcetypes lists native military IDs that collide with SWGB food.
classes={0:{9,10,58,7,49,33,5,29},1:{15,32,8},2:{8},3:{32}}
types={i:[] for i in range(4)}
for line in (work/'mod.txt').read_text().splitlines():
    if not line.startswith('RESOURCE\t'):continue
    _,uid,name,cl,res,amount,flag=line.split('\t')
    cl,res,flag=int(cl),int(res),int(flag)
    if flag==0 and cl in classes[res]:types[res].append(dict(Name=name,ID=int(uid)))
assert all(types.values())
for res,uid in ((0,59),(0,50),(1,7067),(1,348),(2,102),(3,66)):
    assert any(r['ID']==uid for r in types[res]),(res,uid)
assert not any(r['ID']==65 for r in types[0]) # SWGB explosion, native deer.
catalog=dict(ResourceTypes=[dict(Resource=name,Types=types[i]) for name,i in [('Food',0),('Wood',1),('Stone',2),('Gold',3)]])
dest=patch/'resources/_common/dat/airesourcetypes.json';dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text(json.dumps(catalog,indent=2)+'\n')
(work/'ore-bindings.json').write_text(json.dumps(bindings,indent=2))
print('Ore:',len(bindings),'verified SMXs; AI resource types:',{k:len(v) for k,v in types.items()})
