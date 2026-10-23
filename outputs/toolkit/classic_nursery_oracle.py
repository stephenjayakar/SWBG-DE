"""Original idle-animal decisions, with explicit nearest-object query fixtures."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_ESP
from classic_engine_oracle import Oracle,TACTICAL


class NurseryOracle(Oracle):
    def __init__(self):
        super().__init__()
        # The economy-search routine saves/restores its SEH chain at FS:[0].
        # This inert page supplies that storage; no exceptions/OS are emulated.
        self.cpu.mem_map(0,0x1000)

    def decide(self, nurseries=(), fallback=None, computer=True, housed=False, busy=False):
        """Nurseries are already in source nearest-query order: (id,capacity,used).

        Object-list search/pathfinding and ownership changes are not simulated.
        Executes the source idle branch of TRIBE_Action_Artifact::update.
        """
        self.reset()
        action,animal,player,actor_vtable,player_vtable,action_vtable = (
            TACTICAL+n for n in (0x60000,0x61000,0x62000,0x63000,0x64000,0x65000))
        for ptr in (action,animal,player,actor_vtable,player_vtable,action_vtable):
            self.cpu.mem_write(ptr,bytes(0x400))
        self.write(action,action_vtable)
        self.write(action+8,animal)
        self.cpu.mem_write(action+0xC,b'\x06')
        self.write(animal,actor_vtable)
        self.write(animal+0x10,100)
        self.write(animal+0x18,player)
        self.write(animal+0x2C,1 if housed else 0)
        self.write(player,player_vtable)
        records={}
        for i,(uid,capacity,used) in enumerate(nurseries):
            obj=TACTICAL+0x70000+i*0x400
            self.cpu.mem_write(obj,bytes(0x400))
            self.write(obj,actor_vtable)
            self.write(obj+0x10,uid)
            self.write(obj+0x14,obj+0x300)
            self.cpu.mem_write(obj+0x338,bytes([capacity]))
            records[uid]=(obj,used)
        if fallback is not None:
            obj=TACTICAL+0x80000
            self.cpu.mem_write(obj,bytes(0x100))
            self.write(obj+0x10,fallback)
            self.cpu.mem_write(obj+0x48,struct.pack('<fff',10,20,0))
            records[fallback]=(obj,0)
        events=[]
        def bind(table,offset,callback):
            address=TACTICAL+0x90000+len(self.hooks)*16
            self.write(table+offset,address)
            self.hooks[address]=callback
        def arg(n): return self.read(self.cpu.reg_read(UC_X86_REG_ESP)+4+n*4)
        checks=iter((0,int(busy)))
        self.hooks[0x406D90]=lambda:self.ret(next(checks))
        self.hooks[0x565410]=lambda:self.ret(0)
        bind(player_vtable,0x1C,lambda:self.ret(int(computer)))
        bind(actor_vtable,0x1DC,lambda:self.ret()) # variadic diagnostic log, caller cleans
        def garrison_count():
            obj=self.cpu.reg_read(UC_X86_REG_ECX)
            self.ret(next(used for ptr,used in records.values() if ptr==obj))
        bind(actor_vtable,0x288,garrison_count)
        def enter():
            events.append(('garrison',arg(0),arg(1)))
            self.ret(1,args=2)
        bind(actor_vtable,0x218,enter)
        def move():
            events.append(('move',self.read(arg(0)+0x10)))
            self.ret(1,args=4)
        bind(actor_vtable,0x118,move)
        def state():
            events.append(('state',arg(0)))
            self.ret(args=1)
        bind(action_vtable,0x60,state)
        def nearest():
            exclusion=arg(6)
            events.append(('find-nursery',arg(0),arg(3),arg(4),exclusion))
            result=next((records[uid][0] for uid,_,_ in nurseries if uid!=exclusion),0)
            self.ret(result,args=7)
        self.hooks[0x4AF610]=nearest
        def economy():
            events.append(('find-economy',arg(0),arg(1),arg(4),arg(5)))
            self.ret(records[fallback][0] if fallback is not None else 0,args=7)
        self.hooks[0x4AF3E0]=economy
        self.call(0x5650F0,this=action)
        return events

    def nearest(self, buildings, x, y, exclude=-1, economy=False):
        """Execute original search, with (id,rootId,state,x,y) object records.

        Idle animal calls pass no zone object, so no path/zone query is stubbed.
        """
        self.reset()
        objects,array=TACTICAL+0x60000,TACTICAL+0x61000
        self.cpu.mem_write(objects,struct.pack('<iii',0,array,len(buildings)))
        assert len(buildings)<=128
        for index,(uid,root,state,bx,by) in enumerate(buildings):
            obj=TACTICAL+0x70000+index*0x400
            self.cpu.mem_write(obj,bytes(0x400))
            self.write(obj+0x10,uid)
            self.write(obj+0x14,obj+0x200)
            self.cpu.mem_write(obj+0x218,struct.pack('<h',root))
            self.cpu.mem_write(obj+0x58,bytes([state]))
            self.cpu.mem_write(obj+0x48,struct.pack('<ff',bx,by))
            self.write(array+index*4,obj)
        bits=lambda v:struct.unpack('<i',struct.pack('<f',v))[0]
        if economy:
            result=self.call(0x4AF3E0,(109,68,bits(x),bits(y),1,2,0),this=objects)
        else:
            result=self.call(0x4AF610,(319,bits(x),bits(y),1,2,0,exclude),this=objects)
        return self.read(result+0x10) if result else -1

    def idle_delay(self, player):
        """Execute the real state-10 transition's timer assignment."""
        self.reset()
        action,animal,owner=TACTICAL+0x60000,TACTICAL+0x61000,TACTICAL+0x62000
        for ptr in (action,animal,owner): self.cpu.mem_write(ptr,bytes(0x200))
        self.write(action+8,animal)
        self.write(animal+0x18,owner)
        self.write(owner+0xA0,player)
        self.call(0x564F70,(10,),this=action)
        return struct.unpack('<f',self.cpu.mem_read(action+0x2C,4))[0]
