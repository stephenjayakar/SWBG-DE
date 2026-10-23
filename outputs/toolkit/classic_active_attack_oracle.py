"""Execute original taskActiveGroupAttack; selection/task delivery are boundaries.

The complete wrapper executes, including flag tests, time calculation and state
mutations. Target selection and taskGroup are recorded callbacks, not native
pathfinding/orders. Constructor and group list operations execute original code.
"""
import struct
from unicorn.x86_const import UC_X86_REG_ESP
from classic_group_state_oracle import GroupStateOracle
from classic_engine_oracle import TACTICAL

class ActiveAttackOracle(GroupStateOracle):
    def snapshot_group(self, p):
        return [self.read(p+x) for x in (0xf8,0xfc,0x100,0x44,0x1a0,0x250)]+[
            self.read(p+x) for x in (0x104,0x108,0x10c,0x244,0x248,0x24c)]

    def run(self, case):
        self.begin();h=self.create();p=self.pointers[h]
        kind,flags,enabled,now,previous,has_target,transport,yielded,target,typ=case
        self.write(p+0x48,kind);self.write(p+0x1a0,flags)
        self.write(p+0x130,previous);self.write(TACTICAL+0x9010,now)
        self.write(TACTICAL+0x1480,enabled)
        self.write(TACTICAL+0x1620,-7);self.write(TACTICAL+0x1628,-8)
        self.write(TACTICAL+0xf4,TACTICAL+0x40000)
        self.write(TACTICAL+0x1400,TACTICAL+0x41000)
        self.write(TACTICAL+0x140c,1);self.write(TACTICAL+0x41000,321)
        for off,values in ((0x104,(9.,8.,7.)),(0x194,(2.,4.,6.)),(0x244,(1.,3.,5.))):
            self.cpu.mem_write(p+off,struct.pack('<3f',*values))
        record=TACTICAL+0x42000
        self.cpu.mem_write(record,struct.pack('<ihHBBB',target,typ,0,23,45,67))
        events=[];queries=[]
        def find():
            sp=self.cpu.reg_read(UC_X86_REG_ESP)
            args=[self.read(sp+4*i) for i in range(1,6)]
            queries.append([args[0],args[1],args[2],args[4]])
            self.ret(0,args=5)
        def select():
            sp=self.cpu.reg_read(UC_X86_REG_ESP)
            args=[self.read(sp+4*i) for i in range(1,8)]
            assert args[0]==321 and args[1]==p and args[2]==777
            self.write(args[6],transport)
            if yielded:self.write(p+0x1a0,self.read(p+0x1a0)|64)
            events.append(['select'])
            self.ret(record if has_target else 0,args=7)
        def task():
            sp=self.cpu.reg_read(UC_X86_REG_ESP)
            events.append(['task',self.read(sp+12),self.read(sp+16),self.snapshot_group(p)])
            self.ret(1,args=4)
        self.hooks[0x5ad020]=find
        self.hooks[0x5931e0]=select
        self.hooks[0x59b160]=task
        self.call(0x5a3c40,(p,777))
        return dict(state=self.snapshot_group(p),events=events,queries=queries,
                    deferred=[self.read(TACTICAL+0x1620),self.read(TACTICAL+0x1628)])
