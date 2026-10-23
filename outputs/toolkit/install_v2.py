from pathlib import Path
import csv,json,zlib,shutil,hashlib,struct
out=Path('outputs'); dataset=out/'SWGB-DE-Trooper-MVP'; assets=out/'SWGB-DE-Assets'
local=Path.home()/'Games/Age of Empires 2 DE/76561198022514833/mods/local'
mapping=list(csv.DictReader(open('work/next-graphic-mapping.tsv'),delimiter='\t'))
source={r['id']:r for r in csv.DictReader(open(out/'ef-graphics.tsv'),delimiter='\t')}
raw=Path('work/next-mod.raw').read_bytes(); co=zlib.compressobj(9,zlib.DEFLATED,-15); data=co.compress(raw)+co.flush()
assert zlib.decompress(data,-15)==raw and raw[:7]==b'VER 8.9'
dat=dataset/'resources/_common/dat/empires2_x2_p1.dat'; dat.parent.mkdir(parents=True,exist_ok=True);dat.write_bytes(data)
spr=assets/'resources/_common/drs/graphics';spr.mkdir(parents=True,exist_ok=True)
frames=0
for r in mapping:
 for suffix,folder in [('_x1','next-converted'),('_x2','next-converted4x')]:
  b=(Path('work')/folder/('swgb_'+r['source']+'.smx')).read_bytes()
  assert b[:4]==b'SMPX'; n=struct.unpack_from('<H',b,6)[0];g=source[r['source']]
  assert n==int(g['frames'])*int(g['angles'])
  (spr/(r['filename'].replace('_x1',suffix)+'.smx')).write_bytes(b);frames+=n
# A data-only package is selected in the lobby; checkbox companion supplies media.
# Remove only our known media files after preserving them in the companion package.
for root in (dataset,local/dataset.name):
 for r in mapping:
  for suffix in ('_x1','_x2',''):
   p=root/'resources/_common/drs/graphics'/('swgb_'+r['source']+suffix+'.smx')
   if p.exists():p.unlink()
strings=assets/'resources/en/strings/key-value/key-value-modded-strings-utf8.txt';strings.parent.mkdir(parents=True,exist_ok=True)
strings.write_text('600000 "Imperial Trooper"\n600001 "Rebel Trooper"\n600002 "Imperial Mech"\n',encoding='utf-8')
for folder,description in [(dataset,'V2 data mod: select in Skirmish Data Mod dropdown. Requires checkbox SWGB-DE-Assets. Troopers, blasters and Imperial Scorpion mechs.'),(assets,'Enable this checkbox for SWGB-DE-Trooper-MVP graphics and English unit names. Standard and enhanced sprites included.')]:
 (folder/'info.json').write_text(json.dumps(dict(Author='Local SWGB port project',CacheStatus=0,Title=folder.name,Description=description,Version=Path('VERSION').read_text().strip()),indent=2))
 shutil.copytree(folder,local/folder.name,dirs_exist_ok=True)
 for p in folder.rglob('*'):
  if p.is_file():assert p.read_bytes()==(local/folder.name/p.relative_to(folder)).read_bytes()
units=list(csv.DictReader(open('work/next-reloaded-units.tsv'),delimiter='\t'))
graphics={r['id']:r for r in csv.DictReader(open('work/next-reloaded-graphics.tsv'),delimiter='\t')}
for c in range(1,60):
 for uid in (4,24,492,279,542):
  u=next(r for r in units if r['civ']==str(c) and r['id']==str(uid))
  for state in ('standing','walking','attack','dying'):
   g=graphics[u[state]];assert g['file'].startswith('swgb_') and (spr/(g['file']+'.smx')).exists()
  if uid in (279,542):assert u['dead']=='2703'
native=Path(r'E:\SteamLibrary\steamapps\common\AoE2DE\resources\_common\dat\empires2_x2_p1.dat')
assert hashlib.sha256(native.read_bytes()).hexdigest()=='ce3530df36cf0b333a9751cb0ff94460fe904f811feecec8ae9794701622b4cf'
report=dict(status='Installed v2; requires game restart and a new match; engine verification pending',graphics=len(mapping),sprite_variants=len(mapping)*2,frames_across_variants=frames,projectile_ids=[2701,2702],mech_corpse_id=2703,dat_sha256=hashlib.sha256(data).hexdigest(),installed_files_match=True,native_dat_unchanged=True,unit_graphic_references_checked=295,user_report='User confirmed working Savannah and improved trooper rendering. Release 0.0.1 enlarges laser projectiles threefold; visibility and complete combat verification pending.')
(out/'build-report.json').write_text(json.dumps(report,indent=2));shutil.copy2('work/next-graphic-mapping.tsv',out/'graphic-mapping.tsv')
shutil.copy2('work/next-converted/swgb_6470.smx.png',out/'imperial-mech-preview.png')
print(json.dumps(report,indent=2))
