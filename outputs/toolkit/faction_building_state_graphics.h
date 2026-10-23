#pragma once

// Compatibility candidate for DE building-state transitions. SWGB has none of
// these DE-only indicator fields. Supply a valid invisible sprite object so a
// native transition cannot dereference a missing indicator graphic. This does
// not establish that the reported RVA is one of these three fields.
inline void repairFactionBuildingStateGraphics(genie::DatFile &target,const genie::DatFile &native){
 int blank=-1;
 for(size_t i=0;i<target.Graphics.size();i++)if(target.GraphicPointers[i]&&target.Graphics[i].Name=="SWGB_EMPTY_BUILDING_STATE"){
  if(blank>=0)throw std::runtime_error("Duplicate building-state placeholder");blank=int(i);
 }
 if(blank<0){
  const auto &prototype=native.Graphics.at(12293);
  if(prototype.Name!="ResearchCompleteGlow 3x3"||prototype.SLP!=-1||prototype.FrameCount!=1||prototype.AngleCount!=1||!prototype.Deltas.empty())
   throw std::runtime_error("Native research indicator template changed");
  if(target.Graphics.size()>=32767)throw std::runtime_error("No signed graphic ID available");
  auto g=prototype;blank=int(target.Graphics.size());g.ID=int16_t(blank);
  g.Name="SWGB_EMPTY_BUILDING_STATE";g.FileName="";g.SLP=-1;g.ParticleEffectName="";
  g.SoundID=-1;g.WwiseSoundID=0;g.AngleSoundsUsed=0;g.AngleSounds.clear();
  target.Graphics.push_back(g);target.GraphicPointers.push_back(1);
 }
 const auto &g=target.Graphics.at(blank);
 if(g.SLP!=-1||!g.FileName.empty()||!g.ParticleEffectName.empty()||!g.Deltas.empty()||g.FrameCount!=1||g.AngleCount!=1)
  throw std::runtime_error("Building-state placeholder is not empty");
 size_t changed=0;
 for(auto &civ:target.Civs)for(size_t id=0;id<civ.Units.size();id++)if(civ.UnitPointers[id]&&civ.Units[id].Type==80){
  auto &u=civ.Units[id];
  for(auto field:{&u.Building.ResearchingGraphic,&u.Building.ResearchCompletedGraphic,&u.Creatable.UpgradeGraphic})
   if(*field<0){*field=int16_t(blank);changed++;}
 }
 std::cout<<"Building-state graphics candidate: "<<changed<<" missing fields bound to empty graphic "<<blank<<". Not runtime verified.\n";
}
