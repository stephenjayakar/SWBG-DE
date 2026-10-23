"""Differential checks for original conversion-target scan selection."""
from pathlib import Path
import itertools,json,random,re,struct,subprocess
from classic_conversion_target import Candidate,select
from classic_conversion_target_oracle import ConversionTargetOracle
from classic_unit_identity import sha
from check_classic_air_planner import CMAKE,PREFIX

ROOT=Path('work/classic-engine/conversion-target-host');TOOLKIT=Path('outputs/toolkit')
MAIN=r'''
#include <cstring>
#include <cstdint>
uint32_t bits(float v){uint32_t b;std::memcpy(&b,&v,4);return b;}
int main(){int n;while(std::cin>>n){
    classicConversionTargetReset();
    for(int i=0;i<n;i++) {int uid,enemy,present,state,can,distance,hp,cls;
        std::cin>>uid>>enemy>>present>>state>>can>>distance>>hp>>cls;
        classicConversionTargetAdd(uid,enemy,present,state,can,distance,hp,cls);
    }
    std::cout<<classicConversionTargetID<<' '<<bits(classicConversionTargetDistance)<<' '<<bits(classicConversionTargetScore)<<'\n';
    if(!arrays.empty())throw std::runtime_error("Selector allocated arrays");
}}
'''
def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
def fixtures():
    yield []
    for distance,hp,cls in itertools.product(range(256),(-32768,-1,0,1,100,32767),(32,47)):
        # Repeated equal rational scores expose extended-vs-stored precision.
        yield [Candidate(uid=1,distance=distance,max_hp=hp,source_class=cls),
               Candidate(uid=2,distance=distance,max_hp=hp,source_class=cls)]
    for enemy,present,state,convertible in itertools.product((False,True),(False,True),(0,1,2,3,4,255),(False,True)):
        yield [Candidate(1),Candidate(2,enemy,present,state,convertible,0,32767)]
    rng=random.Random(0x5B4E80)
    for n in (0,1,2,8,40,128,256,1024):
        for iteration in range(12):
            yield [Candidate(uid=rng.randrange(1,30),enemy=bool(rng.randrange(2)),present=rng.randrange(5)!=0,
                state=rng.randrange(5),convertible=bool(rng.randrange(2)),distance=rng.randrange(256),
                max_hp=rng.randrange(-32768,32768),source_class=rng.choice((47,32,50,18)),memory_owner=rng.randrange(256)) for _ in range(n)]

def main():
    ROOT.mkdir(parents=True,exist_ok=True);xs=(TOOLKIT/'classic_conversion_target.xs').read_text()
    (ROOT/'combined.xs').write_text(xs)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(ROOT/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    (ROOT/'target.cpp').write_text(PREFIX+xs+MAIN)
    (ROOT/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(target LANGUAGES CXX)\nadd_executable(target target.cpp)\ntarget_compile_features(target PRIVATE cxx_std_17)\ntarget_compile_options(target PRIVATE /fp:strict)\n')
    for args in ([CMAKE,'-S',str(ROOT),'-B',str(ROOT/'build')],[CMAKE,'--build',str(ROOT/'build'),'--config','Release']):
        run=subprocess.run(args,capture_output=True,text=True);assert run.returncode==0,run.stdout+run.stderr
    oracle=ConversionTargetOracle();inputs=[];expected=[];null_cases=0;rounding_cases=0
    for i,cs in enumerate(fixtures()):
        result=select(cs);actual=oracle.select(cs)
        assert actual==result[:2],(i,cs,actual,result)
        if i%100==0:
            assert oracle.select(cs,distance_pointer=False)==(result[0],-123.);null_cases+=1
        if len(cs)==2 and cs[0].distance==cs[1].distance and cs[0].max_hp==cs[1].max_hp and result[0]==2:rounding_cases+=1
        inputs.append(str(len(cs)))
        inputs.extend(' '.join(map(str,(c.uid,int(c.enemy),int(c.present),c.state,int(c.convertible),c.distance,c.max_hp,c.source_class))) for c in cs)
        expected.append(f'{result[0]} {bits(result[1])} {bits(result[2])}')
    run=subprocess.run([str(ROOT/'build/Release/target.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    actual=run.stdout.splitlines();assert len(actual)==len(expected)
    for i,(got,want) in enumerate(zip(actual,expected)):assert got==want,(i,got,want)
    report=dict(passed=True,cases=len(expected),null_output_cases=null_cases,repeated_ratio_replacement_cases=rounding_cases,
        hashes={n:sha(TOOLKIT/n) for n in ('classic_conversion_target.py','classic_conversion_target.xs','classic_conversion_target_oracle.py','check_classic_conversion_target.py')},
        installed=False,full_behavior_parity=False,
        limitations=['LOS scan, enemy relation, lookup and conversion eligibility are fixtures.',
                     'Caller must preserve source scan order and byte distance, rather than substitute a new distance metric.',
                     'Native observation and conversion order delivery remain unfinished.'])
    (ROOT.parent/'conversion-target-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {len(expected)} source/XS selectors / {null_cases} null outputs / {rounding_cases} rounded-score replacements')

if __name__=='__main__':main()
