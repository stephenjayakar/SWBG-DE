from pathlib import Path
import csv,json,hashlib
source=Path(r'E:\GOG Games\Star Wars - Galactic Battlegrounds\Game\Data\resgen.txt')
records=[]
units={(int(r['civ']),int(r['id'])):r for r in csv.DictReader(open('work/faction-source/units.tsv'),delimiter='\t')}
rates={(int(r['civ']),int(r['unit'])):float(r['workrate']) for r in csv.DictReader(open('work/faction-source/unit-behavior.tsv'),delimiter='\t')}
roster=json.loads(Path('outputs/faction-roster-report.json').read_text())
maps=json.loads(Path('outputs/faction-map-report.json').read_text())['maps']
for line in source.read_text().splitlines():
 uid,res,mode,control=line.split();uid=int(uid);res=int(res);control=int(control)
 assert mode=='r' and control in (215,216,217,218)
 records.append(dict(unit=uid,name=units[1,uid]['name'],resource=res,control_resource=control,
  source_workrate={str(c):rates[c,uid] for c in (1,3)},
  production_factions=[c for c in ('1','3') if uid in {r['id'] for r in roster[c]['production_roster']}],
  maps=[m['name'] for m in maps if uid in m['objects']]))
report=dict(source_file=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
 source_code='https://github.com/rva2895/efpatch/blob/f2773079b3deb53737d86165351a7279fa71b5e9/cheatdll/resgenbldgs.cpp',
 source_formula='control resource / 60 * master work_rate, once per observed one-second building update (loaded version >= 6)',
 records=records,adapter_implemented=False,
 limits='List consumers identified; existing generation loop/version has not been verified in a running source match. Map matches use the current exported object inventory.')
Path('outputs/faction-resource-producers.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(records,indent=2))
