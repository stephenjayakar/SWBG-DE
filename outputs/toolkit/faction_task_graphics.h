#pragma once
// SWGB shared task graphics use empty selectors followed by -C1 .. -C15
// variants. Materialize faction choices because DE does not perform that lookup.
inline void importFactionTaskGraphics(genie::DatFile &target,const genie::DatFile &source){
 std::map<std::string,int> names;
 for(size_t g=0;g<source.Graphics.size();g++)if(source.GraphicPointers[g])names[source.Graphics[g].Name]=int(g);
 std::ofstream audit("work/faction-task-graphics.tsv");audit<<"civ\tunit\tselector\tgraphic\n";
 for(size_t c=0;c<target.Civs.size();c++){
  int sourceCiv=c==2?3:1;
  auto &civ=target.Civs[c];
  for(size_t u=0;u<civ.Units.size();u++)if(civ.UnitPointers[u]&&civ.Units[u].Type>=40){
   for(auto &t:civ.Units[u].Bird.TaskList)
    for(auto p:{&t.MovingGraphicID,&t.ProceedingGraphicID,&t.WorkingGraphicID,&t.CarryingGraphicID}){
     if(*p<0)continue;
     const auto &g=source.Graphics.at(*p);
     if(g.SLP!=-1||!g.Deltas.empty())continue;
     auto variant=names.find(g.Name+"-C"+std::to_string(sourceCiv));
     if(variant==names.end())continue;
     if(source.Graphics.at(variant->second).SLP<6)throw std::runtime_error("Empty faction task variant");
     audit<<c<<'\t'<<u<<'\t'<<*p<<'\t'<<variant->second<<'\n';
     *p=int16_t(variant->second);
    }
  }
 }
}
