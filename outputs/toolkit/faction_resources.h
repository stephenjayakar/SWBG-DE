#pragma once
// Verified common resource roles from AGE Lists.cpp. Unimplemented SWGB
// mechanics are stored outside native engine resource slots, not misinterpreted
// as DE bonuses. Those custom values still need behavior implementations.
inline int factionResource(int source){
 if(source<0)return source;
 if(source==59)return 58; // Starting Tech Level / Dark Age tech.
 if(source==60)return 25; // TL2 / Feudal.
 if(source==61)return 23; // TL3 / Castle.
 if(source==63)return 24; // TL4 / Imperial.
 if(source==214)return 47; // Nova / gold mining productivity.
 static const std::set<int> divergent={10,18,19,23,24,25,26,29,30,31,33,38,47,51,56,58,59,60,61,63,87};
 if(source<=102&&!divergent.count(source))return source;
 if(source==176||source==177||source==178||source==179||source==180||source==181||source==182||source==183||source==189||source==190||source==191||source==192||source==193||source==194||source==195||source==197)return source;
 if(source>30767)throw std::runtime_error("Custom source resource exceeds signed ID space");
 return 2000+source;
}
inline void translateFactionResources(genie::DatFile &target,const genie::DatFile &native){
 std::ofstream report("work/faction-resource-mapping.tsv");report<<"source\ttarget\tstatus\n";
 for(size_t i=0;i<target.Civs[0].Resources.size();i++)report<<i<<'\t'<<factionResource(int(i))<<'\t'<<(factionResource(int(i))>=2000?"stored-only; behavior unresolved":"native role")<<'\n';
 for(size_t c=0;c<target.Civs.size();c++){
  auto &civ=target.Civs[c];auto source=civ.Resources;civ.Resources=native.Civs[std::min(c,native.Civs.size()-1)].Resources;
  civ.Resources.resize(std::max(civ.Resources.size(),size_t(2000)+source.size()),0);
  for(size_t i=0;i<source.size();i++)civ.Resources.at(factionResource(int(i)))=source[i];
  for(size_t i=0;i<civ.Units.size();i++){
   if(!civ.UnitPointers[i])continue;auto &u=civ.Units[i];
   for(auto &r:u.ResourceStorages)r.Type=int16_t(factionResource(r.Type));
   for(auto &r:u.Creatable.ResourceCosts)r.Type=int16_t(factionResource(r.Type));
  }
 }
 auto tasks=[](auto &list){for(auto &t:list){
  t.ResourceIn=int16_t(factionResource(t.ResourceIn));t.ResourceOut=int16_t(factionResource(t.ResourceOut));
  t.ResourceMultiplier=int16_t(factionResource(t.ResourceMultiplier));t.UnusedResource=int16_t(factionResource(t.UnusedResource));
 }};
 for(auto &h:target.UnitHeaders)tasks(h.TaskList);
 for(auto &c:target.Civs)for(size_t i=0;i<c.Units.size();i++)if(c.UnitPointers[i]&&c.Units[i].Type>=40)tasks(c.Units[i].Bird.TaskList);
 for(auto &t:target.Techs)for(auto &r:t.ResourceCosts)r.Type=int16_t(factionResource(r.Type));
 for(auto &effect:target.Effects)for(auto &command:effect.EffectCommands)if(command.Type==1||command.Type==6)command.A=int16_t(factionResource(command.A));
}
