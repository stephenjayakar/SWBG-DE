"""Validate and install the isolated repair into the two-faction assembly."""
from pathlib import Path
import hashlib,json,shutil,zlib
work=Path('work/worker-ui-repair');root=Path('outputs/SWGB-DE-Factions-Draft');patch=work/'patch'
prior=json.loads((work/'faction-package-manifest.json').read_text())
old={r['path']:r for r in prior['files']}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}==old.keys()
for name,r in old.items():assert digest(root/name)==r['sha256'],('Assembly drift',name)
raw=zlib.decompress((root/'resources/_common/dat/empires2_x2_p1.dat').read_bytes(),-15)
assert raw==Path('work/economy-repair/candidate.raw').read_bytes()
ui=json.loads(Path('outputs/resource-ui-validation.json').read_text())
ai=json.loads(Path('outputs/faction-ai-validation.json').read_text())
assert ui['untouched_atlas_blocks_exact'] and ui['individual_pixels_exact'] and len(ui['regions'])==24
assert ai['findings']==0
for name in ai['entry_points']:assert digest(patch/name)==ai['sha256']
for scale in (1,2):
    log=(work/f'ore-mask-{scale}.log').read_text()
    bindings=[r for r in json.loads((work/'ore-bindings.json').read_text()) if r['scale']==scale]
    assert log.count('neutral-mask=PASS pixels-and-anchors=UNCHANGED')==len(bindings)
    for b in bindings:
        assert (patch/b['path']).read_bytes()==(work/f'ore-output-{scale}'/f'swgb_{b["graphic"]}.smx').read_bytes()
files=[]
for p in sorted(patch.rglob('*')):
    if not p.is_file():continue
    name=p.relative_to(patch).as_posix()
    assert name in old or name=='resources/_common/dat/airesourcetypes.json' or (
        name.startswith('widgetui/textures/') and Path(r'E:/SteamLibrary/steamapps/common/AoE2DE',name).is_file()),name
    if name in old and digest(p)==old[name]['sha256']:continue
    files.append(dict(path=name,sha256=digest(p),bytes=p.stat().st_size))
assert 'resources/_common/dat/empires2_x2_p1.dat' not in {r['path'] for r in files}
for r in files:
    name=r['path'];dest=root/name
    if dest.exists():
        backup=work/'assembly-before'/name;backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dest,backup)
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(patch/name,dest)
    assert digest(dest)==r['sha256'];old[name]=r
prior.update(files=list(old.values()),total_bytes=sum(r['bytes'] for r in old.values()),status='worker/resource UI repair candidate; runtime unverified')
Path('outputs/faction-package-manifest.json').write_text(json.dumps(prior,indent=2))
Path('outputs/worker-ui-repair-validation.json').write_text(json.dumps(dict(files=files,dat_unchanged=True,
    ai_parser_findings=0,ore_pixels_anchors_exact=True,ui_other_blocks_exact=True,engine_verified=False),indent=2))
print('Assembled',len(files),'changed/new files; DAT and every other payload unchanged')
