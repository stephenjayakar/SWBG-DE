"""Recover source combat-domain selectors; this does not modify DE targeting."""
from pathlib import Path
import csv,hashlib,json,struct
root=Path(r'E:\GOG Games\Star Wars - Galactic Battlegrounds\Game')
data=(root/'battlegrounds_x2.exe').read_bytes()
sha=hashlib.sha256(data).hexdigest()
assert sha=='d64e7f0ecc546c3bd833c5c6a7bc97b75ee74940d89b1cb22349b0ace0f3fc58'
pe=struct.unpack_from('<I',data,60)[0]
count=struct.unpack_from('<H',data,pe+6)[0]
optional=struct.unpack_from('<H',data,pe+20)[0]
base=struct.unpack_from('<I',data,pe+52)[0]
sections=[]
for i in range(count):
 off=pe+24+optional+40*i
 virtual_size,rva,raw_size,raw=struct.unpack_from('<IIII',data,off+8)
 sections.append((rva,max(virtual_size,raw_size),raw))
def at(address,size):
 rva=address-base
 start,extent,raw=next(s for s in sections if s[0]<=rva<s[0]+s[1])
 return data[raw+rva-start:raw+rva-start+size]
def dword(address):return struct.unpack('<I',at(address,4))[0]
# Jump destinations decoded from the exact installed executable's two switches.
categories={0x41c5fd:4,0x41c604:0,0x41c608:10,0x41c60f:12,
 0x41c616:13,0x41c61d:1,0x41c624:2,0x41c62b:3,0x41c632:9,
 0x41c639:6,0x41c640:5,0x41c647:7,0x41c64e:15,0x41c655:-1}
branches={0x41c673:'air-only',0x41c69b:'ground-only',0x41c6c3:'ground-only',
 0x41c6e1:'dual-purpose',0x41c6eb:'none'}
class_modes={}
for cls in range(65):
 category=-1
 if cls>=5:
  destination=dword(0x41c6f4+4*at(0x41c72c+cls-5,1)[0])
  category=categories[destination]
 branch=0x41c6eb if category<0 else dword(0x41c768+4*at(0x41c778+category,1)[0])
 class_modes[cls]=branches[branch]
assert class_modes[52]=='ground-only' and class_modes[48]=='dual-purpose'
assert class_modes[9]=='air-only' and class_modes[43]=='ground-only'
lists={name:{int(v) for v in (root/'Data'/name).read_text().split()} for name in ('ground-to-air.txt','air-to-air.txt')}
units={(r['civ'],int(r['id'])):r for r in csv.DictReader(open('work/faction-source/units.tsv'),delimiter='\t')}
roster=json.loads(Path('outputs/faction-roster-report.json').read_text())
result=[]
for civ in ('1','3'):
 for entry in roster[civ]['production_roster']:
  uid=entry['id'];unit=units[civ,uid];cls=int(unit['class'])
  mode=class_modes.get(cls,'none');reason='source class switch'
  if uid in lists['ground-to-air.txt'] and cls!=4:
   mode='dual-purpose';reason='ground-to-air.txt early return'
  elif uid in (500,603):
   mode='ground-only until resource 31 > 0; then dual-purpose';reason='source AT-AT technology gate before class switch'
  elif uid in lists['air-to-air.txt'] and cls!=4:
   mode='air-only';reason='EF air-to-air category override'
  result.append(dict(civ=int(civ),unit=uid,name=unit['name'],source_class=cls,domain=mode,reason=reason))
report=dict(source_executable_sha256=sha,source_function='0x41C530',
 airborne_target_classes=[43,48,59,62,63,64],
 unconditional_target_exclusions=dict(unit_ids=[696],classes=[21,28]),
 source_lists={name:dict(ids=sorted(ids),sha256=hashlib.sha256((root/'Data'/name).read_bytes()).hexdigest()) for name,ids in lists.items()},
 class_modes=class_modes,roster=result,
 limits=['Domain gate only: does not establish an attack task, weapon, range, diplomacy, visibility or pathing',
 'Initial target virtual-method rejection is not modeled',
 'Installed EF DLL execution and DE runtime adapter remain unverified'],de_adapter_implemented=False)
Path('outputs/faction-target-domains.json').write_text(json.dumps(report,indent=2)+'\n')
from collections import Counter
print(dict(Counter(r['domain'] for r in result)))
print('AT-AT entries:',[r for r in result if r['unit'] in (500,603)])
