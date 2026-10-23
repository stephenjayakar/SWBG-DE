import csv,json,struct,sys
from pathlib import Path
records=json.loads(Path('outputs/archive-manifest.json').read_text())
graphics={int(r['id']):r for r in csv.DictReader(open('outputs/ef-graphics.tsv'),delimiter='\t')}
ids=[int(r['source']) for r in csv.DictReader(open(sys.argv[1] if len(sys.argv)>1 else 'outputs/graphic-mapping.tsv'),delimiter='\t') if int(r['slp'])>=0]
dst=Path(sys.argv[2] if len(sys.argv)>2 else 'work/slp');dst.mkdir(exist_ok=True)
for gid in ids:
    g=graphics[gid];slp=int(g['slp']); candidates=[r for r in records if r['ext']=='slp' and r['id']==slp and r['archive'].lower() in ['graphics_p1.drs','graphics_x1_p1.drs','graphics_x2.drs']]
    rank={'graphics_p1.drs':0,'graphics_x1_p1.drs':1,'graphics_x2.drs':2}
    r=max(candidates,key=lambda r:rank[r['archive'].lower()])
    with (Path(r'E:\GOG Games\Star Wars - Galactic Battlegrounds\Game\Data')/r['archive']).open('rb') as f:f.seek(r['offset']);b=f.read(r['size'])
    (dst/f'{gid}.slp').write_bytes(b)
    print(gid,g['name'],g['frames'],g['angles'],b[:4],struct.unpack_from('<I',b,4)[0])
