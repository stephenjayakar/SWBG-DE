#pragma once
// DE monk class prioritizes conversion. Use infantry for armed Force users and
// the shipped Sun Ce conversion ability for an explicit conversion command.
// Holocron carriers (source class 51) retain their separate native class 43.
inline void adaptFactionForce(genie::DatFile &target,const genie::DatFile &source,const genie::DatFile &native){
 const auto &model=native.Civs.at(1).Units.at(2040);
 if(model.Name!="HSUNCE"||model.Creatable.ChargeType!=-4||model.Creatable.MaxCharge<=0)
  throw std::runtime_error("Re-audit native conversion ability template");
 const auto attack=std::find_if(model.Bird.TaskList.begin(),model.Bird.TaskList.end(),[](const auto &t){return t.ActionType==7;});
 if(attack==model.Bird.TaskList.end())throw std::runtime_error("Missing native combat task");
 std::ofstream audit("work/faction-force-adapter.tsv");
 audit<<"civ\tunit\tconversion\tclass\trange\tchance\tcooldown\n";
 for(size_t c=0;c<target.Civs.size();c++){
  const auto &from=source.Civs.at(c==2?3:c);auto &to=target.Civs[c];
  for(size_t uid=0;uid<from.Units.size();uid++){
   if(!from.UnitPointers[uid]||from.Units[uid].Class!=50)continue;
   auto &u=to.Units.at(uid);if(u.Class!=6||u.Type!=70)throw std::runtime_error("Unexpected Force unit class/type");
   bool hasAttack=false,canConvert=false;
   for(auto &t:u.Bird.TaskList){
    if(t.ActionType==7){
     t.AutoSearchTargets=attack->AutoSearchTargets;t.EnableTargeting=attack->EnableTargeting;
     t.CombatLevelFlag=attack->CombatLevelFlag;t.TargetDiplomacy=attack->TargetDiplomacy;hasAttack=true;
    }
    if(t.ActionType==104&&t.EnableTargeting&&t.CombatLevelFlag&&t.TargetDiplomacy==2)canConvert=true;
   }
   if(!hasAttack)throw std::runtime_error("Force unit lacks combat task");
   if(canConvert){
    auto &v=u.Creatable;const auto &n=model.Creatable;
    v.ChargeType=-4;v.MaxCharge=n.MaxCharge;v.RechargeRate=n.RechargeRate;
    v.ChargeEvent=int16_t(from.Resources.at(5));v.ChargeTarget=n.ChargeTarget;
    v.ButtonIconID=n.ButtonIconID;v.ButtonShortTooltipID=898001;v.ButtonExtendedTooltipID=898002;
    v.ButtonHotkeyAction=n.ButtonHotkeyAction;
    // DE uses displayed reload for conversion rolls. Actual melee reload stays source-exact.
    u.Type50.DisplayedReloadTime=model.Type50.DisplayedReloadTime;
   }
   audit<<c<<'\t'<<uid<<'\t'<<canConvert<<'\t'<<u.Class<<'\t'<<u.Creatable.ChargeEvent<<'\t'<<u.Creatable.ChargeTarget<<'\t'<<(canConvert?u.Creatable.MaxCharge/u.Creatable.RechargeRate:0)<<'\n';
  }
 }
}
