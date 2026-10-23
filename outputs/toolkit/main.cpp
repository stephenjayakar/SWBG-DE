#include "genie/dat/DatFile.h"
#include <fstream>
#include <iostream>
#include <map>
#include <functional>
#include <sstream>
#include "source_manifest.h"
#include "faction_dependencies.h"
#include "faction_builder.h"
#include "faction_interactions.h"
#include "faction_behavior_report.h"
#include "economy_report.h"
#include "classic_combat_report.h"
#include "faction_building_state_graphics.h"
#include "faction_defenses.h"
#include "faction_defense_extension.h"
#include "faction_build_menu.h"
#include "faction_defense_shields.h"
#include "faction_defense_validation.h"
int run(int argc,char**argv){
 if(argc<4)return 1;
 genie::DatFile d;d.setGameVersion((std::string(argv[1])=="ef"||std::string(argv[1])=="source-ai-lines"||std::string(argv[1])=="source-economy-report"||std::string(argv[1])=="source-manifest"||std::string(argv[1])=="source-interactions")?genie::GV_CCV2:genie::GV_LatestDE2);d.load(argv[2]);
 if(std::string(argv[1])=="defense-mechanics-report"){
  genie::DatFile source,native;source.setGameVersion(genie::GV_CCV2);source.load("work/ef.raw");native.setGameVersion(genie::GV_LatestDE2);native.load("work/de.raw");
  std::ofstream o(argv[3]);
  auto dump=[&](genie::DatFile &f,const char *label,int c,int id,bool original){auto &u=f.Civs[c].Units[id];auto &v=u.Creatable;auto &b=u.Type50;
   o<<label<<" UNIT "<<c<<' '<<id<<' '<<u.Name<<" type="<<+u.Type<<" class="<<u.Class<<" hp="<<u.HitPoints<<" trait="<<+u.Trait<<" range="<<b.MaxRange<<" blast="<<b.BlastWidth<<" projectile="<<b.ProjectileUnitID<<" charge="<<v.ChargeType<<','<<v.ChargeEvent<<','<<v.MaxCharge<<','<<v.RechargeRate<<','<<v.ChargeTarget<<" blastlevel="<<+b.BlastAttackLevel<<" reload="<<b.ReloadTime<<" death="<<u.DeadUnitID<<" swap="<<+u.Bird.TaskSwapGroup<<"\n";
   for(auto x:b.Attacks)o<<" ATTACK "<<x.Class<<' '<<x.Amount<<"\n";
   for(auto x:u.ResourceStorages)o<<" STORE "<<x.Type<<' '<<x.Amount<<' '<<+x.Flag<<"\n";
   const auto &tasks=original?f.UnitHeaders[id].TaskList:u.Bird.TaskList;
   for(auto t:tasks)o<<" TASK "<<t.ID<<" action="<<t.ActionType<<" target="<<t.UnitID<<" class="<<t.ClassID<<" flag="<<+t.CombatLevelFlag<<" diplo="<<+t.TargetDiplomacy<<" auto="<<+t.AutoSearchTargets<<" targeting="<<+t.EnableTargeting<<" default="<<+t.IsDefault<<" enabled="<<t.Enabled<<" range="<<t.WorkRange<<" values="<<t.WorkValue1<<','<<t.WorkValue2<<" wait="<<t.SearchWaitTime<<" in="<<t.ResourceIn<<" out="<<t.ResourceOut<<"\n";
  };
  for(int c:{1,3})for(int id:{79,236,598,1576,1869,5075,5076,5078,5080,5081,213,215})dump(source,"source",c,id,true);
  for(int c:{1,2})for(int id:{79,236,598,1576,1869,5075,5076,5078,5080,5081,213,215})dump(d,"current",c,id,false);
  for(size_t id=0;id<native.Civs[0].Units.size();id++)if(native.Civs[0].UnitPointers[id]){
   auto &u=native.Civs[0].Units[id];bool aura=false;for(auto t:u.Bird.TaskList)if(t.ActionType==155)aura=true;
   if(u.Creatable.ChargeType!=0||aura||id==440||id==527)dump(native,"native",0,int(id),false);
  }
  return 0;
 }
 if(std::string(argv[1])=="audit-defense-extension"){
  if(argc!=5)throw std::runtime_error("Expected candidate, restored output, baseline DAT");
  genie::DatFile before;before.setGameVersion(genie::GV_LatestDE2);before.load(argv[4]);
  if(d.Civs.size()!=before.Civs.size()||d.Techs.size()!=before.Techs.size()+2||d.Effects.size()!=before.Effects.size()+2)throw std::runtime_error("Unexpected extension tables");
  for(int c:{1,2})for(size_t id=0;id<d.Civs[c].Units.size();id++){
   if(!d.Civs[c].UnitPointers[id])continue;auto &u=d.Civs[c].Units[id];const auto &old=before.Civs[c].Units[id];
   if(extraDefenseButton(int(id))>0){u.Creatable.TrainLocations[0].ButtonID=old.Creatable.TrainLocations[0].ButtonID;u.InterfaceKind=old.InterfaceKind;}
   bool menu=std::find(std::begin(factionAiOnlyBuildings),std::end(factionAiOnlyBuildings),int(id))!=std::end(factionAiOnlyBuildings)
    ||std::find(std::begin(factionShipyardFamily),std::end(factionShipyardFamily),int(id))!=std::end(factionShipyardFamily);
   if(menu)u.Creatable.TrainLocations[0].ButtonID=old.Creatable.TrainLocations[0].ButtonID;
   if(id==1576)u.InterfaceKind=old.InterfaceKind;
   if(id==213||id==215||id==335||id==336){u.Bird.TaskList=old.Bird.TaskList;u.Type50.BreakOffCombat=old.Type50.BreakOffCombat;}
   if(defenseAirTurret(int(id))||defenseGroundTurret(int(id))||id==5075){u.Bird.TaskList=old.Bird.TaskList;u.Bird.DefaultTaskID=old.Bird.DefaultTaskID;u.Class=old.Class;}
  }
  // Shipyard foundation: drop the unit slot and its enabling command.
  for(size_t c=0;c<d.Civs.size();c++){d.Civs[c].Units[factionShipyardFoundation]=before.Civs[c].Units[factionShipyardFoundation];d.Civs[c].UnitPointers[factionShipyardFoundation]=before.Civs[c].UnitPointers[factionShipyardFoundation];}
  for(auto &e:d.Effects)e.EffectCommands.erase(std::remove_if(e.EffectCommands.begin(),e.EffectCommands.end(),[](const auto &cmd){return cmd.Type==2&&cmd.A==factionShipyardFoundation;}),e.EffectCommands.end());
  d.Techs.resize(before.Techs.size());d.Effects.resize(before.Effects.size());d.saveAs(argv[3]);return 0;
 }
 if(std::string(argv[1])=="extend-defense-menu"){
  genie::DatFile source;source.setGameVersion(genie::GV_CCV2);source.load("work/ef.raw");
  extendFactionDefenses(d,source);finalizeFactionBuildMenu(d);
  genie::DatFile native;native.setGameVersion(genie::GV_LatestDE2);native.load("work/de.raw");
  addFactionDefenseShields(d,source,native);validateFactionDefenses(d,source);d.saveAs(argv[3]);return 0;
 }
 if(std::string(argv[1])=="repair-defense-menu"){repairFactionDefenses(d);d.saveAs(argv[3]);return 0;}
 if(std::string(argv[1])=="audit-defense-menu"){
  if(argc!=5)throw std::runtime_error("Expected candidate, restored output, baseline DAT");
  genie::DatFile before;before.setGameVersion(genie::GV_LatestDE2);before.load(argv[4]);
  if(d.Civs.size()!=before.Civs.size())throw std::runtime_error("Changed civ count");
  for(int c:{1,2})for(size_t id=0;id<d.Civs[c].Units.size();id++)if(factionDefenseButton(int(id))>=0){
   auto &u=d.Civs[c].Units[id];const auto &old=before.Civs.at(c).Units.at(id);
   if(u.InterfaceKind!=10||u.Creatable.TrainLocations.size()!=1||u.Creatable.TrainLocations[0].ButtonID!=factionDefenseButton(int(id)))throw std::runtime_error("Unexpected defense menu");
   u.InterfaceKind=old.InterfaceKind;u.Creatable.TrainLocations[0].ButtonID=old.Creatable.TrainLocations[0].ButtonID;
  }
  d.saveAs(argv[3]);return 0;
 }
 if(std::string(argv[1])=="construction-menu-report"){
  genie::DatFile source,native;source.setGameVersion(genie::GV_CCV2);source.load("work/ef.raw");native.setGameVersion(genie::GV_LatestDE2);native.load("work/de.raw");
  if(argc==5){
   std::string name=std::string(argv[4])=="defense"?"SWGB_DEFENSE_LAYOUT":"SWGB_MILITARY_LAYOUT";
   auto e=std::find_if(d.Effects.begin(),d.Effects.end(),[&](const auto &v){return v.Name==name;});
   if(e==d.Effects.end())throw std::runtime_error("Missing construction layout");
   for(int c:{1,2})for(const auto &cmd:e->EffectCommands){
    if(cmd.Type!=0||cmd.C!=defenseLayoutTrainButton||cmd.B!=-1)throw std::runtime_error("Unexpected layout effect");
    d.Civs[c].Units.at(cmd.A).Creatable.TrainLocations.at(0).ButtonID=uint8_t(cmd.D);
   }
  }
  std::ofstream out(argv[3]);out<<"dataset\tciv\tid\tname\tinterface\tclass\tenabled\tlocation\tbutton\thotkey\ticon\n";
  auto dump=[&](genie::DatFile &dat,const char *label,int c){for(size_t id=0;id<dat.Civs[c].Units.size();id++){
   if(!dat.Civs[c].UnitPointers[id])continue;auto &u=dat.Civs[c].Units[id];if(u.Type!=80)continue;
   for(auto &l:u.Creatable.TrainLocations)if(l.LocationID>=0)out<<label<<'\t'<<c<<'\t'<<id<<'\t'<<u.Name<<'\t'<<+u.InterfaceKind<<'\t'<<u.Class<<'\t'<<+u.Enabled<<'\t'<<l.LocationID<<'\t'<<+l.ButtonID<<'\t'<<l.HotKeyID<<'\t'<<u.IconID<<'\n';
  }};
  dump(source,"source",1);dump(source,"source",3);dump(d,"current",1);dump(d,"current",2);dump(native,"native",1);return 0;
 }
 if(std::string(argv[1])=="source-ai-lines"){
  std::ofstream out(argv[3]);out<<"line\tname\tunit\n";
  for(const auto &line:d.UnitLines)for(auto id:line.UnitIDs)out<<line.ID<<'\t'<<line.Name<<'\t'<<id<<'\n';
  return 0;
 }
 if(std::string(argv[1])=="building-state-report"){
  std::ofstream out(argv[3]);
  if(!out)throw std::runtime_error("Cannot open building state report");
  out<<"civ\tunit\tname\tclass\ttrait\tworkrate\tstanding\tconstruction\tresearching\tresearch_completed\tdestruction\trubble\tstack\thead\ttransform\tpile\tbuilt_tech\n";
  for(size_t c=0;c<d.Civs.size()&&c<3;c++)for(size_t id=0;id<d.Civs[c].Units.size();id++){
   if(!d.Civs[c].UnitPointers[id])continue;
   const auto &u=d.Civs[c].Units[id];if(u.Type!=80)continue;const auto &b=u.Building;
   out<<c<<'\t'<<id<<'\t'<<u.Name<<'\t'<<u.Class<<'\t'<<int(u.Trait)<<'\t'<<u.Bird.WorkRate
      <<'\t'<<u.StandingGraphic.first<<'\t'<<b.ConstructionGraphicID<<'\t'<<b.ResearchingGraphic<<'\t'<<b.ResearchCompletedGraphic
      <<'\t'<<b.DestructionGraphicID<<'\t'<<b.DestructionRubbleGraphicID<<'\t'<<b.StackUnitID<<'\t'<<b.HeadUnit
      <<'\t'<<b.TransformUnit<<'\t'<<b.PileUnit<<'\t'<<b.TechID<<'\n';
  }
  if(!out)throw std::runtime_error("Failed to write building state report");
  return 0;
 }
 if(std::string(argv[1])=="repair-building-state-graphics"){
  if(argc!=5)throw std::runtime_error("Expected current DAT, candidate output, native DAT");
  genie::DatFile native;native.setGameVersion(genie::GV_LatestDE2);native.load(argv[4]);
  repairFactionBuildingStateGraphics(d,native);d.saveAs(argv[3]);return 0;
 }
 if(std::string(argv[1])=="audit-building-state-graphics"){
  if(argc!=5)throw std::runtime_error("Expected candidate DAT, restored output, previous DAT");
  genie::DatFile before;before.setGameVersion(genie::GV_LatestDE2);before.load(argv[4]);
  if(d.Civs.size()!=before.Civs.size()||d.Graphics.size()!=before.Graphics.size()+1||d.GraphicPointers.size()!=before.GraphicPointers.size()+1)
   throw std::runtime_error("Unexpected building-state table size");
  int blank=int(before.Graphics.size());const auto &g=d.Graphics.back();
  if(g.ID!=blank||g.Name!="SWGB_EMPTY_BUILDING_STATE"||g.SLP!=-1||!g.FileName.empty()||!g.ParticleEffectName.empty()||!g.Deltas.empty()||g.FrameCount!=1||g.AngleCount!=1||g.SoundID!=-1||g.WwiseSoundID!=0)
   throw std::runtime_error("Invalid empty building-state graphic");
  size_t count=0;
  for(size_t c=0;c<d.Civs.size();c++){
   if(d.Civs[c].Units.size()!=before.Civs[c].Units.size()||d.Civs[c].UnitPointers!=before.Civs[c].UnitPointers)
    throw std::runtime_error("Unexpected building-state unit table change");
   for(size_t i=0;i<d.Civs[c].Units.size();i++)if(d.Civs[c].UnitPointers[i]&&d.Civs[c].Units[i].Type==80){
    auto &u=d.Civs[c].Units[i];const auto &old=before.Civs[c].Units[i];
    auto restore=[&](int16_t &field,int16_t original){
     if(field!=(original<0?blank:original))throw std::runtime_error("Unexpected building-state field");
     if(original<0)count++;field=original;
    };
    restore(u.Building.ResearchingGraphic,old.Building.ResearchingGraphic);
    restore(u.Building.ResearchCompletedGraphic,old.Building.ResearchCompletedGraphic);
    restore(u.Creatable.UpgradeGraphic,old.Creatable.UpgradeGraphic);
   }
  }
  d.Graphics=before.Graphics;d.GraphicPointers=before.GraphicPointers;
  d.saveAs(argv[3]);std::cout<<"Restored "<<count<<" candidate fields for byte-exact collateral comparison.\n";return 0;
 }
 if(std::string(argv[1])=="classic-ai-identity"){
  if(argc!=5)throw std::runtime_error("Expected current DAT, output TSV, source DAT");
  genie::DatFile source;source.setGameVersion(genie::GV_CCV2);source.load(argv[4]);
  std::ofstream out(argv[3]);
  if(!out)throw std::runtime_error("Cannot open identity report");
  out<<"civ\tsource_civ\tslot\tde_id\tde_copy\tde_base\tde_type\tde_class\tsource_id\tsource_copy\tsource_base\tsource_type\tsource_class\tsource_trait\tsource_fog\tsource_line\tde_name\tsource_name\tsource_volley_missile\n";
  for(size_t c=0;c<d.Civs.size();c++){
   if(c>2)throw std::runtime_error("Classic identity export expects only Gaia, Empire and Rebels");
   const auto &s=source.Civs.at(c==2?3:c);const auto &t=d.Civs[c];
   for(size_t id=0;id<t.Units.size();id++){
    if(!t.UnitPointers.at(id))continue;
    if(id>=s.Units.size()||!s.UnitPointers.at(id))throw std::runtime_error("Unmapped Classic unit slot "+std::to_string(id));
    const auto &u=t.Units[id];const auto &v=s.Units[id];
    out<<c<<'\t'<<(c==2?3:c)<<'\t'<<id<<'\t'<<u.ID<<'\t'<<u.CopyID<<'\t'<<u.BaseID<<'\t'<<int(u.Type)<<'\t'<<u.Class
       <<'\t'<<v.ID<<'\t'<<v.CopyID<<'\t'<<v.BaseID<<'\t'<<int(v.Type)<<'\t'<<v.Class<<'\t'<<int(v.Trait)<<'\t'<<int(v.FogVisibility)<<'\t'<<v.Unitline<<'\t'<<u.Name<<'\t'<<v.Name<<'\t'<<(v.Type>=70?v.Creatable.SecondaryProjectileUnit:-1)<<'\n';
   }
  }
  if(!out)throw std::runtime_error("Failed to write identity report");
  return 0;
 }
 if(std::string(argv[1])=="classic-combat-report"){
  if(argc!=5)throw std::runtime_error("Expected current DAT, output directory, source DAT");
  genie::DatFile source;source.setGameVersion(genie::GV_CCV2);source.load(argv[4]);
  classicCombatReport(d,source,argv[3]);return 0;
 }
 if(std::string(argv[1])=="nursery-report"){
  std::ofstream o(argv[3]);
  for(size_t c=0;c<d.Civs.size();c++){
   if(c>2&&c!=42)continue;
   for(size_t id=0;id<d.Civs[c].Units.size();id++){
    if(!d.Civs[c].UnitPointers[id])continue;
    const auto &u=d.Civs[c].Units[id];
    if(u.Class!=58&&id!=319&&id!=320&&id!=321&&id!=322&&!(id>=3550&&id<=3553)&&id!=68)continue;
    o<<"UNIT "<<c<<" "<<id<<" "<<u.Name<<" type="<<+u.Type<<" class="<<u.Class<<" trait="<<+u.Trait<<" size="<<+u.Creatable.CreatableType<<" capacity="<<+u.GarrisonCapacity<<" accepts="<<+u.Building.GarrisonType<<" base="<<u.CopyID<<" default="<<u.Bird.DefaultTaskID<<"\n";
    for(const auto &t:u.Bird.TaskList)o<<"TASK "<<t.ID<<" action="<<t.ActionType<<" target="<<t.UnitID<<" class="<<t.ClassID<<" enabled="<<t.Enabled<<" default="<<+t.IsDefault<<" targeting="<<+t.EnableTargeting<<" auto="<<+t.AutoSearchTargets<<" in="<<t.ResourceIn<<" out="<<t.ResourceOut<<" range="<<t.WorkRange<<"\n";
   }
   o<<"LIVESTOCK_RESOURCE "<<c<<" "<<d.Civs[c].Resources.at(254)<<"\n";
  }
  return 0;
 }
 if(std::string(argv[1])=="economy-report"||std::string(argv[1])=="source-economy-report"){economyReport(d,argv[3]);return 0;}
 if(std::string(argv[1])=="repair-economy"){
  genie::DatFile source,native;source.setGameVersion(genie::GV_CCV2);source.load("work/ef.raw");
  native.setGameVersion(genie::GV_LatestDE2);native.load("work/de.raw");
  repairFactionEconomy(d,source,native);d.saveAs(argv[3]);return 0;
 }
 if(std::string(argv[1])=="audit-economy"){
  if(argc!=5)throw std::runtime_error("Expected candidate, restored output, previous DAT");
  genie::DatFile before;before.setGameVersion(genie::GV_LatestDE2);before.load(argv[4]);
  d.TerrainRestrictions=before.TerrainRestrictions;
  d.Civs.at(0).Units.at(285).Creatable.CreatableType=before.Civs.at(0).Units.at(285).Creatable.CreatableType;
  d.saveAs(argv[3]);return 0;
 }
 if(std::string(argv[1])=="behavior-report"){factionBehaviorReport(d,argv[3]);return 0;}
 if(std::string(argv[1])=="source-interactions"||std::string(argv[1])=="de-interactions"){exportFactionInteractions(d,argv[3]);return 0;}
 if(std::string(argv[1])=="de-dependencies"){std::filesystem::create_directories(argv[3]);factionDependencies(d,argv[3]);return 0;}
 if(std::string(argv[1])=="build-factions"){buildFactions(d,argv[3]);return 0;}
 if(std::string(argv[1])=="source-manifest"||std::string(argv[1])=="de-manifest"){sourceManifest(d,argv[3]);factionBehaviorReport(d,argv[3]);if(std::string(argv[1])=="source-manifest")factionDependencies(d,argv[3]);return 0;}
 if(std::string(argv[1])=="audit-faction-blast"){
  genie::DatFile previous;previous.setGameVersion(genie::GV_LatestDE2);previous.load("work/factions-pre-combat.raw");
  if(d.Civs.size()!=previous.Civs.size())throw std::runtime_error("Blast audit civ mismatch");
  int changed=0;
  for(size_t c=0;c<d.Civs.size();c++){
   if(d.Civs[c].Units.size()!=previous.Civs[c].Units.size())throw std::runtime_error("Blast audit unit mismatch");
   for(size_t id=0;id<d.Civs[c].Units.size();id++){
    auto &u=d.Civs[c].Units[id];const auto &old=previous.Civs[c].Units[id];
    if(d.Civs[c].UnitPointers[id]&&u.Type>=50){
     if(old.Type50.BlastDamage!=0||u.Type50.BlastDamage!=1)throw std::runtime_error("Unexpected blast multiplier");
     u.Type50.BlastDamage=old.Type50.BlastDamage;changed++;
    }
   }
  }
  d.saveAs(argv[3]);std::cout<<"Restored "<<changed<<" explicit blast multipliers for collateral audit.\n";return 0;
 }
 if(std::string(argv[1])=="roundtrip"){d.saveAs(argv[3]);return 0;}
 if(std::string(argv[1])=="audit-behavior"){
  if(argc!=5)throw std::runtime_error("Expected current, restored-output, previous DAT paths");
  genie::DatFile before;before.setGameVersion(genie::GV_LatestDE2);before.load(argv[4]);
  if(d.Civs.size()!=before.Civs.size()||d.Graphics.size()!=before.Graphics.size())throw std::runtime_error("Behavior audit table count changed");
  for(size_t c=0;c<d.Civs.size();c++){
   if(d.Civs[c].Units.size()!=before.Civs[c].Units.size())throw std::runtime_error("Behavior audit unit count changed");
   for(size_t id=0;id<d.Civs[c].Units.size();id++){
    auto &u=d.Civs[c].Units[id];const auto &old=before.Civs[c].Units[id];
    u.Trait=old.Trait;u.CollisionSize=old.CollisionSize;u.Type50.GarrisonFirepower=old.Type50.GarrisonFirepower;
   }
  }
  for(size_t id=0;id<d.Graphics.size();id++)d.Graphics[id].SequenceType=before.Graphics[id].SequenceType;
  d.saveAs(argv[3]);return 0;
 }
 if(std::string(argv[1])=="audit-aircraft-classes"){
  if(argc!=5)throw std::runtime_error("Expected current, restored-output, previous DAT paths");
  genie::DatFile before;before.setGameVersion(genie::GV_LatestDE2);before.load(argv[4]);
  if(d.Civs.size()!=before.Civs.size())throw std::runtime_error("Aircraft audit civ count changed");
  size_t changed=0;
  for(size_t c=0;c<d.Civs.size();c++){
   if(d.Civs[c].Units.size()!=before.Civs[c].Units.size())throw std::runtime_error("Aircraft audit unit count changed");
   for(size_t id=0;id<d.Civs[c].Units.size();id++){
    auto &u=d.Civs[c].Units[id];const auto &old=before.Civs[c].Units[id];
    if(u.Class!=old.Class){
     if(old.Class!=38||(u.Class!=0&&u.Class!=13))throw std::runtime_error("Unexpected class change");
     changed++;
    }
    u.Class=old.Class;u.Bird.TaskList=old.Bird.TaskList;u.Bird.DefaultTaskID=old.Bird.DefaultTaskID;
   }
  }
  // Class-selector expansion is independently verified by source parity.
  // Restore its output to expose any other binary changes against the snapshot.
  d.Effects=before.Effects;d.UnitHeaders=before.UnitHeaders;d.saveAs(argv[3]);
  std::cout<<"Restored "<<changed<<" aircraft classifications and class-selector tables for collateral audit.\n";
  return 0;
 }
 if(std::string(argv[1])=="inspect-ef"){
  genie::DatFile s;s.setGameVersion(genie::GV_CCV2);s.load("work/ef.raw");
  for(int id:{83,448}){std::cout<<"Unit "<<id<<" default task "<<s.Civs[1].Units[id].Bird.DefaultTaskID<<"\n";for(auto &t:s.UnitHeaders[id].TaskList)std::cout<<"task "<<t.ID<<" action "<<t.ActionType<<" class "<<t.ClassID<<" target "<<t.UnitID<<"\n";}
  for(int id:{5090,2337}){auto &p=s.Civs[1].Units.at(id);std::cout<<"Projectile "<<id<<" type "<<int(p.Projectile.ProjectileType)<<" trail "<<p.DeadFish.TrackingUnit<<" mode "<<int(p.DeadFish.TrackingUnitMode)<<" density "<<p.DeadFish.TrackingUnitDensity<<" speed "<<p.Speed<<"\n";if(p.DeadFish.TrackingUnit>=0){auto &t=s.Civs[1].Units.at(p.DeadFish.TrackingUnit);std::cout<<" Trail "<<t.Name<<" standing "<<t.StandingGraphic.first<<" dying "<<t.DyingGraphic<<" type "<<int(t.Type)<<" decay "<<t.ResourceDecay<<" hp "<<t.HitPoints<<" tracking "<<t.DeadFish.TrackingUnit<<"\n";}}
  {auto &t=d.Civs[1].Units.at(247);std::cout<<"Native trail type "<<int(t.Type)<<" decay "<<t.ResourceDecay<<" hp "<<t.HitPoints<<"\n";}
  for(int c=1;c<=8;c++){
   const auto &u=s.Civs[c].Units.at(70);const auto &g=s.Graphics.at(u.StandingGraphic.first);
   std::cout<<"Civ "<<c<<" house "<<u.StandingGraphic.first<<" construction "<<u.Building.ConstructionGraphicID<<" death "<<u.DyingGraphic<<"\n";
   for(auto x:u.DamageGraphics)std::cout<<" damage "<<x.GraphicID<<" at "<<x.DamagePercent<<" mode "<<int(x.ApplyMode)<<"\n";
   auto &cg=s.Graphics.at(u.Building.ConstructionGraphicID);std::cout<<" construction slp "<<cg.SLP<<" frames "<<cg.FrameCount<<" deltas "<<cg.Deltas.size()<<"\n";
   for(const auto &delta:g.Deltas){auto &a=s.Graphics.at(delta.GraphicID);std::cout<<"  delta "<<delta.GraphicID<<" "<<a.Name<<" slp "<<a.SLP<<" frames "<<a.FrameCount<<" offsets "<<delta.OffsetX<<","<<delta.OffsetY<<"\n";}
  }return 0;
 }
 if(std::string(argv[1])=="civ-probe"){
  genie::DatFile native;native.setGameVersion(genie::GV_LatestDE2);native.load("work/de.raw");
  auto empire=d.Civs.at(1),rebels=d.Civs.at(2);empire.Name="SWGB-EMPIRE";rebels.Name="SWGB-REBELS";
  for(size_t c=0;c<native.Civs.size();c++)for(size_t u=0;u<native.Civs[c].Units.size();u++)d.Civs[c].Units[u]=native.Civs[c].Units[u];
  d.Civs.push_back(empire);d.Civs.push_back(rebels);
  d.setGameVersion(genie::GV_LatestDE2);d.saveAs(argv[3]);
  std::cerr<<"Civ selection probe: "<<d.Civs.size()<<" civ entries. Native units restored; new faction technology progression remains experimental.\n";return 0;
 }
 if(std::string(argv[1])=="audit"||std::string(argv[1])=="audit-houses"){
  genie::DatFile original;original.setGameVersion(genie::GV_LatestDE2);original.load("work/de.raw");
  auto bytes=[](auto &object){std::ostringstream stream(std::ios::binary);object.writeObject(stream);return stream.str();};
  if(d.Civs.size()!=original.Civs.size())throw std::runtime_error("Civ count changed");
  for(size_t c=0;c<d.Civs.size();c++){
   auto &civ=d.Civs[c];auto &base=original.Civs[c];
   if(std::string(argv[1])=="audit-houses")for(int offset=0;offset<2;offset++){
    auto &bolt=civ.Units.at(base.Units.size()+offset);int trailId=base.Units.size()+3+offset;
    if(bolt.DeadFish.TrackingUnit!=trailId || bolt.DeadFish.TrackingUnitMode!=2 || std::abs(bolt.DeadFish.TrackingUnitDensity-0.035f)>0.000001f)throw std::runtime_error("Invalid blaster tracking configuration");
    auto &trail=civ.Units.at(trailId);if(trail.Type!=20 || trail.DeadFish.TrackingUnit!=-1 || trail.StandingGraphic.first<0)throw std::runtime_error("Invalid trail effect unit");
   }
   if(civ.Units.size()!=base.Units.size()+(std::string(argv[1])=="audit-houses"?5:3) || civ.UnitPointers.size()!=base.UnitPointers.size()+(std::string(argv[1])=="audit-houses"?5:3))throw std::runtime_error("Unexpected appended units");
   if(c)for(int id:{4,24,492,279,542}){
    auto copy=civ.Units[id];auto &b=base.Units[id];
    copy.Name=b.Name;copy.LanguageDLLName=b.LanguageDLLName;copy.StandingGraphic=b.StandingGraphic;
    copy.DeadFish.WalkingGraphic=b.DeadFish.WalkingGraphic;copy.Type50.AttackGraphic=b.Type50.AttackGraphic;
    copy.Type50.AttackGraphic2=b.Type50.AttackGraphic2;copy.Creatable.IdleAttackGraphic=b.Creatable.IdleAttackGraphic;
    copy.DyingGraphic=b.DyingGraphic;copy.UndeadGraphic=b.UndeadGraphic;copy.DeadUnitID=b.DeadUnitID;
    copy.Type50.FrameDelay=b.Type50.FrameDelay;copy.Type50.ProjectileUnitID=b.Type50.ProjectileUnitID;
    if(bytes(copy)!=bytes(b))throw std::runtime_error("Unexpected unit gameplay change: "+std::to_string(c)+":"+std::to_string(id));
    civ.Units[id]=b;
   }
   if(c)for(int id:{3,26,496}){auto copy=civ.Units[id];auto &b=base.Units[id];copy.StandingGraphic=b.StandingGraphic;if(bytes(copy)!=bytes(b))throw std::runtime_error("Unexpected corpse changes");civ.Units[id]=b;}
   if(std::string(argv[1])=="audit-houses" && (c==1||c==2))for(int id:{70,463,464,465}){
    auto copy=civ.Units[id];auto &b=base.Units[id];copy.StandingGraphic=b.StandingGraphic;
    copy.Building.ConstructionGraphicID=b.Building.ConstructionGraphicID;copy.Building.SnowGraphicID=b.Building.SnowGraphicID;copy.DamageGraphics=b.DamageGraphics;
    if(bytes(copy)!=bytes(b))throw std::runtime_error("Unexpected house gameplay changes");civ.Units[id]=b;
   }
   civ.Units.resize(base.Units.size());civ.UnitPointers.resize(base.UnitPointers.size());
  }
  d.Graphics.resize(original.Graphics.size());d.GraphicPointers.resize(original.GraphicPointers.size());
  d.saveAs(argv[3]);std::cerr<<"Normalized known modifications; compare output byte-for-byte with native raw DAT\n";return 0;
 }
 if(std::string(argv[1])=="build"||std::string(argv[1])=="build-next"||std::string(argv[1])=="build-houses"){
  bool houses=std::string(argv[1])=="build-houses";
  bool next=std::string(argv[1])!="build";
  genie::DatFile src;src.setGameVersion(genie::GV_CCV2);src.load("work/ef.raw");
  std::map<int,int> mapped;std::ofstream manifest(houses?"work/building-graphic-mapping.tsv":next?"work/next-graphic-mapping.tsv":"outputs/graphic-mapping.tsv");manifest<<"source\ttarget\tslp\tfilename\n";
  std::function<int(int)> graphic=[&](int id)->int{
   if(id<0)return -1;if(mapped.count(id))return mapped[id];
   auto s=src.Graphics.at(id);int newId=(int)d.Graphics.size();mapped[id]=newId;
   bool composite=houses && (s.SLP<0 || (s.SLP<6 && !s.Deltas.empty()));
   auto g=d.Graphics.at(houses && id<2000 && s.AngleCount==1?2197:633);g.ID=newId;g.Name="SWGB_"+std::to_string(id);g.FileName="swgb_"+std::to_string(id)+"_x1";g.SLP=composite?-1:900000+id;if(composite)g.FileName="";
   g.FirstFrame=0;g.FrameCount=s.FrameCount;g.AngleCount=s.AngleCount;g.MirroringMode=s.MirroringMode;g.FrameDuration=s.FrameDuration;g.AnimationDuration=s.FrameCount*s.FrameDuration;g.ReplayDelay=s.ReplayDelay;g.SequenceType=s.SequenceType;g.Layer=s.Layer;
   g.SoundID=-1;g.WwiseSoundID=0;g.AngleSoundsUsed=0;g.AngleSounds.clear();g.Deltas.clear();g.ParticleEffectName="";
   g.Coordinates=s.Coordinates;for(auto &v:g.Coordinates)v*=1;
   d.Graphics.push_back(g);d.GraphicPointers.push_back(1);
   for(auto delta:s.Deltas){delta.GraphicID=graphic(delta.GraphicID);delta.OffsetX*=1;delta.OffsetY*=1;delta.setGameVersion(genie::GV_LatestDE2);d.Graphics[newId].Deltas.push_back(delta);}
   manifest<<id<<'\t'<<newId<<'\t'<<(composite?-1:s.SLP)<<'\t'<<g.FileName<<'\n';return newId;
  };
  int empireProjectile=-1,rebelProjectile=-1;
  if(next){
   for(int sourceId:{5090,2337}){
    // Modern DE stores task lists in each civ unit, not the legacy UnitHeaders array.
    int id=d.Civs.at(0).Units.size();
    const auto &s=src.Civs[1].Units.at(sourceId);
    for(auto &civ:d.Civs){
     if(civ.Units.size()!=id||civ.UnitPointers.size()!=id)throw std::runtime_error("Nonuniform native unit arrays: header="+std::to_string(id)+" units="+std::to_string(civ.Units.size())+" pointers="+std::to_string(civ.UnitPointers.size()));
     auto p=civ.Units.at(363);p.ID=id;p.CopyID=id;p.BaseID=id;p.Name=sourceId==5090?"SWGB Empire Blaster":"SWGB Rebel Blaster";
     p.StandingGraphic={graphic(s.StandingGraphic.first),-1};p.DeadFish.WalkingGraphic=graphic(s.DeadFish.WalkingGraphic);p.DyingGraphic=graphic(s.DyingGraphic);p.DeadUnitID=-1;p.UndeadGraphic=-1;p.Projectile.ProjectileArc=0;p.Speed=s.Speed;
     civ.Units.push_back(p);civ.UnitPointers.push_back(1);
    }
    if(sourceId==5090)empireProjectile=id;else rebelProjectile=id;
   }
  }
  for(size_t c=1;c<d.Civs.size();c++){
   int sourceUnit=c==2?460:448;auto &s=src.Civs[1].Units[sourceUnit];
   for(int id:{4,24,492}){auto &u=d.Civs[c].Units[id];u.StandingGraphic={graphic(s.StandingGraphic.first),-1};u.DeadFish.WalkingGraphic=graphic(s.DeadFish.WalkingGraphic);u.Type50.AttackGraphic=graphic(s.Type50.AttackGraphic);u.Type50.AttackGraphic2=-1;u.DyingGraphic=graphic(s.DyingGraphic);u.Creatable.IdleAttackGraphic=-1;u.Type50.FrameDelay=std::min<int>(u.Type50.FrameDelay,src.Graphics[s.Type50.AttackGraphic].FrameCount-1);auto &dead=d.Civs[c].Units[u.DeadUnitID];dead.StandingGraphic={graphic(src.Civs[1].Units[s.DeadUnitID].StandingGraphic.first),-1};if(next){u.Type50.ProjectileUnitID=c==2?rebelProjectile:empireProjectile;u.Type50.FrameDelay=s.Type50.FrameDelay;}}
  }
  int mechCorpse=-1;
  if(next){
   mechCorpse=d.Civs[0].Units.size();
   for(auto &civ:d.Civs){auto corpse=civ.Units.at(civ.Units.at(279).DeadUnitID);corpse.ID=mechCorpse;corpse.CopyID=mechCorpse;corpse.BaseID=mechCorpse;corpse.StandingGraphic={graphic(6474),-1};civ.Units.push_back(corpse);civ.UnitPointers.push_back(1);}
  }
  if(next)for(size_t c=1;c<d.Civs.size();c++){
   for(int id:{4,24,492})d.Civs[c].Units[id].LanguageDLLName=600000+(c==2?1:0);
   const auto &s=src.Civs[1].Units.at(485);
   for(int id:{279,542}){
    auto &u=d.Civs[c].Units[id];u.Name="SWGB Imperial Mech";u.LanguageDLLName=600002;
    u.StandingGraphic={graphic(s.StandingGraphic.first),-1};u.DeadFish.WalkingGraphic=graphic(s.DeadFish.WalkingGraphic);
    u.Type50.AttackGraphic=graphic(s.Type50.AttackGraphic);u.Type50.AttackGraphic2=-1;u.Creatable.IdleAttackGraphic=-1;
    u.DyingGraphic=graphic(s.DyingGraphic);u.UndeadGraphic=-1;u.Type50.FrameDelay=s.Type50.FrameDelay;
    u.DeadUnitID=mechCorpse;
   }
  }
  if(houses)for(int sourceProjectile:{5090,2337}){
   const auto &p=src.Civs[1].Units.at(sourceProjectile);const auto &s=src.Civs[1].Units.at(p.DeadFish.TrackingUnit);
   int id=d.Civs[0].Units.size();
   for(auto &civ:d.Civs){
    auto trail=civ.Units.at(247);trail.ID=id;trail.CopyID=id;trail.BaseID=id;trail.Name="SWGB Blaster Trail";
    trail.StandingGraphic={graphic(s.StandingGraphic.first),-1};trail.DyingGraphic=graphic(s.DyingGraphic);trail.UndeadGraphic=-1;trail.DeadUnitID=-1;
    trail.ResourceDecay=s.ResourceDecay;trail.ResourceStorages=s.ResourceStorages;trail.DeadFish.TrackingUnit=-1;
    civ.Units.push_back(trail);civ.UnitPointers.push_back(1);
    auto &bolt=civ.Units.at(sourceProjectile==5090?empireProjectile:rebelProjectile);
    bolt.DeadFish.TrackingUnit=id;bolt.DeadFish.TrackingUnitMode=p.DeadFish.TrackingUnitMode;bolt.DeadFish.TrackingUnitDensity=p.DeadFish.TrackingUnitDensity;
   }
  }
  if(houses)for(int c:{1,2}){
   const auto &s=src.Civs[c==1?1:3].Units.at(70);
   for(int id:{70,463,464,465}){
    auto &u=d.Civs[c].Units[id];u.StandingGraphic={graphic(s.StandingGraphic.first),-1};
    u.Building.ConstructionGraphicID=graphic(s.Building.ConstructionGraphicID);u.Building.SnowGraphicID=-1;
    u.DamageGraphics=s.DamageGraphics;for(auto &x:u.DamageGraphics){x.GraphicID=graphic(x.GraphicID);x.setGameVersion(genie::GV_LatestDE2);}
   }
  }
  // Full native DE economy, technologies and AI remain the playable foundation.
  d.setGameVersion(genie::GV_LatestDE2);d.saveAs(argv[3]);std::cerr<<"Built "<<mapped.size()<<" graphics\n";return 0;
 }
 std::cerr<<d.FileVersion<<" civs="<<d.Civs.size()<<" graphics="<<d.Graphics.size()<<std::endl;
 std::ofstream detail(std::string(argv[3])+"-details.tsv");detail<<"civ\tcivname\tunit\tname\tprojectile\tattackdelay\tstanding2\tconstruction\n";
 for(size_t c=0;c<d.Civs.size();c++)for(int id:{4,24,83,109,448,460,469,485,495,279,542}){auto &x=d.Civs[c].Units[id];detail<<c<<'\t'<<d.Civs[c].Name<<'\t'<<id<<'\t'<<x.Name<<'\t'<<x.Type50.ProjectileUnitID<<'\t'<<x.Type50.FrameDelay<<'\t'<<x.StandingGraphic.second<<'\t'<<x.Building.ConstructionGraphicID<<'\n';}
 std::ofstream terrain(std::string(argv[3])+"-terrains.tsv");for(size_t i=0;i<d.TerrainBlock.Terrains.size();i++)terrain<<i<<'\t'<<d.TerrainBlock.Terrains[i].Name<<'\n';
 std::ofstream g(std::string(argv[3])+"-graphics.tsv");g<<"id\tname\tfile\tslp\tframes\tangles\tduration\tmirror\n";
 for(size_t i=0;i<d.Graphics.size();++i){auto &x=d.Graphics[i];g<<i<<'\t'<<x.Name<<'\t'<<x.FileName<<'\t'<<x.SLP<<'\t'<<x.FrameCount<<'\t'<<x.AngleCount<<'\t'<<x.FrameDuration<<'\t'<<int(x.MirroringMode)<<'\n';}
 std::ofstream u(std::string(argv[3])+"-units.tsv");u<<"civ\tid\tname\tstanding\twalking\tattack\tdying\tdead\n";
 for(size_t c=0;c<d.Civs.size();++c)for(size_t i=0;i<d.Civs[c].Units.size();++i){auto &x=d.Civs[c].Units[i];u<<c<<'\t'<<i<<'\t'<<x.Name<<'\t'<<x.StandingGraphic.first<<'\t'<<x.DeadFish.WalkingGraphic<<'\t'<<x.Type50.AttackGraphic<<'\t'<<x.DyingGraphic<<'\t'<<x.DeadUnitID<<'\n';}
 return 0;
}
int main(int argc,char**argv){try{return run(argc,argv);}catch(const std::exception &e){std::cerr<<"ERROR: "<<e.what()<<std::endl;return 2;}}


