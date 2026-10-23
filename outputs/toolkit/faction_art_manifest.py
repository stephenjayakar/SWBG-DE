"""Bootstrap identity graphic mappings without requiring an existing target DAT."""
from pathlib import Path
import csv
with open('work/faction-art-mapping.tsv','w',newline='') as f:
    w=csv.writer(f,delimiter='\t');w.writerow(('source','target','slp','filename'))
    for r in csv.DictReader(open('work/faction-source/art.tsv'),delimiter='\t'):
        gid=int(r['id']);slp=int(r['slp']);empty=slp<6 or gid in (4866,4868,4891,4893)
        w.writerow((gid,gid,-1 if empty else slp,'' if empty else f'swgb_{gid}_x1'))
