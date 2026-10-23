"""Compose native-getter contracts, source identity, damage and combat estimates."""
from pathlib import Path
from collections import Counter
import json,random,re,struct,subprocess
from classic_combat_catalog import profile
from classic_combat_data import ROOT as DATA,read_units
from classic_combat_model import Combatant
from classic_combat_oracle import CombatOracle
from classic_target_model import Target
from classic_target_oracle import TargetOracle
from classic_damage_oracle import DamageOracle
from classic_unit_identity import sha
from check_classic_combat_estimator import bits
from check_classic_combat_observation import upgraded,unit_input
from check_classic_air_planner import CMAKE,PREFIX
from check_classic_target_ranker import FLOAT_HOST
from check_classic_attack_dispatch_xs import EXTRA
from classic_unit_ai_factory import unit_ai_type

ROOT=Path('work/classic-engine/combat-live-host')
TOOLKIT=Path('outputs/toolkit')
HOST=r'''
#include <cstring>
#include <cstdint>
const int cHitpoints=0,cArmor=8,cAttack=9,cAttackReloadTime=10,cBaseArmor=15;
struct Unit {int civ,copy,base,raw;float hp,reload;bool exists;std::vector<std::pair<int,int>> weapons,armor;};
std::map<int,Unit> objects;int mode=0,queries=0;
bool xsDoesUnitExist(int uid) {return objects.count(uid)&&objects.at(uid).exists;}
int xsGetUnitOwner(int uid) {return objects.at(uid).civ==99?3:objects.at(uid).civ;}
int xsGetPlayerCivilization(int owner) {return owner==3?99:owner;}
int xsGetUnitCopyId(int uid) {return objects.at(uid).copy;}
int xsGetUnitObjectId(int uid) {return objects.at(uid).raw;}
float xsGetUnitAttribute(int uid,int attr,int cls=-1) {
    if(!xsDoesUnitExist(uid))throw std::runtime_error("Attribute query for missing unit");
    queries++;const auto &u=objects.at(uid);
    if(attr==cBaseArmor)return u.base;
    if(attr==cHitpoints)return u.hp;
    if(attr==cAttackReloadTime)return u.reload;
    if(attr!=cArmor&&attr!=cAttack)throw std::runtime_error("Wrong attribute");
    for(auto p:attr==cAttack?u.weapons:u.armor)if(p.first==cls) {
        if(mode==5&&uid==1&&attr==cAttack)return 1.5f;
        return p.second;
    }
    throw std::runtime_error("Absent damage class queried");
}
float xsGetUnitHitpoints(int uid) {
    if(!xsDoesUnitExist(uid))throw std::runtime_error("HP query for missing unit");
    queries++;return objects.at(uid).hp*.5f;
}
void readUnit(int uid) {
    Unit u;int nw,na,exists;
    std::cin>>exists>>u.civ>>u.copy>>u.base>>u.hp>>u.reload>>nw>>na;u.exists=exists!=0;
    for(auto pair:{std::pair<int,std::vector<std::pair<int,int>>*>{nw,&u.weapons},{na,&u.armor}})
        for(int i=0;i<pair.first;i++){int c,v;std::cin>>c>>v;pair.second->push_back({c,v});}
    std::cin>>u.raw;objects[uid]=u;
}
void output(float value) {if(std::isnan(value))std::cout<<" nan";else {uint32_t b;std::memcpy(&b,&value,4);std::cout<<' '<<b;}}
'''
MAIN=r'''
int main() {
    int members=xsArrayCreateInt(40,-1,"members"),enemies=xsArrayCreateInt(128,-1,"enemies");
    classicScoreReset();
    int n,ne,targetId,candidate=0;
    while(std::cin>>n>>ne>>mode>>targetId) {
        objects.clear();queries=0;
        for(int i=0;i<n;i++){readUnit(i+1);xsArraySetInt(members,i,i+1);}
        for(int i=0;i<ne;i++){readUnit(i+101);xsArraySetInt(enemies,i,i+101);}
        readUnit(targetId);
        std::vector<std::pair<int,int>> flags(n*(ne+1));
        for(auto &f:flags)std::cin>>f.first>>f.second;
        int priorScores=classicTargetCount;
        bool ok=classicLiveCombatBegin(members,n,targetId,enemies,ne);
        if(ok) {
            if(classicLiveCombatBegin(members,n,targetId,enemies,ne)||classicLiveCombatFinish()||classicLiveCombatScore())throw std::runtime_error("Busy/unfinished candidate accepted");
            if(classicLiveCombatOutgoing(0,99999,true,false))throw std::runtime_error("Wrong pair accepted");
            if(mode==1)objects.at(1).exists=false;
            if(mode==2)objects.at(targetId).exists=false;
            if(mode==4&&ne)objects.at(101).civ=99;
            if(mode==6)for(int i=0;i<ne;i++)xsArraySetInt(enemies,i,99999);
        }
        int cursor=0;
        for(int i=0;i<n;i++) {
            auto f=flags[cursor++];
            if(ok)ok=classicLiveCombatOutgoing(i,i+1,f.first!=0,f.second!=0,1.25,1.0);
        }
        for(int i=0;i<n;i++)for(int j=0;j<ne;j++) {
            auto f=flags[cursor++];
            if(ok) {
                if(classicLiveCombatIncoming(i,j,99999))throw std::runtime_error("Wrong enemy accepted");
                ok=classicLiveCombatIncoming(i,j,j+101,f.first!=0,f.second!=0,1.25,1.0);
            }
        }
        if(ok)ok=classicLiveCombatFinish();
        if(ok) {
            if(!classicLiveCombatComplete||classicLiveCombatBusy||classicLiveCombatFinish())throw std::runtime_error("Invalid completed state");
            std::cout<<"P";output(classicCombatTTK);output(classicCombatTTBK);std::cout<<'\n';
            if(!classicLiveCombatScore(10.0f+candidate,candidate%2==0,mode==7,false,mode==8)||classicLiveCombatScore()
               ||classicTargetCount!=priorScores+1)throw std::runtime_error("Score submission failed/repeated");
        } else {
            if(classicLiveCombatBusy||classicLiveCombatComplete||classicCombatCount!=0||classicCombatObservationReady)
                throw std::runtime_error("Failed candidate retained partial state");
            std::cout<<"F "<<classicLiveCombatError<<'\n';
            if(classicLiveCombatScore()||classicTargetCount!=priorScores)throw std::runtime_error("Failed candidate entered scores");
        }
        candidate++;
        if(arrays.size()>26)throw std::runtime_error("Live controller leaked arrays");
    }
    for(int repeat=0;repeat<2;repeat++) {
        classicScoreEvaluate();std::cout<<"R "<<classicTargetCount;
        for(int i=0;i<classicTargetCount;i++) {
            if(xsArrayGetBool(classicTargetUnordered,i))std::cout<<" nan";
            else output(xsArrayGetFloat(classicTargetScores,i));
        }
        std::cout<<' '<<classicTargetOrderedCount;
        for(int i=0;i<classicTargetOrderedCount;i++)std::cout<<' '<<xsArrayGetInt(classicTargetOrder,i);
        std::cout<<'\n';
    }
}
'''


