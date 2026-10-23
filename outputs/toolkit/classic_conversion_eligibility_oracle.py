"""Run original conversion predicate with fixture lookup/Padawan/Master traits."""
import struct
from classic_engine_oracle import Oracle,TACTICAL
from unicorn.x86_const import UC_X86_REG_ESP


class ConversionEligibilityOracle(Oracle):
    def conversion(self,s,source_ids=None):
        self.reset()
        ai,own,master,owner,resources,target,target_master,target_owner,vtable,world=(
            TACTICAL+n for n in range(0x90000,0x9A000,0x1000))
        for p in (ai,own,master,owner,resources,target,target_master,target_owner,vtable,world):
            self.cpu.mem_write(p,bytes(0x400))
        self.write(ai+4,own)
        self.write(own,vtable)
        self.write(own+0x14,master)
        self.write(own+0x18,owner)
        self.write(owner+0xAC,resources)
        self.write(owner+0x8C,world)
        self.cpu.mem_write(master+0x1E,struct.pack('<h',s.attacker_class))
        if source_ids is not None:
            self.cpu.mem_write(master+0x18,struct.pack('<hh',*source_ids))
        self.cpu.mem_write(own+0x54,struct.pack('<f',s.force))
        self.write(target+0x14,target_master)
        self.write(target+0x18,target_owner)
        self.write(target_owner+0xA0,s.target_owner)
        self.cpu.mem_write(target_master+0x18,struct.pack('<h',s.target_id))
        self.cpu.mem_write(target_master+0x1E,struct.pack('<h',s.target_class))
        self.cpu.mem_write(target_master+4,bytes([s.target_type]))
        self.cpu.mem_write(target_master+0x1C1,bytes([s.unconvertible]))
        for resource,value in ((67,s.resource67),(27,s.resource27),(87,s.resource87)):
            self.cpu.mem_write(resources+resource*4,struct.pack('<f',value))
        for offset,flag in ((0x30,s.padawan),(0x34,s.master)):
            if source_ids is not None:
                self.write(vtable+offset,0x54B170 if offset==0x30 else 0x54B1D0)
                continue
            address=TACTICAL+0x9A000+offset
            self.write(vtable+offset,address)
            self.hooks[address]=lambda flag=flag:self.ret(int(flag))
        def lookup():
            sp=self.cpu.reg_read(UC_X86_REG_ESP)
            assert self.read(sp+4)==345
            self.ret(target if s.target_exists else 0,args=1)
        self.hooks[0x623DB0]=lookup
        result=self.call(0x5B48E0,(345,int(s.ignore_force)),this=ai)
        assert result in (0,1),result
        return bool(result)
