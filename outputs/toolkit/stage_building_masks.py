"""Select building, Nova and Ore artwork that needs a neutral DE damage mask."""
import csv
from pathlib import Path
def rows(name):
    return list(csv.DictReader((Path('work/faction-source')/(name+'.tsv')).open(),delimiter='\t'))
buildings={(r['civ'],r['unit']) for r in rows('compat-units') if r['type']=='80' or r['class'] in ('29','30')}
roots={int(r['graphic']) for r in rows('unit-art') if (r['civ'],r['unit']) in buildings and r['field'] in ('standing','standing2','garrison','construction','snow')}
children={}
for r in rows('deltas'):children.setdefault(int(r['parent']),set()).add(int(r['child']))
selected=set();pending=list(roots)
while pending:
    g=pending.pop()
    if g<0 or g in selected:continue
    selected.add(g);pending.extend(children.get(g,()))
staged={int(r['source']) for r in csv.DictReader(open('work/faction-roster-art.tsv'),delimiter='\t') if int(r['slp'])>=0}
selected &= staged
Path('work/faction-building-mask-graphics.txt').write_text(''.join(f'{g}\n' for g in sorted(selected)))
print(f'{len(selected)} staged building graphics selected')
