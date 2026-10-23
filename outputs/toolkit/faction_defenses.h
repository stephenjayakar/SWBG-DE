#pragma once
// DE has no SWGB defensive construction page. Use vacant military-page
// positions, keeping all existing economic/military buttons and navigation.
inline int factionDefenseButton(int id) {
 switch(id) {
  case 72:return 3; // Light wall
  case 117:case 155:case 195:return 4; // Wall upgrades
  case 487:case 488:return 8; // Gate foundations
  case 79:case 234:case 235:case 7088:
  case 3599:case 3600:case 3601:return 11; // Turrets, including Rebel upgrades
  case 236:case 196:case 3602:case 3603:return 13; // Anti-air turrets
  default:return -1;
 }
}
inline void repairFactionDefenses(genie::DatFile &d) {
 if(d.Civs.size()!=3)throw std::runtime_error("Defense menu expects Gaia/Empire/Rebels");
 size_t changed=0;
 for(int c:{1,2})for(size_t id=0;id<d.Civs[c].Units.size();id++){
  int button=factionDefenseButton(int(id));if(button<0)continue;
  auto &u=d.Civs[c].Units[id];
  if(!d.Civs[c].UnitPointers[id]||u.Type!=80||u.InterfaceKind!=11)
   throw std::runtime_error("Unexpected defense template "+std::to_string(id));
  if(u.Creatable.TrainLocations.size()!=1||u.Creatable.TrainLocations[0].LocationID!=118)
   throw std::runtime_error("Unexpected defense construction location");
  u.InterfaceKind=10;u.Creatable.TrainLocations[0].ButtonID=uint8_t(button);changed++;
 }
 std::cout<<"Remapped "<<changed<<" defense templates to vacant military construction buttons.\n";
}
