"""Run actual source set/add/multiply armor/weapon methods; no game launch."""
import struct
from classic_engine_oracle import Oracle, TACTICAL


class CombatAttributeOracle(Oracle):
    def modify(self, entries, mode, encoded, attribute=9):
        assert mode in (0, 4, 5) and attribute in (8, 9) and len(entries) <= 1024
        self.reset()
        master, table, other = (TACTICAL + n for n in (0x71000, 0x72000, 0x73000))
        self.cpu.mem_write(master, bytes(0x400))
        data = b''.join(struct.pack('<hh', *entry) for entry in entries)
        # Populate both tables so cross-table writes cannot pass unnoticed.
        self.cpu.mem_write(table, data + b'\xA5' * 16)
        self.cpu.mem_write(other, b'\xA5' * 16)
        offset = 0x132 if attribute == 8 else 0x138
        other_offset = 0x138 if attribute == 8 else 0x132
        self.cpu.mem_write(master + offset, struct.pack('<h', len(entries)))
        self.write(master + (0x134 if attribute == 8 else 0x13C), table if entries else 0)
        self.cpu.mem_write(master + other_offset, struct.pack('<h', 1))
        self.write(master + (0x13C if attribute == 8 else 0x134), other)
        before = bytes(self.cpu.mem_read(master, 0x400))
        encoded_bits = struct.unpack('<i', struct.pack('<f', encoded))[0]
        self.call({0: 0x4899B0, 4: 0x489B10, 5: 0x489D20}[mode], (encoded_bits, attribute), this=master)
        assert bytes(self.cpu.mem_read(master, 0x400)) == before
        assert bytes(self.cpu.mem_read(other, 16)) == b'\xA5' * 16
        assert bytes(self.cpu.mem_read(table + len(data), 16)) == b'\xA5' * 16
        return [struct.unpack('<hh', self.cpu.mem_read(table + i * 4, 4)) for i in range(len(entries))]
