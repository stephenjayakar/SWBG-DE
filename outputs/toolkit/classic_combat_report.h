#pragma once
#include <filesystem>
#include <iomanip>
#include <limits>

// Read-only combat tables. Keep ordered duplicate entries and signed shorts;
// neither a dictionary nor a displayed attack/armor value represents the source.
inline void classicCombatReport(const genie::DatFile &current,const genie::DatFile &source,const char *directory){
 const std::filesystem::path root(directory);
 std::filesystem::create_directories(root);
 if(current.Civs.size()!=3)throw std::runtime_error("Combat report expects Gaia/Empire/Rebels");
 for(bool original:{true,false}){
  const auto &data=original?source:current;
  const std::string prefix=original?"source":"current";
  std::ofstream units(root/(prefix+"-combat.tsv")),effects(root/(prefix+"-effects.tsv"));
  if(!units||!effects)throw std::runtime_error("Cannot open combat report");
  units<<std::setprecision(std::numeric_limits<float>::max_digits10);
  effects<<std::setprecision(std::numeric_limits<float>::max_digits10);
  units<<"civ\tslot\tid\tcopy\ttype\tclass\thp\tbase_armor\treload\tmax_range\tmin_range\tdefense_terrain\tattacks\tarmor\n";
  auto table=[&](const auto &entries){
   bool first=true;
   for(const auto &entry:entries){if(!first)units<<',';first=false;units<<entry.Class<<':'<<entry.Amount;}
  };
  for(size_t c=0;c<current.Civs.size();c++){
   const auto &civ=data.Civs.at(original&&c==2?3:c);
   for(size_t id=0;id<civ.Units.size();id++){
    if(!civ.UnitPointers.at(id))continue;
    const auto &u=civ.Units[id];if(u.Type<50)continue;
    const auto &combat=u.Type50;
    units<<c<<'\t'<<id<<'\t'<<u.ID<<'\t'<<u.CopyID<<'\t'<<int(u.Type)<<'\t'<<u.Class<<'\t'<<u.HitPoints
         <<'\t'<<combat.BaseArmor<<'\t'<<combat.ReloadTime<<'\t'<<combat.MaxRange<<'\t'<<combat.MinRange<<'\t'<<combat.DefenseTerrainBonus<<'\t';
    table(combat.Attacks);units<<'\t';table(combat.Armours);units<<'\n';
   }
  }
  // Include all commands, including upgrades and class selectors, for later
  // dynamic-stat coverage. Exporting a command does not simulate its effect.
  effects<<"effect\tordinal\ttype\ta\tb\tc\td\n";
  for(size_t id=0;id<data.Effects.size();id++){
   const auto &commands=data.Effects[id].EffectCommands;
   for(size_t i=0;i<commands.size();i++){
    const auto &e=commands[i];effects<<id<<'\t'<<i<<'\t'<<int(e.Type)<<'\t'<<e.A<<'\t'<<e.B<<'\t'<<e.C<<'\t'<<e.D<<'\n';
   }
  }
  if(!units||!effects)throw std::runtime_error("Failed to write combat report");
 }
}
