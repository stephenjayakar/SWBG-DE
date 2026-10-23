"""Apply a verified small patch to the previous assembly, not expansion staging."""
from pathlib import Path
import hashlib,json,shutil
work=Path('work/economy-repair');root=Path('outputs/SWGB-DE-Factions-Draft')
prior=json.loads((work/'faction-package-manifest.json').read_text())
patch=json.loads(Path('outputs/economy-repair-validation.json').read_text())
assert patch['raw_roundtrip'] and patch['collateral_audit']
old={r['path']:r for r in prior['files']}
actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
assert actual==old.keys()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,r in old.items():assert digest(root/name)==r['sha256'],('Assembly has drifted',name)
for r in patch['files']:
    assert r['path'] in old and digest(work/'patch'/r['path'])==r['sha256']
for r in patch['files']:
    name=r['path'];backup=work/'assembly-before'/name;backup.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(root/name,backup)
    shutil.copy2(work/'patch'/name,root/name);assert digest(root/name)==r['sha256']
    old[name]=r
prior.update(files=list(old.values()),total_bytes=sum(r['bytes'] for r in old.values()),status='economy repair candidate; runtime unverified')
Path('outputs/faction-package-manifest.json').write_text(json.dumps(prior,indent=2))
print('Assembled',len(patch['files']),'verified replacements; other payload files unchanged')
