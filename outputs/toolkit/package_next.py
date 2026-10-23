from pathlib import Path
import csv,json,zlib,hashlib,shutil,struct
folder=Path('outputs/SWGB-DE-Blaster-MVP');dat=folder/'resources/_common/dat';sprites=folder/'resources/_common/drs/graphics'
dat.mkdir(parents=True,exist_ok=True);sprites.mkdir(parents=True,exist_ok=True)
raw=Path('work/next-mod.raw').read_bytes();c=zlib.compressobj(9,zlib.DEFLATED,-15);data=c.compress(raw)+c.flush();(dat/'empires2_x2_p1.dat').write_bytes(data)
assert zlib.decompress(data,-15)==raw
mapping=list(csv.DictReader(open('work/next-graphic-mapping.tsv'),delimiter='\t'))
source={r['id']:r for r in csv.DictReader(open('outputs/ef-graphics.tsv'),delimiter='\t')}
frames=0
for r in mapping:
 for suffix,where in [('_x1','next-converted'),('_x2','next-converted4x')]:
  dest=sprites/(r['filename'].replace('_x1',suffix)+'.smx');shutil.copy2(Path('work')/where/('swgb_'+r['source']+'.smx'),dest)
  b=dest.read_bytes();assert b[:4]==b'SMPX';n=struct.unpack_from('<H',b,6)[0];g=source[r['source']];angles=int(g['angles']);assert n==int(g['frames'])*(1 if angles==1 else angles//2+1);frames+=n
details=list(csv.DictReader(open('work/next-reloaded-details.tsv'),delimiter='\t'))
for c in range(1,60):
 for unit in (4,24):
  row=next(r for r in details if r['civ']==str(c) and r['unit']==str(unit))
  assert int(row['projectile'])==(2702 if c==2 else 2701)
  assert int(row['attackdelay'])==(2 if c==2 else 5)
(folder/'info.json').write_text(json.dumps({'Author':'Local SWGB port project','CacheStatus':0,'Title':folder.name,'Description':'Staged build: imported Empire/Rebel troopers, blaster bolts and impact animation. Native DE economy and unit stats. Select Britons versus Franks.'},indent=2))
report={'status':'staged, not installed or engine-verified','graphics':len(mapping),'sprite_variants':2*len(mapping),'frames_across_variants':frames,'projectile_ids':[2701,2702],'native_unit_graphics_not_overwritten':True,'reload_and_projectile_reference_checks':'PASS','dat_sha256':hashlib.sha256(data).hexdigest()}
Path('outputs/blaster-build-report.json').write_text(json.dumps(report,indent=2));shutil.copy2('work/next-graphic-mapping.tsv','outputs/blaster-graphic-mapping.tsv');print(json.dumps(report,indent=2))
