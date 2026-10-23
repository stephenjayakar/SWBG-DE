"""Execute source candidate admission and group validity with explicit queries.

The candidate fixture starts at the inner-loop boundary of objectToAttack2 and
stops at admission/rejection. It does not replace the gate with a Python hook.
Only world lookup and virtual observation calls are supplied by the fixture;
isBoat, naval wall scan, branches and integer conversion execute source bytes.
"""
import struct
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EBP,
                              UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP)
from classic_engine_oracle import Oracle, TACTICAL, STACK, RETURN
from classic_admission_model import SelectionContext


class AdmissionOracle(Oracle):
    def arg(self, index):
        return self.read(self.cpu.reg_read(UC_X86_REG_ESP) + 4 + index * 4)

    def bind(self, table, offset, callback):
        address = TACTICAL + 0xF0000 + len(self.hooks) * 16
        self.write(table + offset, address)
        self.hooks[address] = callback

    def candidate(self, target, context=SelectionContext(), reachable_tiles=()):
        self.reset()
        info, main, memory, obj, master, owner, vtable, diplomacy, diptable, monk, unit_ai, ai_table, leader, game, world, map_ptr = (
            TACTICAL + n * 0x1000 for n in range(0x40, 0x50))
        for ptr in (info, main, memory, obj, master, owner, vtable, diplomacy, diptable, monk, unit_ai, ai_table, leader, game, world, map_ptr):
            self.cpu.mem_write(ptr, bytes(0x1000))
        self.write(info + 0x100, main)
        self.write(info + 0x34C, memory)
        self.write(main + 0x6608, diplomacy)
        self.write(diplomacy, diptable)
        self.write(memory, target.uid)
        self.cpu.mem_write(memory + 0xB, bytes([target.memory_owner]))
        self.write(obj, vtable)
        self.write(obj + 0x10, target.uid)
        self.write(obj + 0x14, master)
        self.write(obj + 0x18, owner)
        self.cpu.mem_write(obj + 0x3C, struct.pack('<f', target.hp))
        self.cpu.mem_write(obj + 0x48, struct.pack('<ff', target.x, target.y))
        self.cpu.mem_write(obj + 0x58, bytes([target.state]))
        self.cpu.mem_write(owner + 0xA6, bytes([target.owner_status]))
        self.cpu.mem_write(master + 4, bytes([target.master_type]))
        self.cpu.mem_write(master + 0x18, struct.pack('<h', target.source_id))
        self.cpu.mem_write(master + 0x1E, struct.pack('<h', target.source_class))
        self.cpu.mem_write(master + 0x75, bytes([target.fog_flag]))
        self.write(master + 0xAC, target.object_flags)
        self.write(unit_ai, ai_table)
        self.write(0x6A3684, game)
        self.write(game + 0x420, world)
        self.write(world + 0x34, map_ptr)
        self.write(map_ptr + 8, context.width)
        self.write(map_ptr + 12, context.height)
        self.hooks[0x413850] = lambda: self.ret(obj if target.exists else 0, args=1)
        self.bind(diptable, 0x24, lambda: self.ret(target.relation, args=1))
        self.bind(vtable, 0x16C, lambda: self.ret(target.visibility, args=1))
        self.bind(vtable, 0x300, lambda: self.ret(target.moving))
        self.hooks[0x5526A0] = lambda: self.ret(
            context.leader_zone if self.cpu.reg_read(UC_X86_REG_ECX) == leader else target.zone)
        tiles = set(reachable_tiles)
        self.hooks[0x552610] = lambda: self.ret(
            context.leader_zone if (self.arg(0), self.arg(1)) in tiles else (context.leader_zone + 1) & 255, args=2)
        self.hooks[0x40C840] = lambda: self.ret(unit_ai if context.monk_unit_ai else 0)
        self.bind(ai_table, 0xC0, lambda: self.ret(target.convertible, args=2))
        # Original stack-frame local/argument slots at the start of the loop.
        sp = STACK - 0x200
        self.cpu.mem_write(sp, bytes(0x200))
        for offset, value in ((0x18, context.group_zone), (0x20, info),
                              (0x24, context.land_group), (0x44, leader),
                              (0x48, context.all_monks), (0x58, context.difficulty),
                              (0x64, monk if context.reference_monk else 0),
                              (0xDC, context.player), (0xEC, context.force_different_zone)):
            self.write(sp + offset, value)
        self.cpu.reg_write(UC_X86_REG_ESP, sp)
        self.cpu.reg_write(UC_X86_REG_EAX, 0)  # memory entry byte offset
        self.cpu.reg_write(UC_X86_REG_EBX, info)
        self.cpu.reg_write(UC_X86_REG_EBP, 0)
        for boundary in (0x593796, 0x59382E):
            self.hooks[boundary] = self.cpu.emu_stop
        self.cpu.emu_start(0x5934A9, RETURN, count=100000)
        end = self.cpu.reg_read(UC_X86_REG_EIP)
        assert end in (0x593796, 0x59382E), hex(end)
        return end == 0x593796

    def group(self, members):
        self.reset()
        info, main, ids, output, vtable = (TACTICAL + n for n in (0x40000, 0x41000, 0x42000, 0x43000, 0x44000))
        assert len(members) <= 128 and len({m.uid for m in members}) == len(members)
        for ptr in (info, main, ids, output, vtable):
            self.cpu.mem_write(ptr, bytes(0x1000))
        self.write(info + 0x100, main)
        for offset, value in ((0, 1), (4, -1), (20, 0), (24, -1), (28, 0), (32, 0)):
            self.write(output + offset, value)
        records = {}
        for index, member in enumerate(members):
            obj = TACTICAL + 0x60000 + index * 0x400
            master = obj + 0x200
            self.cpu.mem_write(obj, bytes(0x400))
            self.write(ids + index * 4, member.uid)
            self.write(obj, vtable)
            self.write(obj + 0x10, member.uid)
            self.write(obj + 0x14, master)
            self.cpu.mem_write(master + 0x1E, struct.pack('<h', member.source_class))
            self.write(master + 0xAC, member.object_flags)
            records[member.uid] = obj if member.exists else 0
        self.hooks[0x413850] = lambda: self.ret(records[self.arg(0)], args=1)
        def current_member():
            uid = self.read(self.cpu.reg_read(UC_X86_REG_ECX) + 0x10)
            return next(m for m in members if m.uid == uid)
        self.hooks[0x5526A0] = lambda: self.ret(current_member().zone)
        def position():
            dest = self.arg(0)
            self.cpu.mem_write(dest, struct.pack('<fff', *current_member().position))
            self.ret(dest, args=1)
        self.bind(vtable, 0x2AC, position)
        ok = self.call(0x5941A0, (ids, len(members), output, output + 4, output + 8,
                                output + 20, output + 24, output + 28, output + 32), this=info)
        return (bool(ok), self.read(output), self.read(output + 4),
                struct.unpack('<fff', self.cpu.mem_read(output + 8, 12)),
                self.read(output + 20), self.read(output + 24))
