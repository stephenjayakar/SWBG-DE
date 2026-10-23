"""Check staged artwork coverage, layouts and hashes for both DE resolutions."""
from pathlib import Path
import csv,json,re,struct,hashlib
work=Path('work');meta={int(r['id']):r for r in csv.DictReader(open('outputs/ef-graphics.tsv'),delimiter='\t')}
logs={1:['faction-convert.log','faction-retry.log','faction-new.log','faction-world.log','faction-world-variants.log','faction-map.log','faction-palette-repair.log','faction-layout-repair.log'],2:['faction-enhanced.log','faction-new-enhanced.log','faction-world-enhanced.log','faction-world-variants-enhanced.log','faction-map-enhanced.log','faction-palette-repair-enhanced.log','faction-layout-repair-enhanced.log']}
logs[1].append('faction-tasks.log');logs[2].append('faction-tasks-enhanced.log')
verified={scale:set().union(*(set(map(int,re.findall(r'swgb_(\d+)\.smx frames=\d+ roundtrip=PASS',(work/name).read_text()))) for name in names)) for scale,names in logs.items()}
files=[];empty=[]
mask_report=Path('outputs/faction-building-mask-validation.json')
masked={(r['graphic'],r['scale']):r for r in json.loads(mask_report.read_text())['files']} if mask_report.exists() else {}
for r in csv.DictReader(open('work/faction-roster-art.tsv'),delimiter='\t'):
    gid=int(r['source'])
    if int(r['slp'])<0:assert not r['filename'];empty.append(gid);continue
    for scale,folder in [(1,'faction-roster-converted'),(2,'faction-roster-enhanced')]:
        assert gid in verified[scale],(gid,scale,'no converter roundtrip evidence')
        path=work/folder/f'swgb_{gid}.smx';b=path.read_bytes();assert b[:4]==b'SMPX'
        if (gid,scale) in masked:assert hashlib.sha256(b).hexdigest()==masked[gid,scale]['sha256'],('Mask payload drift',gid,scale)
        count=struct.unpack_from('<H',b,6)[0];m=meta[gid];minimum=int(m['frames'])*int(m['angles'])
        assert count>=minimum,(gid,count,minimum)
        if int(m['angles']) in (8,16):assert count==minimum
        files.append(dict(graphic=gid,scale=scale,frames=count,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
report=dict(files=files,sprite_less=empty,converted_graphics=len(files)//2,omitted_source_overlays=[4866,4868,4891,4893],fixed_paint_repairs=[10611,10612,10613,10614,10615,16291,16292],static_animation_repairs=[5582],engine_rendering_verified=False)
Path('outputs/faction-art-validation.json').write_text(json.dumps(report,indent=2));print(len(files)//2,'graphics verified at both resolutions')
