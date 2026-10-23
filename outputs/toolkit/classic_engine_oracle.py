"""Run isolated, hash-pinned SWGB tactical routines in an x86 emulator.

This never starts or modifies a game. Only local executable bytes are loaded;
OS calls are not available. Allocation/grouping boundaries are explicit stubs.
It is a differential-test oracle, not a simulation of a whole match.
Requires unicorn==2.1.4. No executable bytes are written into release archives.
"""
from pathlib import Path
import hashlib
import struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_FPCW

SOURCE = Path('E:/GOG Games/Star Wars - Galactic Battlegrounds/Game/battlegrounds_x2.exe')
SOURCE_SHA = 'd64e7f0ecc546c3bd833c5c6a7bc97b75ee74940d89b1cb22349b0ace0f3fc58'
TACTICAL = 0x1000000
STACK = 0x11FF000
RETURN = 0x11FFFF0
ARRAYS = range(0xF8, 0x1F8, 16)


class Oracle:
    def __init__(self):
        data = SOURCE.read_bytes()
        assert hashlib.sha256(data).hexdigest() == SOURCE_SHA, 'Unreviewed source executable'
        pe = struct.unpack_from('<I', data, 60)[0]
        machine, count, _, _, _, optsize, _ = struct.unpack_from('<HHIIIHH', data, pe + 4)
        assert data[pe:pe + 4] == b'PE\0\0' and machine == 0x14C
        base = struct.unpack_from('<I', data, pe + 24 + 28)[0]
        size = struct.unpack_from('<I', data, pe + 24 + 56)[0]
        self.cpu = Uc(UC_ARCH_X86, UC_MODE_32)
        self.cpu.mem_map(base, (size + 4095) & ~4095)
        for i in range(count):
            off = pe + 24 + optsize + 40 * i
            _, rva, rawsize, raw = struct.unpack_from('<IIII', data, off + 8)
            if rawsize:
                self.cpu.mem_write(base + rva, data[raw:raw + rawsize])
        self.cpu.mem_map(TACTICAL, 0x200000)
        self.hooks = {}
        self.cpu.hook_add(UC_HOOK_CODE, self._dispatch)
        self.reset()

    def _dispatch(self, cpu, address, size, _):
        if address in self.hooks:
            self.hooks[address]()

    def read(self, address):
        return struct.unpack('<i', self.cpu.mem_read(address, 4))[0]

    def write(self, address, value):
        self.cpu.mem_write(address, struct.pack('<I', value & 0xFFFFFFFF))

    def reset(self):
        self.cpu.mem_write(TACTICAL, bytes(0x3000))
        self.hooks.clear()
        for i, off in enumerate(ARRAYS):
            self.write(TACTICAL + off, TACTICAL + 0x4000 + i * 0x100)
            self.write(TACTICAL + off + 12, 64)
        # Skip the building-position side effect; it does not classify soldiers.
        self.write(TACTICAL + 0x5B4, 1)
        self.cpu.reg_write(UC_X86_REG_FPCW, 0x37F)

    def ret(self, value=0, args=0):
        sp = self.cpu.reg_read(UC_X86_REG_ESP)
        self.cpu.reg_write(UC_X86_REG_EAX, value)
        self.cpu.reg_write(UC_X86_REG_ESP, sp + 4 + args * 4)
        self.cpu.reg_write(UC_X86_REG_EIP, self.read(sp))

    def call(self, address, args=(), this=TACTICAL):
        self.write(STACK, RETURN)
        for i, arg in enumerate(args):
            self.write(STACK + 4 + i * 4, arg)
        self.cpu.reg_write(UC_X86_REG_ESP, STACK)
        self.cpu.reg_write(UC_X86_REG_ECX, this)
        self.cpu.emu_start(address, RETURN, count=10000000)
        assert self.cpu.reg_read(UC_X86_REG_EIP) == RETURN, 'Routine exceeded instruction budget'
        return self.cpu.reg_read(UC_X86_REG_EAX)

    def classification(self, source_class, object_flags=0):
        self.reset()
        obj, master = TACTICAL + 0x6000, TACTICAL + 0x7000
        self.cpu.mem_write(obj, bytes(0x200))
        self.cpu.mem_write(master, bytes(0x200))
        self.write(obj + 0x10, 123)
        self.write(obj + 0x14, master)
        self.cpu.mem_write(master + 0x1E, struct.pack('<h', source_class))
        self.cpu.mem_write(master + 0xAC, bytes([object_flags]))
        # Array contains / append routines run natively. Capacity prevents allocation.
        self.call(0x59FA80, (obj,))
        return [off for off in ARRAYS if self.read(TACTICAL + off + 4)]

    def defaults(self):
        """Unmodified VictoryConditionRuleSystem constructor's SN defaults."""
        self.reset()
        self.call(0x596D10)
        return [self.read(TACTICAL + 4 + i * 4) for i in range(242)]

    def scaled_setting(self, number, value, difficulty, multiplayer=False, no_scaling=False):
        """Run the original setter, including its difficulty scaling/clamps.

        Context queries return only difficulty and multiplayer mode. Other
        subsystems (exploration/economy) are intentionally not supported here.
        """
        assert number in (16, 17, 19, 20, 26, 27, 36, 40, 58, 59, 60, 104, 223, 227, 228, 230)
        self.reset()
        main, player, world, game, vtable = (TACTICAL + n for n in (0x8000, 0x9000, 0xA000, 0xB000, 0xC000))
        self.write(TACTICAL + 0xF4, main)
        self.write(main + 0xF0, player)
        self.write(player + 0x8C, world)
        self.write(0x6A3684, game)
        self.write(game, vtable)
        # Inert synthetic entry point used only as a hook for isMultiplayer.
        self.write(vtable + 0x58, RETURN - 16)
        self.hooks[RETURN - 16] = lambda: self.ret(int(multiplayer))
        self.hooks[0x623D40] = lambda: self.ret(difficulty)
        self.write(TACTICAL + 0x58C, int(no_scaling))
        self.call(0x5A5730, (number, value))
        return self.read(TACTICAL + 0x1F8 + number * 4)

    def attack_counts(self, ground, air, ground_percent, air_percent):
        """Actual attackNow rounding; stub only collection and spatial grouping.

        Boats are disabled here. The grouping stub records the requested count
        and returns no spatial groups. Consequently this tests requested sizes,
        not which members the original spatial clustering will choose.
        """
        self.reset()
        self.write(TACTICAL + 0x584, ground_percent)
        self.write(TACTICAL + 0x574, air_percent)
        self.write(TACTICAL + 0x588, 0)
        self.hooks[0x5AB350] = lambda: self.ret(ground)
        self.hooks[0x5ABF80] = lambda: self.ret(air)
        result = []
        def group():
            sp = self.cpu.reg_read(UC_X86_REG_ESP)
            result.append(self.read(sp + 8))
            self.write(0x6A5438, 0)
            self.ret(args=5)
        self.hooks[0x4506F0] = group
        self.call(0x5AE520)
        expected_categories = ['ground'] * (ground_percent > 0) + ['air'] * (air_percent > 0)
        assert len(result) == len(expected_categories)
        return dict(zip(expected_categories, result))

    def spatial_groups(self, positions, requested, distance=20):
        """Execute source spatial grouping against supplied (id, x, y, zone).

        World lookup, positions and zone queries are the only stubs. Original
        nearest-cluster selection, tie handling, 40-candidate limit and early
        termination all execute from the source binary. Fixtures use one shared
        zone map, as for aircraft with the same source terrain restriction.
        """
        self.reset()
        assert len(positions) <= 1000 and len({p[0] for p in positions}) == len(positions)
        array, storage = TACTICAL + 0x10000, TACTICAL + 0x11000
        game, world, player, vtable = (TACTICAL + n for n in (0xB000, 0xC000, 0xD000, 0xE000))
        self.write(0x6A3684, game)
        self.write(game + 0x420, world)
        self.write(player + 0xA0, 1)
        self.write(vtable + 0x2AC, RETURN - 32)
        self.write(array, storage)
        self.write(array + 4, len(positions))
        self.write(array + 12, len(positions))
        objects, reverse, zones = {}, {}, {}
        for i, (uid, x, y, zone) in enumerate(positions):
            obj = TACTICAL + 0x20000 + i * 0x100
            objects[uid] = obj
            reverse[obj] = (uid, x, y, zone)
            key = (int(x), int(y))
            assert key not in zones or zones[key] == zone, 'Inconsistent zone-map fixture'
            zones[key] = zone
            self.write(storage + i * 4, uid)
            self.write(obj, vtable)
            self.write(obj + 0x10, uid)
            self.write(obj + 0x18, player)
            self.cpu.mem_write(obj + 0x48, struct.pack('<ff', x, y))
        def lookup():
            self.ret(objects.get(self.read(self.cpu.reg_read(UC_X86_REG_ESP) + 4), 0), args=1)
        def position():
            out = self.read(self.cpu.reg_read(UC_X86_REG_ESP) + 4)
            _, x, y, _ = reverse[self.cpu.reg_read(UC_X86_REG_ECX)]
            self.cpu.mem_write(out, struct.pack('<fff', x, 0, y))
            self.ret(out, args=1)
        def zone_here():
            self.ret(reverse[self.cpu.reg_read(UC_X86_REG_ECX)][3])
        def zone_there():
            sp = self.cpu.reg_read(UC_X86_REG_ESP)
            self.ret(zones[(self.read(sp + 4), self.read(sp + 8))], args=2)
        self.hooks.update({0x623DB0: lookup, RETURN - 32: position,
                           0x5526A0: zone_here, 0x552610: zone_there})
        distance_bits = struct.unpack('<I', struct.pack('<f', distance))[0]
        self.call(0x4506F0, (array, requested, distance_bits, 0, TACTICAL), this=0x6A5390)
        count = self.read(0x6A5438)
        return [[self.read(0x6A5390 + 0x14C + g * 160 + i * 4)
                 for i in range(self.read(0x6A5390 + 0xAC + g * 4))] for g in range(count)]


if __name__ == '__main__':
    oracle = Oracle()
    defaults = oracle.defaults()
    print('air defaults', {n: defaults[n] for n in (6, 17, 27, 40, 223, 229, 230)})
    print('air percent scaling', [[oracle.scaled_setting(223, p, d) for p in (1, 50, 75, 100)] for d in range(5)])
    for cls in range(70):
        pools = oracle.classification(cls)
        if pools:
            print('class', cls, 'arrays', [hex(x) for x in pools])
    for percent in (0, 1, 25, 50, 75, 100):
        print('percent', percent, [oracle.attack_counts(0, n, 0, percent).get('air', 0) for n in range(11)])
