"""Execute original record-maintenance wrappers on actual visible lists.

Base movement/transformation are supplied state mutations, not pathfinding or
full master transformation. Ownership executes ONLY its record-update prefix.
"""
import struct
from classic_engine_oracle import TACTICAL, RETURN, UC_X86_REG_EIP, UC_X86_REG_ESP
from classic_visible_membership_oracle import VisibleMembershipOracle

def f32(value):return struct.unpack('<f',struct.pack('<f',value))[0]
def bits(value):return struct.unpack('<I',struct.pack('<f',value))[0]

class VisibleRecordsOracle(VisibleMembershipOracle):
    def obj(self,uid):return TACTICAL+0x100000+uid*0x200 if uid>=0 else TACTICAL+0x130000

    def configure(self,uid,owner,x,y,radius,category,mask):
        obj=self.obj(uid);slot=max(0,uid)
        master=TACTICAL+0xC0000+slot*0x100;player=TACTICAL+0xD0000+slot*0x100
        self.write(obj+0x10,uid);self.write(obj+0x14,master);self.write(obj+0x18,player)
        self.cpu.mem_write(master+0x1E,struct.pack('<h',category))
        self.write(player+0xA0,owner)
        self.cpu.mem_write(obj+0x48,struct.pack('<ff',x,y))
        self.cpu.mem_write(obj+0x16D,bytes([radius&255]));self.write(obj+0x168,mask)

    def move(self,uid,old_x,old_y,new_x,new_y):
        obj=self.obj(uid);self.write(obj+0x10,uid)
        self.cpu.mem_write(obj+0x48,struct.pack('<ff',old_x,old_y))
        # A deliberately different requested position proves that the wrapper
        # uses the post-base object fields. Real collision/path resolution is not run.
        requested=(bits(123.25),bits(45.75),bits(0.0))
        calls=[]
        def base_move():
            sp=self.cpu.reg_read(UC_X86_REG_ESP)
            calls.append(tuple(self.read(sp+4+i*4)&0xFFFFFFFF for i in range(3)))
            self.cpu.mem_write(obj+0x48,struct.pack('<ff',new_x,new_y));self.ret(args=3)
        self.hooks[0x4A1440]=base_move
        try:self.call(0x4461E0,requested,this=obj)
        finally:del self.hooks[0x4A1440]
        assert calls==[requested]

    def owner_prefix(self,uid,owner):
        obj=self.obj(uid);self.write(obj+0x10,uid)
        player=TACTICAL+0xE1000;self.write(player+0xA0,owner)
        self.hooks[0x55B853]=lambda:self.cpu.reg_write(UC_X86_REG_EIP,RETURN)
        try:self.call(0x55B820,(player,),this=obj)
        finally:del self.hooks[0x55B853]

    def transform(self,uid,old_state,new_state):
        self.configure(uid,*old_state);obj=self.obj(uid);calls=[]
        def base_transform():
            # Verify source removal happened before the transformation boundary.
            calls.append(self.snapshot())
            assert not any(key[0]==uid for key in calls[-1][2])
            self.configure(uid,*new_state);self.ret(args=1)
        self.hooks[0x408F80]=base_transform
        try:self.call(0x443E20,(TACTICAL+0xE2000,),this=obj)
        finally:del self.hooks[0x408F80]
        assert len(calls)==1
        return calls[0]
