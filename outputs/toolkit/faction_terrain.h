#pragma once
// AGE's legacy IsWater field is a bitmask in DE (32=land, 128=snow).
// Native farm construction uses three terrain IDs; SWGB uses one land stage.
inline int factionFallbackTerrain(int id,uint8_t flags){
 if(id>=29&&id<=31)return 29;
 if(flags&8)return 28;
 if(flags&16)return 2;
 if(flags&7)return 1;
 if(flags&64)return 35;
 if(flags&128)return 32;
 return 0;
}
inline void translateFactionTerrain(genie::DatFile &target,const genie::DatFile &source){
 std::ifstream input("work/faction-terrain-map.tsv");if(!input)throw std::runtime_error("Missing faction terrain mapping");
 std::map<int,int> forward,reverse;std::string line;std::getline(input,line);
 while(std::getline(input,line)){std::istringstream row(line);std::string name;int s,t,canonical;row>>name>>s>>t>>canonical;forward[s]=t;if(canonical)reverse[t]=s;}
 auto mapTerrain=[&](int id){if(id<0)return id;auto p=forward.find(id);if(p==forward.end())throw std::runtime_error("Unmapped placement/task terrain "+std::to_string(id));return p->second;};
 target.TerrainRestrictions=source.TerrainRestrictions;
 target.FloatPtrTerrainTables=source.FloatPtrTerrainTables;target.TerrainPassGraphicPointers=source.TerrainPassGraphicPointers;
 std::ofstream audit("work/faction-terrain-targets.tsv");audit<<"native\tsource\tstatus\n";
 for(size_t t=0;t<target.TerrainBlock.Terrains.size();t++){
  auto &terrain=target.TerrainBlock.Terrains[t];bool mapped=reverse.count(int(t));
  int src=mapped?reverse[int(t)]:factionFallbackTerrain(int(t),terrain.IsWater);
  audit<<t<<'\t'<<src<<'\t'<<(mapped?"mapped":"fallback surface; no terrain spawns")<<'\n';
  auto &original=source.TerrainBlock.Terrains.at(src);
  if(mapped){
   terrain.TerrainUnitID=original.TerrainUnitID;terrain.TerrainUnitDensity=original.TerrainUnitDensity;
   terrain.TerrainUnitMaskedDensity=original.TerrainUnitMaskedDensity;terrain.TerrainUnitCentering=original.TerrainUnitCentering;
   terrain.NumberOfTerrainUnitsUsed=original.NumberOfTerrainUnitsUsed;
  }else{
   std::fill(terrain.TerrainUnitID.begin(),terrain.TerrainUnitID.end(),-1);
   std::fill(terrain.TerrainUnitDensity.begin(),terrain.TerrainUnitDensity.end(),0);
   std::fill(terrain.TerrainUnitMaskedDensity.begin(),terrain.TerrainUnitMaskedDensity.end(),0);
   terrain.NumberOfTerrainUnitsUsed=0;
  }
 }
 for(size_t i=0;i<target.TerrainRestrictions.size();i++){
  auto &r=target.TerrainRestrictions[i];auto &s=source.TerrainRestrictions[i];
  r.PassableBuildableDmgMultiplier.resize(target.TerrainsUsed1);r.TerrainPassGraphics.resize(target.TerrainsUsed1);
  for(int t=0;t<target.TerrainsUsed1;t++){
   int from=reverse.count(t)?reverse[t]:factionFallbackTerrain(t,target.TerrainBlock.Terrains.at(t).IsWater);
   r.PassableBuildableDmgMultiplier[t]=s.PassableBuildableDmgMultiplier.at(from);
   r.TerrainPassGraphics[t]=s.TerrainPassGraphics.at(from);
  }
 }
 for(auto &c:target.Civs)for(size_t i=0;i<c.Units.size();i++)if(c.UnitPointers[i]){
  auto &u=c.Units[i];
  // Four unused source lookout variants carry an invalid -1 restriction.
  if(i>=1901&&i<=1904&&u.TerrainRestriction==-1)u.TerrainRestriction=1;
  if(u.TerrainRestriction<0||u.TerrainRestriction>=int(target.TerrainRestrictions.size()))throw std::runtime_error("Invalid source terrain restriction");
  for(auto p:{&u.PlacementTerrain,&u.PlacementSideTerrain}){p->first=int16_t(mapTerrain(p->first));p->second=int16_t(mapTerrain(p->second));}
  if(u.Type==80)u.Building.FoundationTerrainID=int16_t(mapTerrain(u.Building.FoundationTerrainID));
  if(u.Type>=40)for(auto &t:u.Bird.TaskList)t.TerrainID=int16_t(mapTerrain(t.TerrainID));
 }
 for(auto &h:target.UnitHeaders)for(auto &t:h.TaskList)t.TerrainID=int16_t(mapTerrain(t.TerrainID));
}
