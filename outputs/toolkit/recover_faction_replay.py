"""Recover selected sections of the exact local diagnostic replay header.
Full-header parsing is unsupported; do not use this as a general replay parser.
No player names or replay contents are written to the public report.
"""
import sys,io,json,collections,math,hashlib,subprocess
from pathlib import Path
raw=Path('work/user-match-header.raw').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='25dcc5503cc894de1cb6fb545e9fa573974f1848351957b8db5a66b5457d142b', 'Different replay requires a fresh format investigation'
parser=Path('work/mgz-fast')
assert subprocess.check_output(['git','-C',str(parser),'rev-parse','HEAD'],text=True).strip()=='6fd28520fea4e80a2f0d67bc219d2bc4cf119751'
sys.path.insert(0,str(parser.resolve()))
from mgz.fast.header import parse_map,parse_players
from mgz.util import Version
stream=io.BytesIO(raw);stream.seek(25852)
m=parse_map(stream,Version.DE,68.0)
assert stream.tell()==661694 and m['dimension']==120 and len(m['tiles'])==14400
players,_,_=parse_players(stream,3,Version.DE,68.0)
assert stream.tell()==8919316 and len(players)==3
objects=players[0]['objects'];starts=[]
for player in players[1:]:
    cc=next(o for o in player['objects'] if o['object_id']==109)
    x,y=cc['position']['x'],cc['position']['y']
    nova=[math.hypot(o['position']['x']-x,o['position']['y']-y) for o in objects if o['object_id']==66]
    starts.append(dict(player=player['number'],command_center=[x,y],terrain=m['tiles'][int(y)*120+int(x)][0]%256,nearest_nova_distance=min(nova)))
report=dict(header_sha256=hashlib.sha256(raw).hexdigest(),parser_commit='6fd28520fea4e80a2f0d67bc219d2bc4cf119751',map_dimension=120,terrain_counts=dict(collections.Counter(t%256 for t,h in m['tiles'])),gaia_resource_counts={str(k):sum(o['object_id']==k for o in objects) for k in (66,102,1159)},starts=starts,limitations=['Selected sections recovered after full-header parser failure; not a general replay parser','Describes the earlier installed build, not the repaired candidate','Object extraction uses the upstream parser; no new match has been generated'])
Path('outputs/faction-replay-repair-evidence.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
