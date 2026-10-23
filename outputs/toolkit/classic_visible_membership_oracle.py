"""Run original visibility constructor and insertion/removal, including growth."""
import struct
from classic_engine_oracle import Oracle,TACTICAL,UC_X86_REG_ESP

class VisibleMembershipOracle(Oracle):
    def initialize(self,players,categories):
        assert 0<=players<=9 and 0<=categories<=16
        self.reset();self.manager=TACTICAL+0x90000;self.heap=TACTICAL+0x30000
        self.allocations={};self.freed=set();self.touched=set();self.players=players;self.categories=categories+1
        self.cpu.mem_write(self.manager,bytes(0x400))
        self.lookup=TACTICAL+0xA000;self.cpu.mem_write(self.lookup,bytes(1024))
        self.write(0x7A1CB4,self.lookup)
        def allocate(size):
            ptr=self.heap;self.heap+=(size+15)//16*16
            assert self.heap<TACTICAL+0x88000
            self.cpu.mem_write(ptr,bytes(size));self.allocations[ptr]=size
            return ptr
        def calloc():
            sp=self.cpu.reg_read(UC_X86_REG_ESP)
            self.ret(allocate(self.read(sp+4)*self.read(sp+8)))
        def malloc():self.ret(allocate(self.read(self.cpu.reg_read(UC_X86_REG_ESP)+4)))
        def free():
            ptr=self.read(self.cpu.reg_read(UC_X86_REG_ESP)+4)
            assert ptr in self.allocations and ptr not in self.freed
            self.freed.add(ptr);self.ret()
        self.hooks[0x632D33]=calloc;self.hooks[0x63328C]=malloc;self.hooks[0x632CCA]=free
        assert self.call(0x614590,(players,categories),this=self.manager)==self.manager
        assert self.read(self.manager+0x18)==players and self.read(self.manager+0x1C)==categories+1

    def update(self,uid,owner,x,y,radius,category,prior,new):
        assert 0<=uid<256 and category>=0
        obj=TACTICAL+0x100000+uid*0x200
        if uid not in self.touched:
            self.cpu.mem_write(obj,bytes(0x200));self.write(obj+0x10,uid)
            self.write(self.lookup+uid*4,obj);self.touched.add(uid)
        self.call(0x614840,(uid,owner,x,y,radius,category,prior,new,obj+0x144),this=self.manager)

    def snapshot(self):
        rows=[];caps=[];expected={};heads=self.read(self.manager)
        for player in range(self.players):
            categories=self.read(heads+player*4);prow=[];pcap=[]
            for cat in range(self.categories):
                ptr,capacity,count=struct.unpack('<IHH',self.cpu.mem_read(categories+cat*8,8))
                assert ptr in self.allocations and ptr not in self.freed and count<=capacity
                values=[struct.unpack('<iBBBB',self.cpu.mem_read(ptr+i*8,8)) for i in range(count)]
                for i,value in enumerate(values):expected[value[0],player]=(cat,i,ptr+i*8)
                prow.append(values);pcap.append(capacity)
            rows.append(prow);caps.append(pcap)
        pointers={}
        for uid in self.touched:
            obj=TACTICAL+0x100000+uid*0x200
            for player in range(self.players):
                actual=self.read(obj+0x144+player*4)
                wanted=expected.get((uid,player))
                assert actual==(wanted[2] if wanted else 0),(uid,player,actual,wanted)
                if wanted:pointers[uid,player]=wanted[:2]
        return rows,caps,pointers

    def scan(self,x,y,los,player,desired,relations):
        assert player>=0 and all(0<=cat<self.categories for cat in desired)
        assert len(relations)==256 and all(0<=bucket<5 for bucket in relations)
        types,mapping=TACTICAL+0xB400,TACTICAL+0xB000
        if desired:self.cpu.mem_write(types,struct.pack('<'+'i'*len(desired),*desired))
        self.cpu.mem_write(mapping,struct.pack('<'+'i'*256,*relations))
        total=self.call(0x614A00,(x,y,los,player,types,len(desired),mapping),this=self.manager)
        buffers=[]
        for bucket in range(5):
            ptr=self.read(0x7A1CA0+bucket*4);count=self.read(0x7A1C8C+bucket*4)
            assert 0<=count<=256
            buffers.append([struct.unpack('<iBBBB',self.cpu.mem_read(ptr+i*8,8)) for i in range(count)])
        return total,buffers
