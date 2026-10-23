"""Execute source target flags, scoring and sorting with explicit fixtures."""
import struct
from classic_engine_oracle import Oracle, TACTICAL, UC_X86_REG_ESP


class TargetOracle(Oracle):
    def target_flags(self, source_class, source_id):
        self.reset()
        obj, master = TACTICAL+0x40000, TACTICAL+0x41000
        self.cpu.mem_write(obj, bytes(0x200))
        self.cpu.mem_write(master, bytes(0x200))
        self.write(obj+0x10, 1)
        self.write(obj+0x14, master)
        self.cpu.mem_write(master+0x18, struct.pack('<h',source_id))
        self.cpu.mem_write(master+0x1E, struct.pack('<h',source_class))
        # Stop before distance/damage collection. Flag classification is original
        # code; the remainder of addUnit is outside this fixture's scope.
        # The hook is inside the function's stack frame: unwind its prologue.
        def finish():
            sp = self.cpu.reg_read(UC_X86_REG_ESP)
            self.cpu.reg_write(UC_X86_REG_ESP, sp+32)
            self.ret(args=7)
        self.hooks[0x59253B] = finish
        self.call(0x592430, (TACTICAL+0x30000,1,0,0,0,obj,0))
        return bool(self.read(TACTICAL+0x20)), bool(self.read(TACTICAL+0x24))

    def evaluate(self, targets, regicide=False, special1=-1, special2=-1, special3=-1):
        assert len(targets) <= 128, 'This fixture does not cover the source marker-array tail'
        self.reset()
        stats, info, main, game, world = (TACTICAL+n for n in (0x60000,0x90000,0xA0000,0xB0000,0xB1000))
        self.cpu.mem_write(stats, bytes(0xE020))
        self.cpu.mem_write(info, bytes(0x3000))
        self.write(info+0x100,main)
        for sn,value in ((106,special1),(107,special2),(108,special3)):
            self.write(main+0x4CF4+0x1F8+sn*4,value)
        self.write(0x6A3684,game)
        self.write(game+0x420,world)
        records={}
        # Countdown state belongs to a player, not a candidate. Share one of
        # four synthetic owners per boolean pair, staying within players 1..8.
        owners={}
        for i,t in enumerate(targets):
            obj,master,owner,memory=(TACTICAL+0x100000+i*0x400+j for j in (0,0x100,0x200,0x300))
            self.cpu.mem_write(obj,bytes(0x400))
            self.write(obj+0x14,master)
            self.write(obj+0x18,owner)
            countdown=(bool(t.enemy_relic_countdown),bool(t.enemy_wonder_countdown))
            player=owners.setdefault(countdown,len(owners)+1)
            self.write(owner+0xA0,player)
            self.cpu.mem_write(master+0x18,struct.pack('<h',t.source_id))
            self.cpu.mem_write(master+0x1E,struct.pack('<h',t.source_class))
            self.write(memory+0x28,int(t.carries_relic))
            self.cpu.mem_write(info+0x20E4+player,bytes([int(t.enemy_relic_countdown)]))
            self.cpu.mem_write(info+0x20ED+player,bytes([int(t.enemy_wonder_countdown)]))
            entry=stats+0x18+i*0x34
            self.cpu.mem_write(entry,struct.pack('<iiiifffi',t.uid,i,int(t.preferred),int(t.wall),
                                               t.ttk,t.ttbk,t.distance,int(t.same_zone)))
            records[t.uid]=(obj if t.alive else 0,memory)
        assert len(owners)<=4
        for j,name in enumerate(('ttk','ttbk','distance')):
            values=[getattr(t,name) for t in targets] or [0.0]
            self.cpu.mem_write(stats+j*8,struct.pack('<ff',min(values),max(values)))
        self.write(stats+0xD018,len(targets))
        def lookup():
            uid=self.read(self.cpu.reg_read(UC_X86_REG_ESP)+4)
            self.ret(records[uid][0],args=1)
        def memory():
            index=self.read(self.cpu.reg_read(UC_X86_REG_ESP)+4)
            self.ret(records[targets[index].uid][1],args=1)
        self.hooks[0x623DB0]=lookup
        self.hooks[0x5EF190]=lambda:self.ret(int(regicide))
        self.hooks[0x587CE0]=memory
        self.call(0x592980,(info,),this=stats)
        scores=[struct.unpack('<f',self.cpu.mem_read(stats+0x48+i*0x34,4))[0] for i in range(len(targets))]
        self.last_components=[struct.unpack('<ffff',self.cpu.mem_read(stats+0x38+i*0x34,16)) for i in range(len(targets))]
        self.call(0x592C30,(info,),this=stats)
        order=[self.read(stats+0xD01C+i*4) for i in range(len(targets))]
        return scores,order
