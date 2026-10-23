"""Differential-check the XS damage -> combat estimates -> scoring/order chain."""
from pathlib import Path
from dataclasses import replace
import hashlib
import json
import random
import re
import subprocess
import sys
from check_classic_air_planner import CMAKE,PREFIX
from check_classic_target_ranker import FLOAT_HOST
from check_classic_attack_dispatch_xs import EXTRA
from check_classic_combat_estimator import MAIN,bits
from classic_damage_oracle import DamageOracle
from classic_combat_oracle import CombatOracle
from classic_target_oracle import TargetOracle
from classic_combat_model import Combatant
from classic_target_model import Target
from classic_engine_oracle import SOURCE_SHA

ROOT=Path('work/classic-engine');TOOLKIT=Path('outputs/toolkit')
READ=r'''
struct Capabilities { bool damage,convert,hasAI=true; };
Capabilities readDamage() {
    int na,nw,base,high,mode,action,building,relics,specialRelics,targetBuilding,targetRelics,targetSpecial,eligible,convert;
    float terrain,az,tz;
    std::cin>>na>>nw>>base>>terrain>>high>>az>>tz>>mode>>action>>building>>relics>>specialRelics>>targetBuilding>>targetRelics>>targetSpecial>>eligible>>convert;
    float modifier=classicDamageModifier(high!=0,az,tz,mode,action!=0,building!=0,relics,specialRelics,targetBuilding!=0,targetRelics,targetSpecial);
    classicDamageReset(base,modifier,terrain);
    for(int i=0;i<na;i++) {int cls,value;std::cin>>cls>>value;classicDamageAddArmor(cls,value);}
    for(int i=0;i<nw;i++) {int cls,value;std::cin>>cls>>value;classicDamageAddWeapon(cls,value);}
    return Capabilities{eligible!=0,convert!=0};
}
'''


