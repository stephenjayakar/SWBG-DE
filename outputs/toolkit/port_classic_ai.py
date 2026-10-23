"""Translate the installed Computer Classic graph; do not replace the stable AI.

Generated source/rule hashes and an explicit compatibility ledger accompany the port.
"""
import argparse
import copy
import hashlib
import json
import re
import csv
from pathlib import Path
from classic_ai_source import SOURCE, graph, specialize, render, atoms
from classic_ai_bindings import unit_bindings, faction_units, tech_bindings
from classic_ai_chat import CHAT_BASE, source_strings
from classic_nursery_bridge import bridge_rules
from reserved_unit_ids import de_unit_id, de_unit_ids
from classic_ai_age_clock import clock_rules, condition as age_time_condition
from classic_ai_opening import rewrite as opening_rewrite
from classic_ai_map_identity import rewrite_per as gaia_vents_rewrite
from classic_ai_extreme import rewrite as extreme_rewrite
from classic_ai_power_placement import rewrite_per as power_placement_rewrite

WORK = Path('work/original-ai')
ROOT = WORK/'patch'
AI = ROOT/'resources/_common/ai'
PREFIX = 'SWGB Classic'


def renamed(s):
    for a,b in [('carbon','wood'),('nova','gold'),('metal','stone'),('holocron','relic'),('jedi','monk')]:
        s=s.replace(a,b)
    return s


