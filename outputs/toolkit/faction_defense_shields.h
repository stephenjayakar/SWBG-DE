#pragma once
#include <filesystem>
// DE adaptation: temporary bonus health + regeneration, not SWGB's separate
// shield pool. Tasks start neutral; the map controller activates powered stacks.
inline void addFactionDefenseShields(genie::DatFile &d,const genie::DatFile &source,const genie::DatFile &native){
 genie::Task model;bool found=false;
 for(const auto &t:native.Civs[0].Units.at(1754).Bird.TaskList)
  if(t.ActionType==155&&t.SearchWaitTime==109){model=t;found=true;break;}
 if(!found)throw std::runtime_error("Missing native regeneration aura template");
 std::set<int> roots;std::ifstream file("work/faction-tree-units.txt");int root;
 while(file>>root)roots.insert(root);
 if(roots.empty())throw std::runtime_error("Missing reachable faction unit inventory");
 std::filesystem::create_directories("work/defenses2");
 std::ofstream audit("work/defenses2/shield-tasks.tsv");
 if(!audit)throw std::runtime_error("Cannot write shield task audit");
 audit<<"civ\tunit\ttask\ttarget\tattribute\tbase_hp\tradius\n";
 for(int c:{1,2}){
  std::set<int> reachable=roots;std::vector<int> pending(roots.begin(),roots.end());
  auto add=[&](int id){if(id>=0&&size_t(id)<d.Civs[c].Units.size()&&d.Civs[c].UnitPointers[id]&&reachable.insert(id).second)pending.push_back(id);};
  for(size_t i=0;i<pending.size();i++){
   const auto &u=d.Civs[c].Units[pending[i]];
   if(u.Type==80){add(u.Building.StackUnitID);add(u.Building.HeadUnit);for(auto a:u.Building.Annexes)add(a.UnitID);}
  }
  for(int gen:{213,215,335,336}){
   auto &u=d.Civs[c].Units.at(gen);u.Type50.BreakOffCombat|=32;
   const size_t first=u.Bird.TaskList.size();
   for(int id:reachable){
    const auto &s=source.Civs[c==2?3:c].Units.at(id);
    if(s.Type<70||s.HitPoints<=0||s.FlyMode||s.Class==6)continue;
    for(int attr:{0,109}){
     auto t=model;t.ID=int16_t(u.Bird.TaskList.size());t.ClassID=-1;t.UnitID=int16_t(id);
     t.SearchWaitTime=float(attr);t.WorkValue1=0;t.WorkValue2=1;
     t.WorkRange=source.Civs[c==2?3:c].Resources.at(24);
     t.CombatLevelFlag=u.Bird.TaskList.size()==first?6:2;t.TargetDiplomacy=1;t.Enabled=-1;t.IsDefault=0;
     t.MovingGraphicID=-1;t.ProceedingGraphicID=-1;t.WorkingGraphicID=-1;t.CarryingGraphicID=-1;
     t.ResourceGatheringSoundID=-1;t.ResourceDepositSoundID=-1;t.WwiseResourceGatheringSoundID=0;t.WwiseResourceDepositSoundID=0;
     u.Bird.TaskList.push_back(t);
     audit<<c<<'\t'<<gen<<'\t'<<t.ID<<'\t'<<id<<'\t'<<attr<<'\t'<<s.HitPoints<<'\t'<<t.WorkRange<<'\n';
    }
   }
   if(u.Bird.TaskList.size()>=32767)throw std::runtime_error("Shield task index overflow");
  }
 }
}
