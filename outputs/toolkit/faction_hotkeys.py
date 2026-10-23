"""Generate dataset-specific spatial production hotkeys and exact DAT bindings."""
from pathlib import Path
import csv,json
from faction_language_ids import name_id
rows=list(csv.DictReader(open('work/faction-source/production.tsv'),delimiter='\t'))
for row in rows:
    if row['kind']=='tech' and row['id'] in ('1','2','3'):
        assert row['location']=='109' and row['button']=='9'
        row['button']='10'
# Keep the canonical defense layout in the C++ patch and hotkey generator aligned.
import re
layout=Path(__file__).with_name('faction_defenses.h').read_text()
defense_buttons={}
for cases,button in re.findall(r'((?:case\s+\d+:\s*)+)return (\d+);',layout):
    for uid in re.findall(r'case\s+(\d+):',cases):defense_buttons[int(uid)]=int(button)
assert len(defense_buttons)==17
layout=Path(__file__).with_name('faction_defense_extension.h').read_text()
for cases,button in re.findall(r'((?:case\s+\d+:\s*)+)return (\d+);',layout):
    for uid in re.findall(r'case\s+(\d+):',cases):defense_buttons[int(uid)]=int(button)
assert len(defense_buttons)==24
for row in rows:
    if row['kind']=='unit' and int(row['id']) in defense_buttons and row['location']=='118':
        row['button']=str(defense_buttons[int(row['id'])])
rosters=json.loads(Path('outputs/faction-roster-report.json').read_text())
selected={}
for source_civ,civ in ((1,1),(3,2)):
    roster=rosters[str(source_civ)]
    units={u['id'] for u in roster['production_roster']}
    techs=set(roster['technologies'])
    for r in rows:
        if r['kind']=='unit':
            if int(r['civ'])!=source_civ or int(r['id']) not in units:continue
            target_civ=civ
        else:
            if int(r['id']) not in techs:continue
            target_civ=-1
        key=(r['kind'],target_civ,int(r['id']),int(r['location']),int(r['button']))
        selected[key]=r
native=json.loads(Path(r'E:\SteamLibrary\steamapps\common\AoE2DE\resources\_common\dat\hotkeys.json').read_text())
entries=[];manifest=[];special=[]
for key,row in sorted(selected.items()):
    kind,civ,uid,location,button=key
    if button==255:continue # Hidden/automatic research has no ordinary grid button.
    if not 1<=button<=15:
        special.append(dict(kind=kind,civ=civ,id=uid,location=location,button=button));continue
    index=1000000+len(manifest)
    letter='QWERTASDFGZXCVB'[button-1]
    label=name_id(kind,civ,uid)
    entries.append(dict(data_name=f'SWGB_{kind.upper()}_{civ}_{uid}_{location}',
        name_string_id=label,string_index_list=[index],
        defaults_list=[dict(name=preset,key=letter) for preset in ('classic','definitive','high definition','left handed')]))
    manifest.append(dict(kind=kind,civ=civ,id=uid,location=location,button=button,hotkey=index,key=letter))
assert len({r['hotkey'] for r in manifest})==len(manifest)
from faction_defense_ui import layout_hotkeys
entries.extend(layout_hotkeys())
# Keep standard movement, selection, menu and camera commands intact.
native['hotkey_group_list'].append(dict(data_name='SWGB_SPATIAL_PRODUCTION',name_string_id=890001,hotkey_list=entries))
dest=Path('work/faction-package/resources/_common/dat');dest.mkdir(parents=True,exist_ok=True)
(dest/'hotkeys.json').write_text(json.dumps(native,indent=2)+'\n')
with open('work/faction-hotkeys.tsv','w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=['kind','civ','id','location','button','hotkey','key'],delimiter='\t');writer.writeheader();writer.writerows(manifest)
Path('outputs/faction-spatial-hotkeys.json').write_text(json.dumps(dict(bindings=manifest,special_buttons=special,engine_verified=False,profile_modified=False),indent=2)+'\n')
print(len(manifest),'unique spatial bindings;',len(special),'special buttons pending')
