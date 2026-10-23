"""Source factory selection/lifecycle plus compiled XS kind mappings."""
from pathlib import Path
import hashlib
import itertools
import json
import re
import subprocess
from classic_unit_ai_factory import unit_ai_type
from classic_unit_ai_factory_oracle import UnitAIFactoryOracle
from classic_engine_oracle import SOURCE_SHA
from check_classic_air_planner import CMAKE,PREFIX

ROOT=Path('work/classic-engine');TOOLKIT=Path('outputs/toolkit')
MAIN=r'''
int main(){
    int cls,volley;
    while(std::cin>>cls>>volley){
        int type=classicUnitAIType(cls,volley);
        std::cout<<type<<' '<<classicUnitAIAttackKind(type)<<' '
                 <<classicUnitAINeutralKind(type)<<' '<<classicUnitAIHasConversion(type)<<'\n';
    }
    if(!arrays.empty())throw std::runtime_error("Unexpected allocation");
}
'''


def fixtures():
    for cls in range(-32768,32768):yield cls,-1,False,False
    for cls,volley,existing,failed in itertools.product(range(-1,71),
            (-2147483648,-2,-1,0,1,2147483647),(False,True),(False,True)):
        yield cls,volley,existing,failed


def main():
    name='classic_unit_ai_factory.xs';xs=(TOOLKIT/name).read_text()
    host=ROOT/'unit-ai-factory-host';host.mkdir(parents=True,exist_ok=True)
    (host/'combined.xs').write_text(xs)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(host/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    (host/'factory.cpp').write_text(PREFIX+xs+MAIN)
    (host/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(factory LANGUAGES CXX)\nadd_executable(factory factory.cpp)\ntarget_compile_features(factory PRIVATE cxx_std_17)\n')
    for args in ([CMAKE,'-S',str(host),'-B',str(host/'build')],[CMAKE,'--build',str(host/'build'),'--config','Release']):
        r=subprocess.run(args,capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
    oracle=UnitAIFactoryOracle()
    inputs,expected=[],[];seen=set();source_cases=0
    for cls,volley,existing,failed in fixtures():
        selected,events=oracle.select(cls,volley,existing,failed)
        reference=unit_ai_type(cls,volley)
        actual_expected=-1 if failed else reference
        assert selected==actual_expected,(cls,volley,existing,failed,selected,reference,events)
        expected_events=[('destroy',)] if existing else []
        if reference!=-1:
            size=428 if reference in (1,2) else 420 if reference==3 else 416
            expected_events.append(('allocate',size))
            if not failed:expected_events.append(('construct',reference,5 if reference==11 else 10))
        assert events==expected_events,(cls,volley,existing,failed,events,expected_events)
        source_cases+=1
        if (cls,volley) not in seen:
            seen.add((cls,volley));inputs.append(f'{cls} {volley}')
            row=oracle.catalog[reference] if reference!=-1 else dict(attack_kind=-1,neutral_kind=4,can_convert=False)
            expected.append(f"{reference} {row['attack_kind']} {row['neutral_kind']} {int(row['can_convert'])}")
    r=subprocess.run([str(host/'build/Release/factory.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    actual=r.stdout.splitlines();assert len(actual)==len(expected),(len(actual),len(expected))
    failures=[dict(case=i,input=inputs[i],actual=a,expected=b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
    (host/'failures.json').write_text(json.dumps(failures,indent=2)+'\n')
    assert not failures,(len(failures),failures[:3])
    names=(name,'classic_unit_ai_factory.py','classic_unit_ai_factory_oracle.py','classic_unit_ai_catalog.py',
           'check_classic_unit_ai_factory.py','classic_engine_oracle.py','check_classic_air_planner.py')
    report=dict(passed=True,source_cases=source_cases,xs_cases=len(inputs),source_sha256=SOURCE_SHA,
                routines=['0x55D430'],catalog=oracle.catalog,
                tool_hashes={n:hashlib.sha256((TOOLKIT/n).read_bytes()).hexdigest() for n in names},
                installed=False,full_behavior_parity=False,
                limitations=['Allocator, constructor bodies and old-instance destructor are fixture boundaries.',
                             'XS selects behavior type; it does not allocate native UnitAI objects.',
                             'Source volley/class observations required; native DE lifecycle not tested.'])
    (ROOT/'unit-ai-factory-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',source_cases,'source factory cases /',len(inputs),'XS type/dispatch cases; not installed')


if __name__=='__main__':main()