def main(eligibility=False,source_types=False):
    eligibility=eligibility or source_types
    names=('classic_target_ranker.xs','classic_target_scorer.xs','classic_combat_estimator.xs',
           'classic_damage_calculator.xs','classic_combat_pipeline.xs')
    gates=None
    reader=READ
    if eligibility:
        from classic_combat_eligibility_fixture import EligibilityFixtures,XS_NAMES,host_reader
        gates=EligibilityFixtures(source_types)
        names=XS_NAMES+names
        if source_types:names=names+('classic_unit_ai_factory.xs','classic_combat_gate.xs')
        reader=reader.replace('Capabilities readDamage()',host_reader(source_types)+'Capabilities readDamage()')
        reader=reader.replace('return Capabilities{eligible!=0,convert!=0};',
            'auto result=readSourceEligibility();if(result.damage!=(eligible!=0) || result.convert!=(convert!=0)) throw std::runtime_error("Source eligibility mismatch");return result;')
    text=(gates.prelude() if gates else '')+'\n'.join((TOOLKIT/n).read_text() for n in names)
    host=ROOT/('combat-factory-pipeline-host' if source_types else 'combat-eligibility-pipeline-host' if gates else 'combat-pipeline-host');host.mkdir(exist_ok=True)
    (host/'combined.xs').write_text(text)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(host/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    text,loops=re.subn(r'for \((\w+) = ([^;]+); < ([^)]+)\)',
                      lambda m:f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)',text)
    assert loops==12
    old_out='float damage;int convert;std::cin>>damage>>convert;classicCombatAddOutgoing(i,damage,convert!=0);'
    old_in='float damage;int convert;std::cin>>damage>>convert;\n            classicCombatAddIncoming(i,damage,e.reload,convert!=0,e.exists!=0,e.ai!=0);'
    assert MAIN.count(old_out)==1 and MAIN.count(old_in)==1
    main_code=MAIN.replace(old_out,'auto cap=readDamage();classicCombatWeaponOutgoing(i,cap.damage,cap.convert,cap.hasAI);')
    main_code=main_code.replace(old_in,'auto cap=readDamage();classicCombatWeaponIncoming(i,e.reload,cap.damage,cap.convert,e.exists!=0,e.ai!=0);')
    main_code=main_code.replace('arrays.size()!=17','arrays.size()!=19')
    prefix=PREFIX.replace('std::vector<vector>>;','std::vector<vector>, std::vector<float>>;')
    (host/'pipeline.cpp').write_text('#include <cstring>\n#include <cstdint>\n'+prefix+FLOAT_HOST+EXTRA+text+reader+main_code)
    (host/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(classic_pipeline LANGUAGES CXX)\nadd_executable(pipeline pipeline.cpp)\ntarget_compile_features(pipeline PRIVATE cxx_std_17)\ntarget_compile_options(pipeline PRIVATE /fp:strict)\n')
    for args in ([CMAKE,'-S',str(host),'-B',str(host/'build')],[CMAKE,'--build',str(host/'build'),'--config','Release']):
        r=subprocess.run(args,capture_output=True,text=True)
        assert r.returncode==0,r.stdout+r.stderr
    rng=random.Random(4449592430)
    armor=DamageOracle();combat=CombatOracle();target_oracle=TargetOracle()
    inputs,expected=[],[]
    pairs=0
    for group in range(40):
        own=[Combatant(i+1,rng.uniform(1,1000),rng.choice((0,0.5,1.7,2)),rng.randrange(9)!=0)
             for i in range(rng.choice((1,2,5,10,40)))]
        enemies=[Combatant(i+101,rng.uniform(1,1000),rng.choice((0,0.5,1.7,2)),rng.randrange(9)!=0,rng.randrange(9)!=0)
                 for i in range(rng.choice((0,1,3,5)))]
        targets=[Combatant(500+i,rng.uniform(1,1000)) for i in range(4)]
        definitions={}
        for u in own+enemies+targets:
            definitions[u.uid]=dict(weapons=[(rng.randrange(6),rng.randrange(30)) for _ in range(rng.randrange(5))],
                                    armor=[(rng.randrange(6),rng.randrange(-5,20)) for _ in range(rng.randrange(6))],
                                    base=rng.choice((0,1000)),terrain=rng.choice((0.5,1,1.25,1.7,2)),
                                    z=rng.randrange(3),building=bool(rng.randrange(2)),
                                    relics=rng.randrange(2),special=rng.randrange(2),mode=rng.choice((0,3)),action=bool(rng.randrange(2)))
            if gates: definitions[u.uid]['eligibility']=gates.definition(army_member=u.uid<100)
        if source_types:
            own=[replace(u,has_ai=definitions[u.uid]['eligibility']['ai_type']>=0) for u in own]
            enemies=[replace(u,has_ai=definitions[u.uid]['eligibility']['ai_type']>=0) for u in enemies]
        damage,convert,queries={},{},{}
        for attackers,victims in ((own,targets),(enemies,own)):
            for a in attackers:
                for v in victims:
                    x,y=definitions[a.uid],definitions[v.uid]
                    modifier_args=(x['z']>y['z'],x['z'],y['z'],x['mode'],x['action'],x['building'],x['relics'],x['special'],y['building'],y['relics'],y['special'])
                    eligible=bool(rng.randrange(2));conversion=bool(rng.randrange(2))
                    observations=[]
                    if gates: eligible,conversion,observations=gates.pair(a,v,x,y)
                    multiplier=armor.modifier(*modifier_args)
                    raw=armor.damage(x['weapons'],y['armor'],y['base'],multiplier,y['terrain'])
                    damage[a.uid,v.uid]=armor.capability(x['weapons'],y['armor'],y['base'],multiplier,y['terrain'],
                                                       has_ai=a.has_ai,can_attack=eligible) if source_types else raw if eligible else 0.0
                    convert[a.uid,v.uid]=conversion
                    values=[len(y['armor']),len(x['weapons']),y['base'],y['terrain']]
                    values += [int(z) if isinstance(z,bool) else z for z in modifier_args]
                    values += [int(eligible),int(conversion)] + [n for pair in y['armor']+x['weapons'] for n in pair]
                    values += observations
                    queries[a.uid,v.uid]=values;pairs+=1
        scored=[]
        for index,t in enumerate(targets):
            cls,uid=rng.choice(((32,4),(18,70),(18,104),(6,117),(8,487),(46,4)))
            distance=rng.uniform(0,1000);zone=bool(rng.randrange(2))
            values=[int(index==0),int(index==3),len(own),len(enemies),t.uid,t.hp,cls,uid,distance,int(zone)]
            for u in own:values += [u.uid,u.hp,u.reload,int(u.exists)]
            for e in enemies:values += [e.uid,e.hp,e.reload,int(e.exists),int(e.has_ai)]
            for u in own:values += queries[u.uid,t.uid]
            for u in own:
                for e in enemies:values += queries[e.uid,u.uid]
            inputs.append(' '.join(map(str,values)))
            ttk,ttbk,_=combat.estimate(own,enemies,t,damage,convert,target_zone=1 if zone else 2,distance=distance)
            expected.append('C '+bits(ttk)+' '+bits(ttbk))
            scored.append(Target(t.uid,cls,uid,ttk,ttbk,distance,same_zone=zone))
        scores,order=target_oracle.evaluate(scored)
        line=' '.join(['R',str(len(scored)),*[bits(s) for s in scores],str(len(order)),*[str(scored[i].uid) for i in order]])
        expected.extend([line,line])
    r=subprocess.run([str(host/'build/Release/pipeline.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    actual=r.stdout.splitlines();assert len(actual)==len(expected),(len(actual),len(expected))
    failures=[dict(line=i,actual=a,expected=b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
    (host/'failures.json').write_text(json.dumps(failures,indent=2)+'\n')
    assert not failures,(len(failures),failures[:3])
    report=dict(passed=True,pair_definitions=pairs,combat_cases=len(inputs),rank_evaluations=80,source_sha256=SOURCE_SHA,
                xs_hashes={n:hashlib.sha256((TOOLKIT/n).read_bytes()).hexdigest() for n in names},
                installed=False,full_behavior_parity=False,
                limitations=['C++ strict-float host, not native DE XS execution.',
                             'Native damage eligibility and conversion capability remain supplied booleans.',
                             'Source integer armor/weapon and environment records are fixtures, not live DE queries.',
                             'No visibility/target-memory or attack-order execution is connected.'])
    report['tool_hashes']={n:hashlib.sha256((TOOLKIT/n).read_bytes()).hexdigest() for n in
                          ('classic_engine_oracle.py','classic_damage_oracle.py','classic_combat_oracle.py','classic_target_oracle.py',
                           'classic_combat_model.py','classic_target_model.py','check_classic_combat_estimator.py',
                           'check_classic_combat_pipeline.py','check_classic_air_planner.py','check_classic_target_ranker.py','check_classic_attack_dispatch_xs.py')}
    if gates:
        for kind in range(8):
            for allowed in (0,1):
                assert gates.outcomes.get(f'{kind}:{allowed}:0',0)>0,gates.outcomes
        assert gates.outcomes.get('8:0:0',0)>0 and all(key=='8:0:0' for key in gates.outcomes if key.startswith('8:')),gates.outcomes
        assert gates.outcomes.get('4:0:1',0)>0 and gates.outcomes.get('4:1:1',0)>0,gates.outcomes
        report['catalog_sha256']=gates.sha
        report['eligibility_counts']=gates.counts
        report['eligibility_outcomes']=gates.outcomes
        report['limitations'][1]='Actual source/XS eligibility gates, with caller-supplied world state and UnitAI kind.'
        for n in ('classic_combat_eligibility_fixture.py','classic_attack_eligibility.py','classic_attack_eligibility_oracle.py',
                  'classic_soldier_eligibility.py','classic_soldier_eligibility_oracle.py',
                  'classic_conversion_eligibility.py','classic_conversion_eligibility_oracle.py'):
            report['tool_hashes'][n]=hashlib.sha256((TOOLKIT/n).read_bytes()).hexdigest()
        if source_types:
            assert gates.outcomes.get('-1:0:0',0)>0,gates.outcomes
            report['factory_cases']=len(gates.factory_types)
            report['limitations'][1]='Original factory selects UnitAI kind from supplied source class/volley; dynamic world observations remain fixtures.'
            for n in ('classic_unit_ai_factory.py','classic_unit_ai_factory_oracle.py','classic_unit_ai_catalog.py'):
                report['tool_hashes'][n]=hashlib.sha256((TOOLKIT/n).read_bytes()).hexdigest()
    path=ROOT/('combat-factory-pipeline-validation.json' if source_types else 'combat-eligibility-pipeline-validation.json' if gates else 'combat-pipeline-validation.json')
    path.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',pairs,'source armor-pair definitions /',len(inputs),'combat cases / 80 rank evaluations;',
          'source eligibility included;' if gates else '', 'not installed')


if __name__=='__main__': main('--eligibility' in sys.argv,'--source-types' in sys.argv)
