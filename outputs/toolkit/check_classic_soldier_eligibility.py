"""Compare soldier gating against actual x86 and compiled source XS."""
from dataclasses import fields,replace
from pathlib import Path
import hashlib
import itertools
import json
import random
import re
import struct
import subprocess
from classic_attack_eligibility import catalog,generate_catalog
from classic_soldier_eligibility import Soldier,can_attack_soldier,can_attack_priest,can_attack_siege,f32
from classic_soldier_eligibility_oracle import SoldierEligibilityOracle
from classic_engine_oracle import SOURCE_SHA
from check_classic_air_planner import CMAKE,PREFIX

ROOT=Path('work/classic-engine')
TOOLKIT=Path('outputs/toolkit')


def neighbors(value):
    center=struct.unpack('<I',struct.pack('<f',value))[0]
    return [struct.unpack('<f',struct.pack('<I',bits))[0] for bits in (center-1,center,center+1)]


def fixtures(ids):
    # Early gates, including catalog overrides that make even normally excluded
    # source classes attack-capable in the base predicate.
    for ac,aid,tc,owner,enemy,action in itertools.product((4,8,9,34,36,48),
            (1,109,ids[0]),(4,5,8,21,28,43,60),(0,1),(0,2),(-2,-1,123,124,125,126)):
        yield Soldier(attacker_class=ac,attacker_id=aid,target_class=tc,owner_id=owner,
                      target_owner=enemy,action_type=action)
    for present,kind,flag,hidden,tid in itertools.product((False,True),(70,80),(0,1,255),(False,True),(1,50,696)):
        yield Soldier(target_present=present,target_type=kind,target_flag=flag,invisible=hidden,target_id=tid)
    for stance,last,order,on,patrol,distances in itertools.product((0,1,2,3,4,255),
            (599,600,601),(0,700,701,711,733),(0,1,2),(0,1,2),
            ((1,20,20),(20,1,20),(20,20,1))):
        sd,hd,pd=distances
        yield Soldier(stance=stance,last_action=last,current_order=order,on_patrol=on,
                      has_patrol=patrol,state_distance=sd,highest_path_distance=hd,patrol_path_distance=pd)
    for stance,owner,wr in itertools.product((1,2),(0,2),(0,0.00001,0.5,1,4,7.75,4095.5,65535.5,16777216.0)):
        offset=5.0 if stance==1 else 2.0 if owner==0 else 0.5
        for distance in neighbors(f32(wr+offset)):
            yield Soldier(stance=stance,target_class=5,target_owner=owner,weapon_range=wr,state_distance=distance)
    for stance,order,on,patrol,which in itertools.product((0,1,2,3),(0,701,711),(0,1),(0,1),
            ('weapon_range','state_distance','highest_path_distance','patrol_path_distance')):
        yield replace(Soldier(stance=stance,current_order=order,on_patrol=on,has_patrol=patrol),**{which:float('nan')})
    rng=random.Random(0x5B6E70)
    for _ in range(2000):
        yield Soldier(attacker_class=rng.choice((8,9,36,48)),attacker_id=rng.choice((1,109,500,603,*ids)),
                      target_class=rng.choice((5,8,43,48,60)),target_owner=rng.choice((0,2)),
                      stance=rng.randrange(4),last_action=rng.choice((600,601)),
                      current_order=rng.choice((0,701,711,733)),on_patrol=rng.randrange(3),has_patrol=rng.randrange(3),
                      state_distance=rng.uniform(0,20),highest_path_distance=rng.uniform(0,20),
                      patrol_path_distance=rng.uniform(0,20),weapon_range=rng.uniform(0,15),
                      resource31=rng.choice((0,1)))


