#pragma once
inline void importFactionHotkeys(genie::DatFile &target){
 std::ifstream file("work/faction-hotkeys.tsv");
 if(!file)throw std::runtime_error("Generate faction_hotkeys.py before building factions");
 std::string line;std::getline(file,line);
 std::string kind,key;int civ,id,location,button,hotkey;
 std::set<int> assigned;int count=0;
 while(file>>kind>>civ>>id>>location>>button>>hotkey>>key){
  if(hotkey<1000000||!assigned.insert(hotkey).second)throw std::runtime_error("Duplicate or invalid spatial hotkey ID");
  int matches=0;
  if(kind=="unit"){
   for(auto &entry:target.Civs.at(civ).Units.at(id).Creatable.TrainLocations)
    if(entry.LocationID==location&&entry.ButtonID==button){entry.HotKeyID=hotkey;matches++;}
  }else if(kind=="tech"){
   for(auto &entry:target.Techs.at(id).ResearchLocations)
    if(entry.LocationID==location&&entry.ButtonID==button){entry.HotKeyID=hotkey;matches++;}
  }else throw std::runtime_error("Invalid spatial hotkey kind");
  if(matches!=1)throw std::runtime_error("Spatial hotkey requires exactly one production location");
  count++;
 }
 std::cout<<"Spatial hotkeys: "<<count<<" unique command bindings.\n";
}
