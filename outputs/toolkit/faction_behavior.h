#pragma once
inline void adaptFactionBehavior(genie::DatFile &target,const genie::DatFile &source,const genie::DatFile &native){
 const std::set<int> airClasses={43,48,62,63,64};
 const float workerFirepower=native.Civs.at(1).Units.at(83).Type50.GarrisonFirepower;
 const float trooperFirepower=native.Civs.at(1).Units.at(4).Type50.GarrisonFirepower;
 if(workerFirepower!=-2.5f||trooperFirepower!=1.f)throw std::runtime_error("Native garrison reference changed");
 std::set<int> airGraphics;
 std::function<void(int)> collect=[&](int id){
  if(id<0||!airGraphics.insert(id).second)return;
  for(const auto &delta:source.Graphics.at(id).Deltas)collect(delta.GraphicID);
 };
 for(size_t c=0;c<target.Civs.size();c++)for(size_t id=0;id<target.Civs[c].Units.size();id++){
  if(!target.Civs[c].UnitPointers[id])continue;
  auto &u=target.Civs[c].Units[id];const auto &s=source.Civs[c==2?3:c].Units[id];
  // Only garrison/ship bits have the same meaning. SWGB detector/stealth/
  // mechanical bits must not become DE transform/build/auto-scout abilities.
  u.Trait&=3;
  if(s.Type==70&&s.Class==47)u.Trait|=16;
  if(s.Type==70&&s.Class==58)u.Type50.GarrisonFirepower=workerFirepower;
  if(s.Type==70&&(s.Class==52||s.Class==55))u.Type50.GarrisonFirepower=trooperFirepower;
  if(s.Type>=70&&s.FlyMode==1&&airClasses.count(s.Class)){
   // DE has no SWGB airspace manager. Zero collision is the established
   // commanded-flight adapter (SiegeEngineers/auto-mods flying_dutchman).
   // Preserve selection geometry, flight altitude, terrain rules and weapons.
   u.CollisionSize={0,0,0};
   collect(s.StandingGraphic.first);collect(s.StandingGraphic.second);
   collect(s.DeadFish.WalkingGraphic);collect(s.DeadFish.RunningGraphic);
   collect(s.Type50.AttackGraphic);
  }
 }
 for(int id:airGraphics){
  auto &g=target.Graphics.at(id);
  if((g.AngleCount==8||g.AngleCount==16)&&g.MirroringMode!=0)g.SequenceType|=2;
 }
}
