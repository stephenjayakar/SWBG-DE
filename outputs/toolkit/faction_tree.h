#pragma once
inline void importFactionTree(genie::DatFile &target,const genie::DatFile &source){
 std::ifstream list("work/faction-tree-units.txt");if(!list)throw std::runtime_error("Generate faction tree unit manifest first");
 std::set<int> units;int id;while(list>>id)units.insert(id);
 auto tree=source.TechTree;
 auto filter=[&](auto &items){items.erase(std::remove_if(items.begin(),items.end(),[&](int v){return !units.count(v);}),items.end());};
 tree.UnitConnections.erase(std::remove_if(tree.UnitConnections.begin(),tree.UnitConnections.end(),[&](const auto &v){return !units.count(v.ID);}),tree.UnitConnections.end());
 auto common=[&](auto &v){
  if(v.SlotsUsed<0||v.SlotsUsed>10)throw std::runtime_error("Source tree exceeds DE link capacity");
  for(int i=0;i<v.SlotsUsed;i++)if(v.Mode[i]==2&&!units.count(v.UnitResearch[i]))throw std::runtime_error("Retained tree node links to omitted unit");
 };
 auto counts=[&](const auto &v){if(v.Buildings.size()>255||v.Units.size()>255||v.Techs.size()>255)throw std::runtime_error("Source tree list exceeds DE byte count");};
 for(auto &v:tree.TechTreeAges){filter(v.Units);common(v.Common);counts(v);
  for(size_t i=10;i<v.BuildingsPerZone.size();i++)if(v.BuildingsPerZone[i]||v.GroupLengthPerZone[i])throw std::runtime_error("Source tree uses more than ten zones");
 }
 for(auto &v:tree.BuildingConnections){filter(v.Units);common(v.Common);counts(v);}
 for(auto &v:tree.ResearchConnections){filter(v.Units);common(v.Common);counts(v);}
 for(auto &v:tree.UnitConnections){filter(v.Units);common(v.Common);if(v.Units.size()>255)throw std::runtime_error("Too many unit tree children");}
 if(tree.ResearchConnections.size()>255||tree.BuildingConnections.size()>255)throw std::runtime_error("Source tree exceeds native table counts");
 target.TechTree=tree;
}