def main():
    AI.mkdir(parents=True,exist_ok=True)
    source,randoms,hashes=graph()
    size_symbols={'TINY-MAP','SMALL-MAP','MEDIUM-MAP','NORMAL-MAP','LARGE-MAP','GIANT-MAP'}
    map_symbols=sorted({n.split()[1] for n in source if isinstance(n,str) and n.startswith('#load-if')
                       and n.split()[1].endswith('-MAP')}-size_symbols)
    map_ids={s:i+1 for i,s in enumerate(map_symbols) if s!='CUSTOM-MAP'}
    map_ids['CUSTOM-MAP']=0
    raw,groups,rms,units=unit_bindings()
    native=Path('E:/SteamLibrary/steamapps/common/AoE2DE/resources/_common/dat/unitlines.json')
    lines=json.loads(native.read_text())
    occupied={r['LineID'] for r in lines['UnitLines']}
    available=iter(i for i in range(-399,-199) if i not in occupied)
    group_ids={}
    equivalent={}
    for name,members in sorted(groups.items()):
        signature=(name.startswith('bldg-'),tuple(members))
        if signature in equivalent:
            group_ids[name]=equivalent[signature]
            continue
        group_ids[name]=next(available)
        equivalent[signature]=group_ids[name]
        lines['UnitLines'].append(dict(Name='SWGB '+name,Identifier='swgb-'+name,
            Building=name.startswith('bldg-'),LineID=group_ids[name],IDChain=de_unit_ids(members)))
    dat=ROOT/'resources/_common/dat';dat.mkdir(parents=True,exist_ok=True)
    (dat/'unitlines.json').write_text(json.dumps(lines,indent=2)+'\n')
    legacy_sns=dict((name,int(number)) for number,name in re.findall(r'(\d+)\s+(sn-[\w-]+)',
                   (SOURCE.parent/'Data/sn.txt').read_text()))
    known={x['label'] for x in json.loads(Path('work/ai-parser/extensions/aoe2-ai-parser-extension/data/completions.json').read_text())['items']}
    rule_map=[];used_bindings={};legacy=set();unresolved=set();directives=set();chat_ids=set()
    output=['; Original Computer Classic port, experimental; select this AI explicitly.',
            '; Source provenance and compatibility exceptions: ORIGINAL-AI.md.',
            '#load-if-defined DIFFICULTY-EXTREME',
            '(defconst DIFFICULTY-HARDEST 1)', '#end-if',
            '(defrule (true) => (set-goal 100 2) (set-strategic-number sn-enable-new-building-system 1)\n'
            ' (set-strategic-number sn-initial-exploration-required 0) (disable-self))',
            '(defrule (true) => (up-get-fact player-number 0 104) (xs-script-call "swgbClassicObserve"))']
    # DE does not restart current-age-time for SWGB Tech Levels (techs 1-3); see classic_ai_age_clock.
    output.append(clock_rules())
    # Source Artifact::update independently automates owned idle livestock.
    # Preserve individual nearest-building decisions, not bulk up-garrison.
    garrisonable={int(r['unit']) for r in csv.DictReader(Path('work/economy-repair/dependencies/detailed-tasks.tsv').open(),delimiter='\t')
                  if r['civ'] in ('1','2') and r['action']=='3' and r['class']=='3'}
    animals=sorted({int(r['id']) for r in csv.DictReader((WORK/'current-dat/units.tsv').open(),delimiter='\t')
                    if r['civ'] in ('1','2') and r['class']=='58' and r['type']=='70'
                    and int(r['id']) in garrisonable})
    output.append(bridge_rules())
    for faction,civ,target,prefix in [('EMPIRE',1,1,'ce-'),('REBEL',3,2,'cr-')]:
        root=specialize(source,faction)
        alternatives={name:specialize(nodes,faction) for name,nodes in randoms.items()}
        allnodes=root+sum(alternatives.values(),[])
        names={n[1]:prefix+re.sub(r'[^\w-]','-',n[1])
               for n in allnodes if isinstance(n,list) and n[0]=='defconst'}
        # Unit/building symbols are bound to DE IDs (SWGB 900-999 moved, see reserved_unit_ids);
        # group symbols are negative LineIDs and rt-/ut- symbols are technology IDs.
        bindings={**{k:de_unit_id(v) for k,v in raw.items()},**group_ids,
                  **{k:de_unit_id(v) for k,v in faction_units(civ,units).items()},**tech_bindings(civ)}
        # Raw, faction-specific aliases retain source enemy-count semantics as well.
        bound={}
        def atom(s):
            low=s.lower()
            # PER user constants are case-sensitive. Source FOOD=2 is a goal
            # category; built-in food=0 is a resource. Never fold these together.
            if s in names:return names[s]
            if low in bindings:
                name=prefix+low
                bound[name]=bindings[low]
                return name
            if low.startswith('tech-level-'):
                return str(int(low.rsplit('-',1)[1])-1)
            if low.startswith('sn-'):
                mapped=renamed(low)
                if mapped in known:return mapped
                if low in ('sn-max-unpowered-buildings','sn-percent-attack-air'):
                    return low
                if low in legacy_sns:
                    name=prefix+low;bound[name]=legacy_sns[low];legacy.add(low)
                    return name
            if low in ('carbon','nova','metal'):return renamed(low)
            if low.startswith(('rt-','ut-','unit-','boat-','bldg-','gaia-','sn-','siege-','uu-','sub-')) and low not in known:
                unresolved.add(low)
            return s
        def translate(n):
            if isinstance(n,str):return atom(n)
            head=n[0].lower()
            if head=='civ-selected':
                return ['true'] if n[1].upper()==faction else ['false']
            if head=='difficulty' and n[1]=='==' and n[2]=='hardest':
                return ['difficulty','<=','hardest']
            if head in ('unit-type-count','unit-type-count-total') and n[1].lower()=='unit-worker':
                return [head,atom('unit-worker-count-line')]+[atom(x) for x in n[2:]]
            if head.startswith('chat-') and '-using-' in head:
                node=copy.deepcopy(n)
                positions=[i for i,s in enumerate(node) if isinstance(s,str) and s.isdigit() and int(s)>=20000]
                ids=[int(node[i]) for i in positions]
                if head.endswith('-range'):
                    assert len(ids)==1 and node[-1].isdigit(), node
                    chat_ids.update(range(ids[0],ids[0]+int(node[-1])))
                else:chat_ids.update(ids)
                for i in positions:node[i]=str(CHAT_BASE+int(node[i]))
                return [node[0]]+[translate(x) for x in node[1:]]
            if head=='or-list':
                children=[translate(x) for x in n[2:]]
                assert int(n[1])==len(children)
                result=children[-1]
                for child in reversed(children[:-1]):result=['or',child,result]
                return result
            if head=='current-age-time':
                return age_time_condition(n[1],atom(n[2]))
            if head=='nursery-headroom':
                return ['up-compare-goal','103','c:'+n[1],atom(n[2])]
            if head in ('soldier-count','warboat-count'):
                group='source-ground-soldier-line' if head=='soldier-count' else 'source-warboat-line'
                return ['unit-type-count',atom(group),atom(n[1]),atom(n[2])]
            if head=='too-many-unpowered-buildings':
                return ['up-compare-goal','101','g:>','100']
            if head=='set-strategic-number' and n[1]=='sn-max-unpowered-buildings':
                return ['set-goal','100',atom(n[2])]
            if head=='set-strategic-number' and n[1]=='sn-percent-attack-air':
                # DE has no separate native aircraft pool. Keep the requested setting
                # visible in goal 102; combat dispatch remains the engine's army pool.
                return ['set-goal','102',atom(n[2])]
            if head=='map-type':
                key=n[1].lower()
                symbol=key.upper()+'-MAP'
                if symbol in map_ids:return ['up-resource-amount','1997','==',str(map_ids[symbol])]
            result=[renamed(head)]+[translate(x) for x in n[1:]]
            if head=='defrule':
                result.insert(1,['civ-selected',str(target)])
                # SWGB attack-now uses separate soldier and aircraft percentages.
                # DE aircraft join the soldier pool, so equal values are exact.
                # The source's only divergent case (soldiers 0, air 100: the
                # Hard/Hardest naval attacks) requests the explicit air dispatch.
                sets={x[1]:x[2] for x in n if isinstance(x,list) and x[0]=='set-strategic-number'}
                air=sets.get('sn-percent-attack-air');soldiers=sets.get('sn-percent-attack-soldiers')
                if air is not None and soldiers is not None and air!=soldiers:
                    assert (air,soldiers)==('100','0'),(air,soldiers)
                    result.append(['set-goal',AIR_REQUEST,'1'])
            return result
        def convert(nodes,label):
            out=[];index=0;conditions=[]
            for node in nodes:
                if isinstance(node,str) and node.startswith('#'):
                    bits=node.split()
                    if len(bits)==2:
                        if bits[1] in map_ids:
                            conditions.append([bits[1],bits[0]=='#load-if-defined'])
                            continue
                        conditions.append(None)
                        bits[1]={'MONUMENT-RACE':'WONDER-RACE','DEFEND-MONUMENT':'DEFEND-WONDER',
                                 'EMPEROR':'REGICIDE','DEATHMATCH':'DEATH-MATCH'}.get(bits[1],bits[1])
                        directives.add(bits[1])
                    elif node=='#else' and conditions[-1] is not None:
                        conditions[-1][1]=not conditions[-1][1]
                        continue
                    elif node=='#end-if' and conditions.pop() is not None:
                        continue
                    out.append(' '.join(bits));continue
                if isinstance(node,list) and node[0]=='load-random':
                    node=copy.deepcopy(node)
                    if prefix=='ce-':
                        node[2::2]=['"'+PREFIX+'/'+prefix+x.strip('"')+'"' for x in node[2::2]]
                        out.append(render(node))
                    else:
                        # Reuse the first variant's selection. Drawing again for
                        # the runtime-inactive faction changes the RNG stream.
                        for name in node[2::2]:
                            key=name.strip('"')
                            out.extend(['#load-if-defined SWGB_CLASSIC_'+key.upper().replace('-','_'),
                                        '(load "'+PREFIX+'/'+prefix+key+'")','#end-if'])
                    continue
                translated=translate(node)
                if isinstance(node,list) and node[0]=='defrule':
                    for condition in conditions:
                        if condition is not None:
                            symbol,positive=condition
                            fact=['up-resource-amount','1997','==',str(map_ids[symbol])]
                            translated.insert(2,fact if positive else ['not',fact])
                    index+=1
                    rule_map.append(dict(faction=faction,module=label,rule=index,
                        source_sha256=hashlib.sha256(render(node).encode()).hexdigest(),
                        target_sha256=hashlib.sha256(render(translated).encode()).hexdigest()))
                    out.append(f'; {faction}/{label}/{index}')
                out.append(render(translated))
            assert not conditions
            return '\n'.join(out)+'\n'
        body=convert(root,'main')
        for name,nodes in alternatives.items():
            path=AI/PREFIX/(prefix+name+'.per');path.parent.mkdir(exist_ok=True)
            flag='(defconst SWGB_CLASSIC_'+name.upper().replace('-','_')+' 1)\n' if prefix=='ce-' else ''
            path.write_text(flag+convert(nodes,name))
        used_bindings[faction]=bound
        output.extend(f'(defconst {k} {v})' for k,v in sorted(bound.items()))
        output.append(body)
    assert not unresolved, sorted(unresolved)
    output.append(air_dispatch_rule(group_ids))
    # No "SWGB Classic AI.ai": DE's own lobby entries load this script (ai_entries.py), and a
    # listing file would show the same AI a second time.
    (AI/(PREFIX+' AI.ai')).unlink(missing_ok=True)
    # DE resolves AI XS includes from resources/_common/xs (per mod); '../ai/...' fails with ERR7000.
    output.append('(include "swgb_classic_ai.xs")')
    # Map-identity race, SWGB building queue and first Carbon Center; see classic_ai_opening.
    text,_=opening_rewrite('\n'.join(output),True)
    # DE's raw counts of the source's gas-vent type IDs are unreliable; see classic_ai_map_identity.
    text,_=gaia_vents_rewrite(text)
    # DE's #load-if-defined ignores defconsts: give each Hardest conditional an Extreme twin.
    text,_=extreme_rewrite(text)
    # DE placement ignores SWGB power: place power-dependent buildings at a Power Core; see classic_ai_power_placement.
    text,_=power_placement_rewrite(text)
    (AI/(PREFIX+' AI.per')).write_text(text)
    chat=source_strings(chat_ids)
    relative='resources/en/strings/key-value/key-value-modded-strings-utf8.txt'
    strings=(Path('outputs/SWGB-DE-Factions-Draft')/relative).read_text()
    existing={int(m) for m in re.findall(r'^(\d+) ',strings,re.M)}
    additions=[]
    for sid,value in chat.items():
        expected=str(CHAT_BASE+sid)+' '+json.dumps(value,ensure_ascii=False)
        if CHAT_BASE+sid in existing:
            assert expected in strings.splitlines(),('AI chat string collision',sid)
        else:additions.append(expected)
    if additions:strings+='\n'+'\n'.join(additions)+'\n'
    path=ROOT/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(strings,encoding='utf-8')
    map_patches=[]
    for row in json.loads(Path('outputs/faction-map-report.json').read_text())['maps']:
        symbol=MAP_NAMES.get(row['name'],row['name'].upper().replace(' ','-'))+'-MAP'
        assert symbol in map_ids,symbol
        relative='resources/_common/random-map-scripts/'+row['file']
        original=Path('outputs/SWGB-DE-Factions-Draft')/relative
        text=original.read_text()
        assert text.count('<PLAYER_SETUP>')==1
        marker='/* Classic AI map identity; reserved resource 1997. */\neffect_amount 1 1997 0 '+str(map_ids[symbol])
        if '/* Classic AI map identity' in text:
            text,count=re.subn(r'/\* Classic AI map identity[^\n]*\*/\neffect_amount[^\n]*',lambda _:marker,text)
            assert count==1
        else:text=text.replace('<PLAYER_SETUP>','<PLAYER_SETUP>\n'+marker+'\n')
        path=ROOT/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        map_patches.append(dict(file=relative,symbol=symbol,identity=map_ids[symbol]))
    report=dict(source_files=hashes,source='Computer Classic',rules=rule_map,bindings=used_bindings,
        groups=groups,group_ids=group_ids,legacy_sns=sorted(legacy),directives=sorted(directives),
        map_ids=map_ids,map_patches=map_patches,chat_strings=len(chat),herdable_ids=animals,
        random_personality_draws_per_player=1,engine_verified=False,full_behavior_parity=False)
    (WORK/'translation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Translated',len(rule_map),'rules;',len(hashes),'source files;',len(groups),'SWGB unit groups')


