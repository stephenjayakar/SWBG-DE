"""Compose source rank/research observations with original conversion decisions."""
from pathlib import Path
import csv,itertools,json,re,struct,subprocess
from classic_conversion_eligibility import Conversion
from classic_conversion_eligibility_oracle import ConversionEligibilityOracle
from classic_unit_identity import sha,packed
from check_classic_air_planner import CMAKE,PREFIX

ROOT=Path('work/classic-engine/conversion-observation-host')
TOOLKIT=Path('outputs/toolkit')
HOST=r'''
#include <cstring>
#include <cstdint>
struct Unit {int raw,copy,owner;bool exists;};
Unit units[2];int civilizations[4]={0,1,2,99};float r67,r27,r87;
bool xsDoesUnitExist(int uid){return uid>=0&&uid<2&&units[uid].exists;}
Unit get(int uid){if(!xsDoesUnitExist(uid))throw std::runtime_error("Missing unit queried");return units[uid];}
int xsGetUnitOwner(int uid){return get(uid).owner;}
int xsGetUnitObjectId(int uid){return get(uid).raw;}
int xsGetUnitCopyId(int uid){return get(uid).copy;}
int xsGetPlayerCivilization(int owner){return civilizations[owner];}
float xsPlayerAttribute(int owner,int resource){
    if(owner!=units[0].owner)throw std::runtime_error("Wrong research player");
    if(resource==67)return r67;if(resource==27)return r27;if(resource==2087)return r87;if(resource==2031)return 0;
    throw std::runtime_error("Unmapped resource");
}
float frombits(uint32_t b){float v;std::memcpy(&v,&b,4);return v;}
'''
MAIN=r'''
int main(){int a,b,ignore,immune;uint32_t force,x,y,z;
while(std::cin>>units[0].raw>>units[0].copy>>units[0].owner>>a
              >>units[1].raw>>units[1].copy>>units[1].owner>>b>>force>>ignore>>immune>>x>>y>>z){
    units[0].exists=a;units[1].exists=b;r67=frombits(x);r27=frombits(y);r87=frombits(z);
    bool ok=classicObserveConversion(0,1,frombits(force),ignore,immune);
    std::cout<<ok<<' '<<classicConversionObservationReady<<' '<<classicConversionObservedAllowed<<'\n';
    if(arrays.size()>2)throw std::runtime_error("Observation leaked arrays");
}}
'''

def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]

