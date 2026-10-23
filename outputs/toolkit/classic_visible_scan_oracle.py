"""Execute original distance-table construction and visible-unit selection."""
import struct
from classic_engine_oracle import Oracle,TACTICAL,UC_X86_REG_ESP

class VisibleScanOracle(Oracle):
    def distance_table(self):
        self.reset();manager=TACTICAL+0x90000;table=TACTICAL+0x91000
        self.cpu.mem_write(manager,bytes(0x100))
        def allocate():
            assert self.read(self.cpu.reg_read(UC_X86_REG_ESP)+4)==1024
            self.ret(table)
        self.hooks[0x63328C]=allocate
        self.call(0x614720,this=manager)
        assert self.read(manager+0x20)==table
        result=bytes(self.cpu.mem_read(table,1024))
        spans=[]
        for address in range(0x69E41C,0x69E46D,4):
            ptr=self.read(address);rows=[]
            for i in range(1024):
                y,lo,hi=struct.unpack('<iii',self.cpu.mem_read(ptr+i*12,12))
                if y==999:break
                rows.append((y,lo,hi))
            else:raise AssertionError('Unterminated source distance spans')
            spans.append(rows)
        return result,spans

    def scan(self,table,categories,desired,relations,x,y,los,player=1,players=3,prior=None):
        assert 0<=player and len(categories)<=32 and all(0<=k<len(categories) for k in desired)
        assert len(relations)==256 and all(0<=v<5 for v in relations)
        assert sum(map(len,categories))<=8192
        self.reset()
        manager,player_heads,category_heads,dist,types,mapping=(TACTICAL+n for n in (0x90000,0x91000,0x92000,0x93000,0x94000,0x95000))
        for p in (manager,player_heads,category_heads,dist,types,mapping):self.cpu.mem_write(p,bytes(0x1000))
        self.write(manager,player_heads);self.write(manager+0x18,players);self.write(manager+0x20,dist)
        self.cpu.mem_write(dist,table)
        if player<players:self.write(player_heads+player*4,category_heads)
        cursor=TACTICAL+0x100000
        for i,records in enumerate(categories):
            self.cpu.mem_write(category_heads+i*8,struct.pack('<IHH',cursor,len(records),len(records)))
            for rec in records:
                self.cpu.mem_write(cursor,struct.pack('<iBBBB',*rec));cursor+=8
        if desired:self.cpu.mem_write(types,struct.pack('<'+'i'*len(desired),*desired))
        self.cpu.mem_write(mapping,struct.pack('<'+'i'*256,*relations))
        prior=prior or [[] for _ in range(5)]
        for group,records in enumerate(prior):
            assert len(records)<=256
            ptr=TACTICAL+0xA0000+group*0x2000
            self.write(0x7A1C8C+group*4,len(records));self.write(0x7A1CA0+group*4,ptr)
            for i,rec in enumerate(records):self.cpu.mem_write(ptr+i*8,struct.pack('<iBBBB',*rec))
        total=self.call(0x614A00,(x,y,los,player,types,len(desired),mapping),this=manager)
        groups=[]
        for group in range(5):
            count=self.read(0x7A1C8C+group*4);assert 0<=count<=256
            ptr=self.read(0x7A1CA0+group*4)
            groups.append([struct.unpack('<iBBBB',self.cpu.mem_read(ptr+i*8,8)) for i in range(count)])
        return total,groups
