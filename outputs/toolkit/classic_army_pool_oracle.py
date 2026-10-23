"""Run the actual source group membership/count/admission routines.

World object lookup and difficulty are explicit inputs. Original group linked
lists, membership searches, count getters and output deduplication execute as
x86. All storage is preallocated; allocator paths are outside these fixtures.
"""
import struct
from unicorn.x86_const import UC_X86_REG_ESP
from classic_engine_oracle import Oracle, TACTICAL


class PoolOracle(Oracle):
    def prepare(self, groups):
        self.reset()
        assert len(groups) <= 128
        sentinel = TACTICAL + 0x1180
        pointers = [TACTICAL + 0x30000 + i * 0x200 for i in range(len(groups))]
        self.write(TACTICAL + 0x11b8, pointers[0] if pointers else sentinel)
        for i, group in enumerate(groups):
            assert len(group.members) <= 40
            pointer = pointers[i]
            self.cpu.mem_write(pointer, bytes(0x200))
            self.write(pointer + 0x38, pointers[i+1] if i+1 < len(pointers) else sentinel)
            self.write(pointer + 0x48, group.kind)
            self.write(pointer + 0xf0, len(group.members))
            for j, uid in enumerate(group.members):
                self.write(pointer + 0x50 + j * 4, uid)
        return pointers

    def membership(self, uid, groups):
        pointers = self.prepare(groups)
        pointer = self.call(0x5AD410, (uid,))
        return pointers.index(pointer) if pointer else -1

    def totals(self, groups):
        self.prepare(groups)
        return {name: self.call(address) for name, address in
                (('ground', 0x5AE490), ('air', 0x5AE4C0), ('boat', 0x5AE4F0))}

    def available(self, pool, classes, groups, aircraft=False, difficulty=1):
        assert len(pool) <= 1024 and len(classes) <= 1024
        self.prepare(groups)
        offset = 0x138 if aircraft else 0x118
        for off, buffer, members in ((offset, TACTICAL + 0x10000, pool),
                                     (0x1420, TACTICAL + 0x20000, [])):
            self.write(TACTICAL + off, buffer)
            self.write(TACTICAL + off + 4, len(members))
            self.write(TACTICAL + off + 12, 1024)
            for i, uid in enumerate(members):
                self.write(buffer + 4*i, uid)
        objects = {}
        for i, (uid, cls) in enumerate(classes.items()):
            obj = TACTICAL + 0x50000 + i * 0x400
            master = obj + 0x200
            self.cpu.mem_write(obj, bytes(0x400))
            self.write(obj + 0x14, master)
            self.cpu.mem_write(master + 0x1e, struct.pack('<h', cls))
            objects[uid] = obj
        # The actual lookup routine is the only world dependency here.
        self.write(0x6A3684, TACTICAL + 0x8000)
        self.write(TACTICAL + 0x8420, TACTICAL + 0x9000)
        self.hooks[0x623DB0] = lambda: self.ret(
            objects.get(self.read(self.cpu.reg_read(UC_X86_REG_ESP) + 4), 0), 1)
        self.hooks[0x42C410] = lambda: self.ret(difficulty)
        result = self.call(0x5ABF80 if aircraft else 0x5AB350)
        count = self.read(TACTICAL + 0x1424)
        assert 0 <= count <= 1024
        return result, [self.read(TACTICAL + 0x20000 + i*4) for i in range(count)]
