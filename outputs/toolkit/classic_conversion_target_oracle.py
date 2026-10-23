"""Execute original priest selection; scanning, lookup and eligibility are fixtures."""
import struct
from classic_engine_oracle import Oracle,TACTICAL,UC_X86_REG_ESP

class ConversionTargetOracle(Oracle):
    def select(self,candidates,initial_distance=-123.,distance_pointer=True):
        assert len(candidates)<=1024
        self.reset();self.events=[];self.index=-1
        ai,own,owner,vt,owner_vt,buffer,out=(TACTICAL+n for n in (0x90000,0x91000,0x92000,0x93000,0x94000,0x30000,0x95000))
        for p in (ai,own,owner,vt,owner_vt,out):self.cpu.mem_write(p,bytes(0x400))
        self.write(ai,vt);self.write(ai+4,own);self.write(own+0x18,owner);self.write(owner,owner_vt)
        self.cpu.mem_write(own+0x48,struct.pack('<ff',13.25,41.5))
        self.cpu.mem_write(out,struct.pack('<f',initial_distance))
        self.write(0x7A1C9C,len(candidates));self.write(0x7A1CB0,buffer)
        for i,c in enumerate(candidates):
            self.cpu.mem_write(buffer+i*8,struct.pack('<iBBBB',c.uid,c.distance&255,c.memory_owner&255,0,0))
            obj=TACTICAL+0x100000+i*0x200;master=obj+0x100
            self.cpu.mem_write(obj,bytes(0x200));self.write(obj+0x10,c.uid);self.write(obj+0x14,master)
            self.cpu.mem_write(obj+0x58,bytes([c.state&255]))
            self.cpu.mem_write(master+0x1E,struct.pack('<H',c.source_class&65535))
            self.cpu.mem_write(master+0x32,struct.pack('<H',c.max_hp&65535))
        def args(n):return struct.unpack('<'+'I'*n,self.cpu.mem_read(self.cpu.reg_read(UC_X86_REG_ESP)+4,n*4))
        def scan():
            assert args(3)==(struct.unpack('<I',struct.pack('<f',13.25))[0],struct.unpack('<I',struct.pack('<f',41.5))[0],1)
            self.events.append(('scan',));self.ret(args=3)
        def enemy():
            self.index+=1;c=candidates[self.index];assert args(1)[0]==(c.memory_owner&255)
            self.events.append(('enemy',self.index));self.ret(int(c.enemy),args=1)
        def lookup():
            c=candidates[self.index];assert args(1)[0]==(c.uid&0xFFFFFFFF)
            self.events.append(('lookup',self.index));self.ret(TACTICAL+0x100000+self.index*0x200 if c.present else 0,args=1)
        def convert():
            c=candidates[self.index];assert args(2)==(c.uid&0xFFFFFFFF,0)
            self.events.append(('convert',self.index));self.ret(int(c.convertible),args=2)
        for table,offset,address,hook in ((vt,0x20,TACTICAL+0x96000,scan),(owner_vt,0x20,TACTICAL+0x96100,enemy),
                                         (vt,0xC0,TACTICAL+0x96200,convert)):
            self.write(table+offset,address);self.hooks[address]=hook
        self.hooks[0x422000]=lookup
        result=self.call(0x5B4E80,(out if distance_pointer else 0,),this=ai)
        if result>=0x80000000:result-=0x100000000
        distance=struct.unpack('<f',self.cpu.mem_read(out,4))[0]
        expected=[('scan',)]
        for i,c in enumerate(candidates):
            expected.append(('enemy',i))
            if c.enemy:
                expected.append(('lookup',i))
                if c.present and (c.state&255)<3:expected.append(('convert',i))
        assert self.events==expected
        return result,distance
