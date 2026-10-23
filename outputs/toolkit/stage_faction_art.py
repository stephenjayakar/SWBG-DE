"""Extract roster graphics with explicit missing-resource and frame-layout reports."""
from pathlib import Path
import csv,json,struct,hashlib,re,sys
GAME=Path(r'E:\GOG Games\Star Wars - Galactic Battlegrounds\Game\Data')
rank={name:i for i,name in enumerate(('graphics.drs','graphics_p1.drs','graphics_x1.drs','graphics_x1_p1.drs','graphics_x2.drs'))}
index={}
for row in json.loads(Path('outputs/archive-manifest.json').read_text()):
    name=row['archive'].lower()
    if row['ext']!='slp' or name not in rank:continue
    old=index.get(row['id'])
    if old is None or rank[name]>rank[old['archive'].lower()]:index[row['id']]=row
meta={int(r['id']):r for r in csv.DictReader(open('outputs/ef-graphics.tsv'),delimiter='\t')}
done=set();known_failed=set()
for name in ('faction-convert.log','faction-retry.log','faction-new.log','faction-world.log','faction-world-variants.log','faction-map.log','faction-palette-repair.log','faction-layout-repair.log','faction-tasks.log'):
    p=Path('work',name)
    if p.exists():
        done.update(map(int,re.findall(r'swgb_(\d+)\.smx frames=\d+ roundtrip=PASS',p.read_text())))
        known_failed.update(map(int,re.findall(r'FAILED (\d+)\.slp:',p.read_text())))
folder=Path('work/faction-valid-slp');folder.mkdir(exist_ok=True)
pending=Path(sys.argv[1] if len(sys.argv)>1 else 'work/faction-new-slp');pending.mkdir(exist_ok=True)
report={'empty_or_composite':[],'missing':[],'frame_anomalies':[],'extracted':[],'new':[],'known_conversion_failures':sorted(known_failed-done)}
report['omitted_source_overlays']=[{'graphic':g,'reason':'Referenced source fishing overlay file absent; independent hull retained'} for g in (4866,4868,4891,4893)]
for row in csv.DictReader(open('work/faction-roster-art.tsv'),delimiter='\t'):
    gid=int(row['source']);slp=int(row['slp'])
    if slp<0:report['empty_or_composite'].append(gid);continue
    entry=index.get(slp)
    if entry is None:report['missing'].append(dict(row));continue
    with (GAME/entry['archive']).open('rb') as f:f.seek(entry['offset']);data=f.read(entry['size'])
    assert len(data)==entry['size']
    frames=struct.unpack_from('<I',data,4)[0];m=meta[gid];per=int(m['frames']);angles=int(m['angles']);mirror=int(m['mirror'])
    expected=per*((angles//2+1) if mirror else angles)
    empty=True
    for i in range(frames):
        _,outline,_,_,_,height,_,_=struct.unpack_from('<8I',data,32+32*i)
        if any(struct.unpack_from('<HH',data,outline+4*y)!=(32768,32768) for y in range(height)):empty=False;break
    valid=empty or (gid==5582 and frames==5 and per==6 and angles==8 and mirror!=0) or (angles in (8,16) and frames==expected) or (angles in (1,3,5) and frames>=per*angles) or (mirror==0 and angles in (2,6,10,11,12,22,24) and frames>=per*angles)
    if not valid:report['frame_anomalies'].append(dict(m,actual_frames=frames));continue
    (folder/f'{gid}.slp').write_bytes(data)
    report['extracted'].append(dict(id=gid,archive=entry['archive'],slp=slp,sha256=hashlib.sha256(data).hexdigest()))
    repairable={10611,10612,10613,10614,10615,16291,16292}
    if gid not in done and (gid not in known_failed or gid in repairable):
        (pending/f'{gid}.slp').write_bytes(data);report['new'].append(gid)
Path('outputs/faction-art-stage-report.json').write_text(json.dumps(report,indent=2))
print({k:len(v) for k,v in report.items()})
