"""Check custom sound references and staged media, not in-engine playback."""
import csv,json
from pathlib import Path
from faction_aliases import source_aliases
def read(folder,name):return list(csv.DictReader(open(f'work/{folder}/{name}.tsv'),delimiter='\t'))
offset=int(Path('work/faction-sound-offset.txt').read_text())
civ=lambda c:str({0:0,1:1,3:2}[int(c)])
source=source_aliases(read('faction-source','unit-sounds'),'unit');target=read('faction-target-dependencies','unit-sounds')
before={(civ(r['civ']),r['unit'],r['event'],str(int(r['sound'])+offset)) for r in source}
after={(r['civ'],r['unit'],r['event'],r['sound']) for r in target}
assert before==after,'Unit sound bindings differ'
angles={r['id']:int(r['angles']) for r in read('faction-source','art')}
before=set()
for row in read('faction-source','graphic-sounds'):
    a=int(row['angle']);count=angles[row['graphic']]
    if a>=0 and count in (8,16):a=(a-3*count//4+count)%count
    before.add((row['graphic'],str(a),row['frame'],str(int(row['sound'])+offset)))
after={(r['graphic'],r['angle'],r['frame'],r['sound']) for r in read('faction-target-dependencies','graphic-sounds')}
assert before==after,'Graphic frame sounds differ'
items={(int(r['sound']),int(r['item'])):r for r in read('faction-target-dependencies','sounds')}
audio=json.loads(Path('outputs/faction-audio-report.json').read_text())
for binding in audio['bindings']:
    item=items[(binding['sound']+offset,binding['item'])]
    expected='swgb_'+Path(binding['file']).stem
    assert item['file']==expected and int(item['probability'])==binding['probability']
    assert (Path('work/faction-package/resources/_common/drs/sounds')/(expected+'.wem')).is_file()
pcm=json.loads(Path('outputs/faction-pcm-report.json').read_text());assert pcm['pcm_roundtrip_exact']
report={'unit_sound_bindings':True,'graphic_frame_sound_bindings':True,'media_files':len(pcm['files']),'bindings':len(audio['bindings']),'source_unresolved':audio['unresolved'],'engine_playback_verified':False}
Path('outputs/faction-audio-validation.json').write_text(json.dumps(report,indent=2));print('Audio bindings and',len(pcm['files']),'lossless PCM media files validated; engine playback not verified')
