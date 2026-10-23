from pathlib import Path
import shutil,zlib,json,hashlib,csv
out=Path('outputs/SWGB-DE-Trooper-MVP')
data=out/'resources/_common/dat';data.mkdir(parents=True,exist_ok=True)
c=zlib.compressobj(9,zlib.DEFLATED,-15);raw=Path('work/mod.raw').read_bytes();compressed=c.compress(raw)+c.flush()
(data/'empires2_x2_p1.dat').write_bytes(compressed)
assert zlib.decompress(compressed,-15)==raw
sprites=out/'resources/_common/drs/graphics';sprites.mkdir(parents=True,exist_ok=True)
for r in csv.DictReader(open('outputs/graphic-mapping.tsv'),delimiter='\t'):
 old=sprites/('swgb_'+r['source']+'.smx')
 if old.exists():old.unlink()
 shutil.copy2(Path('work/converted')/('swgb_'+r['source']+'.smx'),sprites/(r['filename']+'.smx'))
 shutil.copy2(Path('work/converted4x')/('swgb_'+r['source']+'.smx'),sprites/(r['filename'].replace('_x1','_x2')+'.smx'))
for folder,desc in [(out,'Experimental SWGB 2x trooper graphics dataset. Britons use Empire troopers; Franks use Rebels. Native DE gameplay.'),(Path('outputs/SWGB-DE-Maps'),'18 SWGB/EF map layout adaptations with native DE terrain and resources. Six starting troopers per player.')]:
 (folder/'info.json').write_text(json.dumps({'Author':'Local SWGB port project','CacheStatus':0,'Title':folder.name,'Description':desc},indent=2))
 dest=Path.home()/'Games/Age of Empires 2 DE/76561198022514833/mods/local'/folder.name
 if folder==out:
  for r in csv.DictReader(open('outputs/graphic-mapping.tsv'),delimiter='\t'):
   old=dest/'resources/_common/drs/graphics'/('swgb_'+r['source']+'.smx')
   if old.exists():old.unlink()
 shutil.copytree(folder,dest,dirs_exist_ok=True)
 print('Installed',dest)
report={'de_build_id':'24094652','de_dat_version':'VER 8.9','ef_dat_version':'VER 5.9','de_dat_sha256':hashlib.sha256(Path(r'E:\SteamLibrary\steamapps\common\AoE2DE\resources\_common\dat\empires2_x2_p1.dat').read_bytes()).hexdigest(),'output_dat_sha256':hashlib.sha256(compressed).hexdigest(),'sprite_count':len(list(sprites.glob('*.smx'))),'status':'installed; in-game validation pending'}
Path('outputs/build-report.json').write_text(json.dumps(report,indent=2))
