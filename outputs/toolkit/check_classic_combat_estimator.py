"""Compare composed XS combat estimates and target choices with source x86."""
from pathlib import Path
import hashlib
import json
import math
import random
import re
import struct
import subprocess
from check_classic_air_planner import CMAKE, PREFIX
from check_classic_target_ranker import FLOAT_HOST
from check_classic_combat import fixtures
from classic_combat_model import Combatant
from classic_combat_oracle import CombatOracle
from classic_target_model import Target
from classic_target_oracle import TargetOracle
from classic_engine_oracle import SOURCE_SHA

ROOT=Path('work/classic-engine')
TOOLKIT=Path('outputs/toolkit')
MAIN=r'''
#include <cstring>
#include <cstdint>
void output(float value) { if(std::isnan(value)) std::cout<<" nan";else {uint32_t b;std::memcpy(&b,&value,4);std::cout<<' '<<b;} }
struct Enemy { int uid,exists,ai;float hp,reload; };
int main() {
    int first,last,n,ne,target,cls,id,zone;
    float hp,distance;
    while(std::cin>>first>>last>>n>>ne>>target>>hp>>cls>>id>>distance>>zone) {
        if(first) classicScoreReset();
        classicCombatReset();
        for(int i=0;i<n;i++) {int uid,exists;float hp,reload;std::cin>>uid>>hp>>reload>>exists;
            if(classicCombatAddMember(uid,hp,reload,exists!=0)!=i) throw std::runtime_error("Member rejected"); }
        std::vector<Enemy> enemies(ne);
        for(auto &e:enemies) std::cin>>e.uid>>e.hp>>e.reload>>e.exists>>e.ai;
        classicCombatTargetBegin(hp,ne);
        for(int i=0;i<n;i++) {float damage;int convert;std::cin>>damage>>convert;classicCombatAddOutgoing(i,damage,convert!=0);}
        for(int i=0;i<n;i++) for(auto e:enemies) {float damage;int convert;std::cin>>damage>>convert;
            classicCombatAddIncoming(i,damage,e.reload,convert!=0,e.exists!=0,e.ai!=0);}
        classicCombatScoreTarget(target,cls,id,distance,zone!=0);
        std::cout<<'C';output(classicCombatTTK);output(classicCombatTTBK);std::cout<<'\n';
        if(last) {
            for(int repeat=0;repeat<2;repeat++) {
                classicScoreEvaluate();std::cout<<"R "<<classicTargetCount;
                for(int i=0;i<classicTargetCount;i++) {
                    if(xsArrayGetBool(classicTargetUnordered,i)) std::cout<<" nan";
                    else output(xsArrayGetFloat(classicTargetScores,i));
                }
                std::cout<<' '<<classicTargetOrderedCount;
                for(int i=0;i<classicTargetOrderedCount;i++) std::cout<<' '<<xsArrayGetInt(classicTargetOrder,i);
                std::cout<<'\n';
            }
        }
        if(arrays.size()!=17) throw std::runtime_error("Combat array leak");
    }
}
'''


def groups():
    for index,args in enumerate(fixtures()):
        yield [(args,32,4,20.0,index%2==0)]
    for outgoing in (0.0, 1.0, -1.0):
        for incoming in (0.0, 1.0, -1.0):
            for convert in (False,True):
                own=[Combatant(1,reload=0.0),Combatant(3,reload=1.7)]
                enemy=[Combatant(2,reload=0.0),Combatant(4,reload=2.0)]
                target=Combatant(500)
                damage={(1,500):outgoing,(3,500):5,(2,1):incoming,(4,1):7,(2,3):incoming,(4,3):3}
                conversion={key:convert for key in damage}
                yield [((own,enemy,target,damage,conversion),32,4,20.0,True)]
    rng=random.Random(592430592980)
    for case in range(60):
        own=[Combatant(i+1,rng.uniform(1,1000),rng.choice((0.5,1,1.7,2,3)),rng.randrange(9)!=0)
             for i in range(rng.choice((1,2,5,10,40)))]
        enemies=[Combatant(i+101,rng.uniform(1,1000),rng.choice((0.5,1,1.7,2,3)),rng.randrange(9)!=0,rng.randrange(9)!=0)
                 for i in range(rng.choice((0,1,2,5,8)))]
        targets=[Combatant(500+i,rng.uniform(1,1000)) for i in range(8)]
        damage,conversion={},{}
        for attackers,victims in ((own,targets),(enemies,own)):
            for a in attackers:
                for b in victims:
                    damage[a.uid,b.uid]=rng.choice((0,0,1,4.5,13,30,100))
                    conversion[a.uid,b.uid]=bool(rng.randrange(2))
        group=[]
        for t in targets:
            cls,uid=rng.choice(((32,4),(18,70),(18,104),(18,276),(6,117),(8,487),(51,4),(46,4)))
            group.append(((own,enemies,t,damage,conversion),cls,uid,rng.uniform(0,1000),bool(rng.randrange(2))))
        yield group


