#pragma once
#include <map>
inline void factionDependencies(genie::DatFile &d,const std::string &path){
 std::ofstream surfaces(path+"/terrain-surfaces.tsv");
 surfaces<<"terrain\tname\tdraw\tpassable\timpassable\tunits\n";
 for(size_t id=0;id<d.TerrainBlock.Terrains.size();id++){
  auto &t=d.TerrainBlock.Terrains[id];
  surfaces<<id<<'\t'<<t.Name<<'\t'<<t.TerrainToDraw<<'\t'<<int(t.PassableTerrain)<<'\t'<<int(t.ImpassableTerrain)<<'\t'<<t.NumberOfTerrainUnitsUsed<<'\n';
 }
 std::ofstream movement(path+"/unit-movement.tsv"),passArt(path+"/terrain-pass-art.tsv");
 movement<<"civ\tunit\ttrait\ttrait_piece\tformation\tobstruction\tobstruction_class\tfly\tmove_algorithm\trotation\tturn_radius\tturn_speed\tyaw_moving\tyaw_stationary\tstationary_time\n";
 passArt<<"restriction\tterrain\texit\tenter\twalk\n";
 for(size_t r=0;r<d.TerrainRestrictions.size();r++)for(size_t t=0;t<d.TerrainRestrictions[r].TerrainPassGraphics.size();t++){
  auto &g=d.TerrainRestrictions[r].TerrainPassGraphics[t];
  passArt<<r<<'\t'<<t<<'\t'<<g.ExitTileSpriteID<<'\t'<<g.EnterTileSpriteID<<'\t'<<g.WalkTileSpriteID<<'\n';
 }
 std::ofstream mechanics(path+"/unit-mechanics.tsv");
 mechanics<<"civ\tunit\tfly\tcollision_x\tcollision_y\tcollision_z\tgarrison_capacity\tgarrison_type\tcombat_flags\tblast_attack\tblast_defense\tinteraction\tresource_capacity\tresource_decay\tblast_width\tblast_damage\tfriendly_fire\thero_mode\n";
 std::ofstream detailedTasks(path+"/detailed-tasks.tsv"),storage(path+"/storages.tsv");
 detailedTasks<<"civ\tunit\tid\taction\tclass\ttarget\twork1\twork2\trange\tresource_in\tresource_out\tmultiplier\tflags\tdiplomacy\n";
 storage<<"civ\tunit\tslot\ttype\tamount\tmode\n";
 const bool modernTasks=d.getGameVersion()>=genie::GV_C15&&d.getGameVersion()<=genie::GV_LatestDE2;
 std::ofstream behavior(path+"/unit-behavior.tsv"),auras(path+"/aura-tasks.tsv"),drops(path+"/dropsites.tsv");
 behavior<<"civ\tunit\tworkrate\tcombat_ability\n";
 drops<<"civ\tunit\tdropsite\n";
 auras<<"civ\tunit\tid\tclass\ttarget\twork1\twork2\trange\tattribute\tflags\tdiplomacy\tautosearch\tenabled\n";
 std::ofstream tree(path+"/tree-nodes.tsv"),edges(path+"/tree-edges.tsv");
 tree<<"kind\tid\tupper\tenabling\trequired\tline\tlocation\tslots\n";
 edges<<"kind\tid\tmode\ttarget\n";
 auto common=[&](const char *kind,int id,const auto &v){for(int i=0;i<v.SlotsUsed;i++)edges<<kind<<'\t'<<id<<'\t'<<v.Mode.at(i)<<'\t'<<v.UnitResearch.at(i)<<'\n';};
 for(auto &v:d.TechTree.TechTreeAges){tree<<"age\t"<<v.ID<<"\t-1\t-1\t-1\t"<<v.LineMode<<"\t0\t"<<v.Common.SlotsUsed<<'\n';common("age",v.ID,v.Common);}
 for(auto &v:d.TechTree.BuildingConnections){tree<<"building\t"<<v.ID<<"\t-1\t"<<v.EnablingResearch<<"\t-1\t"<<v.LineMode<<'\t'<<int(v.LocationInAge)<<'\t'<<v.Common.SlotsUsed<<'\n';common("building",v.ID,v.Common);}
 for(auto &v:d.TechTree.UnitConnections){tree<<"unit\t"<<v.ID<<'\t'<<v.UpperBuilding<<'\t'<<v.EnablingResearch<<'\t'<<v.RequiredResearch<<'\t'<<v.LineMode<<'\t'<<v.LocationInAge<<'\t'<<v.Common.SlotsUsed<<'\n';common("unit",v.ID,v.Common);}
 for(auto &v:d.TechTree.ResearchConnections){tree<<"tech\t"<<v.ID<<'\t'<<v.UpperBuilding<<"\t-1\t-1\t"<<v.LineMode<<'\t'<<v.LocationInAge<<'\t'<<v.Common.SlotsUsed<<'\n';common("tech",v.ID,v.Common);}
 const std::vector<int> selected=d.Civs.size()==3?std::vector<int>{0,1,2}:std::vector<int>{0,1,3};
 std::ofstream usound(path+"/unit-sounds.tsv"),gsound(path+"/graphic-sounds.tsv"),sounds(path+"/sounds.tsv");
 usound<<"civ\tunit\tevent\tsound\n";gsound<<"graphic\tangle\tframe\tsound\n";sounds<<"sound\titem\tresource\tfile\tciv\tprobability\n";
 for(size_t id=0;id<d.Sounds.size();id++)for(size_t i=0;i<d.Sounds[id].Items.size();i++){auto &s=d.Sounds[id].Items[i];sounds<<id<<'\t'<<i<<'\t'<<s.ResourceID<<'\t'<<s.FileName<<'\t'<<s.Civilization<<'\t'<<s.Probability<<'\n';}
 for(size_t id=0;id<d.Graphics.size();id++)if(d.GraphicPointers[id]){
  auto &g=d.Graphics[id];if(g.SoundID>=0)gsound<<id<<"\t-1\t-1\t"<<g.SoundID<<'\n';
  if(g.AngleSoundsUsed)for(size_t a=0;a<g.AngleSounds.size();a++){auto &s=g.AngleSounds[a];
   if(s.SoundID>=0)gsound<<id<<'\t'<<a<<'\t'<<s.FrameNum<<'\t'<<s.SoundID<<'\n';
   if(s.SoundID2>=0)gsound<<id<<'\t'<<a<<'\t'<<s.FrameNum2<<'\t'<<s.SoundID2<<'\n';
   if(s.SoundID3>=0)gsound<<id<<'\t'<<a<<'\t'<<s.FrameNum3<<'\t'<<s.SoundID3<<'\n';
  }
 }
 std::ofstream terrain(path+"/terrain-units.tsv"),restriction(path+"/terrain-restrictions.tsv"),placement(path+"/unit-placement.tsv");
 terrain<<"terrain\tslot\tunit\tdensity\n";restriction<<"restriction\tterrain\tvalue\n";placement<<"civ\tunit\trestriction\tpl1\tpl2\tside1\tside2\tfoundation\n";
 for(size_t id=0;id<d.TerrainBlock.Terrains.size();id++){auto &t=d.TerrainBlock.Terrains[id];for(size_t i=0;i<t.TerrainUnitID.size();i++)if(t.TerrainUnitID[i]>=0&&t.TerrainUnitDensity[i])terrain<<id<<'\t'<<i<<'\t'<<t.TerrainUnitID[i]<<'\t'<<t.TerrainUnitDensity[i]<<'\n';}
 for(size_t id=0;id<d.TerrainRestrictions.size();id++)for(size_t t=0;t<d.TerrainRestrictions[id].PassableBuildableDmgMultiplier.size();t++)restriction<<id<<'\t'<<t<<'\t'<<d.TerrainRestrictions[id].PassableBuildableDmgMultiplier[t]<<'\n';
 std::ofstream language(path+"/language-ids.tsv");language<<"civ\tkind\tid\tname\tdescription\thelp\ticon\n";
 std::ofstream icons(path+"/icons.tsv");icons<<"civ\tkind\tid\tslp\tframe\n";
 std::ofstream art(path+"/unit-art.tsv"),links(path+"/unit-links.tsv"),built(path+"/building-techs.tsv");
 art<<"civ\tunit\tfield\tgraphic\n";links<<"civ\tunit\tfield\ttarget\n";built<<"civ\tunit\ttech\n";
 std::map<std::pair<int,int>,std::vector<int>> swapGroups;
 for(int c:selected)for(size_t id=0;id<d.Civs[c].Units.size();id++){
  auto &v=d.Civs[c];auto &u=v.Units[id];
  if(v.UnitPointers[id]&&u.Type>=40&&u.Bird.TaskSwapGroup)swapGroups[{c,u.Bird.TaskSwapGroup}].push_back(int(id));
 }
 for(int c:selected)for(size_t id=0;id<d.Civs[c].Units.size();id++){
  auto &v=d.Civs[c];if(!v.UnitPointers[id])continue;auto &u=v.Units[id];
  if(u.Type>=40){
   behavior<<c<<'\t'<<id<<'\t'<<u.Bird.WorkRate<<'\t'<<int(u.Type50.BreakOffCombat)<<'\n';
   for(int drop:u.Bird.DropSites)if(drop>=0)drops<<c<<'\t'<<id<<'\t'<<drop<<'\n';
   const auto &tasks=modernTasks?u.Bird.TaskList:d.UnitHeaders.at(id).TaskList;
   for(const auto &t:tasks)if(t.ActionType==155)auras<<c<<'\t'<<id<<'\t'<<t.ID<<'\t'<<t.ClassID<<'\t'<<t.UnitID<<'\t'<<t.WorkValue1<<'\t'<<t.WorkValue2<<'\t'<<t.WorkRange<<'\t'<<t.SearchWaitTime<<'\t'<<int(t.CombatLevelFlag)<<'\t'<<int(t.TargetDiplomacy)<<'\t'<<int(t.AutoSearchTargets)<<'\t'<<t.Enabled<<'\n';
  }
  if(u.Type>=30)movement<<c<<'\t'<<id<<'\t'<<int(u.Trait)<<'\t'<<u.Nothing<<'\t'<<int(u.Creatable.CreatableType)<<'\t'<<int(u.ObstructionType)<<'\t'<<int(u.ObstructionClass)<<'\t'<<int(u.FlyMode)<<'\t'<<int(u.DeadFish.OldMoveAlgorithm)<<'\t'<<u.DeadFish.RotationSpeed<<'\t'<<u.DeadFish.TurnRadius<<'\t'<<u.DeadFish.TurnRadiusSpeed<<'\t'<<u.DeadFish.MaxYawPerSecondMoving<<'\t'<<u.DeadFish.MaxYawPerSecondStationary<<'\t'<<u.DeadFish.StationaryYawRevolutionTime<<'\n';
  mechanics<<c<<'\t'<<id<<'\t'<<int(u.FlyMode)<<'\t'<<u.CollisionSize.x<<'\t'<<u.CollisionSize.y<<'\t'<<u.CollisionSize.z<<'\t'<<int(u.GarrisonCapacity)<<'\t'<<int(u.Building.GarrisonType)<<'\t'<<int(u.Type50.BreakOffCombat)<<'\t'<<int(u.Type50.BlastAttackLevel)<<'\t'<<int(u.BlastDefenseLevel)<<'\t'<<int(u.InteractionMode)<<'\t'<<u.ResourceCapacity<<'\t'<<u.ResourceDecay<<'\t'<<u.Type50.BlastWidth<<'\t'<<u.Type50.BlastDamage<<'\t'<<u.Type50.FriendlyFireDamage<<'\t'<<int(u.Creatable.HeroMode)<<'\n';
  for(size_t i=0;i<u.ResourceStorages.size();i++){const auto &r=u.ResourceStorages[i];storage<<c<<'\t'<<id<<'\t'<<i<<'\t'<<r.Type<<'\t'<<r.Amount<<'\t'<<int(r.Flag)<<'\n';}
  if(u.Type>=40){const auto &tasks=modernTasks?u.Bird.TaskList:d.UnitHeaders.at(id).TaskList;
   for(const auto &t:tasks)detailedTasks<<c<<'\t'<<id<<'\t'<<t.ID<<'\t'<<t.ActionType<<'\t'<<t.ClassID<<'\t'<<t.UnitID<<'\t'<<t.WorkValue1<<'\t'<<t.WorkValue2<<'\t'<<t.WorkRange<<'\t'<<t.ResourceIn<<'\t'<<t.ResourceOut<<'\t'<<t.ResourceMultiplier<<'\t'<<int(t.CombatLevelFlag)<<'\t'<<int(t.TargetDiplomacy)<<'\n';
  }
  placement<<c<<'\t'<<id<<'\t'<<u.TerrainRestriction<<'\t'<<u.PlacementTerrain.first<<'\t'<<u.PlacementTerrain.second<<'\t'<<u.PlacementSideTerrain.first<<'\t'<<u.PlacementSideTerrain.second<<'\t'<<u.Building.FoundationTerrainID<<'\n';
  language<<c<<"\tunit\t"<<id<<'\t'<<u.LanguageDLLName<<'\t'<<u.LanguageDLLCreation<<'\t'<<u.LanguageDLLHelp<<'\t'<<u.IconID<<'\n';
  if(u.IconID>=0)icons<<c<<"\tunit\t"<<id<<'\t'<<(u.Type==80&&u.Class!=34&&u.Class!=36?53300:53330)+int(v.IconSet)<<'\t'<<u.IconID+u.Building.GraphicsAngle<<'\n';
  auto sound=[&](const char *event,int value){if(value>=0)usound<<c<<'\t'<<id<<'\t'<<event<<'\t'<<value<<'\n';};
  sound("selection",u.SelectionSound);sound("train",u.TrainSound);sound("death",u.DyingSound);sound("damage",u.DamageSound);
  if(u.Type>=40){sound("attack",u.Bird.AttackSound);sound("move",u.Bird.MoveSound);if(modernTasks||id<d.UnitHeaders.size())for(auto &t:modernTasks?u.Bird.TaskList:d.UnitHeaders[id].TaskList){sound("gather",t.ResourceGatheringSoundID);sound("deposit",t.ResourceDepositSoundID);}}
  if(u.Type==80){sound("construction",u.Building.ConstructionSound);sound("transform",u.Building.TransformSound);}
  auto g=[&](const char *name,int value){if(value>=0)art<<c<<'\t'<<id<<'\t'<<name<<'\t'<<value<<'\n';};
  auto l=[&](const char *name,int value){if(value>=0)links<<c<<'\t'<<id<<'\t'<<name<<'\t'<<value<<'\n';};
  g("standing",u.StandingGraphic.first);g("standing2",u.StandingGraphic.second);g("dying",u.DyingGraphic);g("undead",u.UndeadGraphic);
  for(auto &x:u.DamageGraphics)g("damage",x.GraphicID);
  l("dead",u.DeadUnitID);
  if(u.Type>=40&&u.Bird.TaskSwapGroup)for(int peer:swapGroups[{c,u.Bird.TaskSwapGroup}])if(peer!=int(id))l("task-swap",peer);
  if(u.Type>=30){g("walking",u.DeadFish.WalkingGraphic);g("running",u.DeadFish.RunningGraphic);l("tracking",u.DeadFish.TrackingUnit);}
  if(u.Type>=40&&(modernTasks||id<d.UnitHeaders.size()))for(auto &t:modernTasks?u.Bird.TaskList:d.UnitHeaders[id].TaskList){
   g("task-moving",t.MovingGraphicID);g("task-proceeding",t.ProceedingGraphicID);g("task-working",t.WorkingGraphicID);g("task-carrying",t.CarryingGraphicID);
  }
  if(u.Type>=50){g("attack",u.Type50.AttackGraphic);l("projectile",u.Type50.ProjectileUnitID);}
  if(u.Type>=70){g("garrison",u.Creatable.GarrisonGraphic);g("special",u.Creatable.SpecialGraphic);l("secondary-projectile",u.Creatable.SecondaryProjectileUnit);}
  if(u.Type==80){
   g("construction",u.Building.ConstructionGraphicID);g("snow",u.Building.SnowGraphicID);
   l("stack",u.Building.StackUnitID);l("head",u.Building.HeadUnit);l("transform",u.Building.TransformUnit);l("pile",u.Building.PileUnit);
   for(auto &x:u.Building.Annexes)l("annex",x.UnitID);
   if(u.Building.TechID>=0)built<<c<<'\t'<<id<<'\t'<<u.Building.TechID<<'\n';
  }
 }
 for(size_t id=0;id<d.Techs.size();id++){auto &t=d.Techs[id];language<<t.Civ<<"\ttech\t"<<id<<'\t'<<t.LanguageDLLName<<'\t'<<t.LanguageDLLDescription<<'\t'<<t.LanguageDLLHelp<<'\t'<<t.IconID<<'\n';}
 for(int c:selected)for(size_t id=0;id<d.Techs.size();id++)if(d.Techs[id].IconID>=0)icons<<c<<"\ttech\t"<<id<<'\t'<<53360+int(d.Civs[c].IconSet)<<'\t'<<d.Techs[id].IconID<<'\n';
}
