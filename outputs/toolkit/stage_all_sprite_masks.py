"""Repair every installed SWGB sprite, without reading paused faction staging."""
from pathlib import Path
import hashlib,json,shutil
from smx_neutral_masks import neutralize

work=Path('work/all-sprite-masks');work.mkdir(exist_ok=True)
for name in ('faction-package-manifest.json','faction-install-report.json'):
    if not (work/name).exists():shutil.copy2(Path('outputs')/name,work/name)
manifest=json.loads((work/'faction-package-manifest.json').read_text())
root=Path('outputs/SWGB-DE-Factions-Draft');patch=work/'patch';records=[];checks=[]
for r in manifest['files']:
    name=r['path']
    if not name.endswith('.smx'):continue
    assert name.startswith('resources/_common/drs/graphics/swgb_')
    before=(root/name).read_bytes();assert hashlib.sha256(before).hexdigest()==r['sha256'],name
    after,stats=neutralize(before)
    # A second pass verifies explicit zero fields and idempotence independently
    # of the Java decoded-pixel comparison performed before installation.
    again,audit=neutralize(after)
    assert again==after and audit['missing_frames']==audit['nonneutral_frames']==0,name
    dest=root/name
    if after!=before:
        dest=patch/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(after)
    records.append(dict(path=name,before_sha256=r['sha256'],sha256=hashlib.sha256(after).hexdigest(),
        bytes=len(after),changed=after!=before,**stats))
    checks.append(str((root/name).resolve())+'\t'+str(dest.resolve()))
    if len(records)%200==0:print('scanned',len(records),flush=True)
assert len(records)==2414
(work/'verify.tsv').write_text('\n'.join(checks)+'\n')
(work/'scan.json').write_text(json.dumps(dict(files=records),indent=2))
print('COMPLETE',len(records),'files;',sum(r['changed'] for r in records),'changed;',
      sum(r['missing_frames'] for r in records),'missing-mask frames;',
      sum(r['nonneutral_frames'] for r in records),'nonneutral frames',flush=True)
