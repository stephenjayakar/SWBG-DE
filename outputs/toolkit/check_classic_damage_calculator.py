"""Compare actual XS armor/modifier calculations with original x86 routines."""
from pathlib import Path
import hashlib
import json
import re
import struct
import subprocess
from check_classic_air_planner import CMAKE, PREFIX
from check_classic_target_ranker import FLOAT_HOST
from check_classic_attack_dispatch_xs import EXTRA
from check_classic_damage import armor_cases, modifier_fixtures
from classic_damage_oracle import DamageOracle
from classic_damage_model import damage_capability
from classic_engine_oracle import SOURCE_SHA

ROOT=Path('work/classic-engine')
TOOLKIT=Path('outputs/toolkit')
MAIN=r'''
#include <cstring>
#include <cstdint>
int main() {
    char mode;classicDamageReset();
    while(std::cin>>mode) {
        float result=0;
        if(mode=='D' || mode=='C') {
            int nw,na,base;float modifier,terrain;std::cin>>nw>>na>>base>>modifier>>terrain;
            classicDamageReset(base,modifier,terrain);
            for(int i=0;i<na;i++) {int cls,amount;std::cin>>cls>>amount;classicDamageAddArmor(cls,amount);}
            for(int i=0;i<nw;i++) {int cls,amount;std::cin>>cls>>amount;classicDamageAddWeapon(cls,amount);}
            result=classicDamageFinish();
            if(result!=classicDamageFinish()) throw std::runtime_error("Finish mutated damage");
            if(mode=='C') {
                int target,ai,allowed;std::cin>>target>>ai>>allowed;
                result=classicDamageCapability(target!=0,ai!=0,allowed!=0);
            }
        } else {
            int high,special,action,building,relics,specialRelics,targetBuilding,targetRelics,targetSpecial;
            float az,tz;std::cin>>high>>az>>tz>>special>>action>>building>>relics>>specialRelics>>targetBuilding>>targetRelics>>targetSpecial;
            result=classicDamageModifier(high!=0,az,tz,special,action!=0,building!=0,relics,specialRelics,targetBuilding!=0,targetRelics,targetSpecial);
        }
        uint32_t bits;std::memcpy(&bits,&result,4);std::cout<<bits<<'\n';
        if(arrays.size()!=2) throw std::runtime_error("Armor arrays leaked");
    }
}
'''


def main():
    names=('classic_target_ranker.xs','classic_target_scorer.xs','classic_damage_calculator.xs')
    text='\n'.join((TOOLKIT/n).read_text() for n in names)
    host=ROOT/'damage-calculator-host';host.mkdir(exist_ok=True)
    (host/'combined.xs').write_text(text)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(host/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    text,loops=re.subn(r'for \((\w+) = ([^;]+); < ([^)]+)\)',
                      lambda m:f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)',text)
    assert loops==9
    prefix=PREFIX.replace('std::vector<vector>>;','std::vector<vector>, std::vector<float>>;')
    (host/'damage.cpp').write_text(prefix+FLOAT_HOST+EXTRA+text+MAIN)
    (host/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(classic_damage LANGUAGES CXX)\nadd_executable(damage damage.cpp)\ntarget_compile_features(damage PRIVATE cxx_std_17)\ntarget_compile_options(damage PRIVATE /fp:strict)\n')
    for args in ([CMAKE,'-S',str(host),'-B',str(host/'build')],[CMAKE,'--build',str(host/'build'),'--config','Release']):
        r=subprocess.run(args,capture_output=True,text=True)
        assert r.returncode==0,r.stdout+r.stderr
    inputs,expected=[],[]
    oracle=DamageOracle()
    cases=armor_cases()
    for count in (40,128,129,512,1024):
        cases.append(([(3,12),(4,30)],[(i%5,i%9) for i in range(count)],1000,1.25,1.5))
        cases.append(([(i%7,i%20) for i in range(count)],[(3,2),(4,1)],1000,1.25,1.5))
    cases += [([(3,32767)],[(3,-32768)],1000,1.25,2.0),
              ([(3,-32768)],[(3,32767)],1000,-1.25,2.0)]
    for args in cases:
        weapons,armor,base,modifier,terrain=args
        values=['D',len(weapons),len(armor),base,modifier,terrain]
        values += [v for pair in armor+weapons for v in pair]
        inputs.append(' '.join(map(str,values)))
        expected.append(str(struct.unpack('<I',struct.pack('<f',oracle.damage(*args)))[0]))
    capability_cases=0
    raw_cases=armor_cases()[::11]+[
        ([(3,32767)]*1024,[],1000,0.5,2.0),
        ([(3,32767)]*1023+[(3,2)],[(3,32767)],1000,1.25,1.5),
        ([(3,0),(4,-32768)],[],0,1.0,1.0)]
    for args in raw_cases:
        weapons,armor,base,modifier,terrain=args
        for target in (False,True):
            for ai in (False,True):
                for allowed in (False,True):
                    flags=(target,ai,allowed)
                    values=['C',len(weapons),len(armor),base,modifier,terrain]
                    values += [v for pair in armor+weapons for v in pair]+list(map(int,flags))
                    inputs.append(' '.join(map(str,values)))
                    actual=oracle.capability(*args,*flags)
                    reference=damage_capability(*args,*flags)
                    assert struct.pack('<f',actual)==struct.pack('<f',reference),(args,flags,actual,reference)
                    expected.append(str(struct.unpack('<I',struct.pack('<f',actual))[0]))
                    capability_cases+=1
    modifiers=list(modifier_fixtures())
    for args in modifiers:
        inputs.append('M '+' '.join(str(int(v)) if isinstance(v,bool) else str(v) for v in args))
        expected.append(str(struct.unpack('<I',struct.pack('<f',oracle.modifier(*args)))[0]))
    r=subprocess.run([str(host/'build/Release/damage.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    actual=r.stdout.splitlines();assert len(actual)==len(expected),(len(actual),len(expected))
    failures=[dict(case=i,input=inputs[i],actual=a,expected=b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
    (host/'failures.json').write_text(json.dumps(failures,indent=2)+'\n')
    assert not failures,(len(failures),failures[:3])
    report=dict(passed=True,armor_cases=len(cases),modifier_cases=len(modifiers),capability_cases=capability_cases,source_sha256=SOURCE_SHA,
                xs_hashes={n:hashlib.sha256((TOOLKIT/n).read_bytes()).hexdigest() for n in names},
                installed=False,full_behavior_parity=False,
                limitations=['C++ strict-float host, not DE XS VM execution.',
                             'Caller supplies source integer attack/armor tables and environmental state.',
                             'UnitAI presence, canAttackUnit and the upstream modifier are wrapper fixtures.',
                             'Target virtual dispatch is bound to the common combat-object armor method.',
                             'No live eligibility, armor lookup API, shields, memory or commands.'])
    report['tool_hashes']={n:hashlib.sha256((TOOLKIT/n).read_bytes()).hexdigest() for n in
                          ('classic_engine_oracle.py','classic_damage_oracle.py','classic_damage_model.py',
                           'check_classic_damage.py','check_classic_damage_calculator.py',
                           'check_classic_air_planner.py','check_classic_target_ranker.py','check_classic_attack_dispatch_xs.py')}
    (ROOT/'damage-calculator-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(cases)+len(modifiers),'source damage/modifier cases plus',capability_cases,'capability cases; not installed')


if __name__=='__main__': main()
