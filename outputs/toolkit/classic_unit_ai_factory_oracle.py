"""Run original initUnitAI with allocation/constructor/destructor boundaries."""
import struct
from classic_engine_oracle import Oracle,TACTICAL
from classic_unit_ai_catalog import source_catalog
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX


class UnitAIFactoryOracle(Oracle):
    def __init__(self):
        super().__init__()
        self.catalog=source_catalog()
        # Local inert SEH-chain cell for this isolated x86 routine's FS:[0].
        self.cpu.mem_map(0,0x1000)

    def select(self,source_class,volley_missile_id=-1,existing=False,fail_allocation=False):
        self.reset();self.write(0,0x76543210)
        own,master,old,old_vtable,new=(TACTICAL+n for n in (0xA0000,0xA1000,0xA2000,0xA3000,0xA4000))
        for p in (own,master,old,old_vtable,new):self.cpu.mem_write(p,bytes(0x500))
        self.write(own+0x14,master)
        self.write(own+0x7C,old if existing else 0)
        self.cpu.mem_write(master+0x1E,struct.pack('<h',source_class))
        self.write(master+0x1B8,volley_missile_id)
        self.write(old,old_vtable)
        destructor=TACTICAL+0xA5000
        self.write(old_vtable,destructor)
        events=[]
        def destroy():
            sp=self.cpu.reg_read(UC_X86_REG_ESP)
            assert self.cpu.reg_read(UC_X86_REG_ECX)==old and self.read(sp+4)==1
            events.append(('destroy',));self.ret(args=1)
        self.hooks[destructor]=destroy
        def allocate():
            sp=self.cpu.reg_read(UC_X86_REG_ESP)
            events.append(('allocate',self.read(sp+4)))
            self.ret(0 if fail_allocation else new)
        self.hooks[0x632B9D]=allocate
        for row in self.catalog:
            def construct(row=row):
                sp=self.cpu.reg_read(UC_X86_REG_ESP)
                assert self.cpu.reg_read(UC_X86_REG_ECX)==new and self.read(sp+4)==own
                events.append(('construct',row['type'],self.read(sp+8)))
                self.write(new,row['vtable']);self.ret(new,args=2)
            self.hooks[row['constructor']]=construct
        self.call(0x55D430,this=own)
        assert self.read(0)==0x76543210,'SEH chain not restored'
        result=self.read(own+0x7C)
        assert result in (0,new),hex(result)
        selected=-1 if not result else next(row['type'] for row in self.catalog if row['vtable']==self.read(result))
        return selected,events
