"""Extract original interface sheets and plan source roster icon conversion."""
from pathlib import Path
import csv,json,hashlib
game=Path(r'E:\GOG Games\Star Wars - Galactic Battlegrounds\Game\Data')
rank={name:i for i,name in enumerate(('interfac.drs','interfac_x1.drs','interfac_x2.drs'))}
index={}
for row in json.loads(Path('outputs/archive-manifest.json').read_text()):
    name=row['archive'].lower()
    if row['ext']!='slp' or name not in rank:continue
    if row['id'] not in index or rank[name]>rank[index[row['id']]['archive'].lower()]:index[row['id']]=row
roster=json.loads(Path('outputs/faction-roster-report.json').read_text())
folder=Path('work/faction-icon-slp');folder.mkdir(exist_ok=True)
rows=[];sheets={};missing=[]
for r in csv.DictReader(open('work/faction-source/icons.tsv'),delimiter='\t'):
    civ=r['civ']
    if civ not in ('1','3'):continue
    ids={x['id'] for x in roster[civ]['production_roster']} if r['kind']=='unit' else set(roster[civ]['technologies'])
    if int(r['id']) not in ids:continue
    slp=int(r['slp'])
    if slp not in index:missing.append(r);continue
    if slp not in sheets:
        entry=index[slp]
        with (game/entry['archive']).open('rb') as f:f.seek(entry['offset']);data=f.read(entry['size'])
        assert len(data)==entry['size'];(folder/f'{slp}.slp').write_bytes(data)
        sheets[slp]=dict(archive=entry['archive'],sha256=hashlib.sha256(data).hexdigest())
    rows.append(r)
with open('work/faction-icons.tsv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=('civ','kind','id','slp','frame'),delimiter='\t');w.writeheader();w.writerows(rows)
report=dict(bindings=rows,sheets=sheets,missing=missing,status='Source icon frames only; DE UI bindings not installed')
Path('outputs/faction-icon-report.json').write_text(json.dumps(report,indent=2))
print(len(rows),'icon bindings;',len(sheets),'source sheets;',len(missing),'missing')
