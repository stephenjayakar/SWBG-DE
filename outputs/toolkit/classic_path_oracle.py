"""Execute original objectToAttack2 after ranking; geometry is fixture-supplied.

Runs source minimum-range collection, resume/time budget, path-choice branches,
transport recheck, blocker queue and target-memory attack-attempt changes.
No game, Windows APIs, allocations or actual path searches are executed.
"""
import struct
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDX,
                              UC_X86_REG_ESI, UC_X86_REG_ESP, UC_X86_REG_EIP)
from classic_engine_oracle import TACTICAL, STACK, RETURN
from classic_admission_oracle import AdmissionOracle


class PathOracle(AdmissionOracle):
    def choose(self, targets, ranges=(4.0,), can_transport=0, sn241=0,
               resume=None, start_time=0, ticks=(), time_budget=100):
        self.reset()
        info, main, player, world, game, group, vtable, memory, output, storage = (
            TACTICAL + n * 0x1000 for n in range(0x40, 0x4A))
        self.cpu.mem_write(info, bytes(0xA000))
        self.cpu.mem_write(0x781378, bytes(0xE040))
        assert len(targets) <= 128 and len(ranges) <= 40
        assert len({t.uid for t in targets}) == len(targets)
        assert all(t.uid >= 0 for t in targets)
        self.write(info + 0x100, main)
        self.write(info + 0x34C, memory)
        self.write(main + 0xF0, player)
        self.write(player + 0x8C, world)
        self.write(world + 0x118, time_budget)
        self.write(game + 0x420, world)
        self.write(0x6A3684, game)
        mask = self.read(0x665810)
        assert mask != 0
        self.write(group + 0x1A0, mask if resume is not None else 0)
        self.write(group + 0x254, 0 if resume is None else resume)
        self.write(group + 0xF0, len(ranges))
        self.write(output, -1)
        self.write(output + 4, -1)
        events, records, objects, memories = [], {}, {}, {}
        next_obj = TACTICAL + 0x60000
        next_memory = memory

        def create(uid, exists=True):
            nonlocal next_obj, next_memory
            if uid in objects:
                return objects[uid]
            ptr = next_obj
            next_obj += 0x400
            self.cpu.mem_write(ptr, bytes(0x400))
            self.write(ptr, vtable)
            self.write(ptr + 0x10, uid)
            self.write(ptr + 0x18, player)
            self.cpu.mem_write(ptr + 0x48, struct.pack('<fff', 20, 30, 0))
            objects[uid] = ptr
            records[uid] = ptr if exists else 0
            memories[uid] = next_memory
            self.cpu.mem_write(next_memory, bytes(0x2C))
            self.write(next_memory, uid)
            next_memory += 0x2C
            return ptr

        for index, target in enumerate(targets):
            create(target.uid, target.exists)
            entry = 0x781390 + index * 0x34
            self.write(entry, target.uid)
            self.write(entry + 4, index)
            self.write(entry + 0x1C, target.same_zone)
            self.write(0x78E394 + index * 4, index)
        for target in targets:
            for uid in target.blockers:
                create(uid, uid not in target.missing_blockers)
        assert next_memory < output, 'Fixture object-memory capacity exceeded'
        own_ids = []
        for index, radius in enumerate(ranges):
            uid = 1000000 + index
            assert uid not in objects
            ptr = create(uid, radius is not None)
            self.cpu.mem_write(ptr + 0x30, struct.pack('<f', 0 if radius is None else radius))
            self.write(group + 0x50 + index * 4, uid)
            own_ids.append(uid)
        leader = create(2000000)  # caller already verified its leader
        self.write(0x78E390, len(targets))
        self.write(0x78F394, 0)
        self.write(0x78F398, 0)
        self.hooks[0x623DB0] = lambda: self.ret(records.get(self.arg(0), 0), args=1)
        self.hooks[0x413850] = lambda: self.ret(records.get(self.arg(0), 0), args=1)
        self.hooks[0x587CE0] = lambda: self.ret(memories.get(self.arg(0), 0), args=1)
        # Source memory refresh is a world service outside this slice. Priority
        # insertion/access (59BC70/59BC50) run unmodified, including the cap.
        self.hooks[0x5886F0] = lambda: self.ret(args=1)
        self.hooks[0x5A5710] = lambda: self.ret(sn241, args=1)
        def position():
            dest = self.arg(0)
            obj = self.cpu.reg_read(UC_X86_REG_ECX)
            self.cpu.mem_write(dest, bytes(self.cpu.mem_read(obj + 0x48, 12)))
            self.ret(dest, args=1)
        self.bind(vtable, 0x2AC, position)
        # Return the fixture weapon range in x87 ST(0), exactly like a virtual
        # float-returning engine call. Source then chooses the minimum itself.
        range_code = TACTICAL + 0xEF000
        self.cpu.mem_write(range_code, b'\xD9\x41\x30\xC3')  # fld [ecx+30h]; ret
        self.write(vtable + 0x194, range_code)
        by_id = {t.uid: t for t in targets}
        calls = {}
        def attack_path():
            uid = self.read(self.cpu.reg_read(UC_X86_REG_EDX) + 0x10)
            count = calls.get(uid, 0)
            calls[uid] = count + 1
            events.append(('direct' if count == 0 else 'plain-retry', uid))
            self.ret(by_id[uid].direct if count == 0 else by_id[uid].plain_retry, args=13)
        self.hooks[0x4BD560] = attack_path
        self.hooks[0x4BC380] = lambda: self.ret(args=1)  # empty scratch path fixture
        self.hooks[0x4BC400] = lambda: self.ret()
        self.hooks[0x632B42] = lambda: self.ret()  # cdecl free; source removes argument
        def transport_path():
            uid = self.arg(4)
            events.append(('transport', uid))
            assert tuple(self.arg(i) for i in range(7, 11)) == (22, 23, 16, 15)
            self.ret(by_id[uid].transport, args=14)
        self.bind(vtable, 0x23C, transport_path)
        def exception():
            # ESI still holds the candidate throughout this branch.
            uid = self.read(self.cpu.reg_read(UC_X86_REG_ESI) + 0x10)
            terrain = self.arg(0)
            events.append(('exception', uid, terrain))
            self.ret(int(terrain in by_id[uid].exception_terrains), args=4)
        self.bind(vtable, 0x240, exception)
        def obstruction_path():
            uid, dest = self.arg(0), self.arg(5)
            events.append(('obstruction', uid))
            blockers = by_id[uid].blockers
            assert len(blockers) <= 128
            self.write(dest, storage)
            self.write(dest + 4, len(blockers))
            self.write(dest + 8, len(blockers))
            self.write(dest + 12, 128)
            for index, value in enumerate(blockers):
                self.write(storage + index * 4, value)
            self.ret(by_id[uid].obstruction, args=6)
        self.bind(vtable, 0x238, obstruction_path)
        clock = iter(ticks)
        clock_address = TACTICAL + 0xEE000
        self.write(0x6543EC, clock_address)
        self.hooks[clock_address] = lambda: self.ret(next(clock, start_time) & 0xFFFFFFFF)
        sp = STACK - 0x200
        self.cpu.mem_write(sp, bytes(0x200))
        for offset, value in ((0x20, info), (0x44, leader), (0xE0, group), (0xE4, start_time),
                              (0xE8, output), (0xF0, can_transport), (0xF4, output + 4)):
            self.write(sp + offset, value)
        self.cpu.reg_write(UC_X86_REG_ESP, sp)
        self.cpu.reg_write(UC_X86_REG_ESI, group)
        self.hooks[0x5940C1] = self.cpu.emu_stop
        self.cpu.emu_start(0x593938, RETURN, count=1000000)
        assert self.cpu.reg_read(UC_X86_REG_EIP) == 0x5940C1
        result = self.cpu.reg_read(UC_X86_REG_EAX)
        return dict(target=self.read(result) if result else None,
                    same_zone=self.read(output), need_transport=self.read(output + 4),
                    resume=self.read(group + 0x254) if self.read(group + 0x1A0) & mask else None,
                    attempts=[t.uid for t in targets if self.read(memories[t.uid] + 0x10)],
                    blockers=[self.read(group + 0x13C + i * 4) for i in range(self.read(group + 0x138))],
                    events=events, radius=struct.unpack('<f', self.cpu.mem_read(sp + 0x28, 4))[0])
