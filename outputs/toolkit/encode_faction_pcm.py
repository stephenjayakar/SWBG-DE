"""Stage lossless Wwise PCM containers and verify decoding with vgmstream.

This does not establish playback in DE's current Wwise build.
"""
import json,struct,subprocess,hashlib,concurrent.futures
from pathlib import Path
def chunks(data):
    assert data[:4]==b'RIFF' and data[8:12]==b'WAVE'
    offset=12;result={}
    while offset+8<=len(data):
        key=data[offset:offset+4];size=struct.unpack_from('<I',data,offset+4)[0]
        assert offset+8+size<=len(data)
        result[key]=data[offset+8:offset+8+size];offset+=8+size+(size&1)
    return result
def chunk(name,data):return name+struct.pack('<I',len(data))+data+(b'\0' if len(data)&1 else b'')
root=Path('work/faction-package/resources/_common/drs/sounds');root.mkdir(parents=True,exist_ok=True)
decoded=Path('work/faction-audio-decoded');decoded.mkdir(exist_ok=True)
cli=Path('work/vgmstream/vgmstream-cli.exe').resolve()
def convert(entry):
    source=Path('work/faction-audio-source',entry['file']).read_bytes();parts=chunks(source)
    tag,channels,rate,byte_rate,align,bits=struct.unpack_from('<HHIIHH',parts[b'fmt '])
    assert tag==1 and bits==16 and channels in (1,2) and align==channels*2 and byte_rate==rate*align
    # Wwise PCM fmt extension: valid bits and serialized speaker configuration.
    channel_mask=4 if channels==1 else 3
    config=(channel_mask<<12)|(1<<8)|channels
    fmt=struct.pack('<HHIIHHHHI',0xfffe,channels,rate,byte_rate,align,bits,6,bits,config)
    body=b'WAVE'+chunk(b'fmt ',fmt)
    if b'smpl' in parts:body+=chunk(b'smpl',parts[b'smpl'])
    body+=chunk(b'data',parts[b'data'])
    name='swgb_'+Path(entry['file']).stem
    wem=root/(name+'.wem');wem.write_bytes(b'RIFF'+struct.pack('<I',len(body))+body)
    wav=decoded/(name+'.wav')
    result=subprocess.run([str(cli),'-i','-o',str(wav),str(wem)],capture_output=True,text=True)
    if result.returncode:raise RuntimeError((name,result.stdout,result.stderr))
    readback=chunks(wav.read_bytes())
    assert readback[b'data']==parts[b'data'],name
    out_fmt=struct.unpack_from('<HHIIHH',readback[b'fmt ']);assert out_fmt[1]==channels and out_fmt[2]==rate and out_fmt[5]==bits,name
    return dict(file=wem.name,sha256=hashlib.sha256(wem.read_bytes()).hexdigest(),pcm_sha256=hashlib.sha256(parts[b'data']).hexdigest(),frames=len(parts[b'data'])//align,rate=rate,channels=channels)
entries=json.loads(Path('outputs/faction-audio-report.json').read_text())['files']
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(convert,entries))
Path('outputs/faction-pcm-report.json').write_text(json.dumps({'files':results,'decoder':'vgmstream r2117','pcm_roundtrip_exact':True,'engine_playback_verified':False},indent=2))
print(len(results),'Wwise PCM files decoded byte-exactly; in-game playback remains unverified')
