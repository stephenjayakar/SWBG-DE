"""Check original list order and object-pointer repair after every update."""
from pathlib import Path
import hashlib,json,random
from classic_visible_membership import VisibleMembership
from classic_visible_membership_oracle import VisibleMembershipOracle
from classic_unit_identity import sha

ROOT=Path('work/classic-engine');TOOLKIT=Path('outputs/toolkit')

def fixtures(players,categories):
    masks={};cats={};all_players=(1<<players)-1
    for uid in range(150):
        masks[uid]=all_players;cats[uid]=0
        yield uid,uid%9,uid,255-uid,uid%8,0,0,all_players
    # Force non-tail deletions after both 64->128 and 128->256 growth.
    for uid in range(0,150,2):
        yield uid,0,0,0,0,0,masks[uid],0;masks[uid]=0
    # Same bits retain old record bytes even if new values are supplied.
    for uid in range(1,150,2):
        yield uid,255,-1,300,999,0,masks[uid],masks[uid]
    rng=random.Random(0x614840+players*100+categories)
    for i in range(500):
        uid=rng.randrange(150);old=masks[uid];new=rng.randrange(1<<players) if players else 0
        if old==0:cats[uid]=rng.randrange(categories+1)
        category=cats[uid]
        yield uid,rng.randrange(300),rng.randrange(-10,300),rng.randrange(-10,300),rng.randrange(300),category,old,new
        masks[uid]=new
    # Out-of-range categories and high visibility bits must not edit lists.
    for uid in range(20):
        yield uid,1,1,1,1,categories+1,0,all_players
        yield uid,1,1,1,1,cats[uid],masks[uid],masks[uid]|0xFFFF0000
    for uid in range(150):
        yield uid,0,0,0,0,cats[uid],masks[uid],0

def main():
    oracle=VisibleMembershipOracle();cases=0;growths=0;traces=[]
    for players,categories in ((0,0),(1,0),(3,2),(9,3)):
        oracle.initialize(players,categories);model=VisibleMembership(players,categories)
        assert oracle.snapshot()==model.snapshot()
        steps=[]
        for args in fixtures(players,categories):
            oracle.update(*args);model.update(*args)
            got,want=oracle.snapshot(),model.snapshot();assert got==want,(players,categories,cases,args)
            steps.append(args);cases+=1
        assert all(not bucket for row in model.rows for bucket in row)
        growths+=model.growths
        traces.append(dict(players=players,categories=categories,steps=steps,growths=model.growths,freed_blocks=len(oracle.freed)))
    trace_path=ROOT/'visible-membership-traces.json';trace_path.write_text(json.dumps(traces)+'\n')
    report=dict(passed=True,updates=cases,constructors=len(traces),growths=growths,
        trace_sha256=sha(trace_path),tool_hashes={n:sha(TOOLKIT/n) for n in ('classic_visible_membership.py','classic_visible_membership_oracle.py','check_classic_visible_membership.py')},
        installed=False,xs_implemented=False,full_behavior_parity=False,
        limitations=['Visibility-mask/category events are fixtures, not native visibility notifications.',
                     'Allocators/free are fixtures; original constructor, copy/move and pointer repair execute.',
                     'Removal requires a valid source pointer; missing-object lookup and inconsistent-event cases remain untested.'])
    (ROOT/'visible-membership-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {cases} source membership updates / {len(traces)} constructors / {growths} growths with pointer repair')

if __name__=='__main__':main()
