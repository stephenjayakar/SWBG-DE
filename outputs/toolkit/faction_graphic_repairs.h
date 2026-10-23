#pragma once
inline bool absentFactionOverlay(int id,const genie::DatFile &source){
 const std::map<int,std::tuple<int,int,int>> overlays={
  {4866,{2946,4854,4879}},{4868,{2948,4856,4881}},
  {4891,{2952,4885,4879}},{4893,{2954,4887,4881}}
 };
 auto it=overlays.find(id);if(it==overlays.end())return false;
 auto [slp,parent,hull]=it->second;
 if(source.Graphics.at(id).SLP!=slp)throw std::runtime_error("Fishing overlay source changed");
 bool childFound=false,hullFound=false;
 for(const auto &delta:source.Graphics.at(parent).Deltas){childFound|=delta.GraphicID==id;hullFound|=delta.GraphicID==hull;}
 if(!childFound||!hullFound)throw std::runtime_error("Cannot omit missing overlay without independent boat hull");
 // These four references have no file in any installed source archive.
 // Keep their graphic records for timing/sounds, but no unresolved sprite lookup.
 return true;
}
