#pragma once
// Reserve DE's engine flag slot without discarding the source graphic there.
inline void importFactionMarker(genie::DatFile &target,const genie::DatFile &native){
 std::ofstream report("work/faction-marker-relocation.tsv");
 report<<"source\ttarget\treferences\n";
 for(int old:{1963,2961,2962}){
 const int moved=int(target.Graphics.size());
 if(moved>=32767||(old==1963&&native.Graphics.at(old).FileName!="flags")||(old==2961&&native.Graphics.at(old).FileName!="MOVETO")||(old==2962&&native.Graphics.at(old).FileName!="b_misc_waypoint_flag_x1"))throw std::runtime_error("Unexpected native flag layout");
 auto saved=target.Graphics.at(old);saved.ID=moved;
 target.Graphics.push_back(saved);target.GraphicPointers.push_back(target.GraphicPointers.at(old));
 int changes=0;
 auto fix=[&](auto &id){if(id==old){id=moved;changes++;}};
 auto tasks=[&](auto &list){for(auto &t:list){fix(t.MovingGraphicID);fix(t.ProceedingGraphicID);fix(t.WorkingGraphicID);fix(t.CarryingGraphicID);}};
 for(auto &g:target.Graphics)for(auto &d:g.Deltas)fix(d.GraphicID);
 for(auto &h:target.UnitHeaders)tasks(h.TaskList);
 for(auto &c:target.Civs)for(size_t id=0;id<c.Units.size();id++){
  if(!c.UnitPointers[id])continue;auto &u=c.Units[id];
  fix(u.StandingGraphic.first);fix(u.StandingGraphic.second);fix(u.DyingGraphic);fix(u.UndeadGraphic);
  for(auto &d:u.DamageGraphics)fix(d.GraphicID);
  fix(u.DeadFish.WalkingGraphic);fix(u.DeadFish.RunningGraphic);tasks(u.Bird.TaskList);
  fix(u.Type50.AttackGraphic);fix(u.Creatable.GarrisonGraphic);fix(u.Creatable.SpecialGraphic);
  fix(u.Building.ConstructionGraphicID);fix(u.Building.SnowGraphicID);
 }
 target.Graphics[old]=native.Graphics[old];target.GraphicPointers[old]=native.GraphicPointers[old];
 report<<old<<'\t'<<moved<<'\t'<<changes<<'\n';
 std::cout<<"Native flag slot restored; source graphic moved to "<<moved<<" ("<<changes<<" references).\n";
 }
}
