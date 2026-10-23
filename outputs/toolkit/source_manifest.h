#pragma once
#include <filesystem>
inline void sourceManifest(genie::DatFile &d,const std::string &path){
 std::filesystem::create_directories(path);
 std::ofstream civ(path+"/civs.tsv"),units(path+"/units.tsv"),cost(path+"/costs.tsv"),train(path+"/production.tsv"),tech(path+"/techs.tsv"),req(path+"/requirements.tsv"),fx(path+"/effects.tsv"),res(path+"/resources.tsv"),tasks(path+"/tasks.tsv"),art(path+"/art.tsv"),delta(path+"/deltas.tsv");
 civ<<"id\tname\ttechtree\tteam_bonus\tunit_slots\n";
 units<<"civ\tid\tname\ttype\tenabled\tclass\thp\tspeed\tstanding\twalking\tattack\tdying\tdead\tprojectile\ttracking\tconstruction\trange\treload\n";
 cost<<"kind\tciv\tid\tresource\tamount\tflag\n";train<<"kind\tciv\tid\tlocation\ttime\tbutton\thotkey\n";
 tech<<"id\tname\tciv\teffect\tprerequisite_count\n";req<<"tech\tprerequisite\n";
 fx<<"effect\tname\tcommand\ttype\ta\tb\tc\td\n";res<<"civ\tid\tvalue\n";
 tasks<<"unit\ttask\ttype\tclass\tunit_target\tmove_graphic\tproceed_graphic\twork_graphic\tcarry_graphic\n";
 art<<"id\tname\tslp\tframes\tangles\n";delta<<"parent\tchild\tx\ty\n";
 for(size_t c=0;c<d.Civs.size();c++){
  auto &v=d.Civs[c];civ<<c<<'\t'<<v.Name<<'\t'<<v.TechTreeID<<'\t'<<v.TeamBonusID<<'\t'<<v.Units.size()<<'\n';
  for(size_t r=0;r<v.Resources.size();r++)res<<c<<'\t'<<r<<'\t'<<v.Resources[r]<<'\n';
  if(d.Civs.size()!=3&&c!=0&&c!=1&&c!=3)continue;
  for(size_t id=0;id<v.Units.size();id++){
   auto &u=v.Units[id];if(!v.UnitPointers[id])continue;
   units<<c<<'\t'<<id<<'\t'<<u.Name<<'\t'<<int(u.Type)<<'\t'<<int(u.Enabled)<<'\t'<<u.Class<<'\t'<<u.HitPoints<<'\t'<<u.Speed<<'\t'<<u.StandingGraphic.first<<'\t'<<u.DeadFish.WalkingGraphic<<'\t'<<u.Type50.AttackGraphic<<'\t'<<u.DyingGraphic<<'\t'<<u.DeadUnitID<<'\t'<<u.Type50.ProjectileUnitID<<'\t'<<u.DeadFish.TrackingUnit<<'\t'<<u.Building.ConstructionGraphicID<<'\t'<<u.Type50.MaxRange<<'\t'<<u.Type50.ReloadTime<<'\n';
   for(auto &x:u.Creatable.ResourceCosts)if(x.Type>=0)cost<<"unit\t"<<c<<'\t'<<id<<'\t'<<x.Type<<'\t'<<x.Amount<<'\t'<<x.Flag<<'\n';
   for(auto &x:u.Creatable.TrainLocations)if(x.LocationID>=0)train<<"unit\t"<<c<<'\t'<<id<<'\t'<<x.LocationID<<'\t'<<x.QueueTime<<'\t'<<int(x.ButtonID)<<'\t'<<x.HotKeyID<<'\n';
  }
 }
 for(size_t id=0;id<d.Techs.size();id++){
  auto &t=d.Techs[id];tech<<id<<'\t'<<t.Name<<'\t'<<t.Civ<<'\t'<<t.EffectID<<'\t'<<t.RequiredTechCount<<'\n';
  for(auto x:t.RequiredTechs)if(x>=0)req<<id<<'\t'<<x<<'\n';
  for(auto &x:t.ResourceCosts)if(x.Type>=0)cost<<"tech\t"<<t.Civ<<'\t'<<id<<'\t'<<x.Type<<'\t'<<x.Amount<<'\t'<<int(x.Flag)<<'\n';
  for(auto &x:t.ResearchLocations)if(x.LocationID>=0)train<<"tech\t"<<t.Civ<<'\t'<<id<<'\t'<<x.LocationID<<'\t'<<x.QueueTime<<'\t'<<int(x.ButtonID)<<'\t'<<x.HotKeyID<<'\n';
 }
 for(size_t id=0;id<d.Effects.size();id++){auto &e=d.Effects[id];for(size_t i=0;i<e.EffectCommands.size();i++){auto &x=e.EffectCommands[i];fx<<id<<'\t'<<e.Name<<'\t'<<i<<'\t'<<int(x.Type)<<'\t'<<x.A<<'\t'<<x.B<<'\t'<<x.C<<'\t'<<x.D<<'\n';}}
 for(size_t id=0;id<d.UnitHeaders.size();id++)for(size_t i=0;i<d.UnitHeaders[id].TaskList.size();i++){auto &t=d.UnitHeaders[id].TaskList[i];tasks<<id<<'\t'<<i<<'\t'<<t.ActionType<<'\t'<<t.ClassID<<'\t'<<t.UnitID<<'\t'<<t.MovingGraphicID<<'\t'<<t.ProceedingGraphicID<<'\t'<<t.WorkingGraphicID<<'\t'<<t.CarryingGraphicID<<'\n';}
 for(size_t id=0;id<d.Graphics.size();id++){if(!d.GraphicPointers[id])continue;auto &g=d.Graphics[id];art<<id<<'\t'<<g.Name<<'\t'<<g.SLP<<'\t'<<g.FrameCount<<'\t'<<g.AngleCount<<'\n';for(auto &x:g.Deltas)delta<<id<<'\t'<<x.GraphicID<<'\t'<<x.OffsetX<<'\t'<<x.OffsetY<<'\n';}
 std::ofstream runtime(path+"/runtime-tasks.tsv");
 runtime<<"civ\tunit\tdefault_task\tindex\tid\taction\tclass\ttarget\tresource_in\tresource_out\tresource_multiplier\tunused_resource\n";
 for(size_t c=0;c<d.Civs.size();c++){
  if(d.Civs.size()!=3&&c!=0&&c!=1&&c!=3)continue;
  auto &v=d.Civs[c];
  for(size_t id=0;id<v.Units.size();id++)if(v.UnitPointers[id]&&v.Units[id].Type>=40){
   auto &u=v.Units[id];
   auto &list=d.Civs.size()==3?u.Bird.TaskList:d.UnitHeaders.at(id).TaskList;
   for(size_t i=0;i<list.size();i++){auto &t=list[i];runtime<<c<<'\t'<<id<<'\t'<<u.Bird.DefaultTaskID<<'\t'<<i<<'\t'<<t.ID<<'\t'<<t.ActionType<<'\t'<<t.ClassID<<'\t'<<t.UnitID<<'\t'<<t.ResourceIn<<'\t'<<t.ResourceOut<<'\t'<<t.ResourceMultiplier<<'\t'<<t.UnusedResource<<'\n';}
  }
 }
 std::cout<<"Exported source semantic tables to "<<path<<'\n';
}
