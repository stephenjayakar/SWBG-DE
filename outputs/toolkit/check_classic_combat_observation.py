"""Validate layout/native-getter contracts and damage integration in an XS host.

Native getters are explicit mocks. This is not DE runtime verification.
"""
from pathlib import Path
import json
import re
import struct
import subprocess
from classic_combat_data import ROOT as DATA, read_units
from classic_combat_catalog import profile
from classic_damage_oracle import DamageOracle
from classic_damage_model import damage_capability
from classic_unit_identity import sha
from check_classic_air_planner import CMAKE, PREFIX
from check_classic_target_ranker import FLOAT_HOST
from check_classic_attack_dispatch_xs import EXTRA

ROOT = Path('work/classic-engine/combat-observation-host')
TOOLKIT = Path('outputs/toolkit')
HOST = r'''
#include <cstdint>
#include <cstring>
const int cHitpoints=0,cArmor=8,cAttack=9,cAttackReloadTime=10,cBaseArmor=15;
struct Unit {int civ,copy,base;float hp,reload;std::vector<std::pair<int,int>> weapons,armor;};
Unit attacker,target;int mode=0,queries=0;
bool xsDoesUnitExist(int uid) {return uid==41 ? mode!=3 : uid==42 && mode!=2;}
int xsGetUnitOwner(int uid) {return (uid==41?attacker:target).civ==0?0:uid-40;}
int xsGetPlayerCivilization(int owner) {return owner==1 ? (mode==4?99:attacker.civ) : target.civ;}
int xsGetUnitCopyId(int uid) {return mode==9&&uid==41 ? 999999 : (uid==41?attacker:target).copy;}
float xsGetUnitAttribute(int uid,int attr,int cls=-1) {
    if(!xsDoesUnitExist(uid))throw std::runtime_error("Queried absent unit");
    queries++;const auto &u=uid==41?attacker:target;
    if(attr==cBaseArmor) return mode==7?32768:u.base;
    if(attr==cHitpoints) return u.hp;
    if(attr==cAttackReloadTime) return mode==6?std::numeric_limits<float>::quiet_NaN():u.reload;
    if(attr!=cArmor&&attr!=cAttack)throw std::runtime_error("Unknown attribute");
    for(auto p:attr==cAttack?u.weapons:u.armor) if(p.first==cls) {
        if(mode==5&&uid==41&&attr==cAttack)return 1.5f;
        return p.second;
    }
    throw std::runtime_error("Queried an absent damage class");
}
float xsGetUnitHitpoints(int uid) {
    if(uid!=42||!xsDoesUnitExist(uid))throw std::runtime_error("Wrong HP query");
    queries++;return mode==8?-1:target.hp*.5f;
}
void readUnit(Unit &u) {
    int nw,na;std::cin>>u.civ>>u.copy>>u.base>>u.hp>>u.reload>>nw>>na;
    u.weapons.clear();u.armor.clear();
    for(auto pair:{std::pair<int,std::vector<std::pair<int,int>>*>{nw,&u.weapons},{na,&u.armor}})
        for(int i=0;i<pair.first;i++){int c,v;std::cin>>c>>v;pair.second->push_back({c,v});}
}
uint32_t bits(float v) {uint32_t result;std::memcpy(&result,&v,4);return result;}
'''
MAIN = r'''
int main() {
    // Ensure every supplied template decodes its exact ordered profile first.
    int metadataCount;std::cin>>metadataCount;
    for(int i=0;i<metadataCount;i++) {
        int civ,copy,n;std::cin>>civ>>copy>>n;int offset=classicCombatLayout(copy,civ);
        if(offset<0)throw std::runtime_error("Missing source layout");
        for(int j=0;j<n;j++){int want;std::cin>>want;if(xsArrayGetInt(classicCombatLayouts,offset+j)!=want)throw std::runtime_error("Wrong layout");}
    }
    if(classicCombatLayout(-1,1)!=-1||classicCombatLayout(448,99)!=-1||classicCombatLayout(999999,1)!=-1)
        throw std::runtime_error("Unknown layout accepted");
    while(std::cin>>mode) {
        readUnit(attacker);readUnit(target);queries=0;
        bool ok=classicCombatObserveDamage(41,42,1.25,1.0);
        float result=classicDamageCapability(classicCombatObservedTargetPresent,true,true);
        std::cout<<ok<<' '<<classicCombatObservationStatus<<' '<<classicCombatObservationReady<<' '
                 <<classicCombatObservedTargetPresent<<' '<<bits(result)<<' '
                 <<bits(classicCombatObservedReload)<<' '<<bits(classicCombatObservedTargetHP)<<' '
                 <<bits(classicCombatObservedTargetMaxHP)<<' '<<queries<<'\n';
        if(arrays.size()!=4)throw std::runtime_error("Leaked query arrays");
    }
}
'''


def bits(value): return struct.unpack('<I',struct.pack('<f',value))[0]


def upgraded(row,epoch):
    value=dict(row)
    # Deliberately change mocked live stats without changing catalog/template.
    # This checks fresh getter use; it is not a simulated research sequence.
    value['attacks']=[(c,max(-32768,min(32767,v+7*epoch))) for c,v in row['attacks']]
    value['armor']=[(c,max(-32768,min(32767,v+3*epoch))) for c,v in row['armor']]
    value['hp']=float(row['hp'])+100*epoch
    value['reload']=float(row['reload'])+0.25*epoch
    value['base_armor']=int(row['base_armor'])
    return value


