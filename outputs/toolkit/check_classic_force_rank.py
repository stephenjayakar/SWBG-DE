"""Check raw/copy rank predicates and native research getter contracts."""
from pathlib import Path
import csv,itertools,json,re,struct,subprocess
from classic_force_rank import ranks,PADAWAN_COPY,PADAWAN_RAW,MASTER_COPY,MASTER_RAW
from classic_force_rank_oracle import ForceRankOracle
from classic_unit_identity import sha
from classic_engine_oracle import SOURCE_SHA
from check_classic_air_planner import CMAKE,PREFIX

ROOT=Path('work/classic-engine/force-rank-host');TOOLKIT=Path('outputs/toolkit')
HOST=r'''
#include <cstring>
#include <cstdint>
int raw=-1,copy=-1,civ=0,owner=0,calls=0;bool exists=false;
float r67=0,r27=0,r87=0,r31=0;
bool xsDoesUnitExist(int unit) {return unit==42&&exists;}
int xsGetUnitOwner(int unit) {if(unit!=42||!exists)throw std::runtime_error("Wrong owner query");return owner;}
int xsGetUnitObjectId(int unit) {if(unit!=42||!exists)throw std::runtime_error("Wrong raw ID query");return raw;}
int xsGetUnitCopyId(int unit) {if(unit!=42||!exists)throw std::runtime_error("Wrong copy ID query");return copy;}
int xsGetPlayerCivilization(int player) {if(player!=owner)throw std::runtime_error("Wrong civilization query");return civ;}
float xsPlayerAttribute(int player,int resource) {
    if(player!=owner)throw std::runtime_error("Wrong resource owner");calls++;
    if(resource==67)return r67;if(resource==27)return r27;if(resource==2087)return r87;if(resource==2031)return r31;
    throw std::runtime_error("Unmapped source resource");
}
float frombits(uint32_t b){float v;std::memcpy(&v,&b,4);return v;}
uint32_t bits(float v){uint32_t b;std::memcpy(&b,&v,4);return b;}
'''
MAIN=r'''
int main(){char kind;while(std::cin>>kind>>raw>>copy){
    if(kind=='R'){std::cout<<classicForcePadawan(raw,copy)<<' '<<classicForceMaster(raw,copy)<<'\n';continue;}
    int present;uint32_t a,b,c,d;std::cin>>civ>>present>>a>>b>>c>>d;
    exists=present!=0;owner=civ==0?0:7;r67=frombits(a);r27=frombits(b);r87=frombits(c);r31=frombits(d);calls=0;
    classicConvertSetPermissions(true,1,1,1);
    bool ok=classicForceObservePermissions(42);
    std::cout<<ok<<' '<<classicForceRankReady<<' '<<classicForceObservedPadawan<<' '<<classicForceObservedMaster<<' '
             <<classicConvertEnabled<<' '<<classicConvertForceUsers<<' '<<classicConvertMechanical<<' '
             <<classicForceObservedOwner<<' '<<classicForceObservedSourceID<<' '<<classicForceObservedCopyID<<' '
             <<bits(classicForceObservedAirResearch)<<' '<<calls<<'\n';
    if(arrays.size()>2)throw std::runtime_error("Rank adapter leaked arrays");
}}
'''

def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]

