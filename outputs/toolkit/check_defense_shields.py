"""Execute shield power/task decisions in a mock host, not the DE engine."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path('work/defenses2/shield-host')
CMAKE = 'C:/Program Files/Microsoft Visual Studio/2022/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
HOST = r'''
#include <vector>
#include <map>
#include <string>
#include <iostream>
#include <stdexcept>
#include <cmath>
struct vector {float x,y,z;};
struct Task {std::map<int,float> fields;};
struct Unit {int id,owner,copy,type,category,holder;float hp,built,time;vector pos;std::vector<Task> tasks;};
std::map<int,Unit> units; std::vector<std::vector<int>> arrays;
std::map<int,float> resources; Task buffer;int writes=0;
const int cHitpoints=0,cTrainTime=101,cTaskAttrTaskType=1,cTaskAttrSearchWaitTime=2,
 cTaskAttrObjectId=3,cTaskAttrWorkValue1=4,cTaskAttrWorkRange=5;
int xsGetNumPlayers(){return 2;} bool xsGetPlayerInGame(int){return true;}
float xsPlayerAttribute(int,int id){return resources[id];}
int xsCeilToInt(float f){return int(std::ceil(f));}
bool xsDoesUnitExist(int u){return units.count(u);}
float xsGetUnitHitpoints(int u){return units.at(u).hp;}
int xsGetUnitType(int u){return units.at(u).type;}
int xsGetUnitOwner(int u){return units.at(u).owner;}
int xsGetUnitCopyId(int u){return units.at(u).copy;}
int xsGetGarrisonedInUnitId(int u){return units.at(u).holder;}
float xsGetUnitBuildPoints(int u){return units.at(u).built;}
float xsGetUnitAttribute(int u,int){return units.at(u).time;}
float xsGetObjectAttribute(int p,int id,int){return id==83?float(40*p):100.0f;}
vector xsGetUnitPosition(int u){return units.at(u).pos;}
float xsVectorGetX(vector v){return v.x;} float xsVectorGetY(vector v){return v.y;}
int xsArrayGetSize(int a){return int(arrays.at(a).size());}
int xsArrayGetInt(int a,int i){return arrays.at(a).at(i);}
int xsGetPlayerUnitIds(int p,int category,int reuse){
 if(reuse<0){reuse=int(arrays.size());arrays.push_back({});}
 auto &a=arrays.at(reuse);a.clear();for(auto &kv:units)if(kv.second.owner==p&&kv.second.category==category)a.push_back(kv.first);return reuse;
}
int xsGetUnitTaskCount(int u){return int(units.at(u).tasks.size());}
bool xsUnitTaskAmount(int u,int t){buffer=units.at(u).tasks.at(t);return true;}
float xsGetTaskAmount(int f){return buffer.fields.at(f);}
void xsTaskAmount(int f,float v){buffer.fields[f]=v;}
bool xsModifyUnitTasks(int u,int t,bool edit){if(!edit)throw std::runtime_error("Unexpected insertion");units.at(u).tasks.at(t)=buffer;writes++;return true;}
Task task(float kind,float attr,float amount){return {{{1,kind},{2,attr},{3,83},{4,amount},{5,9}}};}
void reset(){
 units.clear();arrays.clear();writes=0;resources={{2018,10},{2030,5},{2024,9},{2010,1},{2025,1}};
 units[1]={1,1,335,80,903,-1,1500,100,100,{0,0,0},{task(155,0,0),task(155,109,0),task(155,13,3),task(7,0,0)}};
 units[2]={2,1,12,80,903,-1,1000,100,100,{3,4,0},{}};
}
void check(bool b,const char* why){if(!b)throw std::runtime_error(why);}
float amount(int t){return units.at(1).tasks.at(t).fields.at(4);}
'''
MAIN = r'''
int main(){int cases=0;
 for(int core:{12,498,132,20,3554,3555,3556,3557,1009,1013})
 for(int state=0;state<9;state++){
  reset();swgbDefenseBuildings=-1;swgbDefenseOther=-1;
  auto &c=units[2];c.copy=core;if(core==1009||core==1013){c.type=70;c.category=911;}
  bool expected=true;
  if(state==1){c.pos={100,0,0};expected=false;}
  if(state==2){c.hp=0;expected=false;}
  if(state==3){c.owner=2;expected=false;}
  if(state==4){c.holder=999;expected=false;}
  if(state==5){units[1].built=50;expected=false;}
  if(state==6){c.built=50;expected=c.type!=80;}
  if(state==7){c.pos={0,core==1009||core==1013?5.001f:10.001f,0};expected=false;}
  if(state==8)c.pos={0,core==1009||core==1013?5.0f:10.0f,0};
  swgbDefenseTick();check(amount(0)==(expected?40:0),"Power/HP decision");check(amount(1)==(expected?120:0),"Regen decision");
  check(amount(2)==3&&amount(3)==0,"Unrelated task changed");
  int before=writes;swgbDefenseTick();check(writes==before,"Repeated writes without changes");check(arrays.size()==2,"Query-array leak");cases++;
 }
 reset();swgbDefenseBuildings=-1;swgbDefenseOther=-1;
 swgbDefenseTick();units.erase(2);swgbDefenseTick();check(amount(0)==0&&amount(1)==0,"Power loss did not clear protection");cases++;
 reset();swgbDefenseBuildings=-1;swgbDefenseOther=-1;
 units[3]={3,1,213,80,903,-1,100,50,100,{0,0,0},{}};units[1].time=0;
 swgbDefenseTick();check(amount(0)==0,"Unfinished head projects aura");units[3].built=100;swgbDefenseTick();check(amount(0)==40,"Completed head failed");cases++;
 reset();swgbDefenseBuildings=-1;swgbDefenseOther=-1;
 swgbDefenseTick();resources[2024]=12;resources[2010]=2;swgbDefenseTick();
 check(units[1].tasks[0].fields[5]==12&&amount(1)==240,"Research modifiers not applied");cases++;
 units[1].owner=2;units[2].owner=2;swgbDefenseTick();check(amount(0)==80,"Conversion owner not refreshed");cases++;
 for(int head:{213,215}){reset();swgbDefenseBuildings=-1;swgbDefenseOther=-1;units[1].copy=head;swgbDefenseTick();check(writes==0,"Head duplicated shield");cases++;}
 reset();swgbDefenseBuildings=-1;swgbDefenseOther=-1;resources[2024]=0;swgbDefenseTick();check(amount(0)==0,"Zero range shield");cases++;
 reset();swgbDefenseBuildings=-1;swgbDefenseOther=-1;swgbDefenseTick();
 // Simulate save/load with live task state retained but queries rebuilt.
 arrays.clear();swgbDefenseBuildings=-1;swgbDefenseOther=-1;units[2].pos={100,0,0};swgbDefenseTick();check(amount(0)==0,"Reload stale aura");cases++;
 std::cout<<cases<<" host scenarios passed\n";
}
'''


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    source = Path('outputs/toolkit/faction_defense_shields.xs').read_text()
    code = source.split('rule swgbDefenseShieldTick')[0]
    code = re.sub(r'for \((\w+) = ([^;\n]+); (<=|<) (.+)\) (?=\{)',
                  lambda m: f'for (int {m[1]} = {m[2]}; {m[1]} {m[3]} {m[4]}; ++{m[1]})', code)
    (ROOT / 'main.cpp').write_text(HOST + code + MAIN)
    (ROOT / 'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.15)\nproject(shield_host LANGUAGES CXX)\nset(CMAKE_CXX_STANDARD 17)\nadd_executable(shield_host main.cpp)\n')
    subprocess.run([CMAKE, '-S', str(ROOT), '-B', str(ROOT / 'build')], check=True, capture_output=True)
    subprocess.run([CMAKE, '--build', str(ROOT / 'build'), '--config', 'Release'], check=True)
    result = subprocess.run([str(ROOT / 'build/Release/shield_host.exe')], check=True, capture_output=True, text=True)
    print(result.stdout.strip())
    report = dict(passed=True, result=result.stdout.strip(),
        source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        engine_verified=False, scope='Mocked unit queries/task editing; native aura HP behavior and save/load remain in-game checks')
    (ROOT.parent / 'shield-host-validation.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
