"""Replay source-verified visibility events through the XS membership controller."""
from pathlib import Path
import json,re,subprocess
from classic_visible_membership import VisibleMembership
from classic_unit_identity import sha
from check_classic_air_planner import CMAKE,PREFIX
from check_classic_attack_dispatch_xs import EXTRA

ROOT=Path('work/classic-engine/visible-membership-host');TOOLKIT=Path('outputs/toolkit')
MAIN=r'''
int main(){int players,categories,n;
while(std::cin>>players>>categories>>n){classicVMemberInit(players,categories);
    std::set<int> touched;
    for(int step=0;step<n;step++){
        int uid,owner,x,y,radius,cat,oldMask,newMask;
        std::cin>>uid>>owner>>x>>y>>radius>>cat>>oldMask>>newMask;
        if(touched.insert(uid).second)classicVMemberSetLookup(uid,true);
        if(!classicVMemberUpdate(uid,owner,x,y,radius,cat,oldMask,newMask))throw std::runtime_error("Valid source event rejected");
        std::set<std::pair<int,int>> retained;
        for(int player=0;player<players;player++)for(int c=0;c<=categories;c++){
            int list=player*(categories+1)+c,base=xsArrayGetInt(classicVMemberBases,list),count=xsArrayGetInt(classicVMemberCounts,list);
            std::cout<<xsArrayGetInt(classicVMemberCaps,list)<<' '<<count<<' ';
            for(int i=0;i<count;i++){int at=base+i,unit=xsArrayGetInt(classicVMemberIDs,at),d=xsArrayGetInt(classicVMemberDetails,at),p=xsArrayGetInt(classicVMemberPositions,at);
                std::cout<<unit<<' '<<d%256<<' '<<d/256<<' '<<p%256<<' '<<p/256<<' ';
                retained.insert({unit,player});
                if(xsArrayGetInt(classicVMemberPointers,unit*players+player)!=at)throw std::runtime_error("Unrepaired source pointer");
            }
        }
        for(int unit:touched)for(int player=0;player<players;player++)
            if(!retained.count({unit,player})&&xsArrayGetInt(classicVMemberPointers,unit*players+player)!=-1)
                throw std::runtime_error("Removed record retained a pointer");
        std::cout<<'\n';
        if(arrays.size()!=8)throw std::runtime_error("Membership controller leaked arrays");
    }
}}
'''

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    proof=json.loads((ROOT.parent/'visible-membership-validation.json').read_text())
    assert proof['passed']
    traces=ROOT.parent/'visible-membership-traces.json';assert sha(traces)==proof['trace_sha256']
    for name,digest in proof['tool_hashes'].items():assert sha(TOOLKIT/name)==digest
    xs=(TOOLKIT/'classic_visible_membership.xs').read_text();(ROOT/'combined.xs').write_text(xs)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(ROOT/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    cpp=re.sub(r'for \((\w+) = ([^;]+); < ([^)]+)\)',lambda m:f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)',xs)
    (ROOT/'membership.cpp').write_text(PREFIX+EXTRA+'\n#include <set>\n'+cpp+MAIN)
    (ROOT/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(membership LANGUAGES CXX)\nadd_executable(membership membership.cpp)\ntarget_compile_features(membership PRIVATE cxx_std_17)\n')
    for args in ([CMAKE,'-S',str(ROOT),'-B',str(ROOT/'build')],[CMAKE,'--build',str(ROOT/'build'),'--config','Release']):
        run=subprocess.run(args,capture_output=True,text=True);assert run.returncode==0,run.stdout+run.stderr
    inputs=[];expected=[]
    for trace in json.loads(traces.read_text()):
        players,categories=trace['players'],trace['categories'];model=VisibleMembership(players,categories)
        inputs.append(f"{players} {categories} {len(trace['steps'])}")
        for args in trace['steps']:
            # C++/XS integers use the signed representation of source masks.
            args=list(args);args[-2:]=[(v+2**31)%2**32-2**31 for v in args[-2:]]
            inputs.append(' '.join(map(str,args)));model.update(*args);out=[]
            for player in range(players):
                for cat in range(categories+1):
                    bucket=model.rows[player][cat];out.extend((model.capacity[player][cat],len(bucket)))
                    out.extend(v for r in bucket for v in r)
            expected.append(' '.join(map(str,out)))
    run=subprocess.run([str(ROOT/'build/Release/membership.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    actual=[line.strip() for line in run.stdout.splitlines()];assert len(actual)==len(expected),(len(actual),len(expected))
    for i,(a,b) in enumerate(zip(actual,expected)):assert a==b,(i,a[:200],b[:200])
    report=dict(passed=True,updates=len(expected),source_proof_sha256=sha(ROOT.parent/'visible-membership-validation.json'),
        hashes={n:sha(TOOLKIT/n) for n in ('classic_visible_membership.xs','check_classic_visible_membership_xs.py')},
        installed=False,full_behavior_parity=False,
        limitations=['Source mask/category/lookup events are supplied; native visibility lifecycle is not connected.',
                     'Invalid removals reject rather than dereferencing invalid source memory; caller must discard the pass.',
                     'Missing-object pointer-repair branches remain untested.'])
    (ROOT.parent/'visible-membership-xs-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {len(expected)} XS membership updates with ordered records, capacities and repaired pointers')

if __name__=='__main__':main()
