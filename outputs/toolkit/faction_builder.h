#pragma once
#include <set>
#include "faction_classes.h"
#include "faction_resources.h"
#include "faction_terrain.h"
#include "faction_audio.h"
#include "faction_scout.h"
#include "faction_icons.h"
#include "faction_tree.h"
#include "faction_graphic_repairs.h"
#include "faction_power.h"
#include "faction_hotkeys.h"
#include "faction_defenses.h"
#include "faction_defense_extension.h"
#include "faction_build_menu.h"
#include "faction_defense_shields.h"
#include "faction_marker.h"
#include "faction_language.h"
#include "faction_task_graphics.h"
#include "faction_force.h"
#include "faction_behavior.h"
#include "faction_economy_repair.h"
// Unit slots keep their SWGB IDs here (source parity checks depend on it). DE reserves 900-999 for
// class groups; reserved-unit-id-remap.json moves those units when the DAT is packaged
// (install_parity_dat.py / package_factions.py, see reserved_unit_ids.py).
inline void buildFactions(genie::DatFile &target,const std::string &output){
 genie::DatFile source;source.setGameVersion(genie::GV_CCV2);source.load("work/ef.raw");
 const auto gv=genie::GV_LatestDE2;
 genie::DatFile native;native.setGameVersion(gv);native.load("work/de.raw");
 // Keep the native terrain/UI/schema envelope, importing source indices intact.
 // This intermediate is not installable until graphics and engine semantics pass.
 target.Civs={source.Civs.at(0),source.Civs.at(1),source.Civs.at(3)};
 target.Civs[1].Name="SWGB-EMPIRE";target.Civs[2].Name="SWGB-REBELS";
 target.Effects=source.Effects;target.Techs=source.Techs;
 for(size_t id=0;id<target.Techs.size();id++){
  auto &t=target.Techs[id];
  t.LanguageDLLName=factionLanguageName(true,0,int(id));t.LanguageDLLDescription=t.LanguageDLLName+1000;
  t.LanguageDLLHelp=t.LanguageDLLName+100000;t.LanguageDLLTechTree=t.LanguageDLLName+140000;
  if(t.Civ==3)t.Civ=2;else if(t.Civ>=2)t.Civ+=10;
 }
 // Source TL3 has three invalid placeholder upgrades; DE indexes unit[-1].
 auto &tl3=target.Effects.at(2).EffectCommands;
 int omitted=0;
 for(auto it=tl3.begin();it!=tl3.end();){
  if(it->Type==3&&it->A==-1&&it->B==-1&&it->C==-1&&it->D==0){it=tl3.erase(it);omitted++;}
  else ++it;
 }
 if(omitted!=3)throw std::runtime_error("Unexpected TL3 placeholder layout");
 for(auto &effect:target.Effects)for(auto &e:effect.EffectCommands)
  if(e.Type==3&&(e.A<0||e.B<0))throw std::runtime_error("Invalid unit upgrade endpoint");
 target.UnitHeaders=source.UnitHeaders;
 target.Graphics=source.Graphics;target.GraphicPointers=source.GraphicPointers;
 std::ofstream art("work/faction-art-mapping.tsv");art<<"source\ttarget\tslp\tfilename\n";
 for(size_t id=0;id<target.Graphics.size();id++){
  auto &g=target.Graphics[id];if(!target.GraphicPointers[id])continue;
  bool parent=g.SLP<6||absentFactionOverlay(int(id),source);
  g.Name="SWGB_"+std::to_string(id);g.FileName=parent?"":"swgb_"+std::to_string(id)+"_x1";
  art<<id<<'\t'<<id<<'\t'<<(parent?-1:g.SLP)<<'\t'<<g.FileName<<'\n';
  g.SLP=parent?-1:900000+id;g.SoundID=-1;g.WwiseSoundID=0;g.AngleSoundsUsed=0;g.AngleSounds.clear();
  g.AnimationDuration=g.FrameDuration*g.FrameCount;g.ParticleEffectName="";
 }
 for(size_t c=0;c<target.Civs.size();c++){
  auto &civ=target.Civs[c];
  for(size_t id=0;id<civ.Units.size();id++){
   auto &u=civ.Units[id];if(!civ.UnitPointers[id])continue;
   if(id<source.UnitHeaders.size()&&u.Type>=40)u.Bird.TaskList=source.UnitHeaders[id].TaskList;
   u.LanguageDLLName=factionLanguageName(false,int(c),int(id));u.LanguageDLLCreation=u.LanguageDLLName+1000;
   u.LanguageDLLHelp=u.LanguageDLLName+100000;u.LanguageDLLHotKeyText=u.LanguageDLLName+140000;
   // Prevent foreign sound IDs from resolving to unrelated DE voice events.
   u.TrainSound=-1;u.WwiseTrainSoundID=0;
   u.Building.TransformSound=-1;u.Building.ConstructionSound=-1;u.Building.WwiseTransformSoundID=0;u.Building.WwiseConstructionSoundID=0;
   for(auto &t:u.Bird.TaskList){t.ResourceGatheringSoundID=-1;t.ResourceDepositSoundID=-1;t.WwiseResourceGatheringSoundID=0;t.WwiseResourceDepositSoundID=0;}
   u.SelectionSound=-1;u.DyingSound=-1;u.DamageSound=-1;u.WwiseSelectionSoundID=0;u.WwiseDyingSoundID=0;u.WwiseDamageSoundID=0;
   u.Bird.AttackSound=-1;u.Bird.MoveSound=-1;u.Bird.WwiseAttackSoundID=0;u.Bird.WwiseMoveSoundID=0;
  }
 }
 // SWGB's area attack applies the normal attack modifier. DE stores a
 // separate splash multiplier; the field is absent in the source schema.
 for(auto &civ:target.Civs)for(size_t id=0;id<civ.Units.size();id++)
  if(civ.UnitPointers[id]&&civ.Units[id].Type>=50)civ.Units[id].Type50.BlastDamage=1.0f;
 importFactionAudio(target,source);
 importFactionTaskGraphics(target,source);
 translateFactionTerrain(target,source);
 target.Civs.at(0).Units.at(285).Creatable.CreatableType=native.Civs.at(0).Units.at(285).Creatable.CreatableType;
 translateFactionResources(target,native);
 translateFactionClasses(target,source);
 importFactionIcons(target,source);
 adaptFactionForce(target,source,native);
 adaptFactionScout(target,source);
 adaptFactionBehavior(target,source,native);
 importFactionTree(target,source);
 importFactionPower(target,source,native);
 // Keep age advancement away from source availability techs sharing slot 9.
 for(int age:{1,2,3})for(auto &location:target.Techs.at(age).ResearchLocations){
  if(location.LocationID!=109||location.ButtonID!=9)throw std::runtime_error("Unexpected source age-up location");
  location.ButtonID=10;
 }
 repairFactionDefenses(target);
 extendFactionDefenses(target,source);
 addFactionDefenseShields(target,source,native);
 importFactionHotkeys(target);
 finalizeFactionBuildMenu(target);
 importFactionMarker(target,native);
 target.setGameVersion(gv);target.saveAs(output.c_str());
 std::cout<<"Source-rule intermediate: "<<target.Civs.size()<<" civs, "<<target.Civs[1].Units.size()<<" unit slots/civ, "<<target.Techs.size()<<" technologies. Not engine-validated.\n";
}
