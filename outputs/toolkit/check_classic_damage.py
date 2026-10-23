"""Differential-check source armor formula and its sentinel/duplicate behavior."""
from pathlib import Path
import hashlib,itertools,json,random,struct
from classic_damage_model import armor_damage,attack_modifier
from classic_damage_oracle import DamageOracle
from classic_engine_oracle import SOURCE_SHA


def armor_cases():
    cases=[]
    for weapons in ([],[(3,0)],[(3,5)],[(3,-5)],[(3,5),(4,8)],[(3,5),(3,8)]):
        for armor in ([],[(3,0)],[(3,10)],[(3,-10)],[(3,1),(3,4)],[(3,4),(3,1)],[(3,2),(4,2)]):
            for base in (0,1000):
                for modifier in (0,0.5,1,1.25,-1):
                    for terrain in (0.5,1,1.25,2):
                        cases.append((weapons,armor,base,modifier,terrain))
    rng=random.Random(4449)
    for _ in range(500):
        weapons=[(rng.randrange(20),rng.randint(-10,100)) for i in range(rng.randrange(12))]
        armor=[(rng.randrange(20),rng.randint(-10,100)) for i in range(rng.randrange(20))]
        cases.append((weapons,armor,rng.choice((0,1000)),rng.uniform(0.5,2),rng.uniform(0.5,2)))
    return cases


def modifier_fixtures():
    for high,z,mode,action,building,target_building in itertools.product((False,True),(-1,0,1),(0,3),(False,True),(False,True),(False,True)):
        for relics,special,target_relics,target_special in itertools.product((0,1),(0,1),(0,1),(0,1)):
            yield (high,z,0,mode,action,building,relics,special,target_building,target_relics,target_special)


def main():
    oracle=DamageOracle()
    cases=armor_cases()
    for i,args in enumerate(cases):
        actual=oracle.damage(*args);expected=armor_damage(*args)
        assert struct.pack('<f',actual)==struct.pack('<f',expected),(i,args,actual,expected)
    modifier_cases=0
    for args in modifier_fixtures():
        actual=oracle.modifier(*args);expected=attack_modifier(*args)
        assert struct.pack('<f',actual)==struct.pack('<f',expected),(args,actual,expected)
        modifier_cases+=1
    names=('classic_damage_model.py','classic_damage_oracle.py','check_classic_damage.py')
    report=dict(passed=True,checks=len(cases)+modifier_cases,armor_cases=len(cases),modifier_cases=modifier_cases,
                source_sha256=SOURCE_SHA,routines=['0x004449C0','0x0055BBC0','0x00557BA0'],
                tool_hashes={n:hashlib.sha256((Path('outputs/toolkit')/n).read_bytes()).hexdigest() for n in names},
                coverage=['per-class armor','base armor for absent class','last duplicate armor wins',
                          'per-class nonpositive clipping','minimum one damage','empty weapons',
                          'defense terrain multiplier and minimum','height modifier','special-mode/action gate',
                          'building relic/special-relic modifiers'],
                limitations=['Eligibility, higher-ground and action-presence predicates, live inputs and shield application remain separate.',
                             'A reference formula is not a DE unit-query adapter or proof of XS arithmetic parity.'],
                installed=False,full_behavior_parity=False)
    Path('work/classic-engine/damage-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(cases)+modifier_cases,'source damage/modifier comparisons')


if __name__=='__main__':main()
