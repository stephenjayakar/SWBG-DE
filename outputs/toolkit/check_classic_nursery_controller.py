"""Execute the XS nursery decisions in a mock C++ host; DE commands stay pending."""
from pathlib import Path
import hashlib,json,random,re,subprocess
from check_classic_air_planner import CMAKE,PREFIX
from classic_nursery_model import nearest_building,nursery_decision
from classic_nursery_bridge import PER
from classic_ai_source import parse

WORK=Path('work/classic-engine/nursery-host')
TOOLKIT=Path('outputs/toolkit')
HOST=r'''
#include <map>
struct Unit { int id,owner,copy,type,finished,holder,action,order,used,capacity; float x,y; };
std::vector<Unit> units;
int goals[512]={}; int now=0;
const int cTrainTime=101,cGarrisonCapacity=102;
Unit& unit(int id) { for(auto& u:units) if(u.id==id) return u; throw std::runtime_error("Missing unit"); }
bool xsDoesUnitExist(int id) { for(auto u:units) if(u.id==id) return true; return false; }
int xsGetUnitOwner(int id) { return unit(id).owner; }
int xsGetUnitCopyId(int id) { return unit(id).copy; }
int xsGetGarrisonedInUnitId(int id) { return unit(id).holder; }
int xsGetGoal(int id) { return goals[id]; }
void xsSetGoal(int id,int value) { goals[id]=value; }
int xsGetGameTime() { return now; }
vector xsGetUnitPosition(int id) { auto u=unit(id); return vector(u.x,u.y,0); }
float xsGetUnitBuildPoints(int id) { return unit(id).finished?100.0f:50.0f; }
float xsGetUnitAttribute(int id,int attr) { return attr==cTrainTime?100.0f:float(unit(id).capacity); }
int xsArrayGetSize(int id) { return int(std::get<std::vector<int>>(arrays.at(id)).size()); }
int xsGetPlayerUnitIds(int player,int category,int reuse) {
    if(reuse<0) reuse=xsArrayCreateInt(0,0,"");
    auto& a=std::get<std::vector<int>>(arrays.at(reuse)); a.clear();
    for(auto u:units) if(u.owner==player && ((category==903 && u.type==80)||(category==958 && u.type==70))) a.push_back(u.id);
    return reuse;
}
'''
MAIN=r'''
int main() {
    int n,player;
    while(std::cin>>now>>player>>n) {
        units.clear();
        for(int i=0;i<n;i++) {
            Unit u;std::cin>>u.id>>u.owner>>u.copy>>u.type>>u.finished>>u.holder>>u.action>>u.order>>u.used>>u.capacity>>u.x>>u.y;
            units.push_back(u);
        }
        goals[104]=player;
        swgbClassicNurseryBegin();
        std::vector<std::string> commands;
        int iterations=0;
        while(true) {
            swgbClassicNurseryNext();
            if(goals[106]<0) break;
            if(++iterations>n) throw std::runtime_error("Unbounded queue");
            auto a=unit(goals[106]);
            if(a.action!=-1 || a.order!=-1) continue;
            swgbClassicNurseryChoose();
            if(goals[107]<0) continue;
            if(goals[108]==7) {
                goals[111]=unit(goals[107]).used;
                swgbClassicNurseryCapacity();
            }
            if(goals[107]>=0) commands.push_back(std::to_string(a.id)+":"+std::to_string(goals[107])+":"+std::to_string(goals[108]));
        }
        std::cout<<commands.size();for(auto c:commands)std::cout<<' '<<c;std::cout<<'\n';
        if(arrays.size()!=3) throw std::runtime_error("Array allocation growth");
    }
}
'''