def main():
    ids,sha=catalog()
    names=('classic_attack_eligibility.xs','classic_soldier_eligibility.xs')
    xs=generate_catalog(ids,sha)+'\n'.join((TOOLKIT/n).read_text() for n in names)
    host=ROOT/'soldier-eligibility-host';host.mkdir(parents=True,exist_ok=True)
    (host/'combined.xs').write_text(xs)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(host/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    members=list(fields(Soldier))
    declarations='\n'.join(('uint32_t' if field.type is float else 'int')+' '+field.name+';' for field in members)
    reads='>>'.join(field.name for field in members)
    arguments=[('asfloat('+field.name+')' if field.type is float else field.name) for field in members]
    call=','.join(arguments[:12])
    priest_call=','.join(arguments[:11]+['held'])
    motion=','.join(arguments[12:]+['target_owner'])
    main='#include <cstring>\n#include <cstdint>\nfloat asfloat(uint32_t b){float f;std::memcpy(&f,&b,4);return f;}\n'
    main+='int main(){char mode;int held,ownState,computer;'+declarations+'\nwhile(std::cin>>mode>>held>>ownState>>computer>>'+reads+') {classicAttackSoldierSetMotion('+motion+');classicAttackSiegeSetState(ownState,computer);'
    main+='bool result=mode==\'G\'?classicAttackSiege('+call+'):mode==\'P\'?classicAttackPriest('+priest_call+'):classicAttackSoldier('+call+");std::cout<<result<<'\\n';}\n"
    main+='if(!arrays.empty())throw std::runtime_error("Unexpected allocation");}\n'
    (host/'soldier.cpp').write_text(PREFIX+xs+main)
    (host/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(soldier LANGUAGES CXX)\nadd_executable(soldier soldier.cpp)\ntarget_compile_features(soldier PRIVATE cxx_std_17)\ntarget_compile_options(soldier PRIVATE /fp:strict)\n')
    for args in ([CMAKE,'-S',str(host),'-B',str(host/'build')],[CMAKE,'--build',str(host/'build'),'--config','Release']):
        result=subprocess.run(args,capture_output=True,text=True)
        assert result.returncode==0,result.stdout+result.stderr
    inputs,expected=[],[]
    oracle=SoldierEligibilityOracle()
    def role_fixtures():
        for s in fixtures(ids):
            yield ('S',0,2,1,s)
            yield ('P',0,2,1,s)
            yield ('G',0,2,1,replace(s,action_type=max(-1,s.action_type)))
        for cls,held,stance,owner,tc in itertools.product((8,34,36,50,51,64),
                (-1,0,56,57,58,32767),(0,1,2,3),(0,2),(5,8,43)):
            yield ('P',held,2,1,Soldier(attacker_class=cls,attacker_id=ids[0],stance=stance,target_owner=owner,target_class=tc))
        for ac,tc,hidden,tid,computer in itertools.product((8,34,35,36,48),range(-1,71),
                (False,True),(1,696),(-1,0,1,2)):
            yield ('G',0,2,computer,Soldier(attacker_class=ac,target_class=tc,invisible=hidden,target_id=tid))
        for ac,state,action,computer,owner,flag in itertools.product((8,34,35,36),(0,1,2,3,255),
                (-1,123,124,125,126),(0,1),(0,1),(0,1)):
            yield ('G',0,state,computer,Soldier(attacker_class=ac,target_class=8,target_type=80,
                     action_type=action,owner_id=owner,target_owner=0,target_flag=flag))
    counts=dict(soldier=0,priest=0,siege=0)
    for i,(mode,held,state,computer,s) in enumerate(role_fixtures()):
        priest=mode=='P'
        siege=mode=='G'
        result=oracle.soldier(s,priest=priest,held_attribute=held,siege=siege,own_state=state,computer_player=computer)
        reference=can_attack_siege(s,state,computer,ids) if siege else can_attack_priest(s,held,ids) if priest else can_attack_soldier(s,ids)
        assert result==reference,(i,mode,held,s,result,reference)
        counts['siege' if siege else 'priest' if priest else 'soldier']+=1
        row=[]
        for field in members:
            value=getattr(s,field.name)
            row.append(str(struct.unpack('<I',struct.pack('<f',value))[0] if field.type is float else int(value)))
        inputs.append(' '.join(map(str,(mode,held,state,computer)))+' '+' '.join(row));expected.append(str(int(result)))
    result=subprocess.run([str(host/'build/Release/soldier.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    actual=result.stdout.splitlines();assert len(actual)==len(expected),(len(actual),len(expected))
    failures=[dict(case=i,input=inputs[i],actual=a,expected=b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
    (host/'failures.json').write_text(json.dumps(failures,indent=2)+'\n')
    assert not failures,(len(failures),failures[:3])
    tools=(*names,'classic_soldier_eligibility.py','classic_soldier_eligibility_oracle.py','check_classic_soldier_eligibility.py',
           'classic_attack_eligibility.py','classic_attack_eligibility_oracle.py','classic_engine_oracle.py','check_classic_air_planner.py')
    report=dict(passed=True,cases=len(inputs),case_counts=counts,source_sha256=SOURCE_SHA,catalog_sha256=sha,
                routines=['0x5B6E70','0x5B4B60','0x5B8180','0x41C530','0x7B2170'],
                tool_hashes={n:hashlib.sha256((TOOLKIT/n).read_bytes()).hexdigest() for n in tools},
                installed=False,full_behavior_parity=False,
                limitations=['Range, distance/path geometry, action/patrol and invisibility observations are fixtures.',
                             'Finite ranges/distances and NaN branch tests; not exhaustive floating-point equivalence.',
                             'No native DE XS execution, live observations or attack commands.'])
    (ROOT/'soldier-eligibility-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(inputs),'mobile predicate source/XS cases;',counts,'; not installed')


if __name__=='__main__':main()
