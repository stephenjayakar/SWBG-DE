"""Compare animal automation and nursery choice against original x86 routines."""
from pathlib import Path
import hashlib,itertools,json,random
from classic_engine_oracle import SOURCE_SHA
from classic_nursery_oracle import NurseryOracle
from classic_nursery_model import nursery_decision,nearest_building


def main():
    oracle=NurseryOracle()
    checks=0
    for player in range(9):
        assert oracle.idle_delay(player)==(0.5 if player==0 else 1.0)
        checks+=1
    for computer,housed,busy,fallback in itertools.product((False,True),(False,True),(False,True),(None,999)):
        for nurseries in ([],[(1,10,0)],[(1,10,9)],[(1,10,10)],[(1,10,11)],
                          [(1,10,10),(2,10,0)],[(1,10,10),(2,10,10)],[(1,0,0),(2,0,0)]):
            args=(nurseries,fallback,computer,housed,busy)
            assert oracle.decide(*args)==nursery_decision(*args),args
            checks+=1
    fixtures=[([],0,0), ([(1,319,2,0,10),(2,319,2,0,-10)],0,0),
              ([(1,319,1,0,0),(2,319,2,50,50)],0,0),
              ([(1,320,2,0,0),(2,319,2,10,10)],0,0)]
    rng=random.Random(5650)
    for _ in range(350):
        buildings=[(i+1,rng.choice((319,320,109,68,50)),rng.choice((0,1,2,2,3)),
                    rng.uniform(0,120),rng.uniform(0,120)) for i in range(rng.randrange(1,40))]
        fixtures.append((buildings,rng.choice((-1,rng.uniform(0,120))),rng.choice((-1,rng.uniform(0,120)))))
    for buildings,x,y in fixtures:
        for exclude in (-1,1,2):
            assert oracle.nearest(buildings,x,y,exclude)==nearest_building(buildings,x,y,exclude),(buildings,x,y,exclude)
            checks+=1
        assert oracle.nearest(buildings,x,y,economy=True)==nearest_building(buildings,x,y,economy=True)
        checks+=1
    names=('classic_nursery_oracle.py','classic_nursery_model.py','check_classic_nursery_engine.py')
    report=dict(passed=True,checks=checks,source_sha256=SOURCE_SHA,
                routines=['0x005650F0 (idle branch)','0x00564F70 (state 10)','0x004AF610','0x004AF3E0'],
                tool_hashes={n:hashlib.sha256((Path('outputs/toolkit')/n).read_bytes()).hexdigest() for n in names},
                coverage=['human/busy/garrisoned gates','nearest complete nursery','full nearest nursery fallback',
                          'command-center/mill fallback','object-list order and distance ties','source raw master ID'],
                limitations=['Nearest queries are tested separately; decision fixtures supply their results.',
                             'Ownership-change and action-stack completion branches are not simulated.',
                             'Issued enter/move commands and native pathfinding are recorded, not executed.',
                             'No DE runtime or save/load test.'],installed=False,full_behavior_parity=False)
    Path('work/classic-engine/nursery-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',checks,'source nursery-engine comparisons')


if __name__=='__main__':main()
