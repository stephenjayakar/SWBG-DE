"""Document the original evaluator's low-damage own-UnitAI precondition.

Expected source failures occur only inside Unicorn, never in a running game.
This does not add a source crash to the XS controller or claim support for it.
"""
from pathlib import Path
import hashlib
import json
from unicorn import UcError
from unicorn.x86_const import UC_X86_REG_EIP
from classic_combat_oracle import CombatOracle
from classic_combat_model import Combatant
from classic_engine_oracle import SOURCE_SHA


def main():
    oracle=CombatOracle();target=Combatant(500)
    cases=[]
    for has_ai in (False,True):
        for damage in (0.0,1.0):
            own=[Combatant(1,has_ai=has_ai)]
            failed=False;address=None
            try:
                oracle.estimate(own,[],target,{(1,500):damage},{})
            except UcError:
                address=oracle.cpu.reg_read(UC_X86_REG_EIP)
                assert not has_ai and damage==0 and address==0x5925FB,(has_ai,damage,address)
                failed=True
            assert failed==(not has_ai and damage==0),(has_ai,damage,failed)
            cases.append(dict(has_ai=has_ai,damage=damage,source_fault=failed,address=hex(address) if address else None))
    names=('check_classic_combat_precondition.py','classic_combat_oracle.py','classic_combat_model.py','classic_engine_oracle.py')
    report=dict(passed=True,cases=cases,source_sha256=SOURCE_SHA,
                tool_hashes={n:hashlib.sha256((Path('outputs/toolkit')/n).read_bytes()).hexdigest() for n in names},
                installed=False,full_behavior_parity=False,
                limitation='A low-damage own attacker without UnitAI violates the original evaluator precondition; no native DE crash is reproduced.')
    Path('work/classic-engine/combat-precondition-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS 4 source precondition probes; original null dereference confirmed at 0x5925FB')


if __name__=='__main__':main()
