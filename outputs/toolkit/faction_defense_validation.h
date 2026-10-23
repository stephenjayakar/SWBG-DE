#pragma once
inline void validateFactionDefenses(const genie::DatFile &d,const genie::DatFile &s){
 auto require=[](bool value,const char *why){if(!value)throw std::runtime_error(why);};
 size_t pairs=0,auras=0;
 for(int c:{1,2}){
  for(size_t id=0;id<d.Civs[c].Units.size();id++){
   if(!d.Civs[c].UnitPointers[id])continue;const auto &u=d.Civs[c].Units[id];
   bool aa=defenseAirTurret(int(id)),land=defenseGroundTurret(int(id))||id==5075;
   if(aa||land){
    require(id!=5075||u.Class==35,"Mine lacks native demolition class");
    require(u.Bird.DefaultTaskID==0,"Invalid defense default task");
    for(size_t i=0;i<u.Bird.TaskList.size();i++)require(u.Bird.TaskList[i].ID==i,"Non-contiguous defense task IDs");
    for(int tc:{0,1,2})for(size_t target=0;target<d.Civs[tc].Units.size();target++){
     if(!d.Civs[tc].UnitPointers[target])continue;const auto &v=d.Civs[tc].Units[target];if(v.Type<70)continue;
     bool air=s.Civs[tc==2?3:tc].Units.at(target).FlyMode!=0,match=false;
     for(const auto &t:u.Bird.TaskList)if(t.ActionType==7&&
        ((t.UnitID>=0&&t.UnitID==target)||(t.UnitID<0&&t.ClassID==v.Class)))match=true;
     require(match==(aa?air:!air),"Air/ground target selector mismatch");pairs++;
    }
   }
  }
  for(int id:{213,215,335,336}){
   const auto &u=d.Civs[c].Units[id];int visible=0,count=0;
   require((u.Type50.BreakOffCombat&32)!=0,"Missing aura ability");
   for(size_t i=0;i<u.Bird.TaskList.size();i++){
    const auto &t=u.Bird.TaskList[i];if(t.ActionType!=155)continue;
    require(t.ID==i&&t.UnitID>=0&&t.ClassID==-1,"Invalid shield recipient task");
    const auto &v=s.Civs[c==2?3:c].Units.at(t.UnitID);
    require(v.Type>=70&&v.HitPoints>0&&!v.FlyMode&&v.Class!=6,"Invalid shield recipient");
    require((t.SearchWaitTime==0||t.SearchWaitTime==109)&&t.WorkValue1==0&&t.WorkValue2==1,"Non-neutral shield task");
    require(t.TargetDiplomacy==1&&t.Enabled==-1&&t.WorkRange==s.Civs[c==2?3:c].Resources[24],"Invalid shield scope");
    require(t.CombatLevelFlag==2||t.CombatLevelFlag==6,"Invalid shield circle");
    if(t.CombatLevelFlag==6)visible++;count++;
   }
   require(visible==1&&count>0&&count%2==0,"Invalid shield task pairs");auras+=count;
  }
 }
 for(int mode=0;mode<2;mode++){
  const auto &t=d.Techs.at(d.Techs.size()-2+mode);
  require(t.Name==(mode?"SWGB_DEFENSE_LAYOUT":"SWGB_MILITARY_LAYOUT")&&t.Repeatable==1&&t.Civ==-1&&t.RequiredTechCount==0,"Invalid layout research");
  require(t.IconID>=0&&t.ResearchLocations.size()==1,"Invalid layout icon/location");
  const auto &l=t.ResearchLocations[0];
  require(l.LocationID==109&&l.ButtonID==11+mode&&l.QueueTime==defenseLayoutResearchTime&&l.HotKeyID==1100010+mode,"Invalid layout button/time");
  for(auto r:t.ResourceCosts)require(!r.Flag&&r.Amount==0,"Layout costs resources");
  for(auto r:t.RequiredTechs)require(r==-1,"Layout has requirement");
  const auto &e=d.Effects.at(t.EffectID);require(e.Name==t.Name&&!e.EffectCommands.empty(),"Layout effect missing");
  for(auto cmd:e.EffectCommands)require(cmd.Type==0&&cmd.C==defenseLayoutTrainButton&&cmd.B==-1&&cmd.A>=0&&cmd.D>=0&&cmd.D<=13,"Unexpected layout mutation");
  for(size_t other=0;other<d.Techs.size()-2;other++)for(const auto &loc:d.Techs[other].ResearchLocations)
   require(loc.LocationID!=109||loc.ButtonID!=l.ButtonID,"Command Center research collision");
 }
 std::cout<<"Defense validation: "<<pairs<<" target pairs, "<<auras<<" neutral aura tasks; layout contracts passed.\n";
}
