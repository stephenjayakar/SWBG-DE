"""Extract referenced faction audio; DE event/bank integration is a separate step."""
import csv,json,hashlib,struct
from pathlib import Path
from collections import defaultdict,Counter
GAME=Path(r'E:\GOG Games\Star Wars - Galactic Battlegrounds\Game')
def read(name):return list(csv.DictReader(open('work/faction-source/'+name+'.tsv'),delimiter='\t'))
roster=json.loads(Path('outputs/faction-roster-report.json').read_text())
unit_sounds=defaultdict(set)
for x in read('unit-sounds'):unit_sounds[(int(x['civ']),int(x['unit']))].add(int(x['sound']))
graphic_sounds=defaultdict(set)
for x in read('graphic-sounds'):graphic_sounds[int(x['graphic'])].add(int(x['sound']))
sound_items=defaultdict(list)
for x in read('sounds'):sound_items[int(x['sound'])].append(x)
rank={'sounds.drs':0,'sounds_x1.drs':1,'sounds_x2.drs':2};index={}
for x in json.loads(Path('outputs/archive-manifest.json').read_text()):
    if x['ext']!='wav' or x['archive'].lower() not in rank:continue
    old=index.get(x['id'])
    if old is None or rank[x['archive'].lower()]>rank[old['archive'].lower()]:index[x['id']]=x
folder=Path('work/faction-audio-source');folder.mkdir(exist_ok=True)
files={};missing=[];bindings=[];silent=[]
for civ in (0,1,3):
    records=roster[str(civ)]
    ids=set().union(*(unit_sounds[(civ,u)] for u in records['unit_dependencies']),*(graphic_sounds[g] for g in records['graphics']))
    for sound in sorted(ids):
        candidates=[x for x in sound_items[sound] if int(x['civ']) in (-1,civ) and int(x['probability'])>0]
        if not candidates:silent.append(dict(civ=civ,sound=sound,reason='source has no eligible sound item for this civilization'));continue
        for item in candidates:
            resource=int(item['resource']);entry=index.get(resource);data=None
            if entry:
                with (GAME/'Data'/entry['archive']).open('rb') as f:f.seek(entry['offset']);data=f.read(entry['size'])
                assert len(data)==entry['size'];name=f'{resource}.wav';origin=entry['archive']
            else:
                filename=Path(item['file']).name
                for base in (GAME/'Sound',GAME/'Sounds'):
                    p=base/filename
                    if p.is_file():data=p.read_bytes();break
                name=f'{sound}_{item["item"]}_{filename}';origin='loose sound file'
            if data is None:missing.append(dict(civ=civ,sound=sound,item=item,reason='missing audio resource'));continue
            if data[:4]!=b'RIFF' or data[8:12]!=b'WAVE':missing.append(dict(civ=civ,sound=sound,resource=resource,reason='not RIFF/WAVE'));continue
            offset=12;fmt=None
            while offset+8<=len(data):
                chunk=data[offset:offset+4];size=struct.unpack_from('<I',data,offset+4)[0]
                if offset+8+size>len(data):raise ValueError(('truncated WAV chunk',name))
                if chunk==b'fmt ':fmt=struct.unpack_from('<HHIIHH',data,offset+8)
                offset+=8+size+(size&1)
            if fmt is None:raise ValueError(('missing WAV fmt',name))
            dest=folder/name
            if name in files:assert files[name]['sha256']==hashlib.sha256(data).hexdigest()
            else:
                dest.write_bytes(data);files[name]=dict(file=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),origin=origin,format=fmt[0],channels=fmt[1],sample_rate=fmt[2])
            bindings.append(dict(civ=civ,sound=sound,item=int(item['item']),file=name,probability=int(item['probability'])))
report={'files':list(files.values()),'bindings':bindings,'unresolved':missing,'source_silent_groups':silent,'status':'Source clips extracted; custom WEM conversion and dataset bindings checked separately; engine playback unverified'}
Path('outputs/faction-audio-report.json').write_text(json.dumps(report,indent=2))
print('Files',len(files),'bindings',len(bindings),'unresolved',len(missing),'formats',dict(Counter(x['format'] for x in files.values())))
