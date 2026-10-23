"""Inventory reachable resource effects that lack a native behavior mapping."""
from pathlib import Path
from collections import defaultdict
import csv,json

def rows(path):return list(csv.DictReader(open(path),delimiter='\t'))
mapping={int(r['source']):int(r['target']) for r in rows('work/faction-resource-mapping.tsv')}
techs={int(r['id']):r for r in rows('work/faction-source/techs.tsv')}
effects=defaultdict(list)
for r in rows('work/faction-source/effects.tsv'):effects[int(r['effect'])].append(r)
rosters=json.loads(Path('outputs/faction-roster-report.json').read_text())
findings=[]
for civ in ('1','3'):
    for tid in rosters[civ]['technologies']:
        tech=techs[tid]
        for effect in effects[int(tech['effect'])]:
            if effect['type'] not in ('1','6'):continue
            resource=int(effect['a'])
            if mapping.get(resource,-1)<2000:continue
            findings.append(dict(civ=int(civ),tech=tid,name=tech['name'],
                                 effect=int(tech['effect']),command=int(effect['command']),
                                 resource=resource,target_resource=mapping[resource],
                                 operation=int(effect['type']),mode=int(effect['b']),value=float(effect['d']),
                                 status='experimental power adapter' if resource in (18,19,30) else 'experimental XS repair adapter' if resource==212 else 'special map buildings; stored only' if resource in (215,216,217,218) else 'stored only; behavior unresolved'))
grouped=defaultdict(list)
for row in findings:grouped[row['resource']].append(row)
report=dict(scope='Reachable resource effects only; not a complete mechanics audit',
            findings=findings,resources={str(k):len(v) for k,v in sorted(grouped.items())})
Path('outputs/faction-mechanics-audit.json').write_text(json.dumps(report,indent=2))
lines=['# Reachable source-resource effects','',
       'These effects change isolated resource slots in the draft. Power and Astromech Repairs have experimental adapters; the remaining slots have no implemented behavior. Counts include automatic and prerequisite technologies; they are not all visible research buttons. This audit does not cover hardcoded unit IDs, task semantics, attributes, flags or artwork.','',
       '| Source resource | Commands across both factions | Affected technology IDs | Status |',
       '|---|---:|---|---|']
for resource,entries in sorted(grouped.items()):
    lines.append(f"| {resource} | {len(entries)} | {', '.join(map(str,sorted({r['tech'] for r in entries})))} | {entries[0]['status']} |")
lines+=['','Do not treat a technology as implemented merely because its costs, button, prerequisite and effect data are present. Resources 215–218 are consumed by eight buildings listed in the installed resgen.txt, none present in either production roster or the 20 current map object inventories; see RESOURCE-PRODUCERS.md. Their special-map behavior remains unimplemented. Other unresolved resources still need a source-behavior specification, engine adapter and runtime verification. See faction-mechanics-audit.json for command values and per-faction details.','']
Path('outputs/MECHANICS-AUDIT.md').write_text('\n'.join(lines))
print(len(findings),'reachable resource commands across',len(grouped),'isolated resource slots')