AIR_REQUEST='112'
AIR_TARGET_PLAYER='113'
AIR_LINES=('unit-fighter-line','unit-bomber-line','unit-attacker-line','unit-airspeeder-line')
AIR_CRUISERS=(625,634)  # Empire/Rebel Air Cruiser; air transports stay excluded.


def air_dispatch_rule(group_ids):
    """Source sn-percent-attack-air 100 with soldiers 0: send every combat aircraft."""
    finds=[f' (up-find-local c: {group_ids[name]} c: 240)' for name in AIR_LINES]
    finds+=[f' (up-find-local c: {de_unit_id(unit)} c: 240)' for unit in AIR_CRUISERS]
    return '\n'.join(['; Source air-only attack percentage (Hard/Hardest naval attacks).',
        f'(defrule (goal {AIR_REQUEST} 1) =>',' (up-full-reset-search)',
        f' (up-find-player enemy find-closest {AIR_TARGET_PLAYER})',
        f' (up-modify-sn sn-focus-player-number g:= {AIR_TARGET_PLAYER})',*finds,
        ' (up-find-remote c: building-class c: 20)',' (up-target-objects 0 action-default -1 -1)',
        ' (up-full-reset-search)',f' (set-goal {AIR_REQUEST} 0))'])


MAP_NAMES={'WaterMass':'WATER-MASS','LandMass':'LAND-MASS','Islands':'LAND-SATELLITES',
           'Team Islands':'TEAM-LAND-SATELLITES'}


if __name__=='__main__':main()