def resources():
    root=ROOT.parent
    mapping={27:27,31:2031,67:67,87:2087}
    def read(name):return list(csv.DictReader((root/name).open(),delimiter='\t'))
    before={(int(r['civ']),int(r['id'])):float(r['value']) for r in read('force-source/resources.tsv')}
    after={(int(r['civ']),int(r['id'])):float(r['value']) for r in read('force-current/resources.tsv')}
    for c in range(3):
        for old,new in mapping.items():assert before[(3 if c==2 else c),old]==after[c,new]
    def effects(name,convert):
        result={}
        for r in read(name):
            a=int(r['a'])
            if r['type'] not in ('1','6') or a not in convert:continue
            key=int(r['effect']);result.setdefault(key,[]).append((r['type'],convert[a],r['b'],r['c'],r['d']))
        return result
    source=effects('force-source/effects.tsv',mapping)
    current=effects('force-current/effects.tsv',{v:v for v in mapping.values()})
    assert source==current
    return dict(initial_values=12,effect_commands=sum(map(len,source.values())),mapping=mapping,
                hashes={str(p):sha(p) for name in ('force-source','force-current') for p in ((root/name/'resources.tsv'),(root/name/'effects.tsv'))})

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    resource_evidence=resources()
    identity=ROOT.parent/'classic_unit_identity.xs'
    names=('classic_conversion_eligibility.xs','classic_force_rank.xs')
    text=identity.read_text()+'\n'+'\n'.join((TOOLKIT/n).read_text() for n in names)
    (ROOT/'combined.xs').write_text(text)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(ROOT/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    (ROOT/'rank.cpp').write_text(PREFIX+HOST+text+MAIN)
    (ROOT/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(rank LANGUAGES CXX)\nadd_executable(rank rank.cpp)\ntarget_compile_features(rank PRIVATE cxx_std_17)\n')
    for args in ([CMAKE,'-S',str(ROOT),'-B',str(ROOT/'build')],[CMAKE,'--build',str(ROOT/'build'),'--config','Release']):
        run=subprocess.run(args,capture_output=True,text=True);assert run.returncode==0,run.stdout+run.stderr
    oracle=ForceRankOracle();inputs=[];expected=[]
    ids=PADAWAN_COPY|PADAWAN_RAW|MASTER_COPY|MASTER_RAW
    cases={(v,-1) for v in range(-32768,32768)}|{(-1,v) for v in range(-32768,32768)}|set(itertools.product(ids,repeat=2))
    for raw,copy in sorted(cases):
        answer=oracle.ranks(raw,copy);assert answer==ranks(raw,copy),(raw,copy,answer)
        inputs.append(f'R {raw} {copy}');expected.append(' '.join(str(int(v)) for v in answer))
    copy_cases=[]
    for before,source in (((180,180,180,50),(115,115,115,50)),((104,104,104,18),(276,276,276,8)),
                          ((123,500,7,34),(999,180,9,35)),((1077,180,41,50),(180,115,77,51))):
        old,new=oracle.copy_identity(before,source)
        assert old==(before[0],source[1],before[2],before[3]) and new==(source[0],source[1],before[0],source[3]),(old,new)
        copy_cases.append(dict(before=before,source=source,after=old,source_after=new))
    known={int(r['slot']) for r in csv.DictReader((ROOT.parent/'unit-identity.tsv').open(),delimiter='\t') if r['civ']=='0'}
    native=0
    values=list(itertools.product((-1.0,0.0,1.0),repeat=3))+[(float('nan'),1.0,1.0),(1.0,float('nan'),float('inf'))]
    for raw,copy in ((0,0),(180,115),(115,180),(1075,115),(1077,180),(99999,115),(115,99999),(-1,115),(115,-1)):
        for civ,present,(r67,r27,r87) in itertools.product((0,1,2,99),(False,True),values):
            r31=1.5
            inputs.append(' '.join(map(str,['N',raw,copy,civ,int(present),bits(r67),bits(r27),bits(r87),bits(r31)])))
            ok=present and civ in (0,1,2) and raw in known and copy in known
            if ok:
                padawan,master=ranks(raw,copy)
                result=[1,1,padawan,master,r67>0,master and r27>0,master and r87>0,0 if civ==0 else 7,raw,copy,bits(r31),4]
            else:result=[0,0,0,0,0,0,0,-1,-1,-1,0,0]
            expected.append(' '.join(str(int(v)) for v in result));native+=1
    run=subprocess.run([str(ROOT/'build/Release/rank.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    actual=run.stdout.splitlines();assert len(actual)==len(expected)
    for i,(got,want) in enumerate(zip(actual,expected)):assert got==want,(i,inputs[i],got,want)
    report=dict(passed=True,source_rank_pairs=len(cases),source_rank_calls=2*len(cases),native_contract_cases=native,
                source_sha256=SOURCE_SHA,copy_identity_probes=copy_cases,resources=resource_evidence,
                hashes={n:sha(TOOLKIT/n) for n in (*names,'classic_force_rank.py','classic_force_rank_oracle.py','check_classic_force_rank.py')},
                identity_sha256=sha(identity),installed=False,full_behavior_parity=False,
                limitations=['Native getters mocked; object/copy ID behavior after DE upgrades unverified.',
                             'Master copy probes use empty dynamic lists and a stub for empty-name copying.',
                             'Player notifications, transforms, source UnitAI persistence and conversion execution remain open.'])
    (ROOT.parent/'force-rank-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {len(cases)} source rank pairs / {native} native contracts / 4 identity-copy probes')

if __name__=='__main__':main()
