"""Run original membership then original scans, compare the composed XS path."""
from pathlib import Path
import json,re,subprocess
from classic_visible_membership import VisibleMembership
from classic_visible_membership_oracle import VisibleMembershipOracle
from classic_visible_scan_oracle import VisibleScanOracle
from classic_visible_scan import scan
from classic_unit_identity import sha
from check_classic_air_planner import CMAKE,PREFIX
from check_classic_attack_dispatch_xs import EXTRA

ROOT=Path('work/classic-engine/visible-pipeline-host');TOOLKIT=Path('outputs/toolkit')
MAIN=r'''
int main(){int players,categories,n;
int desired=xsArrayCreateInt(20,0,"desired"),relations=xsArrayCreateInt(256,0,"relations");
while(std::cin>>players>>categories>>n){classicVisibilityReset(players,categories);std::set<int> touched;
    for(int step=0;step<n;step++){
        int uid,owner,x,y,radius,cat,oldMask,newMask;
        std::cin>>uid>>owner>>x>>y>>radius>>cat>>oldMask>>newMask;
        if(touched.insert(uid).second)classicVMemberSetLookup(uid,true);
        if(!classicVMemberUpdate(uid,owner,x,y,radius,cat,oldMask,newMask))throw std::runtime_error("Source update rejected");
        int qx,qy,los,player,nd;std::cin>>qx>>qy>>los>>player>>nd;
        for(int i=0;i<nd;i++){int v;std::cin>>v;xsArraySetInt(desired,i,v);}
        for(int i=0;i<256;i++){int v;std::cin>>v;xsArraySetInt(relations,i,v);}
        std::cout<<classicVisibilityScan(qx,qy,los,player,desired,nd,relations);
        for(int g=0;g<5;g++){int count=xsArrayGetInt(classicVisibleCounts,g);std::cout<<' '<<count;
            for(int i=0;i<count;i++){int at=g*256+i,d=xsArrayGetInt(classicVisibleDetails,at),p=xsArrayGetInt(classicVisiblePositions,at);
                std::cout<<' '<<xsArrayGetInt(classicVisibleIDs,at)<<' '<<d%256<<' '<<d/256<<' '<<p%256<<' '<<p/256;}}
        std::cout<<'\n';if(arrays.size()!=15)throw std::runtime_error("Visibility pipeline leaked arrays");
    }
}}
'''
def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    proof=json.loads((ROOT.parent/'visible-membership-validation.json').read_text());assert proof['passed']
    traces=ROOT.parent/'visible-membership-traces.json';assert sha(traces)==proof['trace_sha256']
    for name,digest in proof['tool_hashes'].items():assert sha(TOOLKIT/name)==digest
    scan_proof=json.loads((ROOT.parent/'visible-scan-validation.json').read_text());assert scan_proof['passed']
    generated=ROOT.parent/'visible-scan-host/classic_visible_distance.xs';assert sha(generated)==scan_proof['generated_sha256']
    names=('classic_visible_membership.xs','classic_visible_scan.xs','classic_visible_pipeline.xs')
    xs=generated.read_text()+'\n'+'\n'.join((TOOLKIT/n).read_text() for n in names)
    (ROOT/'combined.xs').write_text(xs)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(ROOT/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    cpp=re.sub(r'for \((\w+) = ([^;]+); < ([^)]+)\)',lambda m:f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)',xs)
    (ROOT/'pipeline.cpp').write_text(PREFIX+EXTRA+'\n#include <set>\n'+cpp+MAIN)
    (ROOT/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(pipeline LANGUAGES CXX)\nadd_executable(pipeline pipeline.cpp)\ntarget_compile_features(pipeline PRIVATE cxx_std_17)\n')
    for args in ([CMAKE,'-S',str(ROOT),'-B',str(ROOT/'build')],[CMAKE,'--build',str(ROOT/'build'),'--config','Release']):
        run=subprocess.run(args,capture_output=True,text=True);assert run.returncode==0,run.stdout+run.stderr
    table,_=VisibleScanOracle().distance_table();oracle=VisibleMembershipOracle();inputs=[];expected=[];retained=0;records=0
    for trace in json.loads(traces.read_text()):
        players,categories=trace['players'],trace['categories'];model=VisibleMembership(players,categories)
        oracle.initialize(players,categories);prior=[[] for _ in range(5)]
        inputs.append(f"{players} {categories} {len(trace['steps'])}")
        for step,args in enumerate(trace['steps']):
            oracle.update(*args);model.update(*args)
            signed=list(args);signed[-2:]=[(v+2**31)%2**32-2**31 for v in signed[-2:]]
            inputs.append(' '.join(map(str,signed)))
            player=step%(players+1)
            desired=[] if step%11==0 else [i%(categories+1) for i in range(step%7+1)]
            relations=[(i+step)%5 for i in range(256)]
            x,y=(128,128) if step%2 else (step%256,255-step%256)
            los=(-1,0,7,15,30)[step%5]
            inputs.append(' '.join(map(str,[x,y,los,player,len(desired),*desired,*relations])))
            result=oracle.scan(x,y,los,player,desired,relations)
            rows=model.rows[player] if player<players else [[] for _ in range(categories+1)]
            reference=scan(table,rows,desired,relations,x,y,los,player,players,prior)
            assert result==reference,(players,step,result,reference)
            total,buffers=result;records+=total
            if not desired or player>=players:retained+=1
            prior=buffers;out=[total]
            for buf in buffers:out.append(len(buf));out.extend(v for r in buf for v in r)
            expected.append(' '.join(map(str,out)))
    run=subprocess.run([str(ROOT/'build/Release/pipeline.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    actual=run.stdout.splitlines();assert len(actual)==len(expected)
    for i,(a,b) in enumerate(zip(actual,expected)):assert a==b,(i,a[:200],b[:200])
    report=dict(passed=True,update_then_scan_cases=len(expected),retained_buffer_cases=retained,returned_records=records,
        hashes={n:sha(TOOLKIT/n) for n in (*names,'classic_visible_membership_oracle.py','check_classic_visible_pipeline.py')},
        generated_sha256=sha(generated),installed=False,full_behavior_parity=False,
        limitations=['Visibility/category/lookup events and relations are fixtures; actual source updates feed actual source scans.',
                     'Native events, object movement field updates and UnitAI scan-cache gating remain unfinished.'])
    (ROOT.parent/'visible-pipeline-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {len(expected)} source/XS update-then-scan cases / {retained} retained buffers / {records} returned records')

if __name__=='__main__':main()
