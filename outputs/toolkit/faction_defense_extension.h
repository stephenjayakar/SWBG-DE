#pragma once
#include <algorithm>
#include <iterator>
#include <map>
#include <set>
#include "faction_defenses.h"
// Worker military page (build_menu.py documents DE's page model and mirrors these tables).
// DE has no SWGB kind-11 page: kind 11 lands on the military page, so the advanced defenses
// must not share a position with anything. Positions 14/15 are DE's next-page/cancel buttons.
// Sentry Post: always at 7 (the Advanced Infantry Center held 7 but only SWGB cheat and hidden
// AI research enable it, so it gets ButtonID 0). Anti-Air Battery, Shield Generator and Trip
// Mine share 2/5/6 with Shipyard, Mech Factory and Temple and are swapped by the layout
// research, which moves ButtonIDs (attribute 43); the hidden family sits at ButtonID 0.
// faction_build_menu.h applies the final state after the hotkey import.
inline int extraDefenseButton(int id){
 switch(id){
  case 598:case 3598:return 7;
  case 1869:case 3604:return 2;
  case 213:case 215:return 5;
  case 5081:return 6;
  default:return -1;
 }
}
inline bool layoutDefense(int id){return extraDefenseButton(id)>0&&extraDefenseButton(id)!=7;}
const int factionAiOnlyBuildings[]={4908}; // Advanced Infantry Center
const int defenseLayoutTrainButton=43;     // DE attribute "Train Button"
const int defenseLayoutResearchTime=1;     // 0 + no prerequisite: DE researches it at game start
inline bool defenseGroundTurret(int id){return id==79||id==234||id==235||id==7088||id==3599||id==3600||id==3601;}
inline bool defenseAirTurret(int id){return id==196||id==236||id==3602||id==3603||id==1869||id==3604;}
inline void extendFactionDefenses(genie::DatFile &d,const genie::DatFile &source){
 if(d.Civs.size()!=3)throw std::runtime_error("Expected two-faction dataset");
 std::map<int,int> displaced;std::set<int> extras;
 for(int c:{1,2})for(size_t id=0;id<d.Civs[c].Units.size();id++){
  if(!d.Civs[c].UnitPointers[id])continue;auto &u=d.Civs[c].Units[id];
  int button=extraDefenseButton(int(id));
  if(button>0){
   if(u.Type!=80||u.InterfaceKind!=11||u.Creatable.TrainLocations.size()!=1||u.Creatable.TrainLocations[0].LocationID!=118)
    throw std::runtime_error("Unexpected advanced defense template");
   // Hotkeys are imported at this position; finalizeFactionBuildMenu() (faction_build_menu.h)
   // then hides the layout defenses until the defense layout is researched.
   u.InterfaceKind=10;u.Creatable.TrainLocations[0].ButtonID=uint8_t(button);extras.insert(int(id));
  }
  // Every variant of the three displaced production families moves together.
  else if(u.Type==80&&u.InterfaceKind==10)for(const auto &l:u.Creatable.TrainLocations)
   if(l.LocationID==118&&(l.ButtonID==2||l.ButtonID==5||l.ButtonID==6)){
    if(u.Creatable.TrainLocations.size()!=1)throw std::runtime_error("Displaced building needs one train location");
    auto it=displaced.emplace(int(id),int(l.ButtonID)).first;
    if(it->second!=l.ButtonID)throw std::runtime_error("Displaced building moves between factions");
   }
  if(id==1576){if(u.Creatable.TrainLocations[0].LocationID!=13)throw std::runtime_error("Sea lookout builder changed");u.InterfaceKind=2;}
 }
 if(extras.size()!=7)throw std::runtime_error("Unexpected advanced defense family count");
 for(int mode=0;mode<2;mode++){
  genie::Effect effect;effect.setGameVersion(genie::GV_LatestDE2);
  effect.Name=mode?"SWGB_DEFENSE_LAYOUT":"SWGB_MILITARY_LAYOUT";
  auto set=[&](int id,int button){genie::EffectCommand cmd;cmd.setGameVersion(genie::GV_LatestDE2);cmd.Type=0;cmd.A=int16_t(id);cmd.B=-1;cmd.C=defenseLayoutTrainButton;cmd.D=float(button);effect.EffectCommands.push_back(cmd);};
  for(const auto &[id,button]:displaced)set(id,mode?0:button);
  for(int id:extras)if(layoutDefense(id))set(id,mode?extraDefenseButton(id):0);
  // Repeatable native research changes only build-page visibility. It never
  // disables production or changes the AI's ability to construct buildings.
  genie::Tech tech;tech.setGameVersion(genie::GV_LatestDE2);
  tech.Name=effect.Name;tech.RequiredTechCount=0;tech.Civ=-1;tech.FullTechMode=1;
  for(auto &r:tech.RequiredTechs)r=-1;
  for(auto &r:tech.ResourceCosts){r.Type=-1;r.Amount=0;r.Flag=0;}
  tech.LanguageDLLName=898010+mode;tech.LanguageDLLDescription=899010+mode;
  tech.LanguageDLLHelp=998010+mode;tech.LanguageDLLTechTree=1038010+mode;
  tech.IconID=d.Techs.at(mode?181:33).IconID;
  if(tech.IconID<0)throw std::runtime_error("Menu switch requires converted tech icon");
  tech.Repeatable=1;tech.Type=0;tech.EffectID=int16_t(d.Effects.size());
  tech.ResearchLocations={genie::ResearchLocation(109,defenseLayoutResearchTime,uint8_t(11+mode),1100010+mode)};
  d.Effects.push_back(effect);d.Techs.push_back(tech);
 }
 // Source classes encode air/ground attack restrictions in SWGB executable
 // code. Restore the distinction with explicit native combat-task selectors.
 std::set<int> air,ground;std::map<int,std::set<int>> classes;std::set<int> airClasses;
 for(int c:{0,1,2})for(size_t id=0;id<d.Civs[c].Units.size();id++){
  if(!d.Civs[c].UnitPointers[id])continue;const auto &u=d.Civs[c].Units[id];
  if(u.Type<70)continue;const auto &s=source.Civs[c==2?3:c].Units.at(id);
  if(s.FlyMode){air.insert(int(id));airClasses.insert(u.Class);}else ground.insert(int(id));
  classes[u.Class].insert(int(id));
 }
 classes[35].insert(5075); // Mine acquires native Petard classification below.
 for(int c:{1,2})for(size_t id=0;id<d.Civs[c].Units.size();id++){
  if(!d.Civs[c].UnitPointers[id])continue;auto &u=d.Civs[c].Units[id];
  bool aa=defenseAirTurret(int(id)),land=defenseGroundTurret(int(id))||id==5075;
  if(!aa&&!land)continue;
  auto old=u.Bird.TaskList;auto it=std::find_if(old.begin(),old.end(),[](const auto &t){return t.ActionType==7;});
  if(it==old.end())throw std::runtime_error("Defense lacks combat task");
  genie::Task combat=*it;u.Bird.TaskList.clear();
  auto append=[&](int cl,int uid){auto t=combat;t.ID=int16_t(u.Bird.TaskList.size());t.ClassID=int16_t(cl);t.UnitID=int16_t(uid);u.Bird.TaskList.push_back(t);};
  if(aa){for(int target:air)append(-1,target);}
  else for(const auto &entry:classes){
   if(!airClasses.count(entry.first))append(entry.first,-1);
   else for(int target:entry.second)if(ground.count(target)&&!air.count(target))append(-1,target);
  }
  for(auto t:old)if(t.ActionType!=7){t.ID=int16_t(u.Bird.TaskList.size());u.Bird.TaskList.push_back(t);}
  u.Bird.DefaultTaskID=0;
  if(id==5075)u.Class=35; // Native Petard UnitAI supplies one-shot detonation.
 }
 std::cout<<"Added repeatable construction layouts; repaired land/air targeting and mine detonation.\n";
}
