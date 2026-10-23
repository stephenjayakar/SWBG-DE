"""Install the experimental draft using the prototype's data/media separation.

Does not select a dataset, toggle mods, or alter the original game files.
"""
from pathlib import Path
import hashlib,json,shutil

root=Path('outputs/SWGB-DE-Factions-Draft')
manifest=json.loads(Path('outputs/faction-package-manifest.json').read_text())
local=Path(r'C:\Users\aj12a\Games\Age of Empires 2 DE\76561198022514833\mods\local').resolve()
data=local/'SWGB-DE-Factions-Draft'
media=local/'SWGB-DE-Factions-Assets'
base=Path(r'E:\SteamLibrary\steamapps\common\AoE2DE\resources\_common\dat\empires2_x2_p1.dat')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
base_before=digest(base)
assert base_before=='ce3530df36cf0b333a9751cb0ff94460fe904f811feecec8ae9794701622b4cf'
for folder in (data,media):
    assert folder.resolve().parent==local
    if folder.exists():
        info=json.loads((folder/'info.json').read_text())
        assert info.get('Author')=='Local SWGB port project' and info.get('Title')==folder.name, 'Unexpected existing local mod'
        if info.get('Version') is None:
            # DE rewrites info.json and removes Version after loading a local mod.
            # Verify ownership using the previous complete installed-file manifest.
            previous=json.loads(Path('outputs/faction-install-report.json').read_text())
            assert previous['version']=='0.0.2-dev'
            prior_files=[r for r in previous['installed_files'] if r['mod']==folder.name]
            assert prior_files, 'No previous install evidence'
            assert all(digest(folder/r['path'])==r['sha256'] for r in prior_files), 'Installed files differ from previous build'
        else:
            assert info['Version']=='0.0.2-dev', 'Unexpected existing mod version'
    folder.mkdir(parents=True,exist_ok=True)
installed=[];expected={data:set(),media:set()}
media_roots=('widgetui/textures/','widgetui/morematerials.json','resources/_common/drs/','resources/_common/sound/music/','resources/en/','resources/_common/random-map-scripts/',
             'resources/_common/xs/','resources/_common/ai/')
for item in manifest['files']:
    name=item['path']
    if name=='info.json':continue
    source=root/name
    assert digest(source)==item['sha256'],('Stale build manifest',name)
    target_root=media if name.startswith(media_roots) else data
    target=target_root/name
    assert target.resolve().is_relative_to(target_root.resolve())
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists() or digest(target)!=item['sha256']:
        shutil.copy2(source,target)
    assert digest(target)==item['sha256']
    expected[target_root].add(name)
    installed.append(dict(mod=target_root.name,path=name,sha256=item['sha256']))
for folder,description in [(data,'EXPERIMENTAL source Empire/Rebels dataset. Requires SWGB-DE-Factions-Assets checkbox companion. Not engine verified.'),
                           (media,'EXPERIMENTAL graphics, audio, strings, maps, XS and SWGB Classic AI for SWGB-DE-Factions-Draft. Enable only with the matching faction dataset.')]:
    metadata=dict(Author='Local SWGB port project',CacheStatus=0,Title=folder.name,Version='0.0.2-dev',Description=description)
    (folder/'info.json').write_text(json.dumps(metadata,indent=2))
    expected[folder].add('info.json')
    # Retire only manifest-owned files relocated to the companion, retaining
    # a verified backup and checking both absolute roots before unlinking.
    prior=json.loads(Path('outputs/faction-install-report.json').read_text())['installed_files']
    for record in prior:
        if record['mod']!=folder.name or record['path'] in expected[folder]:continue
        other=media if folder==data else data
        if record['path'] not in expected[other]:continue
        old=folder/record['path']
        assert old.resolve().is_relative_to(folder.resolve()) and digest(old)==record['sha256']
        backup=Path('work/retired-relocated-ui').resolve()/folder.name/record['path']
        assert backup.resolve().is_relative_to(Path('work/retired-relocated-ui').resolve())
        backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old,backup)
        assert digest(backup)==record['sha256'];old.unlink()
    for old in (folder/'widgetui/textures/swgb').glob('*.png'):
        relative=old.relative_to(folder).as_posix()
        if old.with_suffix('.dds').relative_to(folder).as_posix() not in expected[folder]:continue
        prior=json.loads(Path('outputs/faction-install-report.json').read_text())['installed_files']
        record=next(r for r in prior if r['mod']==folder.name and r['path']==relative)
        assert digest(old)==record['sha256']
        backup=Path('work/retired-icon-pngs').resolve()/folder.name/relative
        assert old.resolve().is_relative_to(folder.resolve())
        assert backup.resolve().is_relative_to(Path('work/retired-icon-pngs').resolve())
        backup.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(old,backup)
        assert digest(backup)==record['sha256']
        old.unlink()
    actual={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    assert actual==expected[folder],('Unexpected stale local-mod files',folder.name,sorted(actual-expected[folder]))
assert digest(base)==base_before
report=dict(version='0.0.2-dev',installed_files=installed,data_mod=str(data),asset_mod=str(media),
            base_game_dat_unchanged=True,automatically_enabled=False,engine_verified=False)
Path('outputs/faction-install-report.json').write_text(json.dumps(report,indent=2))
print('Installed',len(installed),'verified files in separate data/asset mods; not enabled or engine verified')
