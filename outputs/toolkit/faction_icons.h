#pragma once
inline void importFactionIcons(genie::DatFile &target,const genie::DatFile &source){
 std::ifstream file("work/faction-ui-icons.tsv");if(!file)throw std::runtime_error("Generate faction UI icon manifest first");
 std::string line;std::getline(file,line);std::string kind;int civ,id,icon;
 while(file>>kind>>civ>>id>>icon){
  if(icon<0||icon>=32768)throw std::runtime_error("Invalid icon ID");
  if(kind=="unit")target.Civs.at(civ).Units.at(id).IconID=int16_t(icon);
  else if(kind=="tech")target.Techs.at(id).IconID=int16_t(icon);
  else throw std::runtime_error("Unknown icon kind");
 }
 // Worker job changes select a different unit record. Every source worker in
 // these factions uses frame 59 on its faction sheet, including both genders.
 std::ofstream workers("work/faction-worker-icon-repairs.tsv");
 workers<<"civ\tunit\ticon\n";
 for(int c:{1,2}){
  const auto &from=source.Civs.at(c==2?3:1);auto &to=target.Civs.at(c);
  const auto &base=from.Units.at(83);int portrait=to.Units.at(83).IconID;
  if(portrait<0||base.Class!=58)throw std::runtime_error("Missing worker portrait");
  for(size_t uid=0;uid<from.Units.size();uid++){
   if(!from.UnitPointers[uid]||from.Units[uid].Class!=58)continue;
   const auto &u=from.Units[uid];
   if(u.IconID+u.Building.GraphicsAngle!=base.IconID+base.Building.GraphicsAngle)
    throw std::runtime_error("Worker job has a different source portrait; convert it explicitly");
   to.Units.at(uid).IconID=int16_t(portrait);
   workers<<c<<'\t'<<uid<<'\t'<<portrait<<'\n';
  }
 }
 // The mapped roster is only a subset of the imported source data. Gaia's
 // trees and disabled/editor records can still carry source icon indices far
 // beyond DE's UI vectors. -1 is the native no-icon sentinel.
 std::ifstream bounds("work/faction-ui-icon-limits.tsv");
 if(!bounds)throw std::runtime_error("Generate native icon limits first");
 std::map<std::string,int> limits;std::string category;int count;
 while(bounds>>category>>count)limits[category]=count;
 if(limits.size()!=3||limits.at("Units")<=0||limits.at("Buildings")<=0||limits.at("Techs")<=0)
  throw std::runtime_error("Invalid native icon limits");
 std::ofstream audit("work/faction-icon-bounds-repairs.tsv");
 audit<<"kind\tciv\tid\tcategory\tbefore\tafter\n";
 auto repair=[&](int16_t &value,const std::string &kind,int c,int uid,const std::string &cat){
  if(value< -1||value>=limits.at(cat)){
   audit<<kind<<'\t'<<c<<'\t'<<uid<<'\t'<<cat<<'\t'<<value<<"\t-1\n";value=-1;
  }
 };
 for(size_t c=0;c<target.Civs.size();c++)for(size_t uid=0;uid<target.Civs[c].Units.size();uid++){
  if(!target.Civs[c].UnitPointers[uid])continue;
  auto &u=target.Civs[c].Units[uid];
  repair(u.IconID,"unit",int(c),int(uid),u.Type==80&&u.Class!=34&&u.Class!=36?"Buildings":"Units");
 }
 for(size_t tid=0;tid<target.Techs.size();tid++)repair(target.Techs[tid].IconID,"tech",-1,int(tid),"Techs");
}
