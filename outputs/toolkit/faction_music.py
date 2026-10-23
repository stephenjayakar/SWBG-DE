"""Port installed SWGB/EF music into DE's documented music override slots.

Requires the existing vgmstream decoder. Does not change original game files.
The 30 DE slots contain contiguous portions of the two installed OGG streams;
use Standard playlist for source order and the faction opening theme.
"""
from pathlib import Path
import hashlib,json,struct,subprocess,wave

GAME=Path(r'E:\GOG Games\Star Wars - Galactic Battlegrounds\Game')
ROOT=Path('work/faction-package/resources/_common/sound/music')
CACHE=Path('work/faction-music');ROOT.mkdir(parents=True,exist_ok=True);CACHE.mkdir(exist_ok=True)
CLI=Path('work/vgmstream/vgmstream-cli.exe').resolve()

def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()

def decode(source):
    dest=CACHE/(source.stem+'.wav');stamp=dest.with_suffix('.sha256')
    source_hash=digest(source)
    if not dest.exists() or not stamp.exists() or stamp.read_text()!=source_hash:
        subprocess.run([str(CLI),'-i','-o',str(dest),str(source)],check=True,capture_output=True)
        stamp.write_text(source_hash)
    return dest

def write_wem(name,pcm,rate,channels):
    align=channels*2;config=((4 if channels==1 else 3)<<12)|(1<<8)|channels
    fmt=struct.pack('<HHIIHHHHI',0xfffe,channels,rate,rate*align,align,16,6,16,config)
    body=b'WAVE'+b'fmt '+struct.pack('<I',len(fmt))+fmt+b'data'+struct.pack('<I',len(pcm))+pcm
    dest=ROOT/name;dest.write_bytes(b'RIFF'+struct.pack('<I',len(body))+body)
    check=CACHE/'readback.wav'
    subprocess.run([str(CLI),'-i','-o',str(check),str(dest)],check=True,capture_output=True)
    with wave.open(str(check),'rb') as w:
        assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(rate,channels,2)
        assert w.readframes(w.getnframes())==pcm,name
    return dict(file=name,sha256=digest(dest),pcm_sha256=hashlib.sha256(pcm).hexdigest(),
                frames=len(pcm)//align,rate=rate,channels=channels)

def main():
    originals=[GAME/'MUSIC'/name for name in ('Track02.ogg','Track03.ogg')]
    streams=[wave.open(str(decode(p)),'rb') for p in originals]
    for w in streams:assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(44100,2,2)
    total=sum(w.getnframes() for w in streams);files=[];cursor=0;stream=0
    all_pcm=hashlib.sha256()
    for slot in range(1,31):
        end=total*slot//30;needed=end-cursor;pieces=[]
        while needed:
            w=streams[stream];take=min(needed,w.getnframes()-w.tell())
            pieces.append(w.readframes(take));needed-=take
            if w.tell()==w.getnframes():stream+=1
        pcm=b''.join(pieces);all_pcm.update(pcm)
        row=write_wem(f'ingame{slot:02}.wem',pcm,44100,2)
        row.update(shared_start_frame=cursor,shared_end_frame=end);files.append(row);cursor=end
        print(f'Music {slot}/30 verified',flush=True)
    assert cursor==total and stream==2
    for w in streams:w.close()
    # EF hooks use stream/ef_civ%d.mp3, using the source civilization number.
    cues={'GalacticEmpire_theme.wem':'ef_civ1.mp3','RebelAlliance_theme.wem':'ef_civ3.mp3',
          'frontend01.wem':'ef_menu_yavin.mp3','credits01.wem':'CREDITS.MP3',
          'win01.wem':'WON1.MP3','win02.wem':'won2.mp3','lose01.wem':'lost.mp3'}
    for name,source_name in cues.items():
        source=GAME/'Sound/Stream'/source_name
        with wave.open(str(decode(source)),'rb') as w:
            assert w.getsampwidth()==2
            row=write_wem(name,w.readframes(w.getnframes()),w.getframerate(),w.getnchannels())
        row.update(source=source.relative_to(GAME).as_posix(),source_sha256=digest(source));files.append(row)
    # Lobby uses the installed EF menu theme; no invented faction playlist.
    import shutil
    shutil.copy2(ROOT/'frontend01.wem',ROOT/'lobby01.wem')
    files.append(dict(next(r for r in files if r['file']=='frontend01.wem'),file='lobby01.wem'))
    assert {p.name for p in ROOT.iterdir()}=={r['file'] for r in files}
    report=dict(files=files,shared_sources=[dict(file=p.relative_to(GAME).as_posix(),sha256=digest(p)) for p in originals],
                shared_frames=total,shared_pcm_sha256=all_pcm.hexdigest(),shared_seconds=total/44100,
                pcm_readback_exact=True,engine_playback_verified=False,
                limits=['DE controls playlist order/transitions; 30 slots are contiguous portions, not original song boundaries',
                        'Standard playlist includes faction theme; Classic omits it; shuffle changes source order',
                        'Faction selection cue is played at match start using DE civilization themes',
                        'Menu music applies globally while the companion is enabled'])
    Path('outputs/faction-music-report.json').write_text(json.dumps(report,indent=2))
    print(f'{len(files)} music files verified; {total/44100/60:.2f} minutes shared music')

if __name__=='__main__':main()
