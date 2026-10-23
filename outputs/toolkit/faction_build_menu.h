#pragma once
// Worker build menu, final state. build_menu.py documents DE's page model and mirrors these steps
// on assembled DATs (fix_build_menu.py); check_build_menu.py guards the result.
//  * DE never shows the native Dock IDs 45/133/47/51 in a build menu, so the worker builds a
//    Shipyard foundation (like Fortress 1211 -> 82) that becomes unit 45 when it is finished.
//  * The layout research swaps three advanced defenses with Shipyard/Mech Factory/Temple by train
//    button (attribute 43); the hidden family sits at button 0. Default = military layout.
//  * Runs after importFactionHotkeys(), which matches hotkeys by position: the foundation copies
//    the Shipyard's assigned hotkey.
#include <algorithm>
#include <iterator>
#include <map>
#include <set>
#include "faction_defense_extension.h"
const int factionShipyard=45;
const int factionShipyardFoundation=1696; // free, unreferenced after the 900-999 remap block
const int factionShipyardFamily[]={45,133,47,51,3586,3587,3588,3589};
inline void addShipyardFoundation(genie::DatFile &d){
 const int f=factionShipyardFoundation;
 for(size_t c=0;c<d.Civs.size();c++){
  auto &civ=d.Civs[c];
  if(civ.Units.size()<=size_t(f)||civ.UnitPointers[f])throw std::runtime_error("Shipyard foundation slot is not free");
  if(!civ.UnitPointers[factionShipyard]||civ.Units[factionShipyard].Type!=80)throw std::runtime_error("Missing Shipyard");
  genie::Unit u=civ.Units[factionShipyard];
  u.ID=int16_t(f);u.CopyID=int16_t(f);u.BaseID=int16_t(f);u.Name="BLDG-TRAINBOAT-BUILD";
  u.Enabled=0;u.HideInEditor=1;
  u.Building.DisappearsWhenBuilt=1;u.Building.StackUnitID=int16_t(factionShipyard);u.Building.HeadUnit=-1;
  civ.Units[f]=u;civ.UnitPointers[f]=1;
 }
 // Enabled together with the Shipyard (Tech Level 1).
 genie::Effect *owner=nullptr;size_t index=0;int hits=0;
 for(auto &e:d.Effects)for(size_t i=0;i<e.EffectCommands.size();i++){
  const auto &cmd=e.EffectCommands[i];
  if(cmd.Type==2&&cmd.A==factionShipyard&&cmd.B==1){owner=&e;index=i;hits++;}
 }
 if(hits!=1)throw std::runtime_error("Shipyard needs exactly one enabling effect command");
 genie::EffectCommand enable=owner->EffectCommands[index];enable.A=int16_t(f);
 owner->EffectCommands.insert(owner->EffectCommands.begin()+index+1,enable);
}
inline void finalizeFactionBuildMenu(genie::DatFile &d){
 addShipyardFoundation(d);
 auto worker=[](genie::Unit &u)->genie::unit::TrainLocation&{
  if(u.Type!=80||u.Creatable.TrainLocations.size()!=1||u.Creatable.TrainLocations[0].LocationID!=118)
   throw std::runtime_error("Unexpected worker building "+std::to_string(u.ID));
  return u.Creatable.TrainLocations[0];
 };
 size_t hidden=0;
 for(int c:{1,2}){
  auto &units=d.Civs[c].Units;
  for(int id:factionShipyardFamily){worker(units.at(id)).ButtonID=0;hidden++;}
  for(int id:factionAiOnlyBuildings){worker(units.at(id)).ButtonID=0;hidden++;}
  for(size_t id=0;id<units.size();id++)if(d.Civs[c].UnitPointers[id]&&extraDefenseButton(int(id))>0){
   auto &u=units[id];auto &l=worker(u);u.InterfaceKind=10;
   l.ButtonID=uint8_t(layoutDefense(int(id))?0:extraDefenseButton(int(id)));if(!l.ButtonID)hidden++;
  }
 }
 if(hidden!=2*(8+1+5))throw std::runtime_error("Unexpected hidden worker building count");
 // Families the defense layout hides: every kind-10 worker building at 2/5/6 (now the Shipyard
 // foundation, Mech Factory and Temple lines).
 std::map<int,int> displaced;
 for(int c:{1,2})for(size_t id=0;id<d.Civs[c].Units.size();id++){
  if(!d.Civs[c].UnitPointers[id]||extraDefenseButton(int(id))>0)continue;auto &u=d.Civs[c].Units[id];
  if(u.Type!=80||u.InterfaceKind!=10)continue;
  for(const auto &l:u.Creatable.TrainLocations)if(l.LocationID==118&&(l.ButtonID==2||l.ButtonID==5||l.ButtonID==6)){
   worker(u);auto it=displaced.emplace(int(id),int(l.ButtonID)).first;
   if(it->second!=l.ButtonID)throw std::runtime_error("Displaced building moves between factions");
  }
 }
 for(int mode=0;mode<2;mode++){
  const char *name=mode?"SWGB_DEFENSE_LAYOUT":"SWGB_MILITARY_LAYOUT";
  auto t=std::find_if(d.Techs.begin(),d.Techs.end(),[&](const auto &v){return v.Name==name;});
  if(t==d.Techs.end()||t->ResearchLocations.size()!=1)throw std::runtime_error("Missing layout research");
  t->ResearchLocations[0].QueueTime=defenseLayoutResearchTime;
  auto &e=d.Effects.at(t->EffectID);e.EffectCommands.clear();
  auto set=[&](int id,int button){genie::EffectCommand cmd;cmd.setGameVersion(genie::GV_LatestDE2);cmd.Type=0;cmd.A=int16_t(id);cmd.B=-1;cmd.C=defenseLayoutTrainButton;cmd.D=float(button);e.EffectCommands.push_back(cmd);};
  for(const auto &[id,button]:displaced)set(id,mode?0:button);
  for(size_t id=0;id<d.Civs[1].Units.size();id++)if(layoutDefense(int(id)))set(int(id),mode?extraDefenseButton(int(id)):0);
 }
 std::cout<<"Build menu: Shipyard foundation "<<factionShipyardFoundation<<", "<<displaced.size()<<" layout-swapped buildings.\n";
}
