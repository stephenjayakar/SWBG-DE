"""Execute source create/delete/add/remove routines and their real constructor.

Only malloc/free are intercepted; a small arena supplies memory and controlled
allocation failures. Path destruction executes on constructor-empty paths.
"""
from unicorn.x86_const import UC_X86_REG_ESP
from classic_engine_oracle import Oracle, TACTICAL

FIELDS = dict(id=0x40, kind=0x48, desired=0xf4, action=0xf8, target=0xfc,
              target_type=0x100, in_use=0x44, flags=0x1a0, retreat=0x258, last_added=0x190)


class GroupStateOracle(Oracle):
    def __init__(self, next_id=1):
        super().__init__()
        self.cpu.mem_map(0, 4096)  # inert SEH link used by source createGroup
        self.begin(next_id)

    def begin(self, next_id=1):
        self.reset()
        self.serial = 0
        self.fail = False
        self.pointers = {}
        self.freed = set()
        sentinel = TACTICAL + 0x1180
        self.write(sentinel + 0x38, sentinel)
        self.write(sentinel + 0x3c, sentinel)
        self.write(TACTICAL + 0x13dc, next_id)
        self.write(0x6A3684, TACTICAL + 0x8000)
        self.write(TACTICAL + 0x8420, TACTICAL + 0x9000)
        self.hooks[0x632B9D] = self.allocate
        self.hooks[0x632B42] = self.free

    def allocate(self):
        size = self.read(self.cpu.reg_read(UC_X86_REG_ESP) + 4)
        assert size == 0x25c, ('Unexpected source allocation', size)
        if self.fail:
            self.ret(0)
            return
        self.serial += 1
        assert self.serial < 1024
        pointer = TACTICAL + 0x10000 + self.serial * 0x300
        self.cpu.mem_write(pointer, bytes(0x300))
        self.pointers[self.serial] = pointer
        self.ret(pointer)

    def free(self):
        pointer = self.read(self.cpu.reg_read(UC_X86_REG_ESP) + 4)
        assert pointer in self.pointers.values() and pointer not in self.freed
        self.freed.add(pointer)
        self.ret()

    def handle(self, pointer):
        return next((key for key, value in self.pointers.items() if value == pointer), 0)

    def create(self, initialize=1, fail=False):
        self.fail = fail
        pointer = self.call(0x5ACE30, (initialize,))
        self.fail = False
        return self.handle(pointer)

    def add(self, handle, uid, now):
        self.write(TACTICAL + 0x9010, now)
        return self.call(0x59ACB0, (uid,), self.pointers[handle])

    def remove(self, handle, uid):
        return self.call(0x59AD00, (uid,), self.pointers[handle])

    def delete(self, gid):
        return self.call(0x5ACEE0, (gid,))

    def delete_kind(self, kind):
        return self.call(0x5ACF40, (kind,))

    def containing(self, uid):
        return self.handle(self.call(0x5AD410, (uid,)))

    def set_kind(self, handle, kind):
        self.write(self.pointers[handle] + 0x48, kind)

    def snapshot(self):
        sentinel = TACTICAL + 0x1180
        pointer = self.read(sentinel + 0x38)
        previous = sentinel
        seen = set()
        groups = []
        while pointer != sentinel:
            assert pointer and pointer not in seen and pointer not in self.freed
            assert self.read(pointer + 0x3c) == previous
            seen.add(pointer)
            row = {name: self.read(pointer + off) for name, off in FIELDS.items()}
            row['members'] = [self.read(pointer + 0x50 + 4*i) for i in range(self.read(pointer + 0xf0))]
            groups.append(row)
            previous, pointer = pointer, self.read(pointer + 0x38)
        assert self.read(sentinel + 0x3c) == previous
        assert seen | self.freed == set(self.pointers.values()), 'Source lost an allocated group'
        return dict(next_id=self.read(TACTICAL + 0x13dc), count=self.read(TACTICAL + 0x13e0), groups=groups)
