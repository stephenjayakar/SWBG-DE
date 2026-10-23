"""Validate source continuity, faction theme names and shipped music hashes."""
from pathlib import Path
import hashlib,json,struct,sys,wave
from faction_music import GAME,ROOT,CACHE,digest

report=json.loads(Path('outputs/faction-music-report.json').read_text())
assert report['pcm_readback_exact']
names={r['file'] for r in report['files']}
assert len(names)==38 and {f'ingame{i:02}.wem' for i in range(1,31)}<=names
assert {p.name for p in ROOT.iterdir()}==names
civs=json.loads(Path('work/faction-package/resources/_common/dat/civilizations.json').read_text())['civilization_list']
assert {c['internal_name']+'_theme.wem' for c in civs[1:]}<=names
assert {r['file']:r.get('source') for r in report['files']}['GalacticEmpire_theme.wem']=='Sound/Stream/ef_civ1.mp3'
assert {r['file']:r.get('source') for r in report['files']}['RebelAlliance_theme.wem']=='Sound/Stream/ef_civ3.mp3'
emitted=hashlib.sha256();frames=0
for r in report['files']:
    p=ROOT/r['file'];assert digest(p)==r['sha256'],p
    with p.open('rb') as f:
        head=f.read(52)
        assert head[:4]==b'RIFF' and head[8:16]==b'WAVEfmt ' and head[44:48]==b'data'
        assert struct.unpack_from('<HHI',head,20)==(65534,r['channels'],r['rate'])
        assert struct.unpack_from('<I',head,48)[0]==r['frames']*r['channels']*2
        pcm=f.read();assert hashlib.sha256(pcm).hexdigest()==r['pcm_sha256']
        if r['file'].startswith('ingame'):
            assert r['shared_start_frame']==frames
            frames+=r['frames'];assert r['shared_end_frame']==frames
            emitted.update(pcm)
    if 'source' in r:assert digest(GAME/r['source'])==r['source_sha256']
source=hashlib.sha256()
for r in report['shared_sources']:
    assert digest(GAME/r['file'])==r['sha256']
    with wave.open(str(CACHE/(Path(r['file']).stem+'.wav')),'rb') as w:
        while pcm:=w.readframes(262144):source.update(pcm)
assert frames==report['shared_frames']
assert emitted.hexdigest()==source.hexdigest()==report['shared_pcm_sha256']
if '--installed' in sys.argv:
    install=json.loads(Path('outputs/faction-install-report.json').read_text())
    for root in (Path('outputs/SWGB-DE-Factions-Draft'),Path(install['asset_mod'])):
        for r in report['files']:
            assert digest(root/'resources/_common/sound/music'/r['file'])==r['sha256']
print(f'PASS: {len(names)} music files, exact shared PCM order, correct faction theme names; engine playback unverified')
