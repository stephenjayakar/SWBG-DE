"""Run original search, real RNG/radius/visible query; lookup/notify are fixtures."""
import struct
from classic_visible_membership_oracle import VisibleMembershipOracle
from classic_engine_oracle import TACTICAL,UC_X86_REG_ESP,UC_X86_REG_ECX

RELATIONS=[0,1,4]+[0]*253
DESIRED=[1,0,1]

def records():
    return [(uid,uid%3,(uid%7)*3+5,(uid//7)*3+5,uid%4,uid%2,0,7) for uid in range(24)]

class SearchCacheOracle(VisibleMembershipOracle):
    def update_entry(self,timer,elapsed,used=1,total=999,seen=7,seed=0x12345678):
        self.reset()
        ai,own,owner,world,vtable=(TACTICAL+n for n in (0x90000,0x91000,0x92000,0x93000,0x94000))
        for p in (ai,own,owner,world,vtable):self.cpu.mem_write(p,bytes(0x400))
        self.write(ai+4,own);self.write(own,vtable);self.write(own+0x18,owner);self.write(owner+0x8C,world)
        self.write(vtable+0x68,TACTICAL+0x95000);self.hooks[TACTICAL+0x95000]=lambda:self.ret(1)
        self.cpu.mem_write(ai+0x174,struct.pack('<f',timer));self.cpu.mem_write(world+0xA8,struct.pack('<f',elapsed))
        self.cpu.mem_write(ai+0x178,bytes([seen]));self.write(ai+0x18C,42)
        self.write(0x6A3394,17);self.write(0x6A3398,used);self.write(0x6A339C,total);self.write(0x6A33A0,19)
        self.write(0x69EC98,seed)
        assert self.call(0x419250,(123,),this=ai)==0
        assert self.read(ai+0x18C)==-1 and self.read(0x6A3394)==0 and self.read(0x6A33A0)==0
        return dict(used=self.read(0x6A3398),total=self.read(0x6A339C),
                    timer_bits=self.read(ai+0x174)&0xFFFFFFFF,seen=self.cpu.mem_read(ai+0x178,1)[0],seed=self.read(0x69EC98)&0xFFFFFFFF)

    def search(self,s):
        self.initialize(3,1)
        for row in records():self.update(*row)
        _,prior=self.scan(10,10,15,1,[0,1],RELATIONS)
        own,master,owner,follow,fmaster,fowner,ai,ovtable,pvtable,world,desired=(
            TACTICAL+n for n in (0xB0000,0xB1000,0xB2000,0xB3000,0xB4000,0xB5000,0xB6000,0xB7000,0xB8000,0xB9000,0xBA000))
        for p in (own,master,owner,follow,fmaster,fowner,ai,ovtable,pvtable,world,desired):self.cpu.mem_write(p,bytes(0x400))
        self.write(own,ovtable);self.write(own+0x10,s.actor);self.write(own+0x14,master);self.write(own+0x18,owner)
        self.write(ovtable+0x1D0,0x552E10 if s.static_radius else 0x409B70)
        self.cpu.mem_write(master+0x34,struct.pack('<f',s.los));self.cpu.mem_write(master+0x10C,struct.pack('<f',s.search_radius))
        self.write(owner,pvtable);self.write(owner+0x8C,world if s.world else 0);self.write(owner+0xA0,s.owner)
        self.cpu.mem_write(owner+0xE4,struct.pack('<'+'i'*9,*RELATIONS[:9]))
        self.write(follow+0x14,fmaster);self.write(follow+0x18,fowner);self.write(fowner+0xA0,s.follow_owner)
        self.cpu.mem_write(follow+0x48,struct.pack('<ff',s.follow_x,s.follow_y));self.cpu.mem_write(fmaster+0x34,struct.pack('<f',s.follow_los))
        self.write(ai+4,own);self.write(ai+0x28,s.order);self.write(ai+0x4C,s.follow_id)
        self.write(ai+0x160,desired if s.desired else 0);self.write(ai+0x164,s.count)
        self.cpu.mem_write(ai+0x174,struct.pack('<f',s.timer));self.cpu.mem_write(ai+0x178,bytes([s.seen&255]))
        self.cpu.mem_write(desired,struct.pack('<iii',*DESIRED))
        self.write(0x6A3398,s.used);self.write(0x6A339C,s.cached_total);self.write(0x69EC98,s.seed)
        queries=[];notifications=[]
        def args(n):return struct.unpack('<'+'i'*n,self.cpu.mem_read(self.cpu.reg_read(UC_X86_REG_ESP)+4,n*4))
        def query():
            x,y,los,player,types,count,mapping=args(7)
            assert types==desired and mapping==owner+0xE4
            queries.append((x,y,los,player,count))
        self.hooks[0x614A00]=query  # Observe entry, then execute the real query.
        def lookup():
            assert args(1)==(s.follow_id,) and self.cpu.reg_read(UC_X86_REG_ECX)==world
            self.ret(follow if s.follow_found else 0,args=1)
        self.hooks[0x623DB0]=lookup
        def action():
            assert self.cpu.reg_read(UC_X86_REG_ECX)==follow
            self.ret(1 if s.follow_action else 0)
        self.hooks[0x40C840]=action
        def notify():
            assert self.cpu.reg_read(UC_X86_REG_ECX)==owner
            notifications.append(args(6))
            # Search must restore its saved draw even if notification uses RNG.
            self.write(0x69EC98,0xABCDEF01);self.ret(args=6)
        self.write(pvtable+0x12C,TACTICAL+0xBC000);self.hooks[TACTICAL+0xBC000]=notify
        xy=[struct.unpack('<I',struct.pack('<f',v))[0] for v in (s.x,s.y)]
        self.call(0x419EE0,(*xy,s.allow),this=ai)
        buffers=[]
        for bucket in range(5):
            ptr=self.read(0x7A1CA0+bucket*4);count=self.read(0x7A1C8C+bucket*4)
            buffers.append([struct.unpack('<iBBBB',self.cpu.mem_read(ptr+i*8,8)) for i in range(count)])
        return dict(seed=self.read(0x69EC98)&0xFFFFFFFF,used=self.read(0x6A3398),total=self.read(0x6A339C),
            seen=self.cpu.mem_read(ai+0x178,1)[0],timer_bits=self.read(ai+0x174)&0xFFFFFFFF,
            queries=queries,notifications=notifications,buffers=buffers),prior
