"""Promote verified neutral-mask sprites into staging, not into the game."""
import hashlib,json,re,shutil
from pathlib import Path
ids=set(map(int,Path('work/faction-building-mask-graphics.txt').read_text().split()))
records=[]
for scale,source,destination,log in [
    (1,'faction-masked','faction-roster-converted','faction-masks.log'),
    (2,'faction-masked-enhanced','faction-roster-enhanced','faction-masks-enhanced.log')]:
    evidence=set(map(int,re.findall(r'swgb_(\d+)\.smx frames=\d+ neutral-mask=PASS pixels-and-anchors=UNCHANGED',Path('work',log).read_text())))
    assert evidence==ids,('Incomplete neutral mask readback',scale)
    for gid in sorted(ids):
        src=Path('work',source,f'swgb_{gid}.smx');dest=Path('work',destination,src.name)
        records.append(dict(graphic=gid,scale=scale,sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                            source_sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
# Both resolutions pass before any staged sprite is replaced.
for r in records:
    source='faction-masked' if r['scale']==1 else 'faction-masked-enhanced'
    destination='faction-roster-converted' if r['scale']==1 else 'faction-roster-enhanced'
    dest=Path('work',destination,f"swgb_{r['graphic']}.smx")
    shutil.copy2(Path('work',source,dest.name),dest)
    assert hashlib.sha256(dest.read_bytes()).hexdigest()==r['sha256']
Path('outputs/faction-building-mask-validation.json').write_text(json.dumps(dict(
    files=records,graphics=len(ids),visible_pixels_and_anchors_unchanged=True,mask_modifier=0,engine_verified=False),indent=2))
print(f'Promoted {len(records)} verified sprites; engine damage shading remains to be tested')