def fixtures(rows):
    # Full installed source identity domain; deterministic rank/research variants.
    actors=((180,115),(180,180),(115,115),(1077,180),(1075,115))
    for index,((civ,uid),r) in enumerate(rows.items()):
        actor=(*actors[index%len(actors)],1,True)
        resources=((1.,1.,1.),(0.,1.,1.),(1.,0.,1.),(1.,1.,0.))[index%4]
        yield actor,(uid,uid,civ,True),(99.,100.,101.)[index%3],index%7==0,index%2,*resources
    # Independent raw/copy fields on real command-center and temple upgrades.
    for raw,copy,force,ignore,immune,r67,r27,r87 in itertools.product(
        (109,104),(71,30),(0.,100.),(False,True),(0,1),(0.,1.),(0.,1.),(0.,1.)):
        yield (180,115,1,True),(raw,copy,2,True),force,ignore,immune,r67,r27,r87
    # Missing objects, unknown source IDs/factions, and non-converter dispatch.
    for actor,target in itertools.product(
        ((180,115,1,True),(180,115,1,False),(-1,115,1,True),(180,99999,1,True),
         (180,115,3,True),(109,109,1,True)),
        ((4,4,2,True),(4,4,2,False),(99999,4,2,True),(4,99999,2,True),(4,4,3,True))):
        yield actor,target,100.,False,0,1.,1.,1.
    for force in (-1.,0.,100.,float('nan'),float('inf')):
        for r67,r27,r87 in itertools.product((float('nan'),0.,1.),repeat=3):
            yield (180,115,1,True),(115,115,2,True),force,False,0,r67,r27,r87

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    table=ROOT.parent/'unit-identity.tsv'
    rows={(int(r['civ']),int(r['slot'])):r for r in csv.DictReader(table.open(),delimiter='\t')}
    def lookup(owner,uid):return rows.get((owner,uid),rows.get((0,uid))) if owner in (0,1,2) else None
    identity=ROOT.parent/'classic_unit_identity.xs'
    names=('classic_unit_ai_factory.xs','classic_conversion_eligibility.xs','classic_force_rank.xs','classic_conversion_observation.xs')
    xs=identity.read_text()+'\n'+'\n'.join((TOOLKIT/n).read_text() for n in names)
    (ROOT/'combined.xs').write_text(xs)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(ROOT/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    (ROOT/'observe.cpp').write_text(PREFIX+HOST+xs+MAIN)
    (ROOT/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(observe LANGUAGES CXX)\nadd_executable(observe observe.cpp)\ntarget_compile_features(observe PRIVATE cxx_std_17)\ntarget_compile_options(observe PRIVATE /fp:strict)\n')
    for args in ([CMAKE,'-S',str(ROOT),'-B',str(ROOT/'build')],[CMAKE,'--build',str(ROOT/'build'),'--config','Release']):
        run=subprocess.run(args,capture_output=True,text=True);assert run.returncode==0,run.stdout+run.stderr
    oracle=ConversionEligibilityOracle();inputs=[];expected=[];source_cases=0;allowed=0;incomplete=0
    for actor,target,force,ignore,immune,r67,r27,r87 in fixtures(rows):
        raw,copy,owner,exists=actor;traw,tcopy,towner,texists=target
        ar,ac=lookup(owner,raw),lookup(owner,copy);tr,tc=lookup(towner,traw),lookup(towner,tcopy)
        ok=exists and ar is not None and ac is not None;answer=False
        converter=ok and (packed(ac)//33554432%16-1)==6
        if converter and texists and (tr is None or tc is None):ok=False
        if ok and converter:
            s=Conversion(attacker_class=int(ar['source_class']),force=force,ignore_force=ignore,
                target_exists=texists,target_owner=towner,target_class=int(tr['source_class']) if tr else 7,
                target_id=traw if texists else 4,target_type=int(tc['source_type']) if tc else 70,
                unconvertible=immune,resource67=r67,resource27=r27,resource87=r87)
            answer=oracle.conversion(s,source_ids=(raw,copy));source_cases+=1
        allowed+=answer;incomplete+=not ok
        inputs.append(' '.join(map(str,[raw,copy,owner,int(exists),traw,tcopy,towner,int(texists),bits(force),int(ignore),immune,
                                       bits(r67),bits(r27),bits(r87)])))
        expected.append(f'{int(ok)} {int(ok)} {int(answer)}')
    run=subprocess.run([str(ROOT/'build/Release/observe.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    actual=run.stdout.splitlines();assert len(actual)==len(expected),(len(actual),len(expected))
    for i,(a,b) in enumerate(zip(actual,expected)):assert a==b,(i,inputs[i],a,b)
    report=dict(passed=True,cases=len(expected),source_conversion_with_real_rank_calls=source_cases,allowed=allowed,incomplete=incomplete,
        hashes={n:sha(TOOLKIT/n) for n in (*names,'check_classic_conversion_observation.py','classic_conversion_eligibility_oracle.py')},
        identity_sha256=sha(identity),installed=False,full_behavior_parity=False,
        limitations=['Native getters are mocked; original Force amount and immunity are caller supplied.',
                     'Source lookup/world state is a fixture; original rank functions execute inside original conversion gate.',
                     'Conversion timing/chance, native orders and live UnitAI persistence remain unfinished.'])
    (ROOT.parent/'conversion-observation-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {len(expected)} observation cases / {source_cases} source conversion+rank calls / {allowed} allowed / {incomplete} incomplete')

if __name__=='__main__':main()
