"""Compare original active-attack wrapper with XS group-store continuation.

Selection and task execution are explicit boundaries. Intermediate callback
states are compared as well as final state, not just chosen action numbers.
"""
from pathlib import Path
import hashlib,itertools,json,re,subprocess
from classic_active_attack_oracle import ActiveAttackOracle
from classic_engine_oracle import SOURCE_SHA
from check_classic_air_planner import CMAKE,PREFIX
from check_classic_attack_dispatch_xs import EXTRA

ROOT=Path('work/classic-engine/active-attack-host');TOOLKIT=Path('outputs/toolkit')
HOST=r'''
#include <cstring>
#include <sstream>
vector cInvalidVector(-1,-1,-1);
int floatbits(float v){int b;std::memcpy(&b,&v,4);return b;}
'''
MAIN=r'''
std::string state(int h){std::ostringstream s;
 for(int f:{7,8,9,10,11})s<<classicGroupGet(h,f)<<' ';
 s<<classicActiveTaskTime<<' ';
 for(float v:{classicActivePosition.x,classicActivePosition.y,classicActivePosition.z,
   classicActiveSavedHome.x,classicActiveSavedHome.z,classicActiveSavedHome.y})s<<floatbits(v)<<' ';
 return s.str();
}
int main(){int kind,flags,enabled,now,previous,hasTarget,transport,yielded,target,type;
while(std::cin>>kind>>flags>>enabled>>now>>previous>>hasTarget>>transport>>yielded>>target>>type){
 classicGroupsReset();int h=classicGroupCreate(1);classicGroupSet(h,4,kind);classicGroupSet(h,11,flags);
 classicActiveRequest=0;classicActiveTaskTime=0;classicActiveDeferredGround=-7;classicActiveDeferredAir=-8;
 classicActivePosition=vector(9,8,7);classicActiveHome=vector(2,6,4);classicActiveSavedHome=vector(1,5,3);
 std::string event="";
 if(classicActiveAttackEligible(h,enabled)){
   event="S ";if(yielded)classicGroupSet(h,11,flags|64);
   if(!classicActiveSelect(target,type,vector(23,45,67)))return 6;
   if(!classicActiveAttackComplete(h,classicActiveElapsed(now,previous),now,hasTarget!=0,transport))return 2;
   if(classicActiveRequest==1){
     event+="T "+std::to_string(classicActiveTask)+" "+std::to_string(classicActiveForce)+" "+state(h);
     // Interleaved begin must leave the callback context intact.
     if(classicActiveAttackComplete(h,0,0,false,0))return 3;
     if(classicActiveSelect(999,999,vector(99,99,99)))return 7;
     if(!classicActiveTaskComplete())return 4;
     if(classicActiveTaskComplete())return 5;
   }
 }
 std::cout<<state(h)<<classicActiveDeferredGround<<' '<<classicActiveDeferredAir<<' '<<event<<'\n';
 if(arrays.size()!=5)throw std::runtime_error("Arrays leaked");
}
}
'''

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    names=('classic_group_state.xs','classic_active_attack.xs')
    xs='\n'.join((TOOLKIT/n).read_text() for n in names)
    (ROOT/'combined.xs').write_text(xs)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(ROOT/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    special='for (i = 0; < xsArrayGetSize(classicGroups))'
    assert xs.count(special)==1
    cpp=xs.replace(special,'for (int i = 0; i < xsArrayGetSize(classicGroups); i++)')
    cpp=re.sub(r'for \((\w+) = ([^;]+); < ([^)]+)\)',lambda m:f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)',cpp)
    (ROOT/'active.cpp').write_text(PREFIX+EXTRA+HOST+cpp+MAIN)
    (ROOT/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(active LANGUAGES CXX)\nadd_executable(active active.cpp)\ntarget_compile_features(active PRIVATE cxx_std_17)\ntarget_compile_options(active PRIVATE /fp:strict)\n')
    for args in ([CMAKE,'-S',str(ROOT),'-B',str(ROOT/'build')],[CMAKE,'--build',str(ROOT/'build'),'--config','Release']):
        run=subprocess.run(args,capture_output=True,text=True);assert run.returncode==0,run.stdout+run.stderr
    oracle=ActiveAttackOracle();cases=[];expected=[];traces=[]
    clocks=((0,0),(4999,0),(5000,0),(5001,0),(100,200),(-2147483648,2147483000),
            (2147483647,-1),(0,-5000),(-1,-5001))
    counts=dict(selected=0,tasks=0,deferred=0,skipped=0)
    for kind,flags,enabled,clock,selection in itertools.product(
            (100,102,108,101), (0,8,32,40,64,96,-2147483648), (0,1), clocks,
            ((0,0,0),(1,0,0),(1,1,0),(1,2,0),(1,1,1),(0,0,1))):
        i=len(cases);target=-1 if i%13==0 else 555;typ=-32768 if i%11==0 else 123
        case=(kind,flags,enabled,*clock,*selection,target,typ)
        result=oracle.run(case);events=[]
        for event in result['events']:
            if event[0]=='select':events+=['S'];counts['selected']+=1
            else:events+=['T',*event[1:3],*event[3]];counts['tasks']+=1
        if not events:counts['skipped']+=1
        if result['deferred']!=[-7,-8]:counts['deferred']+=1
        # These are explicit selector-boundary fixtures, not native transport searches.
        if events:assert result['queries']==[[110,1,-1,-1],[110,0,-1,-1],[104,1,-1,-1],[104,0,-1,-1]]
        expected.append(' '.join(map(str,[*result['state'],*result['deferred'],*events])))
        cases.append(' '.join(map(str,case)));traces.append(dict(input=case,source=result))
    run=subprocess.run([str(ROOT/'build/Release/active.exe')],input='\n'.join(cases)+'\n',capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    actual=[s.strip() for s in run.stdout.splitlines()]
    assert len(actual)==len(expected),(len(actual),len(expected))
    for i,(a,b) in enumerate(zip(actual,expected)):assert a==b,(i,cases[i],a,b)
    trace=ROOT/'traces.json';trace.write_text(json.dumps(traces)+'\n')
    files=(*names,'classic_active_attack_oracle.py','classic_group_state_oracle.py','classic_engine_oracle.py','check_classic_active_attack.py')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    report=dict(passed=True,cases=len(cases),counts=counts,source_sha256=SOURCE_SHA,
        hashes={n:sha(TOOLKIT/n) for n in files},trace_sha256=sha(trace),installed=False,engine_verified=False,
        limitations=['Target selection and task delivery are callback fixtures; source wrapper runs directly.',
                     'Transport availability queries return no group; their selection policy is not implemented here.',
                     'XS uses one synchronous scratch context; caller must persist group vectors and deliver tasks.',
                     'Live native group scheduling, pathfinding and issued orders remain unconnected.'])
    (ROOT.parent/'active-attack-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,cases=len(cases),counts=counts)))

if __name__=='__main__':main()