def bits(value):
    return 'nan' if math.isnan(value) else str(struct.unpack('<I',struct.pack('<f',value))[0])


def main():
    names=('classic_target_ranker.xs','classic_target_scorer.xs','classic_combat_estimator.xs')
    text='\n'.join((TOOLKIT/n).read_text() for n in names)
    host=ROOT/'combat-estimator-host';host.mkdir(exist_ok=True)
    (host/'combined.xs').write_text(text)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(host/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    text,loops=re.subn(r'for \((\w+) = ([^;]+); < ([^)]+)\)',
                      lambda m:f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)',text)
    assert loops==11
    prefix=PREFIX.replace('std::vector<vector>>;','std::vector<vector>, std::vector<float>>;')
    (host/'estimator.cpp').write_text(prefix+FLOAT_HOST+text+MAIN)
    (host/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(classic_combat LANGUAGES CXX)\nadd_executable(estimator estimator.cpp)\ntarget_compile_features(estimator PRIVATE cxx_std_17)\ntarget_compile_options(estimator PRIVATE /fp:strict)\n')
    for args in ([CMAKE,'-S',str(host),'-B',str(host/'build')],[CMAKE,'--build',str(host/'build'),'--config','Release']):
        r=subprocess.run(args,capture_output=True,text=True)
        assert r.returncode==0,r.stdout+r.stderr
    combat=CombatOracle();scorer=TargetOracle()
    inputs,expected=[],[]
    group_count=0
    for group in groups():
        scored=[]
        for index,(args,cls,uid,distance,zone) in enumerate(group):
            own,enemies,target,damage,conversion=args
            first,last=index==0,index==len(group)-1
            values=[int(first),int(last),len(own),len(enemies),target.uid,target.hp,cls,uid,distance,int(zone)]
            for u in own:values += [u.uid,u.hp,u.reload,int(u.exists)]
            for e in enemies:values += [e.uid,e.hp,e.reload,int(e.exists),int(e.has_ai)]
            for u in own:values += [damage.get((u.uid,target.uid),0),int(conversion.get((u.uid,target.uid),False))]
            for u in own:
                for e in enemies:values += [damage.get((e.uid,u.uid),0),int(conversion.get((e.uid,u.uid),False))]
            inputs.append(' '.join(map(str,values)))
            ttk,ttbk,_=combat.estimate(*args,target_zone=1 if zone else 2,distance=distance)
            expected.append('C '+bits(ttk)+' '+bits(ttbk))
            scored.append(Target(target.uid,cls,uid,ttk,ttbk,distance,same_zone=zone))
        scores,order=scorer.evaluate(scored)
        line=' '.join(['R',str(len(scored)),*[bits(s) for s in scores],str(len(order)),*[str(scored[i].uid) for i in order]])
        expected.extend([line,line]);group_count+=1
    r=subprocess.run([str(host/'build/Release/estimator.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    actual=r.stdout.splitlines()
    assert len(actual)==len(expected),(len(actual),len(expected))
    failures=[dict(line=i,actual=a,expected=b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
    (host/'failures.json').write_text(json.dumps(failures,indent=2)+'\n')
    assert not failures,(len(failures),failures[:3])
    report=dict(passed=True,combat_cases=len(inputs),target_groups=group_count,rank_evaluations=group_count*2,
                source_sha256=SOURCE_SHA,xs_hashes={n:hashlib.sha256((TOOLKIT/n).read_bytes()).hexdigest() for n in names},
                installed=False,full_behavior_parity=False,
                limitations=['C++ strict-float host, not native DE XS execution.',
                             'Damage, conversion capability, world state, distances and zones are supplied fixtures.',
                             'Finite ordinary HP/damage/reload observations; zero reload is explicitly represented.',
                             'Overflowing finite sums, signed zero reload and nonfinite output times are not covered.',
                             'Source damage queries, live memory and attack-order delivery remain separate integration.'])
    report['tool_hashes']={n:hashlib.sha256((TOOLKIT/n).read_bytes()).hexdigest() for n in
                          ('classic_engine_oracle.py','classic_combat_oracle.py','classic_target_oracle.py',
                           'classic_combat_model.py','classic_target_model.py','check_classic_combat.py',
                           'check_classic_combat_estimator.py','check_classic_air_planner.py','check_classic_target_ranker.py')}
    (ROOT/'combat-estimator-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(inputs),'source combat cases /',group_count*2,'composed rank evaluations; not installed')


if __name__=='__main__': main()
