"""Execute the original combat-object armor formula with no damage-method stub."""
import struct
from classic_engine_oracle import Oracle,TACTICAL,RETURN


class DamageOracle(Oracle):
    def result_float(self):
        out=TACTICAL+0x69000
        self.cpu.mem_write(RETURN,b'\xD9\x1D'+struct.pack('<I',out))
        self.cpu.emu_start(RETURN,RETURN+6,count=10)
        return struct.unpack('<f',self.cpu.mem_read(out,4))[0]

    def _damage_fixture(self,weapons,armor,base_armor,terrain_modifier):
        # Each table has a separate 4 KiB fixture region; source counts are i16.
        assert len(weapons)<=1024 and len(armor)<=1024
        self.reset()
        obj,master,weapon_array,armor_array,owner,world,tile,terrain_table,terrain,out=(
            TACTICAL+n for n in (0x60000,0x61000,0x62000,0x63000,0x64000,0x65000,0x66000,0x67000,0x68000,0x69000))
        for ptr in (obj,master,owner,world,tile,terrain_table,terrain):self.cpu.mem_write(ptr,bytes(0x400))
        self.write(obj+0x14,master)
        self.write(obj+0x18,owner)
        self.write(obj+0x28,tile)
        self.cpu.mem_write(master+0x130,struct.pack('<hh',base_armor,len(armor)))
        self.write(master+0x134,armor_array if armor else 0)
        self.cpu.mem_write(master+0x140,struct.pack('<h',0))
        self.write(owner+0x8C,world)
        self.write(world+0x60,terrain_table)
        self.write(terrain_table,terrain)
        self.cpu.mem_write(terrain,struct.pack('<f',terrain_modifier))
        for pointer,values in ((weapon_array,weapons),(armor_array,armor)):
            for i,(kind,value) in enumerate(values):self.cpu.mem_write(pointer+i*4,struct.pack('<hh',kind,value))
        return obj,weapon_array

    def damage(self,weapons,armor,base_armor=1000,attack_modifier=1.0,terrain_modifier=1.0):
        obj,weapon_array=self._damage_fixture(weapons,armor,base_armor,terrain_modifier)
        modifier=struct.unpack('<i',struct.pack('<f',attack_modifier))[0]
        self.call(0x4449C0,(len(weapons),weapon_array if weapons else 0,modifier,0,0),this=obj)
        # Store the original function's x87 ST0 as a float32 at its caller.
        return self.result_float()

    def capability(self,weapons,armor,base_armor=1000,attack_modifier=1.0,terrain_modifier=1.0,
                   target_present=True,has_ai=True,can_attack=True):
        target,weapon_array=self._damage_fixture(weapons,armor,base_armor,terrain_modifier)
        attacker,master,vtable,target_vtable,ai,ai_vtable=(TACTICAL+n for n in
                                                       (0x6A000,0x6B000,0x6C000,0x6D000,0x6E000,0x6F000))
        for ptr in (attacker,master,vtable,target_vtable,ai,ai_vtable):self.cpu.mem_write(ptr,bytes(0x400))
        self.write(attacker,vtable)
        self.write(attacker+0x14,master)
        self.write(attacker+0x18,TACTICAL+0x64000)
        self.cpu.mem_write(master+0x138,struct.pack('<h',len(weapons)))
        self.write(master+0x13C,weapon_array if weapons else 0)
        self.write(target,target_vtable)
        self.write(target_vtable+0xEC,0x4449C0)
        self.write(ai,ai_vtable)
        modifier_stub,attack_stub=TACTICAL+0x70000,TACTICAL+0x70200
        self.write(vtable+0x17C,modifier_stub)
        self.cpu.mem_write(modifier_stub,b'\xD9\x05'+struct.pack('<I',modifier_stub+0x10)+b'\xC2\x04\x00')
        self.cpu.mem_write(modifier_stub+0x10,struct.pack('<f',attack_modifier))
        self.write(ai_vtable+0x4C,attack_stub)
        self.cpu.mem_write(attack_stub,b'\xC3')
        self.hooks[attack_stub]=lambda:self.ret(int(can_attack),args=1)
        self.hooks[0x40C840]=lambda:self.ret(ai if has_ai else 0)
        # Real wrapper dispatches to the real target armor function. Only the
        # UnitAI query/predicate and already-computed attack modifier are fixtures.
        self.call(0x445F60,(target if target_present else 0,),this=attacker)
        return self.result_float()

    def modifier(self,higher_ground=False,attacker_z=0.0,target_z=0.0,special_mode=0,action_133=False,
                 building=False,relics=0,special_relics=0,target_building=False,
                 target_relics=0,target_special_relics=0):
        self.reset()
        obj,target,master,target_master,vtable=(TACTICAL+n for n in (0x60000,0x61000,0x62000,0x63000,0x64000))
        for ptr in (obj,target,master,target_master,vtable):self.cpu.mem_write(ptr,bytes(0x400))
        self.write(obj,vtable)
        self.write(obj+0x14,master)
        self.write(target+0x14,target_master)
        self.cpu.mem_write(obj+0x50,struct.pack('<f',attacker_z))
        self.cpu.mem_write(target+0x50,struct.pack('<f',target_z))
        self.cpu.mem_write(master+0x1C0,bytes([special_mode]))
        self.cpu.mem_write(target_master+4,bytes([80 if target_building else 70]))
        self.write(obj+0x208,relics)
        self.write(obj+0x20C,special_relics)
        self.write(target+0x208,target_relics)
        self.write(target+0x20C,target_special_relics)
        higher_stub=TACTICAL+0x65000
        self.write(vtable+0x3EC,higher_stub)
        self.hooks[higher_stub]=lambda:self.ret(int(higher_ground),args=1)
        self.hooks[0x406DA0]=lambda:self.ret(int(action_133),args=1)
        self.call(0x557BA0 if building else 0x55BBC0,(target,),this=obj)
        return self.result_float()
