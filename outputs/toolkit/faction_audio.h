#pragma once
inline void importFactionAudio(genie::DatFile &target,const genie::DatFile &source){
 const int offset=int(target.Sounds.size());
 std::ofstream("work/faction-sound-offset.txt")<<offset;
 auto sound=[&](int id){if(id<0)return -1;if(id>=int(source.Sounds.size())||offset+id>=32767)throw std::runtime_error("Invalid source sound ID");return offset+id;};
 // Preserve native UI/global groups; source unit/graphic bindings use appended groups.
 target.Sounds.insert(target.Sounds.end(),source.Sounds.begin(),source.Sounds.end());
 for(size_t id=offset;id<target.Sounds.size();id++){
  auto &group=target.Sounds[id];group.ID=int16_t(id);
  for(size_t i=0;i<group.Items.size();i++){
   auto &item=group.Items[i];
   item.FileName=item.ResourceID>=0?"swgb_"+std::to_string(item.ResourceID):"swgb_"+std::to_string(id-offset)+"_"+std::to_string(i)+"_"+std::filesystem::path(item.FileName).stem().string();
   item.ResourceID=-1;
   if(item.Civilization==3)item.Civilization=2;else if(item.Civilization>=2)item.Civilization+=10;
  }
 }
 for(size_t id=0;id<target.Graphics.size();id++)if(target.GraphicPointers[id]){
  auto &g=target.Graphics[id];auto &s=source.Graphics[id];g.SoundID=int16_t(sound(s.SoundID));g.WwiseSoundID=0;
  g.AngleSoundsUsed=s.AngleSoundsUsed;g.AngleSounds=s.AngleSounds;
  if((g.AngleCount==8||g.AngleCount==16)&&g.AngleSounds.size()==size_t(g.AngleCount)){
   for(int angle=0;angle<g.AngleCount;angle++)g.AngleSounds[angle]=s.AngleSounds[(angle+3*g.AngleCount/4)%g.AngleCount];
  }
  for(auto &a:g.AngleSounds){a.SoundID=int16_t(sound(a.SoundID));a.SoundID2=int16_t(sound(a.SoundID2));a.SoundID3=int16_t(sound(a.SoundID3));a.WwiseSoundID=0;a.WwiseSoundID2=0;a.WwiseSoundID3=0;}
 }
 auto taskSound=[&](auto &t,const auto &s){t.ResourceGatheringSoundID=int16_t(sound(s.ResourceGatheringSoundID));t.ResourceDepositSoundID=int16_t(sound(s.ResourceDepositSoundID));t.WwiseResourceGatheringSoundID=0;t.WwiseResourceDepositSoundID=0;};
 for(auto &h:target.UnitHeaders)for(auto &t:h.TaskList)taskSound(t,t);
 const int sourceCivs[]={0,1,3};
 for(size_t c=0;c<target.Civs.size();c++)for(size_t id=0;id<target.Civs[c].Units.size();id++){
  if(!target.Civs[c].UnitPointers[id])continue;auto &u=target.Civs[c].Units[id];auto &s=source.Civs[sourceCivs[c]].Units[id];
  u.SelectionSound=int16_t(sound(s.SelectionSound));u.DyingSound=int16_t(sound(s.DyingSound));u.TrainSound=int16_t(sound(s.TrainSound));u.DamageSound=int16_t(sound(s.DamageSound));
  if(u.Type>=40){
   u.Bird.AttackSound=int16_t(sound(s.Bird.AttackSound));u.Bird.MoveSound=int16_t(sound(s.Bird.MoveSound));
   auto &tasks=source.UnitHeaders.at(id).TaskList;if(u.Bird.TaskList.size()!=tasks.size())throw std::runtime_error("Import audio before expanding tasks");
   for(size_t i=0;i<tasks.size();i++)taskSound(u.Bird.TaskList[i],tasks[i]);
  }
  if(u.Type==80){u.Building.TransformSound=int16_t(sound(s.Building.TransformSound));u.Building.ConstructionSound=int16_t(sound(s.Building.ConstructionSound));}
 }
}
