"""Refresh our existing local publishing copy from a verified upload archive.

Preserve DE's account/publication metadata. Never modify subscribed files.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);args=p.parse_args()
manifest=json.loads(args.archive.with_suffix('.manifest.json').read_text())
assert hashlib.sha256(args.archive.read_bytes()).hexdigest()==manifest['sha256']
report_path=Path('outputs/faction-publish-install-report.json')
prior=json.loads(report_path.read_text());target=Path(prior['directory']).resolve()
install=json.loads(Path('outputs/faction-install-report.json').read_text())
assert target==Path(install['data_mod']).resolve().parent/'SWGB-DE-Factions-Publish'
info=(target/'info.json').read_bytes()
assert json.loads(info)['Title']==prior['title']
old={r['path']:r for r in prior['files']};new={r['path']:r for r in manifest['files']}
assert old.keys()<=new.keys(), 'Unexpected removed publishing payload'
assert set(new)-set(old)<= {'resources/_common/dat/airesourcetypes.json'}, 'Unexpected new publishing payload'
for name,r in old.items():
    assert (target/name).resolve().is_relative_to(target)
    assert hashlib.sha256((target/name).read_bytes()).hexdigest()==r['sha256'],name
with zipfile.ZipFile(args.archive) as z:
    assert z.testzip() is None and set(z.namelist())==set(new)
    payload={name:z.read(name) for name in new}
for name,data in payload.items():assert hashlib.sha256(data).hexdigest()==new[name]['sha256']
backup=Path('work/publish-backups')/prior['build']
for name,data in payload.items():
    if name in old:
        original=(target/name).read_bytes();saved=backup/name;saved.parent.mkdir(parents=True,exist_ok=True)
        if saved.exists():assert saved.read_bytes()==original
        else:saved.write_bytes(original)
    else:assert not (target/name).exists(), 'Unexpected existing unowned file'
    (target/name).parent.mkdir(parents=True,exist_ok=True)
    (target/name).write_bytes(data)
    assert (target/name).read_bytes()==data
assert (target/'info.json').read_bytes()==info
prior.update(build=manifest['build'],files=manifest['files'],payload_files=len(payload),verified=True,published=False,game_opened=False)
report_path.write_text(json.dumps(prior,indent=2))
print(f'Updated {len(payload)} local publishing files; preserved metadata; subscribed files untouched')
