"""Create a game-files-only data-mod ZIP for manual web submission; never upload."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import zipfile


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as f:
        while chunk := f.read(1024 * 1024):
            result.update(chunk)
    return result.hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument('--build', required=True, help='Existing verified full-share build commit')
args = parser.parse_args()
commit = subprocess.check_output(['git', 'rev-parse', args.build], text=True).strip()
release = Path('outputs/releases')
base = f'SWGB-DE-0.0.2-dev-{commit[:7]}'
full = release / (base + '.zip')
assert digest(full) == full.with_suffix('.zip.sha256').read_text().split()[0]
with zipfile.ZipFile(full) as z:
    build = json.loads(z.read('BUILD.json'))
assert build['commit'] == commit
snapshot = {r['path']: r for r in build['files']}
install = json.loads(Path('outputs/faction-install-report.json').read_text())
root = Path(install['data_mod']).resolve()
files = []
for r in install['installed_files']:
    if r['mod'] != root.name:
        continue
    relative = PurePosixPath(r['path'])
    if str(relative) in ('README.md', 'VERSION'):
        continue
    assert relative.parts[0] in ('resources', 'widgetui'), relative
    # Civ picker emblems/icons live in wpfg next to civilizations.json.
    assert relative.suffix in ('.dat', '.json') or (relative.suffix == '.png' and relative.parts[:3] == ('resources', '_common', 'wpfg')), relative
    source = (root / str(relative)).resolve()
    assert source.is_relative_to(root), relative
    expected = snapshot[root.name + '/' + str(relative)]
    assert digest(source) == r['sha256'] == expected['sha256'], relative
    files.append(dict(path=str(relative), sha256=r['sha256'], bytes=source.stat().st_size))
assert any(r['path'] == 'resources/_common/dat/empires2_x2_p1.dat' for r in files)
destination = release / (base + '-upload-data.zip')
if not destination.exists():
    with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6, allowZip64=False) as z:
        for r in files:
            z.write(root / r['path'], r['path'])
# An existing immutable archive can be re-verified and re-delivered. Never
# overwrite it; any unexpected payload fails the checks below.
with zipfile.ZipFile(destination) as z:
    assert z.testzip() is None
    assert sorted(z.namelist()) == sorted(r['path'] for r in files)
    for r in files:
        assert hashlib.sha256(z.read(r['path'])).hexdigest() == r['sha256']
checksum = digest(destination)
destination.with_suffix('.zip.sha256').write_text(f'{checksum}  {destination.name}\n')
report = dict(build=commit, files=files, bytes=destination.stat().st_size,
              sha256=checksum, archive_integrity_verified=True,
              matches_installed_and_full_share=True, server_acceptance_verified=False,
              uploaded=False)
destination.with_suffix('.manifest.json').write_text(json.dumps(report, indent=2))
print(json.dumps(dict(zip=str(destination.resolve()), **report), indent=2))
shell = shutil.which('pwsh.exe') or shutil.which('powershell.exe')
assert shell, 'PowerShell is required for verified Dropbox delivery'
shell_env = dict(os.environ)
# Do not pass PS7's module search path to a Windows PowerShell 5 fallback.
shell_env.pop('PSModulePath', None)
subprocess.run([shell, '-NoProfile', '-ExecutionPolicy', 'Bypass',
                '-File', str(Path(__file__).with_name('sync_release_dropbox.ps1').resolve()),
                '-Build', commit], env=shell_env, check=True)