def main():
    report_path=Path('work/classic-engine/nursery-validation.json')
    report=json.loads(report_path.read_text());assert report['passed']
    for name,value in report['tool_hashes'].items():
        assert hashlib.sha256((TOOLKIT/name).read_bytes()).hexdigest()==value,name
    observer=Path('work/original-ai/patch/resources/_common/ai/SWGB Classic/swgb_classic_ai.xs')
    source=observer.read_text()
    controller=(TOOLKIT/'classic_nursery_controller.xs').read_text()
    assert source.endswith(controller)
    helpers='\n'.join(re.search(r'bool '+name+r'\([^}]+\}',source)[0] for name in
                      ('classicFinished','classicNursery','classicNurseryAnimal','classicAnimalFallback'))
    checked=subprocess.run(['work/xs-check/xs-check.exe',str(observer)],capture_output=True,text=True,check=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',checked.stdout+checked.stderr)
    assert 'No errors found' in clean and 'Error:' not in clean and 'Warning:' not in clean,clean
    code,count=re.subn(r'for \((\w+) = ([^;]+); < (.+)\)',
                      lambda m:f'for(int {m[1]}={m[2]}; {m[1]}<{m[3]}; {m[1]}++)',controller)
    assert count==2
    WORK.mkdir(parents=True,exist_ok=True)
    (WORK/'nursery.cpp').write_text(PREFIX+HOST+helpers+code+MAIN)
    (WORK/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(classic_nursery LANGUAGES CXX)\nadd_executable(nursery nursery.cpp)\ntarget_compile_features(nursery PRIVATE cxx_std_17)\n')
    subprocess.run([CMAKE,'-S',str(WORK),'-B',str(WORK/'build')],capture_output=True,check=True)
    subprocess.run([CMAKE,'--build',str(WORK/'build'),'--config','Release'],capture_output=True,check=True)
    translation=json.loads(Path('work/original-ai/translation.json').read_text())
    nursery=set(translation['groups']['bldg-dropanim'])
    centers=set(translation['groups']['bldg-main'])
    mills=set(translation['groups']['bldg-dropchow'])
    animals=set(translation['herdable_ids'])
    def canonical(u):
        root=319 if u[2] in nursery else 109 if u[2] in centers else 68 if u[2] in mills else u[2]
        return u[0],root,2 if u[4] else 0,u[-2],u[-1]
    # id owner copy type finished holder action order used capacity x y
    layouts=[[(1000,1,594,70,1,-1,-1,-1,0,0,5,5)]]
    for family in sorted(nursery):
        for used in (0,9,10,11):
            layouts.append([*layouts[0],(10,1,family,80,1,-1,-1,-1,used,10,10,10),
                            (11,1,319,80,1,-1,-1,-1,10,10,20,20)])
    for site in sorted(centers|mills):
        layouts.append([*layouts[0],(10,1,site,80,1,-1,-1,-1,0,10,10,10)])
    rng=random.Random(5650)
    for _ in range(180):
        units=[]
        for i in range(rng.randrange(0,20)):
            units.append((i+1,rng.choice((1,2)),rng.choice(sorted(nursery|centers|mills|{50})),80,
                          rng.randrange(2),-1,-1,-1,rng.choice((0,9,10,11)),10,rng.randrange(100),rng.randrange(100)))
        for i in range(rng.randrange(1,65)):
            units.append((i+1000,rng.choice((1,2)),rng.choice(sorted(animals|{7959})),70,1,
                          rng.choice((-1,-1,10)),rng.choice((-1,-1,610,617)),rng.choice((-1,-1,710,717)),
                          0,0,rng.randrange(100),rng.randrange(100)))
        layouts.append(units)
    inputs,expected=[],[]
    tick=10
    for units in layouts:
        for player in (1,2):
            commands=[]
            buildings=[canonical(u) for u in units if u[1]==player and u[3]==80]
            indexed={u[0]:u for u in units}
            for animal in units:
                uid,owner,copy,type_,_,holder,action,order,*_=animal
                if owner!=player or type_!=70 or holder>=0 or copy not in animals or action!=-1 or order!=-1:continue
                x,y=animal[-2:]
                first=nearest_building(buildings,x,y)
                nurseries=[]
                fallback=None
                if first>=0:
                    u=indexed[first];nurseries.append((first,u[9],u[8]))
                    second=nearest_building(buildings,x,y,exclude=first)
                    if second>=0:
                        u=indexed[second];nurseries.append((second,u[9],u[8]))
                else:
                    candidate=nearest_building(buildings,x,y,economy=True)
                    if candidate>=0:fallback=candidate
                for event in nursery_decision(nurseries,fallback):
                    if event[0] in ('garrison','move'):commands.append(f'{uid}:{event[1]}:{7 if event[0]=="garrison" else 1}')
            line=f'{tick} {player} {len(units)} '+' '.join(' '.join(map(str,u)) for u in units)
            inputs.extend((line,line))
            expected.extend((' '.join([str(len(commands))]+commands),'0'))
        tick+=1
    result=subprocess.run([str(WORK/'build/Release/nursery.exe')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True)
    actual=result.stdout.splitlines()
    assert len(actual)==len(expected)
    for i,(a,e) in enumerate(zip(actual,expected)): assert a==e,(i,a,e)
    rules=[n for n in parse(PER) if isinstance(n,list) and n[0]=='defrule']
    assert len(rules)==9 and rules[7][-1]==['up-jump-rule','-7']
    # UP's own example uses -1 to repeat the current rule, +1 to skip one.
    assert 7+1+int(rules[7][-1][1])==1 and 'swgbClassicNurseryNext' in str(rules[1])
    assert '(up-set-target-object' not in PER and PER.count('(up-set-target-by-id g:')==4
    assert PER.count('(up-target-objects 1 ')==2 and '(up-garrison ' not in PER
    generated=Path('work/original-ai/patch/resources/_common/ai/SWGB Classic AI.per').read_text()
    assert PER in generated
    output=dict(passed=True,cases=len(expected),source_checks=report['checks'],xs_checker_warnings=0,
                xs_sha256=hashlib.sha256(observer.read_bytes()).hexdigest(),
                bridge_sha256=hashlib.sha256(PER.encode()).hexdigest(),
                limitations=['C++ world fixtures are not the DE XS VM or PER runtime.',
                             'DE object-action/order idle reports, target retention and native commands require in-game checks.',
                             'Polling and XS array order may differ from source per-animal action timing and object-list order.'],
                engine_verified=False,full_behavior_parity=False)
    Path('work/classic-engine/nursery-controller-validation.json').write_text(json.dumps(output,indent=2)+'\n')
    print('PASS',len(expected),'nursery controller host cases; nine-rule bridge structure checked')


if __name__=='__main__':main()
