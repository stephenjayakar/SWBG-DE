#pragma once
inline void importFactionPower(genie::DatFile &target,const genie::DatFile &source,const genie::DatFile &native){
 float unpowered=-1;
 for(const auto &e:source.Effects.at(0).EffectCommands)if(e.Type==1&&e.A==19&&e.B==0)unpowered=e.D;
 if(unpowered<=0||unpowered>=1)throw std::runtime_error("Unexpected source unpowered work multiplier");
 for(const auto &fx:source.Effects)for(const auto &e:fx.EffectCommands)
  if((e.Type==0||e.Type==4)&&e.C==13)throw std::runtime_error("Additive work-rate effects require power scaling");
 genie::Task prototype;bool found=false;
 // Native Fortified Church production aura encodes a proportional BONUS:
 // 0.1 means +10%, unlike movement auras whose 1.1 means x1.1.
 for(const auto &t:native.Civs.at(0).Units.at(2275).Bird.TaskList)
  if(t.ActionType==155&&t.SearchWaitTime==13&&std::abs(t.WorkValue1-.1f)<.00001f){prototype=t;found=true;break;}
 if(!found||!(prototype.CombatLevelFlag&1))throw std::runtime_error("Native multiplier aura template changed");
 prototype.MovingGraphicID=-1;prototype.ProceedingGraphicID=-1;prototype.WorkingGraphicID=-1;prototype.CarryingGraphicID=-1;
 prototype.ResourceGatheringSoundID=-1;prototype.ResourceDepositSoundID=-1;prototype.WwiseResourceGatheringSoundID=0;prototype.WwiseResourceDepositSoundID=0;
 std::ifstream list("work/faction-tree-units.txt");std::set<int> reachable;int id;while(list>>id)reachable.insert(id);
 std::set<int> cores={12};bool expanded=true;
 while(expanded){expanded=false;
  for(const auto &fx:source.Effects)for(const auto &e:fx.EffectCommands)
   if(e.Type==3&&cores.count(e.A)&&e.B>=0)expanded=cores.insert(e.B).second||expanded;
 }
 if(cores!=std::set<int>({12,498,132,20,3554,3555,3556,3557}))
  throw std::runtime_error("Re-audit source Power Core upgrade family");
 std::ofstream targets("work/faction-power-targets.tsv"),emitters("work/faction-power-emitters.tsv");
 targets<<"civ\tunit\tsource_workrate\tunpowered_workrate\n";emitters<<"civ\tunit\trange\tmultiplier\tfirst_task\tcount\n";
 const int sourceCivs[]={0,1,3};
 for(size_t c=1;c<target.Civs.size();c++){
  const auto &original=source.Civs[sourceCivs[c]];auto &civ=target.Civs[c];std::vector<int> affected;
  auto exempt=[&](auto &&self,int u,std::set<int> visited)->bool{
   if(!visited.insert(u).second)return false;
   const auto &v=original.Units.at(u);
   if(u==109||u==82||u==50||u==7353||v.Class==9||v.Class==10||v.Class==34||v.Class==36)return true;
   for(int parent:{int(v.Building.HeadUnit),int(v.Building.StackUnitID)})if(parent>=0&&self(self,parent,visited))return true;
   return false;
  };
  for(int u:reachable){const auto &v=original.Units.at(u);if(v.Type!=80||v.Bird.WorkRate<=0||exempt(exempt,u,{}))continue;
   civ.Units[u].Bird.WorkRate=v.Bird.WorkRate*unpowered;affected.push_back(u);
   targets<<c<<'\t'<<u<<'\t'<<v.Bird.WorkRate<<'\t'<<civ.Units[u].Bird.WorkRate<<'\n';
  }
  // Checking only id 12 dropped the aura on every age advancement.
  // Follow its upgrade family; source class 18 also includes other buildings.
  for(int u:reachable){const auto &v=original.Units.at(u);if(!cores.count(u)&&v.Class!=61)continue;
   auto &unit=civ.Units[u];const float range=original.Resources.at(v.Class==61?30:18);
   if(range<=0)throw std::runtime_error("Power emitter has invalid source radius");
   const size_t first=unit.Bird.TaskList.size();unit.Type50.BreakOffCombat|=32;
   for(int recipient:affected){auto task=prototype;
    task.ID=int16_t(unit.Bird.TaskList.size());task.ClassID=-1;task.UnitID=int16_t(recipient);
    task.SearchWaitTime=13;task.WorkValue1=1/unpowered-1;task.WorkValue2=1;task.WorkRange=range;
    // Only one task draws the identical range; avoid 127 overlaid rings.
    task.CombatLevelFlag=unit.Bird.TaskList.size()==first?7:3;
    task.TargetDiplomacy=1;task.IsDefault=false;task.Enabled=-1;
    unit.Bird.TaskList.push_back(task);
   }
   if(unit.Bird.TaskList.size()>32767)throw std::runtime_error("Power aura exceeds task count");
   emitters<<c<<'\t'<<u<<'\t'<<range<<'\t'<<1/unpowered<<'\t'<<first<<'\t'<<affected.size()<<'\n';
  }
 }
}
