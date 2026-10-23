"""Exercise 4+1 conversion and mixed normal/player colors with a second decoder."""
from pathlib import Path
import struct,subprocess
from smx_neutral_masks import neutralize
root=Path('work/all-sprite-masks');p=root/'encoding-before.smx';q=root/'encoding-after.smx'
# Four known palette indices in sections 0,1,2,3; two are player-color commands.
commands=bytes([1,6,1,3]);pixels=bytes([5,14,23,32,0xe4])
payload=struct.pack('<HHII',0,0,len(commands),len(pixels))+commands+pixels
frame=struct.pack('<BBI',1,0,0)+struct.pack('<HHhhII',4,1,2,1,len(payload),0)+payload
before=struct.pack('<4sHHII16s',b'SMPX',2,1,len(frame),0,b'fixture')+frame
after,stats=neutralize(before);assert stats['missing_frames']==1 and stats['pixels']==4
p.write_bytes(before);q.write_bytes(after)
check=root/'encoding-check.tsv';check.write_text(str(p.resolve())+'\t'+str(q.resolve())+'\n')
run=subprocess.run(['java','-cp','Export/SMX Workshop.jar;.', 'VerifyNeutralSprites',str(check.resolve())],
    cwd='work/smx-workshop',check=True,text=True,capture_output=True)
assert 'PASS files=1 visible-pixels=4' in run.stdout,run.stdout
assert neutralize(after)[0]==after
print('PASS: synthetic mixed player/palette 4+1 to 8-to-5 conversion and idempotence')
