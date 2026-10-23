"""Install a clean local data-mod copy for manual publishing inside DE."""
import hashlib
import json
import zipfile
from pathlib import Path

release = Path('outputs/releases/SWGB-DE-0.0.2-dev-b944fbf-upload-data.zip')
manifest = json.loads(release.with_suffix('.manifest.json').read_text())
assert hashlib.sha256(release.read_bytes()).hexdigest() == manifest['sha256']
install = json.loads(Path('outputs/faction-install-report.json').read_text())
local = Path(install['data_mod']).resolve().parent
assert local.name == 'local' and local.parent.name == 'mods'
title = 'SWGB-DE-Factions-Publish'
target = (local / title).resolve()
assert target.parent == local
assert not target.exists(), f'Refusing to overwrite an existing publishing copy: {target}'
payload = {}
with zipfile.ZipFile(release) as z:
    assert z.testzip() is None
    assert sorted(z.namelist()) == sorted(r['path'] for r in manifest['files'])
    for row in manifest['files']:
        destination = (target / row['path']).resolve()
        assert destination.is_relative_to(target)
        data = z.read(row['path'])
        assert hashlib.sha256(data).hexdigest() == row['sha256']
        payload[row['path']] = data
target.mkdir()
for name, data in payload.items():
    destination = target / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
metadata = dict(Author='Local SWGB port project', CacheStatus=0, Title=title,
                Version='0.0.2-dev',
                Description='Experimental Empire/Rebels data, build b944fbf. Requires matching SWGB-DE-Factions-Assets on every PC. Multiplayer unverified. Clean copy for manual publishing.')
(target / 'info.json').write_text(json.dumps(metadata, indent=2))
assert {p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()} == set(payload) | {'info.json'}
for row in manifest['files']:
    assert hashlib.sha256((target / row['path']).read_bytes()).hexdigest() == row['sha256']
report = dict(directory=str(target), title=title, payload_files=len(payload),
              build=manifest['build'], files=manifest['files'], verified=True,
              published=False, game_opened=False)
Path('outputs/faction-publish-install-report.json').write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k != 'files'}, indent=2))
