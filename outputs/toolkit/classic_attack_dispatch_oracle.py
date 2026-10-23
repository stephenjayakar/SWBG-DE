"""Execute attackNow with original pool selection, grouping and group creation.

World lookup, position/zone queries, difficulty, allocation and queued stop
delivery use explicit fixtures. Source routines and list mutations run intact.
Includes the source inline naval collection between ground and air dispatch.
"""
import struct
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_ECX
from classic_engine_oracle import TACTICAL, RETURN
from classic_group_state_oracle import GroupStateOracle


class DispatchOracle(GroupStateOracle):
    def dispatch(self, ground, air, classes, positions, ground_percent, air_percent,
                 difficulty=1, radius=20, now=0, fail_after=None, boats=(), boat_percent=0):
        assert max(len(ground), len(air), len(boats), len(classes)) <= 1024
        self.write(TACTICAL + 0x584, ground_percent)
        self.write(TACTICAL + 0x574, air_percent)
        self.write(TACTICAL + 0x588, boat_percent)
        self.write(TACTICAL + 0x590, radius)
        for offset, buffer, members in ((0x118, TACTICAL + 0x5000, ground),
                                        (0x138, TACTICAL + 0x6000, air),
                                        (0x198, TACTICAL + 0xe000, boats),
                                        (0x1420, TACTICAL + 0x7000, [])):
            self.write(TACTICAL + offset, buffer)
            self.write(TACTICAL + offset + 4, len(members))
            self.write(TACTICAL + offset + 12, 1024)
            for i, uid in enumerate(members):
                self.write(buffer + 4*i, uid)
        player, ai, vtable = TACTICAL + 0xa000, TACTICAL + 0xb000, TACTICAL + 0xc000
        self.write(TACTICAL + 0xf4, ai)
        self.write(ai + 0xf0, player)
        self.write(player + 0xa0, 1)
        self.write(player + 0x8c, TACTICAL + 0x9000)
        self.write(TACTICAL + 0x9010, now)
        self.write(TACTICAL + 0x9068, TACTICAL + 0xd000)
        self.write(vtable + 0x2ac, RETURN - 32)
        objects, reverse, zones = {}, {}, {}
        for i, (uid, cls) in enumerate(classes.items()):
            obj = TACTICAL + 0x100000 + i * 0x300
            master = obj + 0x100
            x, y, zone = positions[uid]
            self.cpu.mem_write(obj, bytes(0x300))
            self.write(obj, vtable)
            self.write(obj + 0x10, uid)
            self.write(obj + 0x14, master)
            self.write(obj + 0x18, player)
            self.cpu.mem_write(obj + 0x48, struct.pack('<ff', x, y))
            self.cpu.mem_write(master + 0x1e, struct.pack('<h', cls))
            objects[uid] = obj
            reverse[obj] = positions[uid]
            key = (int(x), int(y))
            assert key not in zones or zones[key] == zone
            zones[key] = zone
        def arg(n):
            return self.read(self.cpu.reg_read(UC_X86_REG_ESP) + 4*n)
        def position():
            x, y, _ = reverse[self.cpu.reg_read(UC_X86_REG_ECX)]
            self.cpu.mem_write(arg(1), struct.pack('<fff', x, 0, y))
            self.ret(arg(1), 1)
        stops = []
        def stop():
            assert arg(1) == 1 and arg(3) == 1
            stops.append(self.read(arg(2)))
            self.ret(args=3)
        before = self.serial
        def allocate():
            self.fail = fail_after is not None and self.serial - before >= fail_after
            self.allocate()
        self.hooks.update({0x623DB0: lambda: self.ret(objects.get(arg(1), 0), 1),
                           0x42C410: lambda: self.ret(difficulty),
                           0x623D40: lambda: self.ret(difficulty),
                           RETURN - 32: position,
                           0x5526A0: lambda: self.ret(reverse[self.cpu.reg_read(UC_X86_REG_ECX)][2]),
                           0x552610: lambda: self.ret(zones[arg(1), arg(2)], 2),
                           0x44D450: stop, 0x632B9D: allocate})
        self.call(0x5AE520)
        self.fail = False
        return stops
