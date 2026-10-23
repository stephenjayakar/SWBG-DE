"""Original soldier predicate calls the real base predicate/static EF patch.

Fixture boundaries: distance/path geometry, weapon range, active action lookup,
patrol predicates, target invisibility. No game or OS commands are run.
"""
import struct
from classic_attack_eligibility_oracle import AttackEligibilityOracle
from classic_engine_oracle import TACTICAL
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP


class SoldierEligibilityOracle(AttackEligibilityOracle):
    def soldier(self,s,priest=False,held_attribute=0,siege=False,own_state=2,computer_player=1):
        assert not (priest and siege)
        ai,own,target=self._fixture(s.attacker_class,s.attacker_id,s.target_class,s.target_id,
                                    s.invisible,s.resource31,s.owner_id)
        owner,own_vtable,action_list,action=(TACTICAL+n for n in (0x89000,0x8A000,0x8B000,0x8C000))
        for p in (owner,own_vtable,action_list,action):self.cpu.mem_write(p,bytes(0x400))
        self.write(owner+0xA0,s.target_owner)
        self.write(target+0x18,owner)
        self.cpu.mem_write(self.read(target+0x14)+4,bytes([s.target_type]))
        self.cpu.mem_write(target+0x235,bytes([s.target_flag]))
        self.write(own,own_vtable)
        self.cpu.mem_write(own+0x5C,struct.pack('<h',held_attribute))
        self.cpu.mem_write(own+0x58,bytes([own_state]))
        player_vtable=TACTICAL+0x8F000
        self.write(self.read(own+0x18),player_vtable)
        computer_stub=TACTICAL+0x8F400
        self.write(player_vtable+0x1C,computer_stub)
        self.hooks[computer_stub]=lambda:self.ret(computer_player)
        self.write(own+0x13C,action_list if s.action_type != -2 else 0)
        self.cpu.mem_write(action+4,struct.pack('<h',s.action_type))
        self.hooks[0x406EA0]=lambda:self.ret(action if s.action_type>=0 else 0)
        self.cpu.mem_write(ai+0x169,bytes([s.stance]))
        self.write(ai+0x54,s.last_action)
        self.write(ai+0x28,s.current_order)
        # Float return stubs execute FLD and RET, preserving the caller's x87
        # precision and subsequent stored distance/range comparisons.
        def float_stub(index,value,args):
            address=TACTICAL+0x8D000+index*0x100
            self.cpu.mem_write(address,b'\xD9\x05'+struct.pack('<I',address+0x10)+b'\xC2'+struct.pack('<H',args*4))
            self.cpu.mem_write(address+0x10,struct.pack('<f',value))
            return address
        state_stub=float_stub(0,s.state_distance,3)
        self.hooks[0x551C60]=lambda:self.cpu.reg_write(UC_X86_REG_EIP,state_stub)
        self.write(own_vtable+0x194,float_stub(1,s.weapon_range,0))
        self.write(own_vtable+0x270,float_stub(2,s.highest_path_distance,3))
        patrol_stub=float_stub(3,s.patrol_path_distance,3)
        self.hooks[0x4BC700]=lambda:self.cpu.reg_write(UC_X86_REG_EIP,patrol_stub)
        on_patrol_stub=TACTICAL+0x8E000
        self.write(own_vtable+0x338,on_patrol_stub)
        self.hooks[on_patrol_stub]=lambda:self.ret(s.on_patrol)
        self.hooks[0x422080]=lambda:self.ret(s.has_patrol)
        position_stub=TACTICAL+0x8E100
        self.write(self.read(target)+0x2AC,position_stub)
        def position():
            sp=self.cpu.reg_read(UC_X86_REG_ESP)
            output=self.read(sp+4)
            self.cpu.mem_write(output,bytes(12))
            self.ret(output,args=1)
        self.hooks[position_stub]=position
        address=0x5B8180 if siege else 0x5B4B60 if priest else 0x5B6E70
        result=self.call(address,(target if s.target_present else 0,),this=ai)
        assert self.invisibility_calls in ([],[s.owner_id]),self.invisibility_calls
        assert result in (0,1),result
        return bool(result)
