"""Stage original SWGB map logic with explicit terrain translation and dependencies.

The result is a draft: source match_player_civ needs a faction-aware DE adapter.
Never installs over the confirmed native-economy map pack.
"""
from pathlib import Path
from faction_relic_maps import repair_relics
from reserved_unit_ids import de_unit_id
import ast,csv,json,re,hashlib
# SWGB condition labels that DE predefines as built-in map types. DE treats any predefined
# map-type label as TRUE in if/elseif, so the shared SWGB resource include (DRS 54103) took its
# Arena/Fortress/Forced-Deployment branches on every map (no medium/far Nova, no herds, hunt,
# predators, straggler trees or holocrons). Namespace them; Arena re-#defines SWGB_ARENA itself.
DE_MAP_TYPE_COLLISIONS=('ARENA','FORTRESS','MIGRATION')
# Map-size labels intentionally share DE's names and meaning.
SHARED_LABELS={'TINY_MAP','SMALL_MAP','MEDIUM_MAP','LARGE_MAP','HUGE_MAP','GIGANTIC_MAP'}
# DE game-mode/size aliases: SWGB "Terminate the Commander" is keyed on TERMINATE (DE: REGICIDE);
# DE's Ludikris size is larger than SWGB's largest size and should take the Gigantic branches.
MODE_ALIASES='if REGICIDE\n#define TERMINATE\nendif\nif LUDIKRIS_MAP\n#define GIGANTIC_MAP\nendif\n'
root=Path('work/extracted/gamedata_x2')
out=Path('work/faction-package/resources/_common/random-map-scripts');out.mkdir(parents=True,exist_ok=True)
maps={}
for node in ast.parse(Path('work/build_maps.py').read_text()).body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='maps' for t in node.targets):maps.update(ast.literal_eval(node.value))
    if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and isinstance(node.value.func.value,ast.Name) and node.value.func.value.id=='maps' and node.value.func.attr=='update':maps.update(ast.literal_eval(node.value.args[0]))
terrain={r['symbol']:int(r['target']) for r in csv.DictReader(open('work/faction-terrain-map.tsv'),delimiter='\t')}
units={(int(r['civ']),int(r['id'])) for r in csv.DictReader(open('work/faction-source/units.tsv'),delimiter='\t')}
def flatten(entry,stack=()):
    if entry in stack:raise ValueError(('include cycle',stack,entry))
    source=(root/f'{entry}.bin').read_text()
    return re.sub(r'#include_drs\s+\S+\s+(\d+)',lambda m:flatten(int(m[1]),stack+(entry,)),source)
