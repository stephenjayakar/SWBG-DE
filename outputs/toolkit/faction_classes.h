#pragma once
#include <array>
#include <limits>
// Class 38 is DE ambient birds, not a general flying-combat category.
// Use military classes for commanded aircraft; flight height and terrain
// permissions are separate fields and remain source-authored.
// Class effects/tasks below expand explicit source membership on collisions.
inline int factionClass(int source) {
 static constexpr std::array<int,65> classes={
  11,58,9,11,9,10,27,49,39,52,52,22,11,22,21,22,22,
  20,3,37,11,11,34,5,11,33,11,7,42,32,8,15,13,13,
  51,13,54,11,11,22,22,11,11,13,6,19,25,47,0,6,
  6,43,0,13,17,0,12,24,4,20,29,11,13,0,0};
 if(source==-1)return -1;
 if(source<0 || source>=int(classes.size()))throw std::runtime_error("Unmapped SWGB class");
 return classes[source];
}
inline void translateFactionClasses(genie::DatFile &target,const genie::DatFile &source){
 std::map<int,std::set<int>> members, reverse;
 for(int c:{0,1,3})for(size_t id=0;id<source.Civs[c].Units.size();id++){
  if(!source.Civs[c].UnitPointers[id])continue;
  int cl=source.Civs[c].Units[id].Class;
  members[cl].insert(int(id));reverse[factionClass(cl)].insert(cl);
 }
 std::ofstream audit("work/faction-class-mapping.tsv");
 audit<<"source\ttarget\tmembers\tcolliding_classes\n";
 for(int cl=-1;cl<65;cl++)audit<<cl<<'\t'<<factionClass(cl)<<'\t'<<members[cl].size()<<'\t'<<reverse[factionClass(cl)].size()<<'\n';
 size_t expandedEffects=0,expandedTasks=0;
 for(auto &effect:target.Effects){
  auto before=effect.EffectCommands;effect.EffectCommands.clear();
  for(auto command:before){
   if((command.Type==0||command.Type==4||command.Type==5)&&command.B>=0){
    if(command.A>=0)throw std::runtime_error("Combined effect selectors need explicit semantics");
    int cl=command.B;
    if(reverse[factionClass(cl)].size()>1){
     for(int id:members[cl]){
      for(int c:{0,1,3})if(source.Civs[c].UnitPointers[id]&&source.Civs[c].Units[id].Class!=cl)
       throw std::runtime_error("Class effect has inconsistent source civ membership");
      auto copy=command;copy.A=int16_t(id);copy.B=-1;effect.EffectCommands.push_back(copy);
     }
     ++expandedEffects;continue;
    }
    command.B=int16_t(factionClass(cl));
   }
   effect.EffectCommands.push_back(command);
  }
 }
 auto translateTasks=[&](auto &list,int16_t &defaultID){
  auto before=list;list.clear();int16_t translatedDefault=-1;
  for(auto task:before){
   if(task.ID==defaultID&&defaultID>=0)translatedDefault=int16_t(list.size());
   auto append=[&](auto copy){
    if(list.size()>=size_t(std::numeric_limits<int16_t>::max()))throw std::runtime_error("Expanded task table exceeds DE limit");
    copy.ID=int16_t(list.size());list.push_back(copy);
   };
   if(task.ClassID>=0){
    int cl=task.ClassID;
    if(reverse[factionClass(cl)].size()>1){
     if(task.UnitID>=0)throw std::runtime_error("Combined class/unit task needs explicit semantics");
     for(int id:members[cl]){auto copy=task;copy.ClassID=-1;copy.UnitID=int16_t(id);append(copy);}
     ++expandedTasks;continue;
    }
    task.ClassID=int16_t(factionClass(cl));
   }
   append(task);
  }
  if(defaultID>=0&&translatedDefault<0)throw std::runtime_error("Unresolved default task");
  defaultID=translatedDefault;
 };
 for(auto &civ:target.Civs)for(size_t id=0;id<civ.Units.size();id++){
  if(!civ.UnitPointers[id])continue;
  auto &unit=civ.Units[id];unit.Class=int16_t(factionClass(unit.Class));
  if(unit.Type>=40)translateTasks(unit.Bird.TaskList,unit.Bird.DefaultTaskID);
 }
 for(auto &header:target.UnitHeaders){int16_t unused=-1;translateTasks(header.TaskList,unused);}
 std::cout<<"Class conversion: "<<expandedEffects<<" class effects and "<<expandedTasks<<" class tasks expanded to preserve source membership.\n";
}
