"""Check original cache, search dispatch, notification gates and RNG side effects."""
from pathlib import Path
from dataclasses import replace,asdict
import itertools,json,random
from classic_search_cache import Search,run,f32,bits
from classic_search_cache_oracle import SearchCacheOracle,RELATIONS,DESIRED,records
from classic_visible_scan import scan
from classic_visible_scan_oracle import VisibleScanOracle
from classic_visible_membership import VisibleMembership
from classic_unit_identity import sha

ROOT=Path('work/classic-engine');TOOLKIT=Path('outputs/toolkit')

def fixtures():
    for used,desired,count,allow,timer in itertools.product((0,1,2),(False,True),(-1,0,2,3),(0,1,2),(-1.,0.,10.,10.000001,11.,float('nan'))):
        yield Search(used=used,desired=desired,count=count,allow=allow,timer=timer)
    for order,follow_id,world,found,action in itertools.product((0,701),(-1,42),(False,True),(False,True),(False,True)):
        yield Search(order=order,follow_id=follow_id,world=world,follow_found=found,follow_action=action)
    rng=random.Random(0x419EE0)
    for _ in range(180):
        yield Search(seed=rng.randrange(2**32),used=rng.randrange(3),seen=rng.randrange(256),
            timer=rng.choice((0.,10.,11.,float('inf'),float('nan'))),
            los=rng.choice((-.5,0.,.9999999,1.,1.000001,15.,30.)),search_radius=rng.choice((-1.9,0.,6.9,40.)),
            static_radius=bool(rng.randrange(2)),x=rng.uniform(-2,25),y=rng.uniform(-2,25),
            order=rng.choice((0,701)),follow_owner=rng.randrange(4),count=rng.randrange(-1,4),
            allow=rng.randrange(256),follow_los=rng.choice((-1.9,0.,1.9,30.)),follow_x=rng.uniform(-2,25),follow_y=rng.uniform(-2,25))

def main():
    table,_=VisibleScanOracle().distance_table();oracle=SearchCacheOracle();model=VisibleMembership(3,1)
    for event in records():model.update(*event)
    cases=[];scans=0;notifications=0;skips=0;special=0
    for index,s in enumerate(fixtures()):
        actual,prior=oracle.search(s)
        def query(x,y,los,player,count):
            desired=DESIRED[:max(0,count)]
            rows=model.rows[player] if player<3 else [[],[]]
            return scan(table,rows,desired,RELATIONS,x,y,los,player,3,prior)
        expected=run(s,query,prior);assert actual==expected,(index,s,actual,expected)
        scans+=len(actual['queries']);notifications+=len(actual['notifications']);skips+=not actual['queries']
        special+=bool(actual['queries']) and s.order==701 and s.follow_id!=-1 and s.world and s.follow_found and s.follow_action
        # JSON float NaN is retained only in ignored local fixture evidence.
        cases.append(dict(input=asdict(s),output=actual))
    entries=[]
    for timer,elapsed,used in itertools.product((-1.,0.,9.999999,10.,10.000001,11.,10000000.),(-.1,0.,1./60.,.1,1.,100.),(0,1,2)):
        result=oracle.update_entry(timer,elapsed,used)
        assert result==dict(used=0,total=0,timer_bits=bits(f32(f32(timer)+f32(elapsed))),seen=7,seed=0x12345678)
        entries.append(dict(timer=timer,elapsed=elapsed,used=used,output=result))
    entry_trace=ROOT/'search-update-cases.json';entry_trace.write_text(json.dumps(entries)+'\n')
    trace=ROOT/'search-cache-cases.json';trace.write_text(json.dumps(cases)+'\n')
    report=dict(passed=True,cases=len(cases),queries=scans,notifications=notifications,cache_or_null_desired_skips=skips,special_follow_queries=special,
        trace_sha256=sha(trace),update_entry_cases=len(entries),update_trace_sha256=sha(entry_trace),
        hashes={n:sha(TOOLKIT/n) for n in ('classic_search_cache.py','classic_search_cache_oracle.py','check_classic_search_cache.py')},
        installed=False,xs_implemented=False,full_behavior_parity=False,
        limitations=['Own/follow object state, desired arrays and world lookup are fixtures.',
                     'Original search, RNG, searchRadius getters and visible-unit query execute; notification is recorded, not delivered.',
                     'Source cache-reset scheduling and native RNG/event synchronization remain unfinished.'])
    (ROOT/'search-cache-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {len(cases)} source searches / {scans} queries / {notifications} notifications / {skips} skips / {special} follow searches / {len(entries)} update entries')

if __name__=='__main__':main()
