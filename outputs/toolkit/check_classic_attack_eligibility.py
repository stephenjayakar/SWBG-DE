"""Differential source/XS checks for the base attack predicate and EF catalog."""
from pathlib import Path
import hashlib
import itertools
import json
import re
import struct
import subprocess
from classic_attack_eligibility import catalog, can_attack_base, can_attack_tower, can_attack_nullable, can_attack_neutral, generate_catalog
from classic_attack_eligibility_oracle import AttackEligibilityOracle
from classic_engine_oracle import SOURCE_SHA
from check_classic_air_planner import CMAKE, PREFIX

ROOT=Path('work/classic-engine')
TOOLKIT=Path('outputs/toolkit')
MAIN=r'''
#include <cstring>
#include <cstdint>
int main() {
    char mode;int ac,aid,tc,tid,hidden;uint32_t bits;
    while(std::cin>>mode>>ac>>aid>>tc>>tid>>hidden>>bits) {
        float resource;std::memcpy(&resource,&bits,4);
        bool result;
        if(mode=='T') {
            int present,owner,targetOwner,type,flag,state;
            std::cin>>present>>owner>>targetOwner>>type>>flag>>state;
            result=classicAttackTower(ac,aid,tc,tid,hidden!=0,resource,present!=0,owner,targetOwner,type,flag,state);
        } else if(mode=='C' || mode=='L') {
            int present;std::cin>>present;
            result=classicAttackNullable(ac,aid,tc,tid,hidden!=0,resource,present!=0);
        } else if(mode=='M') {int present;std::cin>>present;result=classicAttackNever();}
        else if(mode=='N') result=classicAttackNeutral(ac,tc);
        else if(mode=='W') result=classicAttackBuilding(ac,aid,tc,tid,hidden!=0,resource);
        else result=classicAttackBase(ac,aid,tc,tid,hidden!=0,resource);
        std::cout<<result<<'\n';
    }
    if(!arrays.empty()) throw std::runtime_error("Unexpected allocation");
}
'''


def fixtures(ids):
    classes=(*range(-1,71),-32768,32767)
    for ac,tc,hidden in itertools.product(classes,classes,(False,True)):
        yield (ac,1,tc,1,hidden,0.0)
    # Overrides must never bypass any earlier denial, but do bypass class gates.
    for aid,ac,tc,tid,hidden in itertools.product(ids,(-1,4,8,9,48),(0,21,28,43,59,64),(1,696),(False,True)):
        yield (ac,aid,tc,tid,hidden,0.0)
    for aid,ac,tc,value in itertools.product((499,500,501,602,603,604),(-1,4,8,9,48),
                                            (0,21,28,43,59,64),(-1.0,-0.0,0.0,1e-45,1.0,float('nan'))):
        yield (ac,aid,tc,1,False,value)
    # Neighbors of every catalog entry catch accidental ranges or ID shifts.
    for uid,tc in itertools.product(ids,classes):
        for aid in (uid-1,uid,uid+1):
            yield (-1,aid,tc,1,False,0.0)


def tower_fixtures(ids):
    for ac,tc,owner,enemy,hidden in itertools.product((-1,4,8,9,48,57),
            (-1,4,5,8,21,28,43,48,59,60,64),(0,1),(0,1,2),(False,True)):
        yield (ac,1,tc,1,hidden,0.0,True,owner,enemy,70,0,2)
    for aid,tc,tid,kind,flag,state,present in itertools.product((1,500,603,*ids),
            (5,21,43),(1,50,696),(70,80),(0,1,255),(0,1,2,3,255),(False,True)):
        yield (8,aid,tc,tid,False,1.0,present,1,2,kind,flag,state)


