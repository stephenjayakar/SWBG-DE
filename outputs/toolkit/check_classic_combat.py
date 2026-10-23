"""Differential-check original combat-estimate aggregation with explicit inputs."""
from pathlib import Path
import hashlib
import json
import math
import random
import struct
from classic_combat_model import Combatant,estimated_times
from classic_combat_oracle import CombatOracle
from classic_engine_oracle import SOURCE_SHA


def fixtures():
    own=[Combatant(1)]
    enemies=[Combatant(2)]
    fixtures=[]
    for hit in (0,1e-8,1e-7,1,10,100):
        for incoming in (0,1e-8,1e-7,1,10,100):
            for conversion in (False,True):
                fixtures.append((own,enemies,enemies[0],{(1,2):hit,(2,1):incoming},
                                 {(1,2):conversion,(2,1):conversion}))
    fixtures.extend([
        (own,[],Combatant(2),{(1,2):10},{}),
        ([Combatant(1,exists=False)],enemies,enemies[0],{},{}),
        (own,[Combatant(2,has_ai=False)],Combatant(2,has_ai=False),{(1,2):10,(2,1):20},{}),
        ([Combatant(1),Combatant(3)],enemies,enemies[0],{(1,2):10,(3,2):20,(2,1):10},{}),
        ([Combatant(1,reload=0)],enemies,enemies[0],{},{}),
    ])
    rng=random.Random(592430)
    for index in range(350):
        own=[Combatant(i+1,rng.uniform(1,1000),rng.choice((0.5,1,1.7,2,3)),rng.randrange(9)!=0)
             for i in range(rng.choice((1,2,5,10,40)))]
        enemies=[Combatant(i+101,rng.uniform(1,1000),rng.choice((0.5,1,1.7,2,3)),
                           rng.randrange(9)!=0,rng.randrange(9)!=0)
                 for i in range(rng.choice((0,1,2,5,10,30)))]
        target=Combatant(500,rng.uniform(1,1000))
        damage,conversions={},{}
        for attackers,victims in ((own,[target]),(enemies,own)):
            for a in attackers:
                for b in victims:
                    damage[a.uid,b.uid]=rng.choice((0,0,1,4.5,13,30,100))
                    conversions[a.uid,b.uid]=bool(rng.randrange(2))
        fixtures.append((own,enemies,target,damage,conversions))
    return fixtures


def main():
    oracle=CombatOracle()
    scenarios=fixtures()
    checks=0
    for index,args in enumerate(scenarios):
        for same_zone in (True,False):
            actual=oracle.estimate(*args,target_zone=1 if same_zone else 2)
            expected=(*estimated_times(*args),same_zone and any(u.exists for u in args[0]))
            for i,(a,e) in enumerate(zip(actual,expected)):
                assert (math.isnan(a) if math.isnan(e) else struct.pack('<f',a)==struct.pack('<f',e)), (index,i,a,e,args)
                checks+=1
        if index%100==0: print('PASS combat fixture',index,flush=True)
    names=('classic_combat_model.py','classic_combat_oracle.py','check_classic_combat.py')
    report=dict(passed=True,checks=checks,fixtures=len(scenarios),source_sha256=SOURCE_SHA,
                routine='0x00592430',tool_hashes={n:hashlib.sha256((Path('outputs/toolkit')/n).read_bytes()).hexdigest() for n in names},
                coverage=['reload-weighted damage','conversion fallback','survival-time aggregation',
                          'missing units and absent UnitAI','first valid member zone','zero damage and no enemies'],
                limitations=['Virtual damageCapability, conversion eligibility, world lookup, distance and zones are explicit fixtures.',
                             'No armor calculation, live target admission, memory, group orders or DE runtime is tested.'],
                installed=False,full_behavior_parity=False)
    Path('work/classic-engine/combat-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',checks,'source combat-estimate comparisons;',len(scenarios),'fixtures')


if __name__=='__main__':main()
