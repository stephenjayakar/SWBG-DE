// faction_parity_patch <current.raw> <source ef.raw> <native de.raw> <out.raw>
// Targeted parity repairs applied to the current two-faction DAT (see outputs/PARITY-2026-09-29.md):
//  1. Terrain identities: SWGB terrains that were collapsed onto one DE terrain get distinct DE slots
//     (source passability, spawns and object placement/task references); redwood forest moves off
//     DE snow-forest ground. Mirrors faction_terrain.h semantics for the changed slots only.
//  2. Harbor 7353 garrison bit: SWGB 0x20 (ships) -> DE 0x40 (ships); DE 0x20 means siege.
//  3. CreatableType: DE uses it as a formation category keyed by class; set it from DE's native
//     per-class convention for trainable faction units.
#include "genie/dat/DatFile.h"
#include <iostream>
#include <map>
#include <set>
static int fallbackTerrain(int id,uint8_t flags){
 if(id>=29&&id<=31)return 29; if(flags&8)return 28; if(flags&16)return 2; if(flags&7)return 1;
 if(flags&64)return 35; if(flags&128)return 32; return 0;}
int run(int argc,char**argv){
 if(argc!=5){std::cerr<<"usage: current source native out\n";return 1;}
 genie::DatFile d,s,n; d.setGameVersion(genie::GV_LatestDE2); d.load(argv[1]);
 s.setGameVersion(genie::GV_CCV2); s.load(argv[2]); n.setGameVersion(genie::GV_LatestDE2); n.load(argv[3]);
 // source terrain -> {old collapsed target, new distinct target}
 const std::map<int,std::pair<int,int>> remap={
  {46,{14,45}},   // SAND2 -> Desert, Cracked
  {26,{14,42}},   // RED_DESERT1 -> Dirt 4
  {41,{14,100}},  // YELLOW_PLAINS1 -> Dry Grass
  {44,{40,70}},   // ROCK2 -> Gravel Default
  {50,{10,48}},   // ROCK_CARBON -> slot 48 (dirt texture) with carbon-rock spawns
  {47,{32,125}},  // SNOW_DIRT -> Snow Soft Light
  {33,{32,124}},  // SNOW_ROCK -> Snow Soft
  {55,{32,72}},   // SNOW_GRASS1 -> Underbrush, Snow
  {38,{24,78}},   // PATH3 -> Road, Gravel (Desert)
  {21,{21,56}},   // TREE_G redwood -> Rainforest ground (was Snow Forest)
 };
 auto &TT=d.TerrainBlock.Terrains; auto &ST=s.TerrainBlock.Terrains;
 std::map<int,int> newTargets; for(auto &p:remap)newTargets[p.second.second]=p.first;
 for(auto &p:remap){int t=p.second.second;if(t>=d.TerrainsUsed1||t>=(int)d.TerrainBlock.Terrains.size())throw std::runtime_error("target slot out of range "+std::to_string(t)+" used="+std::to_string(d.TerrainsUsed1));}
 auto copyColumn=[&](int t,int from){
  for(size_t i=0;i<d.TerrainRestrictions.size();i++){auto &r=d.TerrainRestrictions[i];auto &sr=s.TerrainRestrictions.at(i);
   r.PassableBuildableDmgMultiplier.at(t)=sr.PassableBuildableDmgMultiplier.at(from);r.TerrainPassGraphics.at(t)=sr.TerrainPassGraphics.at(from);}};
 for(auto &p:remap){int src=p.first,t=p.second.second;auto &o=ST.at(src);auto &x=TT.at(t);
  x.TerrainUnitID=o.TerrainUnitID;x.TerrainUnitDensity=o.TerrainUnitDensity;x.TerrainUnitMaskedDensity=o.TerrainUnitMaskedDensity;
  x.TerrainUnitCentering=o.TerrainUnitCentering;x.NumberOfTerrainUnitsUsed=o.NumberOfTerrainUnitsUsed;copyColumn(t,src);
  std::cout<<"terrain "<<t<<" <- source "<<src<<" spawns="<<o.NumberOfTerrainUnitsUsed<<"\n";}
 // Slot 21 no longer hosts a source terrain: native surface fallback, no spawns.
 {int t=21;auto &x=TT.at(t);int from=fallbackTerrain(t,x.IsWater);
  std::fill(x.TerrainUnitID.begin(),x.TerrainUnitID.end(),-1);std::fill(x.TerrainUnitDensity.begin(),x.TerrainUnitDensity.end(),0);
  std::fill(x.TerrainUnitMaskedDensity.begin(),x.TerrainUnitMaskedDensity.end(),0);x.NumberOfTerrainUnitsUsed=0;copyColumn(t,from);
  std::cout<<"terrain 21 -> fallback source "<<from<<"\n";}
 // Object terrain references: follow the source value.
 const int civMap[3]={0,1,3}; int refs=0;
 auto fix=[&](int16_t &tv,int16_t sv){auto p=remap.find(sv);if(p!=remap.end()&&tv==p->second.first){tv=int16_t(p->second.second);refs++;}};
 for(int c=0;c<3;c++){auto &tc=d.Civs.at(c);auto &sc=s.Civs.at(civMap[c]);
  for(size_t i=0;i<tc.Units.size()&&i<sc.Units.size();i++){if(!tc.UnitPointers[i]||!sc.UnitPointers[i])continue;
   auto &u=tc.Units[i];auto &o=sc.Units[i];
   fix(u.PlacementTerrain.first,o.PlacementTerrain.first);fix(u.PlacementTerrain.second,o.PlacementTerrain.second);
   fix(u.PlacementSideTerrain.first,o.PlacementSideTerrain.first);fix(u.PlacementSideTerrain.second,o.PlacementSideTerrain.second);
   if(u.Type==80&&o.Type==80)fix(u.Building.FoundationTerrainID,o.Building.FoundationTerrainID);}}
 for(size_t i=0;i<d.UnitHeaders.size()&&i<s.UnitHeaders.size();i++){auto &h=d.UnitHeaders[i].TaskList;auto &o=s.UnitHeaders[i].TaskList;
  for(size_t k=0;k<h.size()&&k<o.size();k++)if(h[k].ActionType==o[k].ActionType)fix(h[k].TerrainID,o[k].TerrainID);}
 std::cout<<"object terrain references remapped: "<<refs<<"\n";
 // Harbor garrison bit.
 int harbor=0;for(int c=0;c<3;c++){auto &tc=d.Civs.at(c);if(7353<tc.Units.size()&&tc.UnitPointers[7353]){auto &b=tc.Units[7353].Building;
   if(b.GarrisonType&0x20){b.GarrisonType=uint8_t((b.GarrisonType&~0x20)|0x40);harbor++;}}}
 std::cout<<"harbor garrison repaired: "<<harbor<<"\n";
 // CreatableType convention from native trainable units (civ 1).
 std::map<int,std::map<int,int>> votes;auto &nc=n.Civs.at(1);
 for(size_t i=0;i<nc.Units.size();i++){if(!nc.UnitPointers[i])continue;auto &u=nc.Units[i];
  if(u.Type!=70||u.Creatable.TrainLocations.empty()||u.Creatable.TrainLocations[0].LocationID<0)continue;votes[u.Class][u.Creatable.CreatableType]++;}
 std::map<int,int> convention;for(auto &v:votes){int best=-1,cnt=-1;for(auto &k:v.second)if(k.second>cnt){cnt=k.second;best=k.first;}convention[v.first]=best;}
 int ct=0;for(int c=1;c<3;c++){auto &tc=d.Civs.at(c);for(size_t i=0;i<tc.Units.size();i++){if(!tc.UnitPointers[i])continue;auto &u=tc.Units[i];
   if(u.Type!=70||u.Creatable.TrainLocations.empty()||u.Creatable.TrainLocations[0].LocationID<0)continue;
   auto p=convention.find(u.Class);if(p==convention.end())continue;if(u.Creatable.CreatableType!=p->second){u.Creatable.CreatableType=uint8_t(p->second);ct++;}}}
 std::cout<<"creatable type set: "<<ct<<" (classes with native convention: "<<convention.size()<<")\n";
 // 4. Start-only producer buildings (e.g. Command Center 109): placed by the map, never enabled and
 //    without a builder. DE's AI refuses to train/research at a building type that is not enabled for
 //    the player (can-train/up-train/can-research all false), so the Classic AI never trained a worker.
 //    Enabling a building that has no train location adds no build button (no human gameplay change).
 {std::set<int> enabledByEffect;for(auto &e:d.Effects)for(auto &c:e.EffectCommands)if(c.Type==2&&c.B==1&&c.A>=0)enabledByEffect.insert(c.A);
  std::set<int> producers;for(int c=1;c<3;c++){auto &tc=d.Civs.at(c);for(size_t i=0;i<tc.Units.size();i++){if(!tc.UnitPointers[i])continue;auto &u=tc.Units[i];
    if(u.Type>=70)for(auto &l:u.Creatable.TrainLocations)if(l.LocationID>=0)producers.insert(l.LocationID);}}
  for(auto &t:d.Techs)if(t.ResearchLocations.size())for(auto &l:t.ResearchLocations)if(l.LocationID>=0)producers.insert(l.LocationID);
  int en=0;for(int c=0;c<3;c++){auto &tc=d.Civs.at(c);for(int id:producers){if(id>=(int)tc.Units.size()||!tc.UnitPointers[id])continue;auto &u=tc.Units[id];
    if(u.Type!=80||u.Enabled||enabledByEffect.count(id))continue;bool buildable=false;for(auto &l:u.Creatable.TrainLocations)if(l.LocationID>=0)buildable=true;
    if(buildable)continue;u.Enabled=1;en++;std::cout<<"enabled start-only producer civ "<<c<<" unit "<<id<<" "<<u.Name<<"\n";}}
  std::cout<<"start-only producers enabled: "<<en<<"\n";}
 // 5. Town Center identity: every native DE Town Center stores resource 506 (amount 1, flag 16), which
 //    the engine/AI uses to count Town Centers. SWGB Command Centers (DE TC slots 109/71/141/142 plus
 //    SWGB variants of the bldg-main line) lacked it, so DE's AI never treated them as Town Centers.
 {const int ccs[]={109,71,141,142,3578,3579,3580,3581,3646,3647,3648,3649,3650,3651,3652,3653,4780,4781,4782,4783};
  int added=0;for(int c=0;c<3;c++){auto &tc=d.Civs.at(c);for(int id:ccs){if(id>=(int)tc.Units.size()||!tc.UnitPointers[id])continue;auto &u=tc.Units[id];
    if(u.Type!=80)continue;bool has=false;for(auto &r:u.ResourceStorages)if(r.Type==506)has=true;if(has)continue;
    bool done=false;for(auto &r:u.ResourceStorages)if(r.Type==-1){r.Type=506;r.Amount=1;r.Flag=16;done=true;break;}
    if(!done){std::cout<<"warning: no free storage slot on civ "<<c<<" CC "<<id<<" "<<u.Name<<"\n";continue;}added++;}}
  std::cout<<"town-center storage 506 added: "<<added<<"\n";}
 d.saveAs(argv[4]);std::cout<<"saved "<<argv[4]<<"\n";return 0;}
int main(int argc,char**argv){try{return run(argc,argv);}catch(const std::exception &e){std::cerr<<"error: "<<e.what()<<"\n";return 2;}}
