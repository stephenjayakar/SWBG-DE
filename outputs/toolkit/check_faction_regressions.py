"""Check serialized repairs for the September 9 crash/marker/scout regressions."""
import csv,json
from pathlib import Path
from PIL import Image
read=lambda n:list(csv.DictReader(open('work/faction-target/'+n+'.tsv'),delimiter='\t'))
assert not [r for r in read('effects') if r['type']=='3' and (int(r['a'])<0 or int(r['b'])<0)]
r={(int(x['civ']),int(x['id'])):float(x['value']) for x in read('resources')}
assert [r[c,263] for c in (0,1,2)]==[550,550,556]
a={int(x['id']):x for x in read('art')}
assert [(a[i]['name'],int(a[i]['frames'])) for i in (1963,2961,2962)]==[('TFLG',10),('MOVEX_NN',8),('WAYPT_NN',90)]
assert not [d for d in read('deltas') if int(d['parent']) in (1963,2961,2962)]
assert Path('work/factions.raw').read_bytes()==Path('work/factions-roundtrip.raw').read_bytes()
print('PASS: upgrade endpoints, faction scouts, three native marker slots, DAT roundtrip; icons checked separately')