def main():
    ids,sha=catalog()
    generated=generate_catalog(ids,sha)
    ROOT.mkdir(parents=True,exist_ok=True)
    (ROOT/'classic_attack_catalog.xs').write_text(generated)
    host=ROOT/'attack-eligibility-host';host.mkdir(exist_ok=True)
    xs=generated+(TOOLKIT/'classic_attack_eligibility.xs').read_text()
    (host/'combined.xs').write_text(xs)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(host/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    (host/'eligibility.cpp').write_text(PREFIX+xs+MAIN)
    (host/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(eligibility LANGUAGES CXX)\nadd_executable(eligibility eligibility.cpp)\ntarget_compile_features(eligibility PRIVATE cxx_std_17)\ntarget_compile_options(eligibility PRIVATE /fp:strict)\n')
    for args in ([CMAKE,'-S',str(host),'-B',str(host/'build')],[CMAKE,'--build',str(host/'build'),'--config','Release']):
        r=subprocess.run(args,capture_output=True,text=True)
        assert r.returncode==0,r.stdout+r.stderr
    inputs,expected=[],[]
    oracle=AttackEligibilityOracle()
    counts=dict(base=0,building=0,tower=0,civilian=0,lion=0,medic=0,neutral=0)
    for i,args in enumerate(fixtures(ids)):
        actual=oracle.base(*args,owner_id=i%9)
        reference=can_attack_base(*args,ground_to_air=ids)
        assert actual==reference,(i,args,actual,reference)
        ac,aid,tc,tid,hidden,resource=args
        bits=struct.unpack('<I',struct.pack('<f',resource))[0]
        line=' '.join(map(str,(ac,aid,tc,tid,int(hidden),bits)))
        inputs.append('B '+line)
        expected.append(str(int(actual)))
        counts['base']+=1
        if i%5==0:
            delegated=oracle.base(*args,owner_id=i%9,building=True)
            assert delegated==actual,(args,delegated,actual)
            inputs.append('W '+line);expected.append(str(int(delegated)))
            counts['building']+=1
        if i%5==0:
            for mode,kind in (('C','civilian'),('L','lion'),('M','medic')):
                for present in (False,True):
                    actual=oracle.nullable(*args,target_present=present,kind=kind)
                    reference=False if kind=='medic' else can_attack_nullable(*args,target_present=present,ground_to_air=ids)
                    assert actual==reference,(kind,args,present,actual,reference)
                    inputs.append(mode+' '+line+' '+str(int(present)))
                    expected.append(str(int(actual)));counts[kind]+=1
    for args in tower_fixtures(ids):
        actual=oracle.tower(*args)
        reference=can_attack_tower(*args,ground_to_air=ids)
        assert actual==reference,(args,actual,reference)
        ac,aid,tc,tid,hidden,resource,*rest=args
        bits=struct.unpack('<I',struct.pack('<f',resource))[0]
        inputs.append('T '+' '.join(map(str,(ac,aid,tc,tid,int(hidden),bits,*map(int,rest)))))
        expected.append(str(int(actual)));counts['tower']+=1
    for kind,tc in itertools.product(range(5),(*range(-1,100),-2147483648,2147483647)):
        actual=oracle.neutral(kind,tc)
        assert actual==can_attack_neutral(kind,tc),(kind,tc,actual)
        inputs.append(f'N {kind} 0 {tc} 0 0 0')
        expected.append(str(int(actual)));counts['neutral']+=1
    r=subprocess.run([str(host/'build/Release/eligibility.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    actual=r.stdout.splitlines();assert len(actual)==len(expected),(len(actual),len(expected))
    failures=[dict(case=i,input=inputs[i],actual=a,expected=b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
    (host/'failures.json').write_text(json.dumps(failures,indent=2)+'\n')
    assert not failures,(len(failures),failures[:3])
    names=('classic_attack_eligibility.py','classic_attack_eligibility.xs','classic_attack_eligibility_oracle.py',
           'check_classic_attack_eligibility.py','classic_engine_oracle.py','check_classic_air_planner.py')
    report=dict(passed=True,cases=len(inputs),case_counts=counts,source_sha256=SOURCE_SHA,catalog_sha256=sha,catalog_ids=ids,
                routines=['0x41C530','0x7B2170','0x5B7CD0','0x5B8A90','0x5B2F80','0x5B28F0',
                          '0x5B2FB0','0x5B2910','0x5B7D70','0x5B4D80','0x5B8440'],generated_sha256=hashlib.sha256(generated.encode()).hexdigest(),
                tool_hashes={n:hashlib.sha256((TOOLKIT/n).read_bytes()).hexdigest() for n in names},
                installed=False,full_behavior_parity=False,
                limitations=['Base/tower/building/civilian/lion/medic/neutrality predicates; mobile wrappers tested separately.',
                             'Fixture target invisibility query and source resource/class/ID observations.',
                             'Static EF membership patch executes; file loader supplied its installed catalog.',
                             'Compiled strict-float host, not native DE XS or gameplay.'])
    (ROOT/'attack-eligibility-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(inputs),'attack predicate source/XS cases;',counts,';',len(ids),'installed EF overrides; not installed')


if __name__=='__main__':main()