def unit_input(row):
    values=[row[k] for k in ('civ','slot','base_armor','hp','reload')]
    values += [len(row['attacks']),len(row['armor'])]
    values += [v for p in row['attacks']+row['armor'] for v in p]
    return ' '.join(map(str,values))


def expected(a,b,mode,oracle,cache):
    af,bf=profile(a)[0],profile(b)[0]
    present=mode!=2
    status=0;queries=0
    if mode==3: status=1
    elif mode in (4,9): status=2
    elif af&5: status=3
    elif present and bf&10: status=3
    elif mode==7: status=4;queries=1
    else:
        queries=(1+len(b['armor'])) if present else 0
        if mode==5: status=4;queries+=1
        else:
            queries+=len(a['attacks'])+1
            if mode==6: status=4
            elif present:
                queries+=2
                if mode==8 or b['hp']<0: status=4
    if status: return [0,status,0,0,0,0,0,0,queries]
    args=(tuple(a['attacks']),tuple(b['armor']) if present else (),b['base_armor'] if present else 1000,1.25,1.0)
    key=(*args,present)
    if key not in cache:
        cache[key]=oracle.capability(*args,present,True,True)
        assert bits(cache[key])==bits(damage_capability(*args,present,True,True))
    return [1,0,1,int(present),bits(cache[key]),bits(a['reload']),
            bits(b['hp']*.5) if present else 0,bits(b['hp']) if present else 0,queries]


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((DATA/'catalog-manifest.json').read_text())
    assert manifest['audit_sha256']==sha(DATA/'audit.json')
    assert manifest['generator_sha256']==sha(TOOLKIT/'classic_combat_catalog.py')
    assert manifest['xs_sha256']==sha(DATA/'classic_combat_catalog.xs')
    names=('classic_target_ranker.xs','classic_target_scorer.xs','classic_damage_calculator.xs','classic_combat_observation.xs')
    text=(DATA/'classic_combat_catalog.xs').read_text()+'\n'+'\n'.join((TOOLKIT/n).read_text() for n in names)
    (ROOT/'combined.xs').write_text(text)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(ROOT/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    text=re.sub(r'for \((\w+) = ([^;]+); < ([^)]+)\)',lambda m:f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)',text)
    prefix=PREFIX.replace('std::vector<vector>>;','std::vector<vector>, std::vector<float>>;')
    (ROOT/'observation.cpp').write_text(prefix+FLOAT_HOST+EXTRA+HOST+text+MAIN)
    (ROOT/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(observation LANGUAGES CXX)\nadd_executable(observation observation.cpp)\ntarget_compile_features(observation PRIVATE cxx_std_17)\ntarget_compile_options(observation PRIVATE /fp:strict)\n')
    for args in ([CMAKE,'-S',str(ROOT),'-B',str(ROOT/'build')],[CMAKE,'--build',str(ROOT/'build'),'--config','Release']):
        run=subprocess.run(args,capture_output=True,text=True);assert run.returncode==0,run.stdout+run.stderr
    rows=read_units(DATA/'source-combat.tsv'); records=list(rows.values())
    fixtures=[]
    for i,row in enumerate(records):
        for epoch in (0,1): fixtures.append((upgraded(row,epoch),upgraded(records[(i*17+31)%len(records)],epoch),0))
        fixtures.append((upgraded(row,0),upgraded(row,0),2))
    regular=next(r for r in records if r['civ']=='1' and profile(r)[0]==0 and r['attacks'] and r['armor'])
    for epoch in (0,1):
        for mode in range(2,10): fixtures.append((upgraded(regular,epoch),upgraded(regular,epoch),mode))
    inputs=[str(len(rows))]
    for (c,uid),row in rows.items():
        p=profile(row);inputs.append(' '.join(map(str,[c,uid,len(p),*p])))
    wants=[];oracle=DamageOracle();cache={}
    for a,b,mode in fixtures:
        inputs.append(str(mode)+' '+unit_input(a)+' '+unit_input(b))
        wants.append(expected(a,b,mode,oracle,cache))
    run=subprocess.run([str(ROOT/'build/Release/observation.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    actual=[list(map(int,line.split())) for line in run.stdout.splitlines()]
    assert len(actual)==len(wants)
    for i,(got,want) in enumerate(zip(actual,wants)): assert got==want,(i,fixtures[i],got,want)
    report=dict(passed=True,metadata_records=len(rows),query_cases=len(fixtures),source_damage_cases=len(cache),
                catalog_manifest_sha256=sha(DATA/'catalog-manifest.json'),
                hashes={n:sha(TOOLKIT/n) for n in (*names,'check_classic_combat_observation.py')},
                installed=False,full_behavior_parity=False,
                limitations=['Mocked native getters, not DE runtime execution.',
                             'Fresh values are read only for supplied units; visibility admission remains the caller responsibility.',
                             'Duplicate/negative relevant table classes return status 3 instead of an estimate.',
                             'Dynamic modifier, eligibility, commands and native class membership still require integration.'])
    (ROOT.parent/'combat-observation-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {len(rows)} layouts / {len(fixtures)} query cases / {len(cache)} source damage comparisons')


if __name__=='__main__': main()
