"""Compare target flags, scores and ranking with original base-engine x86."""
from pathlib import Path
import hashlib
import json
import math
import random
import struct
from classic_engine_oracle import SOURCE_SHA
from classic_target_oracle import TargetOracle
from classic_target_model import Target, ECONOMIC_IDS, FLOAT_MAX, target_scores, target_order


def fixtures():
    fixtures=[([],{}),([Target(1)],{}),
              ([Target(1,ttk=10,ttbk=10),Target(2,ttk=10,ttbk=20)],{}),
              ([Target(1,ttk=FLOAT_MAX),Target(2,ttk=FLOAT_MAX)],{}),
              ([Target(1,source_class=6),Target(2,source_class=8)],{}),
              ([Target(1,source_class=18,source_id=70),Target(2),Target(3,source_class=18,source_id=70,same_zone=False)],{})]
    # Isolate each victory-priority condition and the unreachable-TTK guard.
    for cls,uid in ((46,4),(51,4),(18,104),(8,4),(18,276),(32,4)):
        for ttk in (10,FLOAT_MAX):
            for state in ({'regicide':True},{'special1':1},{'special2':1},{'special3':1},{}):
                for relic,carried,wonder in ((False,False,False),(True,False,False),(True,True,False),(False,False,True)):
                    fixtures.append(([Target(1,source_class=cls,source_id=uid,ttk=ttk,ttbk=20,distance=30,
                                             enemy_relic_countdown=relic,carries_relic=carried,enemy_wonder_countdown=wonder),
                                      Target(2,ttk=30,ttbk=10,distance=10)],state))
    rng=random.Random(549437)
    for _ in range(160):
        targets=[]
        for i in range(rng.choice((2,3,5,8,16,32))):
            cls,uid=rng.choice(((32,4),(18,70),(18,109),(18,104),(18,276),(6,117),(8,487),(51,4),(46,4)))
            targets.append(Target(i+1,cls,uid,rng.randint(1,100),rng.randint(1,100),rng.randint(0,100),
                                  same_zone=bool(rng.randrange(2)),alive=rng.randrange(10)!=0))
        fixtures.append((targets,{}))
    return fixtures


def main():
    oracle=TargetOracle()
    checks=0
    def equal(actual,expected,label):
        nonlocal checks
        assert actual==expected,(label,actual,expected)
        checks+=1
    for cls in range(70):
        for uid in sorted(ECONOMIC_IDS|{4,104,109,276,319,320,3550}):
            target=Target(1,source_class=cls,source_id=uid)
            equal(oracle.target_flags(cls,uid),(target.preferred,target.wall),('target class',cls,uid))
    scenarios=fixtures()
    for index,(targets,state) in enumerate(scenarios):
        scores,order=oracle.evaluate(targets,**state)
        expected=target_scores(targets,**state)
        for i,(actual,want) in enumerate(zip(scores,expected)):
            if math.isnan(want):
                equal(math.isnan(actual),True,('NaN score',index,i))
            else:
                equal(struct.pack('<f',actual),struct.pack('<f',want),('float32 score',index,i))
        equal(order,target_order(targets,expected),('rank',index))
        if index%100==0: print('PASS target fixture',index,flush=True)
    report=dict(passed=True,checks=checks,fixtures=len(scenarios),source_sha256=SOURCE_SHA,
                routines={'flags':'0x00592430..0x0059253B','scores':'0x00592980','sort':'0x00592C30'},
                coverage=['source class/raw-ID classification','exact float32 scores','victory overrides',
                          'unreachable-time guard','zero-range/NaN behavior','seven ranking passes','stable ties'],
                limitations=['Base executable; EF special-type2 hook is not executed.',
                             'Damage estimates, target memory, candidate admission and orders are not simulated.',
                             'Fixtures do not cover the source sort marker-array tail beyond 128 entries.'],
                installed=False,full_behavior_parity=False)
    names=('classic_target_model.py','classic_target_oracle.py','check_classic_targets.py')
    report['tool_hashes']={n:hashlib.sha256((Path('outputs/toolkit')/n).read_bytes()).hexdigest() for n in names}
    Path('work/classic-engine/target-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',checks,'target-selection comparisons;',len(scenarios),'fixtures; not installed')


if __name__=='__main__':main()
