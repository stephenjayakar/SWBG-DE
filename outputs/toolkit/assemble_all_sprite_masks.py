"""Apply the independently verified global mask patch, preserving other files."""
from pathlib import Path
import hashlib,json,shutil
work=Path('work/all-sprite-masks');root=Path('outputs/SWGB-DE-Factions-Draft')
prior=json.loads((work/'faction-package-manifest.json').read_text())
scan=json.loads((work/'scan.json').read_text())['files']
assert (work/'verify-pass.txt').read_text().strip()==f'PASS files={len(scan)} visible-pixels={sum(r["pixels"] for r in scan)}'
assert json.loads((work/'converter-check.json').read_text())['passed']
old={r['path']:r for r in prior['files']}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}==old.keys()
for name,r in old.items():assert digest(root/name)==r['sha256'],('Assembly drift',name)
changed=[r for r in scan if r['changed']]
for r in changed:
    assert r['path'] in old and old[r['path']]['sha256']==r['before_sha256']
    assert digest(work/'patch'/r['path'])==r['sha256']
for r in changed:
    name=r['path'];backup=work/'assembly-before'/name;backup.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(root/name,backup);shutil.copy2(work/'patch'/name,root/name)
    assert digest(root/name)==r['sha256']
    old[name]={k:r[k] for k in ('path','bytes','sha256')}
prior.update(files=list(old.values()),total_bytes=sum(r['bytes'] for r in old.values()),status='global sprite damage-mask repair; runtime confirmation pending')
Path('outputs/faction-package-manifest.json').write_text(json.dumps(prior,indent=2))
report=dict(sprite_files=len(scan),changed_sprite_files=len(changed),
    frames=sum(r['frames'] for r in scan),visible_frames=sum(r['visible_frames'] for r in scan),
    repaired_frames=sum(r['nonneutral_frames']+r['missing_frames'] for r in scan),
    visible_pixels=sum(r['pixels'] for r in scan),independent_pixel_geometry_palette_check=True,
    other_payload_unchanged=True,converter_regression_passed=True,engine_verified=False,files=changed)
Path('outputs/all-sprite-mask-validation.json').write_text(json.dumps(report,indent=2))
print('Assembled',len(changed),'verified sprite repairs; every non-sprite payload unchanged')
