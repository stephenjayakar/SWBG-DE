#pragma once
#include <tuple>
inline void adaptFactionScout(genie::DatFile &target,const genie::DatFile &source){
 // Original maps request Imperial scout 550 and rely on SWGB's civ-unit hook.
 // In this isolated dataset, Rebel 550 is an untrainable alias of Rebel 556.
 // Both source scouts receive identical direct upgrades. Reject future drift.
 for(const auto &effect:source.Effects){
  std::vector<std::tuple<int,int,int,float>> imperial,rebel;
  for(const auto &e:effect.EffectCommands){
   if(e.Type==2)continue; // Availability remains source-specific: only 556 trains.
   if(e.A==550)imperial.emplace_back(e.Type,e.B,e.C,e.D);
   if(e.A==556)rebel.emplace_back(e.Type,e.B,e.C,e.D);
  }
  if(imperial!=rebel)throw std::runtime_error("Scout alias requires identical direct source upgrades");
 }
 for(int c:{0,1,3})if(source.Civs[c].Units[550].Class!=source.Civs[c].Units[556].Class)
  throw std::runtime_error("Scout aliases have different class membership");
 // DE consults resource 263 for starting scouts; native 448 is a SWGB Stormtrooper.
 target.Civs[0].Resources.at(263)=550;
 target.Civs[1].Resources.at(263)=550;
 target.Civs[2].Resources.at(263)=556;
 auto &civ=target.Civs[2];
 if(civ.Units[550].Enabled||civ.Units[556].Enabled)throw std::runtime_error("Unexpected initially enabled scout alias");
 civ.Units[550]=civ.Units[556];
 civ.Units[550].ID=550;civ.Units[550].CopyID=550;civ.Units[550].BaseID=550;
 civ.UnitPointers[550]=civ.UnitPointers[556];
}
