"""Stage spatial defaults for existing source hotkey IDs; report missing IDs."""
from pathlib import Path
import csv,json,collections
rows=list(csv.DictReader(open('work/faction-source/production.tsv'),delimiter='\t'))
rosters=json.loads(Path('outputs/faction-roster-report.json').read_text())
selected={}
for civ in ('1','3'):
 units={r['id'] for r in rosters[civ]['production_roster']};techs=set(rosters[civ]['technologies'])
 for row in rows:
  if (row['kind']=='unit' and row['civ']==civ and int(row['id']) in units) or (row['kind']=='tech' and int(row['id']) in techs):
   selected[(row['kind'],row['civ'],row['id'],row['location'])]=row
bindings=collections.defaultdict(list);pending=[]
for row in selected.values():
 button=int(row['button']);hotkey=int(row['hotkey'])
 if button==255:continue
 if hotkey<0 or not 1<=button<=15:pending.append(row);continue
 bindings[hotkey].append(("QWERTASDFGZXCVB"[button-1],row))
conflicts={str(k):v for k,v in bindings.items() if len({key for key,row in v})>1}
report=dict(existing_hotkey_bindings=len(bindings),conflicts=conflicts,missing_or_special_commands=pending,
 status='Inventory only; unique DAT hotkey IDs are needed before safe installation',profile_modified=False)
Path('outputs/faction-spatial-hotkey-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(len(bindings),'existing IDs;',len(conflicts),'cross-position conflicts;',len(pending),'missing/special commands')