def fixtures():
    import csv
    identity={(int(r['civ']),int(r['slot'])):r for r in csv.DictReader(Path('work/classic-engine/unit-identity.tsv').open(),delimiter='\t')}
    rows=read_units(DATA/'source-combat.tsv')
    def ai(row):
        item=identity[int(row['civ']),int(row['slot'])]
        return unit_ai_type(int(row['class']),int(item['source_volley_missile'])) if row['type'] in ('70','80') else -1
    candidates=[r for r in rows.values() if r['civ'] in ('1','2') and float(r['hp'])>0 and profile(r)[0]==0]
    military=[r for r in candidates if ai(r)>=0 and r['attacks']]
    noai=[r for r in candidates if ai(r)<0]
    rng=random.Random(59243020260916)
    for case in range(36):
        n=(1,2,5,40)[case%4]; ne=(0,1,3,8,41,128)[case%6]
        own=[upgraded(rng.choice(military),case%2) for _ in range(n)]
        enemy=[upgraded(rng.choice(noai if i%7==0 else military),case%2) for i in range(ne)]
        target=upgraded(rng.choice(candidates),case%2)
        for i,r in enumerate(own):r['exists']=i%13!=12;r['ai']=ai(r)
        for i,r in enumerate(enemy):r['exists']=i%11!=10;r['ai']=ai(r)
        target['exists']=True;target['ai']=ai(target)
        flags=[(bool(rng.randrange(2)),r['ai']==6) for r in own]
        flags += [(bool(rng.randrange(2)),e['ai']==6) for r in own for e in enemy]
        yield own,enemy,target,flags,0,0
    ordinary=next(r for r in military if r['attacks'] and r['armor'])
    for mode in (1,2,4,5,6):
        a,b,t=(upgraded(ordinary,0) for _ in range(3))
        for r in (a,b,t):r['exists']=True;r['ai']=ai(r)
        yield [a],[b],t,[(True,False),(True,False)],mode,{1:3,2:2,4:6,5:3,6:0}[mode]
    a=upgraded(next(r for r in noai if not r['attacks']),0)
    t=upgraded(ordinary,0)
    for r in (a,t):r['exists']=True;r['ai']=ai(r)
    yield [a],[],t,[(False,False)],0,5
    # Actual source priest with a permitted conversion and no attack damage.
    p=upgraded(next(r for r in candidates if ai(r)==6),0)
    p['exists']=True;p['ai']=6
    yield [p],[p],t,[(False,True),(False,True)],0,0
    # Missing army members retain their slots but do not contribute.
    gone=upgraded(ordinary,0);gone['exists']=False;gone['ai']=ai(gone)
    yield [gone],[],t,[(True,False)],0,0
    yield [gone],[p],t,[(True,False),(True,False)],0,0
    # Positive raw strength avoids the source's missing-own-UnitAI precondition.
    raw=upgraded(next(r for r in noai if sum(max(0,v) for _,v in r['attacks'])>0),0)
    raw['exists']=True;raw['ai']=-1
    yield [raw],[],t,[(False,False)],0,0
    ambiguous=upgraded(next(r for r in rows.values() if r['civ']=='1' and float(r['hp'])>0 and profile(r)[0]&5),0)
    ambiguous['exists']=True;ambiguous['ai']=ai(ambiguous)
    yield [ambiguous],[],t,[(True,False)],0,3
    invalid=upgraded(ordinary,0);invalid['exists']=True;invalid['ai']=ai(invalid);invalid['hp']=-1
    yield [invalid],[],t,[(True,False)],0,3
    yield [p],[],invalid,[(True,False)],0,3
    unknown=upgraded(ordinary,0);unknown['exists']=True;unknown['ai']=0;unknown['civ']='99'
    yield [p],[],unknown,[(True,False)],0,6
    # Actual temple upgrades retain raw 104, and keep relic-victory priority.
    # Reverse raw/copy pairs check that neither getter can silently substitute.
    for civ in (1,2):
        for raw,copy in ((104,30),(104,31),(30,104),(31,104)):
            upgraded_target=upgraded(rows[civ,copy],0)
            upgraded_target.update(exists=True,ai=ai(upgraded_target),raw=raw)
            yield [p],[],upgraded_target,[(False,True)],7,0
        # Wonder priority likewise keys off the retained raw ID.
        for raw,copy in ((276,30),(30,276)):
            upgraded_target=upgraded(rows[civ,copy],0)
            upgraded_target.update(exists=True,ai=ai(upgraded_target),raw=raw)
            yield [p],[],upgraded_target,[(False,True)],8,0
        # Real economic-building upgrades preserve the source ranking category.
        for raw,copy in ((70,463),(463,70),(68,129),(129,68)):
            upgraded_target=upgraded(rows[civ,copy],0)
            upgraded_target.update(exists=True,ai=ai(upgraded_target),raw=raw)
            yield [p],[],upgraded_target,[(False,True)],0,0


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    generated=(Path('work/classic-engine/classic_unit_identity.xs'),DATA/'classic_combat_catalog.xs')
    names=('classic_target_ranker.xs','classic_target_scorer.xs','classic_damage_calculator.xs','classic_combat_estimator.xs',
           'classic_combat_observation.xs','classic_combat_live.xs')
    text='\n'.join(p.read_text() for p in generated)+'\n'+'\n'.join((TOOLKIT/n).read_text() for n in names)
    (ROOT/'combined.xs').write_text(text)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(ROOT/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    text=re.sub(r'for \((\w+) = ([^;]+); < ([^)]+)\)',lambda m:f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)',text)
    prefix=PREFIX.replace('std::vector<vector>>;','std::vector<vector>, std::vector<float>>;')
    (ROOT/'live.cpp').write_text(prefix+FLOAT_HOST+EXTRA+HOST+text+MAIN)
    (ROOT/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(live LANGUAGES CXX)\nadd_executable(live live.cpp)\ntarget_compile_features(live PRIVATE cxx_std_17)\ntarget_compile_options(live PRIVATE /fp:strict)\n')
    for args in ([CMAKE,'-S',str(ROOT),'-B',str(ROOT/'build')],[CMAKE,'--build',str(ROOT/'build'),'--config','Release']):
        run=subprocess.run(args,capture_output=True,text=True);assert run.returncode==0,run.stdout+run.stderr
    armor=DamageOracle();combat=CombatOracle();cache={};inputs=[];expected=[];failures=Counter();valid=0;scored=[]
    for index,(own,enemy,target,flags,mode,error) in enumerate(fixtures()):
        target_id=500+index
        inputs.append(f'{len(own)} {len(enemy)} {mode} {target_id}')
        for r in [*own,*enemy,target]:inputs.append(str(int(r['exists']))+' '+unit_input(r)+' '+str(r.get('raw',r['slot'])))
        inputs.append(' '.join(str(int(v)) for p in flags for v in p))
        if error:expected.append(f'F {error}');failures[str(error)]+=1;continue
        records={i+1:r for i,r in enumerate(own)}|{i+101:r for i,r in enumerate(enemy)}|{target_id:target}
        damage,convert={},{};cursor=0
        pairs=[(i+1,target_id) for i in range(len(own))]+[(j+101,i+1) for i in range(len(own)) for j in range(len(enemy))]
        for (a,b),flag in zip(pairs,flags):
            actor,victim=records[a],records[b];eligible,conversion=flag
            key=(tuple(actor['attacks']),tuple(victim['armor']),victim['base_armor'],1.25,1.0,True,actor['ai']>=0,eligible)
            if key not in cache:cache[key]=armor.capability(*key)
            damage[a,b]=cache[key];convert[a,b]=conversion
        def unit(uid,r):return Combatant(uid,r['hp']*.5,r['reload'],r['exists'],r['ai']>=0)
        result=combat.estimate([unit(i+1,r) for i,r in enumerate(own)],
                               [unit(i+101,r) for i,r in enumerate(enemy)],unit(target_id,target),damage,convert)
        expected.append('P '+bits(result[0])+' '+bits(result[1]));valid+=1
        scored.append(Target(target_id,int(target['class']),int(target.get('raw',target['slot'])),result[0],result[1],10.0+index,
                             same_zone=index%2==0,enemy_relic_countdown=mode==7,enemy_wonder_countdown=mode==8))
    scores,order=TargetOracle().evaluate(scored)
    ranked=' '.join(['R',str(len(scored)),*[bits(s) for s in scores],str(len(order)),*[str(scored[i].uid) for i in order]])
    expected.extend([ranked,ranked])
    run=subprocess.run([str(ROOT/'build/Release/live.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    actual=run.stdout.splitlines();assert len(actual)==len(expected),(len(actual),len(expected))
    for i,(got,want) in enumerate(zip(actual,expected)):assert got==want,(i,got,want)
    report=dict(passed=True,candidate_cases=len(expected)-2,source_estimate_cases=valid,source_damage_cases=len(cache),rank_evaluations=2,
                failure_cases=dict(failures),hashes={n:sha(TOOLKIT/n) for n in (*names,'check_classic_combat_live.py')},
                generated_hashes={str(p):sha(p) for p in generated},installed=False,full_behavior_parity=False,
                limitations=['Native getters are mocked; eligibility/modifiers remain caller-supplied.',
                             'Caller must perform the full candidate pass synchronously; no inter-frame consistency claim.',
                             'Source AI behavior, native engine getter semantics and command delivery remain unfinished.'])
    (ROOT.parent/'combat-live-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {len(expected)-2} candidate evaluations / {valid} source estimates / {len(cache)} source damage queries / 2 ranking passes')


if __name__=='__main__':main()
