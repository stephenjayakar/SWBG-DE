"""Replay original search evidence through XS plus the maintained visibility lists."""
from pathlib import Path
import json,re,struct,subprocess
from classic_unit_identity import sha
from classic_search_cache import bits
from check_classic_air_planner import CMAKE,PREFIX
from check_classic_attack_dispatch_xs import EXTRA

ROOT=Path('work/classic-engine/search-cache-host');TOOLKIT=Path('outputs/toolkit')
MAIN=r'''
#include <cstring>
#include <cstdint>
float frombits(uint32_t b){float v;std::memcpy(&v,&b,4);return v;}
uint32_t bits(float v){uint32_t b;std::memcpy(&b,&v,4);return b;}
int main(){int desired=xsArrayCreateInt(3,0,"desired"),relations=xsArrayCreateInt(256,0,"relations");
int used,total,seen,lo,hi,allow,uid,owner,hasDesired,count,order,followID,world,found,action,followOwner;
uint32_t timer,x,y,los,radius,fx,fy,flos;
char mode;
while(std::cin>>mode){
    if(mode=='U'){
        uint32_t elapsed;std::cin>>timer>>elapsed>>used;
        classicSearchTimer=frombits(timer);classicSearchUsed=used;classicSearchResult=999;classicSearchSeen=7;
        classicSearchSeedLo=0x5678;classicSearchSeedHi=0x1234;
        classicSearchStartUpdate(frombits(elapsed));
        std::cout<<"U "<<classicSearchUsed<<' '<<classicSearchResult<<' '<<bits(classicSearchTimer)<<' '
                 <<classicSearchSeen<<' '<<classicSearchSeedLo<<' '<<classicSearchSeedHi<<'\n';continue;
    }
    std::cin>>used>>total>>seen>>timer>>lo>>hi>>x>>y>>allow>>uid>>owner>>los>>radius
              >>hasDesired>>count>>order>>followID>>world>>found>>action>>followOwner>>fx>>fy>>flos;
    classicVisibilityReset(3,1);
    for(int i=0;i<24;i++){classicVMemberSetLookup(i,true);
        if(!classicVMemberUpdate(i,i%3,(i%7)*3+5,(i/7)*3+5,i%4,i%2,0,7))throw std::runtime_error("Fixture insertion failed");}
    for(int i=0;i<256;i++)xsArraySetInt(relations,i,i==1?1:i==2?4:0);
    xsArraySetInt(desired,0,0);xsArraySetInt(desired,1,1);
    classicVisibilityScan(10,10,15,1,desired,2,relations);
    xsArraySetInt(desired,0,1);xsArraySetInt(desired,1,0);xsArraySetInt(desired,2,1);
    classicSearchUsed=used;classicSearchResult=total;classicSearchSeedLo=lo;classicSearchSeedHi=hi;
    classicSearchSetActor(uid,owner,frombits(los),frombits(radius),hasDesired?desired:-1,count,relations,
                          order,followID,world,frombits(timer),seen);
    classicSearchSetFollow(found,action,followOwner,frombits(fx),frombits(fy),frombits(flos));
    classicSearchRun(frombits(x),frombits(y),allow);
    std::cout<<classicSearchSeedLo<<' '<<classicSearchSeedHi<<' '<<classicSearchUsed<<' '<<classicSearchResult<<' '
        <<classicSearchSeen<<' '<<bits(classicSearchTimer)<<' '<<classicSearchQueried;
    if(classicSearchQueried)std::cout<<' '<<classicSearchQueryX<<' '<<classicSearchQueryY<<' '<<classicSearchQueryLOS<<' '<<classicSearchQueryOwner<<' '<<count;
    std::cout<<' '<<classicSearchNotifyPending;
    if(classicSearchNotifyPending)std::cout<<' '<<uid<<' '<<uid<<" 528 0 0 0";
    for(int g=0;g<5;g++){int n=xsArrayGetInt(classicVisibleCounts,g);std::cout<<' '<<n;
        for(int i=0;i<n;i++){int at=g*256+i,d=xsArrayGetInt(classicVisibleDetails,at),p=xsArrayGetInt(classicVisiblePositions,at);
            std::cout<<' '<<xsArrayGetInt(classicVisibleIDs,at)<<' '<<d%256<<' '<<d/256<<' '<<p%256<<' '<<p/256;}}
    std::cout<<'\n';if(arrays.size()!=15)throw std::runtime_error("Search controller leaked arrays");
}}
'''
def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    proof=json.loads((ROOT.parent/'search-cache-validation.json').read_text());assert proof['passed']
    trace=ROOT.parent/'search-cache-cases.json';assert sha(trace)==proof['trace_sha256']
    for name,digest in proof['hashes'].items():assert sha(TOOLKIT/name)==digest
    table=ROOT.parent/'visible-scan-host/classic_visible_distance.xs'
    names=('classic_visible_membership.xs','classic_visible_scan.xs','classic_visible_pipeline.xs','classic_search_cache.xs')
    xs=table.read_text()+'\n'+'\n'.join((TOOLKIT/n).read_text() for n in names);(ROOT/'combined.xs').write_text(xs)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(ROOT/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    cpp=re.sub(r'for \((\w+) = ([^;]+); < ([^)]+)\)',lambda m:f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)',xs)
    (ROOT/'search.cpp').write_text(PREFIX+EXTRA+cpp+MAIN)
    (ROOT/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(search LANGUAGES CXX)\nadd_executable(search search.cpp)\ntarget_compile_features(search PRIVATE cxx_std_17)\ntarget_compile_options(search PRIVATE /fp:strict)\n')
    for args in ([CMAKE,'-S',str(ROOT),'-B',str(ROOT/'build')],[CMAKE,'--build',str(ROOT/'build'),'--config','Release']):
        run=subprocess.run(args,capture_output=True,text=True);assert run.returncode==0,run.stdout+run.stderr
    inputs=[];expected=[]
    for case in json.loads(trace.read_text()):
        s=case['input'];r=case['output']
        values=[s['used'],s['cached_total'],s['seen'],bits(s['timer']),s['seed']&65535,s['seed']>>16,
                bits(s['x']),bits(s['y']),s['allow'],s['actor'],s['owner'],bits(s['los']),
                bits(s['los'] if s['static_radius'] else s['search_radius']),int(s['desired']),s['count'],s['order'],s['follow_id'],
                int(s['world']),int(s['follow_found']),int(s['follow_action']),s['follow_owner'],bits(s['follow_x']),bits(s['follow_y']),bits(s['follow_los'])]
        inputs.append('S '+' '.join(map(str,values)))
        out=[r['seed']&65535,r['seed']>>16,r['used'],r['total'],r['seen'],r['timer_bits'],len(r['queries'])]
        out.extend(v for q in r['queries'] for v in q);out.append(len(r['notifications']));out.extend(v for q in r['notifications'] for v in q)
        for buf in r['buffers']:out.append(len(buf));out.extend(v for record in buf for v in record)
        expected.append(' '.join(map(str,out)))
    entry_trace=ROOT.parent/'search-update-cases.json';assert sha(entry_trace)==proof['update_trace_sha256']
    entries=json.loads(entry_trace.read_text())
    for entry in entries:
        inputs.append(f"U {bits(entry['timer'])} {bits(entry['elapsed'])} {entry['used']}")
        r=entry['output'];expected.append(f"U {r['used']} {r['total']} {r['timer_bits']} {r['seen']} {r['seed']&65535} {r['seed']>>16}")
    run=subprocess.run([str(ROOT/'build/Release/search.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    actual=run.stdout.splitlines();assert len(actual)==len(expected)
    for i,(a,b) in enumerate(zip(actual,expected)):assert a==b,(i,a[:250],b[:250])
    report=dict(passed=True,cases=len(expected)-len(entries),update_entry_cases=len(entries),source_proof_sha256=sha(ROOT.parent/'search-cache-validation.json'),
        hashes={n:sha(TOOLKIT/n) for n in (*names,'check_classic_search_cache_xs.py')},distance_table_sha256=sha(table),
        installed=False,full_behavior_parity=False,
        limitations=['Actor/follow state, source RNG seed and cache reset state are supplied, not natively observed.',
                     'Notification becomes a recorded intent; native reentrant event delivery remains unfinished.',
                     'Spatial floats must be finite and fit int32 after truncation. Native source RNG synchronization is unverified.'])
    (ROOT.parent/'search-cache-xs-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {len(expected)-len(entries)} XS searches / {len(entries)} update entries including cache, RNG, timer and result buffers')

if __name__=='__main__':main()
