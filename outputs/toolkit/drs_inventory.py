from pathlib import Path
import struct,json
ROOT=Path(r'E:\GOG Games\Star Wars - Galactic Battlegrounds\Game\Data')
OUT=Path('work/extracted'); OUT.mkdir(exist_ok=True)
records=[]
for p in ROOT.glob('*.drs'):
    with p.open('rb') as f:
        h=f.read(84)
        count=struct.unpack_from('<I',h,76)[0]
        assert count<100,(p,count)
        tables=[struct.unpack('<4sII',f.read(12)) for _ in range(count)]
        for ext,offset,n in tables:
            ext=ext[::-1].decode().strip('\x00 ')
            f.seek(offset)
            entries=[struct.unpack('<III',f.read(12)) for _ in range(n)]
            for id,off,size in entries:
                assert off+size<=p.stat().st_size
                row=dict(archive=p.name,ext=ext,id=id,offset=off,size=size)
                records.append(row)
                if ext in ('bina','bin'):
                    f.seek(off);data=f.read(size)
                    dest=OUT/p.stem;dest.mkdir(exist_ok=True)
                    (dest/f'{id}.bin').write_bytes(data)
Path('outputs/archive-manifest.json').write_text(json.dumps(records,indent=2))
print('Indexed',len(records),'entries')
