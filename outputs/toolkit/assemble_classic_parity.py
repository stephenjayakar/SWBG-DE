"""Install only the verified follow-up files into the existing assembly."""
from pathlib import Path
import hashlib,json,shutil

work=Path('work/classic-parity');root=Path('outputs/SWGB-DE-Factions-Draft')
baseline=json.loads((work/'faction-package-manifest.before.json').read_text())
old={r['path']:r for r in baseline['files']}
validation=json.loads((work/'validation.json').read_text())
assert validation['passed'] and validation['parser_configurations']==81
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}==old.keys()
for name,r in old.items():assert digest(root/name)==r['sha256'],('Assembly drift',name)
for r in validation['files']:assert digest(work/'patch'/r['path'])==r['sha256']
for r in validation['files']:
    name=r['path'];backup=work/'assembly-before'/name
    backup.parent.mkdir(parents=True,exist_ok=True)
    if not backup.exists():shutil.copy2(root/name,backup)
    assert digest(backup)==r['before_sha256']
    shutil.copy2(work/'patch'/name,root/name)
    old[name]={k:r[k] for k in ('path','sha256','bytes')}
for name,r in old.items():assert digest(root/name)==r['sha256'],('Final assembly verification',name)
baseline.update(files=list(old.values()),total_bytes=sum(r['bytes'] for r in old.values()),
                status='Classic AI nursery and loader follow-up; runtime verification pending')
Path('outputs/faction-package-manifest.json').write_text(json.dumps(baseline,indent=2)+'\n')
Path('outputs/classic-parity-validation.json').write_text(json.dumps(validation,indent=2)+'\n')
shutil.copy2(work/'nursery-report.json','outputs/faction-nursery-report.json')
print('Assembled seven verified replacements; all other payload files unchanged')
