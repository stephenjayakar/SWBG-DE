#pragma once
inline void exportFactionInteractions(genie::DatFile &d,const std::string &path){
 std::filesystem::create_directories(path);
 std::ofstream out(path+"/interactions.tsv");
 out<<"civ\tid\tname\tclass\ticon\tdefault_task\tworkrate\tsearch\tlos\tdecay\treload\tdisplayed_reload\tcharge_type\tmax_charge\trecharge\tcharge_event\tcharge_target\tbutton_icon\tbutton_short\tbutton_long\tbutton_hotkey\n";
 std::ofstream tasks(path+"/interaction-tasks.tsv");
 tasks<<"civ\tunit\tid\taction\twork1\twork2\trange\tautosearch\tenable_targeting\tdefault\tenabled\tcombat_flag\tdiplomacy\twork_graphic\n";
 const bool modern=d.getGameVersion()>=genie::GV_C15&&d.getGameVersion()<=genie::GV_LatestDE2;
 for(size_t c=0;c<d.Civs.size();c++){
  if(c!=0&&c!=1&&c!=(d.Civs.size()==3?2:3))continue;
  for(size_t id=0;id<d.Civs[c].Units.size();id++){
   if(!d.Civs[c].UnitPointers[id])continue;auto &u=d.Civs[c].Units[id];if(u.Type!=70)continue;
   auto &v=u.Creatable;
   out<<c<<'\t'<<id<<'\t'<<u.Name<<'\t'<<u.Class<<'\t'<<u.IconID<<'\t'<<u.Bird.DefaultTaskID<<'\t'<<u.Bird.WorkRate<<'\t'<<u.Bird.SearchRadius<<'\t'<<u.LineOfSight<<'\t'<<u.ResourceDecay<<'\t'<<u.Type50.ReloadTime<<'\t'<<u.Type50.DisplayedReloadTime<<'\t'<<v.ChargeType<<'\t'<<v.MaxCharge<<'\t'<<v.RechargeRate<<'\t'<<v.ChargeEvent<<'\t'<<v.ChargeTarget<<'\t'<<v.ButtonIconID<<'\t'<<v.ButtonShortTooltipID<<'\t'<<v.ButtonExtendedTooltipID<<'\t'<<v.ButtonHotkeyAction<<'\n';
   const auto &list=modern?u.Bird.TaskList:d.UnitHeaders.at(id).TaskList;
   for(const auto &t:list)if(t.ActionType==7||t.ActionType==104||t.ActionType==132||t.ActionType==136)
    tasks<<c<<'\t'<<id<<'\t'<<t.ID<<'\t'<<t.ActionType<<'\t'<<t.WorkValue1<<'\t'<<t.WorkValue2<<'\t'<<t.WorkRange<<'\t'<<int(t.AutoSearchTargets)<<'\t'<<int(t.EnableTargeting)<<'\t'<<int(t.IsDefault)<<'\t'<<t.Enabled<<'\t'<<int(t.CombatLevelFlag)<<'\t'<<int(t.TargetDiplomacy)<<'\t'<<t.WorkingGraphicID<<'\n';
  }
 }
}
