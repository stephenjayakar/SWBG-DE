"""Run original addUnit aggregation, stubbing only world/virtual unit queries."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP
from classic_engine_oracle import Oracle,TACTICAL
from classic_target_model import FLOAT_MAX


class CombatOracle(Oracle):
    def estimate(self, own, enemies, target, damage, convertible, zone=1, target_zone=1, distance=20.0):
        assert 0 < len(own) <= 40 and len(enemies) <= 128
        self.reset()
        stats, units, enemy_array, enemy_ids, centroid, game, world, vtable, ai_vtable = (
            TACTICAL+n for n in (0x60000,0x70000,0x71000,0x72000,0x73000,0x74000,0x75000,0x76000,0x77000))
        self.cpu.mem_write(stats,bytes(0xE020))
        for offset in (0,8,16):
            self.cpu.mem_write(stats+offset,struct.pack('<ff',FLOAT_MAX,0.0))
        self.write(0x6A3684,game)
        self.write(game+0x420,world)
        for index,unit in enumerate(own): self.write(units+index*4,unit.uid)
        self.cpu.mem_write(enemy_array,struct.pack('<iiii',enemy_ids,len(enemies),0,128))
        for index,unit in enumerate(enemies): self.write(enemy_ids+index*4,unit.uid)
        self.cpu.mem_write(centroid,bytes(12))
        records = {unit.uid:unit for unit in [*own,*enemies,target]}
        objects, reverse, ai_objects = {}, {}, {}
        for index,(uid,unit) in enumerate(records.items()):
            obj = TACTICAL+0x100000+index*0x400
            objects[uid],reverse[obj],ai_objects[obj+0x200] = obj,unit,unit
            self.cpu.mem_write(obj,bytes(0x400))
            self.write(obj,vtable)
            self.write(obj+0x10,uid)
            self.write(obj+0x14,obj+0x100)
            self.cpu.mem_write(obj+0x3C,struct.pack('<f',unit.hp))
            self.cpu.mem_write(obj+0x11E,struct.pack('<h',32))
            self.write(obj+0x200,ai_vtable)
        # Each float stub executes FLD and RET in the emulator. Hooks only set
        # its explicit virtual-method return fixture; x87 arithmetic is original.
        def float_stub(address,argc,get_value):
            value_address = address+0x10
            self.cpu.mem_write(address,b'\xD9\x05'+struct.pack('<I',value_address)+b'\xC2'+struct.pack('<H',argc*4))
            self.hooks[address] = lambda:self.cpu.mem_write(value_address,struct.pack('<f',get_value()))
        hit_stub,reload_stub,convert_stub = (TACTICAL+n for n in (0x78000,0x78100,0x78200))
        self.write(vtable+0x190,hit_stub)
        self.write(vtable+0x18C,reload_stub)
        self.write(ai_vtable+0xC0,convert_stub)
        def pair():
            attacker = reverse[self.cpu.reg_read(UC_X86_REG_ECX)].uid
            victim_obj = self.read(self.cpu.reg_read(UC_X86_REG_ESP)+4)
            return attacker,reverse[victim_obj].uid
        float_stub(hit_stub,1,lambda:damage.get(pair(),0.0))
        float_stub(reload_stub,0,lambda:reverse[self.cpu.reg_read(UC_X86_REG_ECX)].reload)
        # Fixed distance query avoids replacing the source's combat loop.
        distance_stub = TACTICAL+0x78300
        float_stub(distance_stub,3,lambda:distance)
        self.hooks[0x551C60] = lambda:self.cpu.reg_write(UC_X86_REG_EIP,distance_stub)
        def conversion():
            attacker = ai_objects[self.cpu.reg_read(UC_X86_REG_ECX)].uid
            victim = self.read(self.cpu.reg_read(UC_X86_REG_ESP)+4)
            self.ret(int(convertible.get((attacker,victim),False)),args=2)
        self.hooks[convert_stub] = conversion
        def lookup():
            uid = self.read(self.cpu.reg_read(UC_X86_REG_ESP)+4)
            self.ret(objects[uid] if records[uid].exists else 0,args=1)
        self.hooks[0x623DB0] = lookup
        def unit_ai():
            obj = self.cpu.reg_read(UC_X86_REG_ECX)
            self.ret(obj+0x200 if reverse[obj].has_ai else 0)
        self.hooks[0x40C840] = unit_ai
        self.hooks[0x552610] = lambda:self.ret(target_zone,args=2)
        self.call(0x592430,(units,len(own),enemy_array,centroid,zone,objects[target.uid],0),this=stats)
        assert self.read(stats+0xD018) == 1
        return (*struct.unpack('<ff',self.cpu.mem_read(stats+0x28,8)),bool(self.read(stats+0x34)))