records=[];objects=set()
for entry,name in maps.items():
    source=flatten(entry)
    body=re.sub(r'/\*.*?\*/','',source,flags=re.S)
    assert '#include' not in body
    constants={k:int(v) for k,v in re.findall(r'#const\s+(\S+)\s+(-?\d+)',body)}
    object_symbols=set(re.findall(r'\bcreate_object\s+(\S+)',body))
    assert object_symbols<=constants.keys(),object_symbols-constants.keys()
    ids={constants[s] for s in object_symbols}
    assert all((0,u) in units for u in ids),ids-{u for c,u in units if c==0}
    # Translate only terrain arguments, so shared integer values cannot alter units.
    terrain_symbols=set(re.findall(r'\b(?:create_terrain|base_terrain|terrain_type|terrain_to_place_on|terrain_cost|terrain_size)\s+(\S+)',body))
    terrain_symbols.update(s for pair in re.findall(r'\breplace_terrain\s+(\S+)\s+(\S+)',body) for s in pair)
    missing=terrain_symbols-terrain.keys()
    if missing:raise ValueError((name,'unmapped terrain symbols',sorted(missing)))
    for symbol in sorted(terrain_symbols):
        body=re.sub(r'(#const\s+'+re.escape(symbol)+r'\s+)-?\d+',lambda m:m[1]+str(terrain[symbol]),body)
    # Every other constant is an SWGB object ID. DE reads 900-999 as class groups, so those units
    # use their moved DE IDs (reserved_unit_ids). `ids` above stays in SWGB IDs for the report.
    body=re.sub(r'(#const\s+(\S+)\s+)(-?\d+)',
                lambda m:m[0] if m[2] in terrain_symbols else m[1]+str(de_unit_id(int(m[3]))),body)
    assert body.count('{')==body.count('}')
    # Builder supplies a Rebel-specific 550 alias; no SWGB executable selector.
    matches=len(re.findall(r'\bmatch_player_civ\b',body))
    adapted=0
    def scout(m):
        global adapted
        block=m[0]
        if 'match_player_civ' in block:
            adapted+=1
            return re.sub(r'\bmatch_player_civ\b','',block)
        return block
    body=re.sub(r'create_object\s+UNIT-BIKE-E\s*\{[^{}]*\}',scout,body)
    assert matches==adapted,(name,'unexpected source civilization selector')
    # Savannah previously carried hand-made start/Nova/holocron/straggler workarounds. They only
    # compensated for the DE map-type label collision fixed below, so the source script is used as-is.
    start_repairs=[]
    body=repair_relics(body)
    # Source constants share names with DE's built-in RMS definitions. Namespace
    # every declared constant so the map uses these explicit translated values.
    declared=set(re.findall(r'#const\s+(\S+)\s+-?\d+',body))
    renames={symbol:'SWGB_'+symbol for symbol in declared}
    token_pattern=re.compile(r'(?<![A-Za-z0-9_-])('+'|'.join(re.escape(x) for x in sorted(declared,key=len,reverse=True))+r')(?![A-Za-z0-9_-])')
    body=token_pattern.sub(lambda m:renames[m[0]],body)
    rewritten={k:int(v) for k,v in re.findall(r'#const\s+(\S+)\s+(-?\d+)',body)}
    assert len(rewritten)==len(declared)
    for symbol in terrain_symbols:
        assert rewritten[renames[symbol]]==terrain[symbol]
    assert all(renames[s] in rewritten for s in object_symbols)
    label_pattern=r'(#define|\bif|\belseif)(\s+)('+'|'.join(DE_MAP_TYPE_COLLISIONS)+r')\b'
    body,label_count=re.subn(label_pattern,lambda m:m[1]+m[2]+'SWGB_'+m[3],body)
    used_labels=set(re.findall(r'(?:#define|\bif|\belseif)\s+([A-Z][A-Z0-9_]*)\b',body))
    assert not (used_labels & set(DE_MAP_TYPE_COLLISIONS)),(name,used_labels & set(DE_MAP_TYPE_COLLISIONS))
    assert not re.search(r'(?<![A-Za-z0-9_])(ARENA|FORTRESS|MIGRATION)(?![A-Za-z0-9_])',body),(name,'bare DE map-type label left')
    filename=f'SWGB Factions {name}.rms'
    data=('#includeXS swgb_factions.xs\n/* Full-source faction port; original object distribution. SWGB labels ARENA/FORTRESS/MIGRATION are namespaced (DE predefines them). */\n'+MODE_ALIASES+body).encode('ascii')
    (out/filename).write_bytes(data)
    objects.update(ids)
    records.append(dict(id=entry,name=name,file=filename,sha256=hashlib.sha256(data).hexdigest(),objects=sorted(ids),terrain_symbols=sorted(terrain_symbols),adapted_scout_selectors=adapted,unresolved_civ_selectors=matches-adapted,start_repairs=start_repairs,namespaced_labels=label_count))
report=dict(maps=records,object_roots=sorted(objects),limitations=['Draft only: scout alias and map generation require engine validation','All conditional source branches retained, so asset roots include alternate map environments','Native terrain textures substitute for source terrain; engine generation not verified'])
Path('outputs/faction-map-report.json').write_text(json.dumps(report,indent=2))
print(len(records),'maps;',len(objects),'object roots;',sum(r['unresolved_civ_selectors'] for r in records),'civ selectors require adaptation')
