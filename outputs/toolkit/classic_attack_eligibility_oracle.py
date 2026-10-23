"""Execute base UnitAI attack eligibility, including the installed static patch."""
import struct
from classic_engine_oracle import Oracle, TACTICAL
from classic_attack_eligibility import catalog
from unicorn.x86_const import UC_X86_REG_ESP


class AttackEligibilityOracle(Oracle):
    def __init__(self):
        super().__init__()
        self.ground_to_air, self.catalog_sha = catalog()
        # Supply the file loader's resulting table, but execute the original
        # patched membership loop at 0x7B2180. No OS file call is emulated.
        self.write(0x7B1800, 1)
        self.write(0x7B180C, 0x7B1814)
        self.write(0x7B1810, 0x7B1814 + 4 * len(self.ground_to_air))
        for i, uid in enumerate(self.ground_to_air):
            self.write(0x7B1814 + 4*i, uid)

    def _fixture(self, attacker_class, attacker_id, target_class, target_id,
                 invisible=False, resource31=0.0, owner_id=1):
        self.reset()
        ai, own, master, owner, target, target_master, vtable, resources = (
            TACTICAL+n for n in (0x80000,0x81000,0x82000,0x83000,0x84000,0x85000,0x86000,0x87000))
        for pointer in (ai,own,master,owner,target,target_master,vtable,resources):
            self.cpu.mem_write(pointer, bytes(0x400))
        self.write(ai+4, own)
        self.write(own+0x14, master)
        self.write(own+0x18, owner)
        self.write(owner+0xA0, owner_id)
        self.write(owner+0xAC, resources)
        self.cpu.mem_write(resources+31*4, struct.pack('<f', resource31))
        self.write(target, vtable)
        self.write(target+0x14, target_master)
        for pointer, cls, uid in ((master,attacker_class,attacker_id),(target_master,target_class,target_id)):
            self.cpu.mem_write(pointer+0x18, struct.pack('<h', uid))
            self.cpu.mem_write(pointer+0x1E, struct.pack('<h', cls))
        invisible_stub = TACTICAL+0x88000
        self.write(vtable+0x48, invisible_stub)
        calls=[]
        def is_invisible():
            sp=self.cpu.reg_read(UC_X86_REG_ESP)
            calls.append(self.read(sp+4))
            self.ret(int(invisible), args=1)
        self.hooks[invisible_stub]=is_invisible
        self.invisibility_calls=calls
        return ai,own,target

    def base(self, attacker_class, attacker_id, target_class, target_id,
             invisible=False, resource31=0.0, owner_id=1, building=False):
        ai,own,target=self._fixture(attacker_class,attacker_id,target_class,target_id,
                                    invisible,resource31,owner_id)
        result = self.call(0x5B8A90 if building else 0x41C530, (target,), this=ai)
        assert self.invisibility_calls == [owner_id], self.invisibility_calls
        assert result in (0,1), result
        return bool(result)

    def tower(self, attacker_class, attacker_id, target_class, target_id,
              invisible=False, resource31=0.0, target_present=True, owner_id=1,
              target_owner=2, target_type=70, target_flag=0, own_state=2):
        ai,own,target=self._fixture(attacker_class,attacker_id,target_class,target_id,
                                    invisible,resource31,owner_id)
        owner=TACTICAL+0x89000
        self.cpu.mem_write(owner,bytes(0x400))
        self.write(owner+0xA0,target_owner)
        self.write(target+0x18,owner)
        master=self.read(target+0x14)
        self.cpu.mem_write(master+4,bytes([target_type]))
        self.cpu.mem_write(target+0x235,bytes([target_flag]))
        self.cpu.mem_write(own+0x58,bytes([own_state]))
        result=self.call(0x5B7CD0,(target if target_present else 0,),this=ai)
        assert self.invisibility_calls in ([],[owner_id]),self.invisibility_calls
        assert result in (0,1),result
        return bool(result)

    def nullable(self, attacker_class, attacker_id, target_class, target_id,
                 invisible=False, resource31=0.0, target_present=True,kind='civilian'):
        ai,own,target=self._fixture(attacker_class,attacker_id,target_class,target_id,invisible,resource31)
        address={'civilian':0x5B2F80,'lion':0x5B28F0,'medic':0x5B2FB0}[kind]
        result=self.call(address,(target if target_present else 0,),this=ai)
        assert result in (0,1),result
        return bool(result)

    def neutral(self,kind,target_class):
        self.reset()
        address=(0x5B2910,0x5B7D70,0x5B4D80,0x5B8440,0x5B2FB0)[kind]
        result=self.call(address,(target_class,))
        assert result in (0,1),result
        return bool(result)
