"""Execute both original uint8 Force-rank predicates without stubbing them."""
import struct
from classic_engine_oracle import Oracle,TACTICAL


class ForceRankOracle(Oracle):
    def ranks(self,raw,copy):
        self.reset()
        obj,master=TACTICAL+0xA0000,TACTICAL+0xA1000
        self.cpu.mem_write(obj,bytes(0x100));self.cpu.mem_write(master,bytes(0x100))
        self.write(obj+0x14,master)
        self.cpu.mem_write(master+0x18,struct.pack('<HH',raw&65535,copy&65535))
        values=[self.call(address,this=obj)&255 for address in (0x54B170,0x54B1D0)]
        assert all(v in (0,1) for v in values)
        return tuple(map(bool,values))

    def copy_identity(self,before,source):
        """Probe retained ID/base/class versus copied ID in the real master copy.

        All names and dynamic lists are empty; the empty-name helper is a fixture.
        This does not model player/unit notifications or engine-side transforms.
        """
        self.reset()
        old,new=TACTICAL+0xA0000,TACTICAL+0xA1000
        for ptr,values in ((old,before),(new,source)):
            self.cpu.mem_write(ptr,bytes(0x300))
            self.cpu.mem_write(ptr+4,b'\x46')
            self.cpu.mem_write(ptr+0x18,struct.pack('<hhhh',*values))
        self.hooks[0x4AE9A0]=lambda:self.ret()
        self.call(0x48D390,(new,),this=old)
        return (struct.unpack('<hhhh',self.cpu.mem_read(old+0x18,8)),
                struct.unpack('<hhhh',self.cpu.mem_read(new+0x18,8)))
