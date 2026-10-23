#pragma once
#include "faction_terrain.h"
// Narrow repair for an already built dataset; avoids rebuilding paused factions.
inline void repairFactionEconomy(genie::DatFile &d,const genie::DatFile &source,const genie::DatFile &native){
 std::ifstream in("work/faction-terrain-map.tsv");
 if(!in)throw std::runtime_error("Missing terrain map");
 std::set<int> mapped;std::string line;std::getline(in,line);
 while(std::getline(in,line)){std::istringstream row(line);std::string name;int s,t,c;row>>name>>s>>t>>c;if(c)mapped.insert(t);}
 for(int t=0;t<d.TerrainsUsed1;t++)if(!mapped.count(t)){
  int s=factionFallbackTerrain(t,d.TerrainBlock.Terrains.at(t).IsWater);
  for(size_t r=0;r<d.TerrainRestrictions.size();r++){
   d.TerrainRestrictions[r].PassableBuildableDmgMultiplier[t]=source.TerrainRestrictions.at(r).PassableBuildableDmgMultiplier.at(s);
   d.TerrainRestrictions[r].TerrainPassGraphics[t]=source.TerrainRestrictions.at(r).TerrainPassGraphics.at(s);
  }
 }
 // DE selects formation behavior from native class when this byte is 255.
 // Retain the source holocron unit, artwork, tasks and ownership restrictions.
 d.Civs.at(0).Units.at(285).Creatable.CreatableType=native.Civs.at(0).Units.at(285).Creatable.CreatableType;
}
