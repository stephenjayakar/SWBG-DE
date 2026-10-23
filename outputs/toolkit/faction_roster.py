"""Conservative production/technology reachability for asset staging, not an AI simulator."""
from pathlib import Path
from collections import defaultdict
import csv,json,struct
ROOT=Path('work/faction-source')
def read(name):
    return list(csv.DictReader((ROOT/(name+'.tsv')).open(),delimiter='\t'))
units={(int(x['civ']),int(x['id'])):x for x in read('units')}
techs={int(x['id']):x for x in read('techs')}
effects=defaultdict(list)
for x in read('effects'):effects[int(x['effect'])].append(x)
requirements=defaultdict(list)
for x in read('requirements'):requirements[int(x['tech'])].append(int(x['prerequisite']))
locations=defaultdict(set)
for x in read('production'):locations[(x['kind'],int(x['civ']),int(x['id']))].add(int(x['location']))
building_tech={(int(x['civ']),int(x['unit'])):int(x['tech']) for x in read('building-techs')}
links=defaultdict(set)
for x in read('unit-links'):links[(int(x['civ']),int(x['unit']))].add(int(x['target']))
art=defaultdict(set)
for x in read('unit-art'):art[(int(x['civ']),int(x['unit']))].add(int(x['graphic']))
children=defaultdict(set)
graphic_rows=read('art');graphic_names={r['name']:int(r['id']) for r in graphic_rows}
selectors={int(r['id']):r['name'] for r in graphic_rows if int(r['slp'])==-1}
for x in read('deltas'):
    if int(x['child'])>=0:children[int(x['parent'])].add(int(x['child']))
all_graphics=set();reports={}
for civ in (1,3):
    # Source standard-game roots: command center, worker, scout bike.
    roster={109,83,{1:550,3:556}[civ]};enabled=set(roster);researched=set();disabled=set()
    upgrades=set()
    def apply(effect):
        for x in effects[effect]:
            typ=int(x['type']);a=int(x['a']);b=int(x['b'])
            if typ==102:disabled.add(int(float(x['d'])))
            elif typ==2 and b==1 and a>=0:enabled.add(a)
            elif typ==3:upgrades.add((a,b))
    row=next(x for x in read('civs') if int(x['id'])==civ)
    apply(int(row['techtree']));apply(int(row['team_bonus']))
    # Building-triggered technologies must not auto-research merely because
    # they have no location. All other no-location techs use prerequisites.
    triggered={t for (c,u),t in building_tech.items() if c==civ}
    changed=True
    while changed:
        old=(len(roster),len(researched),len(enabled),len(upgrades))
        for u in tuple(roster):
            t=building_tech.get((civ,u))
            if t is not None and t not in researched and t not in disabled:
                researched.add(t);apply(int(techs[t]['effect']))
        for t,x in techs.items():
            tc=int(x['civ'])
            if tc not in (-1,civ) or t in researched or t in disabled or t in triggered:continue
            if sum(p in researched for p in requirements[t])<int(x['prerequisite_count']):continue
            loc=locations.get(('tech',tc,t),set())
            if loc and not loc.intersection(roster):continue
            researched.add(t);apply(int(x['effect']))
        has_worker=any(units[(civ,u)]['class']=='58' for u in roster)
        for u in enabled:
            if (civ,u) not in units:continue
            if locations.get(('unit',civ,u),set()).intersection(roster) or (has_worker and units[(civ,u)]['type']=='80'):roster.add(u)
        for a,b in upgrades:
            if a in roster and (civ,b) in units:roster.add(b)
        changed=old!=(len(roster),len(researched),len(enabled),len(upgrades))
    dependencies=set(roster);pending=list(roster)
    while pending:
        u=pending.pop()
        for v in links[(civ,u)]:
            if (civ,v) not in units:raise ValueError(('missing unit',civ,u,v))
            if v not in dependencies:dependencies.add(v);pending.append(v)
    graphics=set().union(*(art[(civ,u)] for u in dependencies));pending=list(graphics)
    for g in tuple(graphics):
        variant=graphic_names.get(selectors.get(g,'')+'-C'+str(civ))
        if variant is not None:graphics.add(variant);pending.append(variant)
    while pending:
        g=pending.pop()
        for child in children[g]:
            if child not in graphics:graphics.add(child);pending.append(child)
    all_graphics.update(graphics)
    reports[str(civ)]={'production_roster':[dict(id=u,name=units[(civ,u)]['name']) for u in sorted(roster)],
        'technologies':sorted(researched),'unit_dependencies':sorted(dependencies),'graphics':sorted(graphics)}
    print('Civ',civ,'roster',len(roster),'techs',len(researched),'dependent units',len(dependencies),'graphics',len(graphics))
# Gaia economy and the objects spawned by mapped terrain definitions.
world_roots={594,59,66,102,48,822,126,285,53}
map_report=Path('outputs/faction-map-report.json')
if map_report.exists():world_roots.update(json.loads(map_report.read_text())['object_roots'])
terrain_map=list(csv.DictReader(open('work/faction-terrain-map.tsv'),delimiter='\t'))
terrain_ids={int(x['source']) for x in terrain_map if x['canonical']=='1'}
for x in read('terrain-units'):
    if int(x['terrain']) in terrain_ids:world_roots.add(int(x['unit']))
dependencies=set(world_roots);pending=list(world_roots)
while pending:
    u=pending.pop()
    assert (0,u) in units,('missing Gaia unit',u)
    for v in links[(0,u)]:
        if v not in dependencies:dependencies.add(v);pending.append(v)
graphics=set().union(*(art[(0,u)] for u in dependencies));pending=list(graphics)
while pending:
    g=pending.pop()
    for child in children[g]:
        if child not in graphics:graphics.add(child);pending.append(child)
all_graphics.update(graphics)
reports['0']={'roots':sorted(world_roots),'unit_dependencies':sorted(dependencies),'graphics':sorted(graphics)}
print('Gaia roots',len(world_roots),'dependent units',len(dependencies),'graphics',len(graphics))
mapping={int(x['source']):x for x in csv.DictReader(open('work/faction-art-mapping.tsv'),delimiter='\t')}
with open('work/faction-roster-art.tsv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['source','target','slp','filename'],delimiter='\t');w.writeheader()
    for g in sorted(all_graphics):w.writerow(mapping[g])
reports['limitations']=['Reachability overapproximates alternate research paths; costs/time/population not simulated',
    'Map roots conservatively include all original conditional environments; scenario-only content remains outside the inventory',
    'This inventory does not prove playable production or cross-engine semantics']
Path('outputs/faction-roster-report.json').write_text(json.dumps(reports,indent=2))
Path('work/faction-tree-units.txt').write_text('\n'.join(map(str,sorted({r['id'] for c in ('1','3') for r in reports[c]['production_roster']}))))
