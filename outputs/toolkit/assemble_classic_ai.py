"""Apply a verified, narrow Classic AI patch to the current two-faction package."""
from pathlib import Path
import hashlib
import json
import shutil

work=Path('work/original-ai')
patch=work/'patch'
root=Path('outputs/SWGB-DE-Factions-Draft')
manifest_path=Path('outputs/faction-package-manifest.json')
validation=json.loads((work/'validation.json').read_text())
translation=json.loads((work/'translation.json').read_text())
assert validation['passed'] and len(validation['parser_configurations'])==27
prior=json.loads(manifest_path.read_text())
old={r['path']:r for r in prior['files']}
names={r['path'] for r in validation['files']}
maps={r['file'] for r in translation['map_patches']}
allowed=maps|{'resources/_common/dat/unitlines.json',
    'resources/en/strings/key-value/key-value-modded-strings-utf8.txt',
    'resources/_common/ai/SWGB Classic AI.per',
    'resources/_common/ai/SWGB Classic/swgb_classic_ai.xs'}
allowed|={f'resources/_common/ai/SWGB Classic/{prefix}dip-{personality}.per'
          for prefix in ('ce-','cr-') for personality in ('bully','boomer','feeder')}
assert names==allowed
assert {p.relative_to(patch).as_posix() for p in patch.rglob('*') if p.is_file()}==names
assert {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}==old.keys()

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

for name,record in old.items():assert digest(root/name)==record['sha256'],('Assembly drift',name)
for record in validation['files']:
    assert digest(patch/record['path'])==record['sha256'],('Unverified patch',record['path'])
snapshot=work/'faction-package-manifest.before.json'
if not snapshot.exists():shutil.copy2(manifest_path,snapshot)
baseline={r['path']:r for r in json.loads(snapshot.read_text())['files']}
for name,record in old.items():
    if name not in names:assert record==baseline[name],('Unrelated payload change',name)
stable_names=['resources/_common/drs/gamedata_x2/PromiDE.per2','resources/_common/dat/empires2_x2_p1.dat']
stable={name:digest(root/name) for name in stable_names}
changes=[]
for record in validation['files']:
    name=record['path'];destination=root/name
    if name in baseline:
        backup=work/'assembly-before'/name
        if not backup.exists():
            assert digest(destination)==baseline[name]['sha256']
            backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(destination,backup)
        assert digest(backup)==baseline[name]['sha256']
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(patch/name,destination)
    assert digest(destination)==record['sha256']
    changes.append(dict(record,before_sha256=baseline.get(name,{}).get('sha256')))
    old[name]=record
assert all(digest(root/name)==sha for name,sha in stable.items())
prior.update(files=list(old.values()),total_bytes=sum(r['bytes'] for r in old.values()),
             status='Optional original Classic AI translation; engine verification pending')
manifest_path.write_text(json.dumps(prior,indent=2)+'\n')
for name,record in old.items():assert digest(root/name)==record['sha256']
out=dict(validation,changes=changes,stable_payload_hashes=stable,binary_dat_unchanged=True,
         default_ai_unchanged=True,source_checkpoint='d5131ec',
         source_files=translation['source_files'],source_rule_instances=len(translation['rules']),
         swgb_unit_groups=len(translation['groups']),chat_strings=translation['chat_strings'])
Path('outputs/original-ai-validation.json').write_text(json.dumps(out,indent=2)+'\n')
print('Assembled',len(changes),'verified files; binary DAT and default AI unchanged')
