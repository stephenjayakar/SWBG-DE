#pragma once
// Serialized diagnostics for fields whose semantics differ between SWGB and DE.
inline void factionBehaviorReport(genie::DatFile &d,const std::string &path){
 std::filesystem::create_directories(path);
 std::ofstream units(path+"/compat-units.tsv"),damage(path+"/compat-damage.tsv"),graphics(path+"/compat-graphics.tsv");
 units<<"civ\tunit\tname\ttype\tclass\ttrait\tx\ty\tz\tfirepower\tprojectiles\tmax_projectiles\tsecondary\tcan_burn\n";
 damage<<"civ\tunit\tgraphic\tpercent\tmode\n";
 graphics<<"graphic\tname\tslp\tfirst\tframes\tangles\tmirror\tsequence\tlayer\tcolor\tplayer\tspeed\n";
 for(size_t c=0;c<d.Civs.size();c++){
  if(c!=0&&c!=1&&c!=(d.Civs.size()==3?2:3))continue;
  for(size_t id=0;id<d.Civs[c].Units.size();id++){
   if(!d.Civs[c].UnitPointers[id])continue;const auto &u=d.Civs[c].Units[id];
   units<<c<<'\t'<<id<<'\t'<<u.Name<<'\t'<<int(u.Type)<<'\t'<<u.Class<<'\t'<<int(u.Trait)<<'\t'<<u.CollisionSize.x<<'\t'<<u.CollisionSize.y<<'\t'<<u.CollisionSize.z<<'\t'<<u.Type50.GarrisonFirepower<<'\t'<<u.Creatable.TotalProjectiles<<'\t'<<int(u.Creatable.MaxTotalProjectiles)<<'\t'<<u.Creatable.SecondaryProjectileUnit<<'\t'<<int(u.Building.CanBurn)<<'\n';
   for(const auto &g:u.DamageGraphics)damage<<c<<'\t'<<id<<'\t'<<g.GraphicID<<'\t'<<g.DamagePercent<<'\t'<<int(g.ApplyMode)<<'\n';
  }
 }
 for(size_t id=0;id<d.Graphics.size();id++)if(d.GraphicPointers[id]){
  const auto &g=d.Graphics[id];graphics<<id<<'\t'<<g.Name<<'\t'<<g.SLP<<'\t'<<g.FirstFrame<<'\t'<<g.FrameCount<<'\t'<<g.AngleCount<<'\t'<<int(g.MirroringMode)<<'\t'<<int(g.SequenceType)<<'\t'<<int(g.Layer)<<'\t'<<int(g.OldColorFlag)<<'\t'<<g.PlayerColor<<'\t'<<g.SpeedMultiplier<<'\n';
 }
}
