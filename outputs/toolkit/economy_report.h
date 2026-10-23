#pragma once
// Focused read-only placement/render diagnostics; accepts source or DE data.
inline void economyReport(genie::DatFile &d,const std::string &path){
 std::ofstream o(path);
 for(size_t id=0;id<d.Civs[0].Units.size();id++){
  if(!d.Civs[0].UnitPointers[id])continue;
  auto &u=d.Civs[0].Units[id];
  for(auto &r:u.ResourceStorages)if(r.Type>=0&&r.Type<4&&r.Amount>0)
   o<<"RESOURCE\t"<<id<<"\t"<<u.Name<<"\t"<<u.Class<<"\t"<<r.Type<<"\t"<<r.Amount<<"\t"<<+r.Flag<<"\n";
 }
 for(int c:{0,1,2,3}){
  if(c>=int(d.Civs.size()))continue;
  for(int id:{50,66,285,357,109,68,102,83,293,118}){
   auto &u=d.Civs[c].Units.at(id);
   o<<"UNIT "<<c<<" "<<id<<" "<<u.Name<<" pointer="<<d.Civs[c].UnitPointers[id]<<"\n";
#define FIELD(x) o<<#x<<"="<<+u.x<<" ";
   FIELD(Type) FIELD(Class) FIELD(HitPoints) FIELD(TerrainRestriction)
   FIELD(Enabled) FIELD(Disabled) FIELD(ObstructionType) FIELD(ObstructionClass)
   FIELD(CanBeBuiltOn) FIELD(HillMode) FIELD(FogVisibility) FIELD(FlyMode)
   FIELD(SelectionEffect) FIELD(MinimapMode) FIELD(InteractionMode) FIELD(ResourceGatherGroup) FIELD(Bird.TaskSwapGroup) FIELD(Bird.WorkRate)
   FIELD(Building.StackUnitID) FIELD(Building.HeadUnit) FIELD(Building.AdjacentMode)
   FIELD(Building.FoundationTerrainID) FIELD(Building.DisappearsWhenBuilt)
   FIELD(Building.OldOverlayID) FIELD(Building.PileUnit) FIELD(Creatable.CreatableType)
   FIELD(Creatable.SpecialAbility) FIELD(DeadUnitID)
#undef FIELD
   o<<" collision="<<u.CollisionSize.x<<","<<u.CollisionSize.y<<","<<u.CollisionSize.z
    <<" clearance="<<u.ClearanceSize.first<<","<<u.ClearanceSize.second<<"\n";
   for(auto &r:u.ResourceStorages)o<<" storage="<<r.Type<<":"<<r.Amount<<":"<<+r.Flag;
   o<<"\n";
   int g=u.StandingGraphic.first;
   if(g>=0){auto &a=d.Graphics[g];o<<" graphic="<<g<<" file="<<a.FileName<<" slp="<<a.SLP<<" layer="<<+a.Layer<<" flags="<<+a.TransparentSelection<<" color="<<+a.OldColorFlag<<" frames="<<a.FrameCount<<" angles="<<a.AngleCount<<"\n";
    for(auto &delta:a.Deltas)o<<" delta="<<delta.GraphicID<<"\n";
   }
  }
 }
 for(int t=0;t<int(d.TerrainBlock.Terrains.size());t++){auto &a=d.TerrainBlock.Terrains.at(t);o<<"TERRAIN "<<t<<" name="<<a.Name<<" water="<<+a.IsWater<<" draw="<<a.TerrainToDraw<<"\n";}
 for(int r:{4,7,8}){
  o<<"RESTRICTION "<<r<<"\n";
  auto &row=d.TerrainRestrictions.at(r).PassableBuildableDmgMultiplier;
  for(int t=0;t<int(row.size());t++)if(t<42||row[t]!=0)o<<t<<":"<<row[t]<<" ";
  o<<"\n";
 }
}
