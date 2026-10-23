"""Export the verified two-folder install; never includes profiles or replays."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,zipfile

p=argparse.ArgumentParser()
p.add_argument('--build',required=True,help='Git checkpoint describing the installed payload')
args=p.parse_args()
commit=subprocess.check_output(['git','rev-parse',args.build],text=True).strip()
report=json.loads(Path('outputs/faction-install-report.json').read_text())
local=Path(report['asset_mod']).parent
names=('SWGB-DE-Factions-Draft','SWGB-DE-Factions-Assets')
out=Path('outputs/releases');out.mkdir(parents=True,exist_ok=True)
dest=out/f'SWGB-DE-0.0.2-dev-{commit[:7]}.zip'
assert not dest.exists(),f'Checkpoint archive already exists: {dest}'
manifest=[]
with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
    for r in report['installed_files']:
        assert r['mod'] in names
        root=(local/r['mod']).resolve();source=(root/r['path']).resolve()
        assert source.is_relative_to(root)
        data=source.read_bytes();digest=hashlib.sha256(data).hexdigest()
        assert digest==r['sha256'],f'Installed file differs: {r["path"]}'
        name=r['mod']+'/'+r['path'];z.writestr(name,data)
        manifest.append(dict(path=name,sha256=digest,bytes=len(data)))
    for name in names:
        info=json.loads((local/name/'info.json').read_text())
        assert info['Author']=='Local SWGB port project' and info['Title']==name
        # DE can remove Version from the installed metadata. Restore it for export.
        info['Version']='0.0.2-dev'
        z.writestr(name+'/info.json',json.dumps(info,indent=2))
    for file in ('SHARING.md','FACTION-TESTING.md','TODO.md','WORKER-FORCE-TIMING.md','MUSIC-POWER.md','AIRCRAFT-CRASH.md','FLIGHT-GARRISON-SCOUT.md','ECONOMY-REPAIR.md','WORKER-RESOURCE-UI.md','ALL-SPRITE-SHADING.md','AI-DIFFICULTIES.md','ORIGINAL-AI.md','NURSERIES.md','PUBLISHING.md','DEFENSES.md'):
        z.write(Path('outputs')/file,'INSTALL.md' if file=='SHARING.md' else file)
    z.write('CHANGELOG.md','CHANGELOG.md')
    z.writestr('BUILD.json',json.dumps(dict(version='0.0.2-dev',commit=commit,
        engine_verified=False,files=manifest),indent=2))
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(set(z.namelist()))
    for r in manifest:
        assert hashlib.sha256(z.read(r['path'])).hexdigest()==r['sha256']
digest=hashlib.sha256(dest.read_bytes()).hexdigest()
dest.with_suffix('.zip.sha256').write_text(f'{digest}  {dest.name}\n')
print(json.dumps(dict(zip=str(dest.resolve()),bytes=dest.stat().st_size,
                     payload_files=len(manifest),sha256=digest,commit=commit)))
# A full release also delivers the matching data upload and verified Dropbox pair.
subprocess.run([sys.executable, str(Path(__file__).with_name('package_faction_upload.py')),
                '--build', commit], check=True)
