"""Regression check: original source SLP conversions must emit neutral masks."""
from pathlib import Path
import json,shutil,subprocess
from smx_neutral_masks import neutralize
root=Path('work/all-sprite-masks');source=root/'converter-input';source.mkdir(exist_ok=True)
# Explosion, trooper idle, corpse decay, tree stump: cover omitted categories
# and both plain and player-color pixels through the actual conversion pipeline.
ids=(4990,6951,6954,5169)
for gid in ids:shutil.copy2(Path('work/faction-valid-slp')/f'{gid}.slp',source/f'{gid}.slp')
for scale in (1,2):
    dest=root/f'converter-output-{scale}'
    run=subprocess.run(['java','-cp','Export/SMX Workshop.jar;.', 'PortSprites',
        str(source.resolve()),str(dest.resolve()),'../extracted/interfac_x2/50500.bin',str(scale)],
        cwd='work/smx-workshop',check=True,capture_output=True,text=True)
    (root/f'converter-{scale}.log').write_text(run.stdout)
    for gid in ids:
        before=(dest/f'swgb_{gid}.smx').read_bytes();after,stats=neutralize(before)
        assert after==before and stats['missing_frames']==stats['nonneutral_frames']==0,gid
(root/'converter-check.json').write_text(json.dumps(dict(graphics=ids,scales=[1,2],passed=True),indent=2))
print('PASS: source explosion, trooper, corpse and stump conversions are neutral at both scales')
