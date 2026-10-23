"""Original UnitAI search dispatch/cache behavior over supplied source state."""
from dataclasses import dataclass
import struct

def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]

@dataclass(frozen=True)
class Search:
    seed:int=1
    used:int=0
    cached_total:int=999
    seen:int=7
    timer:float=11.
    x:float=10.5
    y:float=10.5
    allow:int=1
    actor:int=700
    owner:int=1
    los:float=6.5
    search_radius:float=4.5
    static_radius:bool=False
    desired:bool=True
    count:int=2
    order:int=0
    follow_id:int=42
    world:bool=True
    follow_found:bool=True
    follow_action:bool=True
    follow_owner:int=2
    follow_x:float=14.5
    follow_y:float=9.5
    follow_los:float=3.5

def run(s,scan,prior_buffers):
    draw=(((s.seed*214013+2531011)&0xFFFFFFFF)>>16)&32767
    used=s.used;total=s.cached_total;seen=s.seen&255;timer=f32(s.timer)
    queries=[];notifications=[];buffers=prior_buffers
    if used!=1:
        used=1
        if s.desired:
            special=s.order==701 and s.follow_id!=-1 and s.world and s.follow_found and s.follow_action
            if special:
                q=(int(f32(s.follow_x)),int(f32(s.follow_y)),int(f32(s.follow_los)),s.follow_owner,s.count)
            else:
                radius=s.los if s.static_radius else s.search_radius
                q=(int(f32(s.x)),int(f32(s.y)),max(int(f32(radius)),int(f32(s.los))+1),s.owner,s.count)
            queries.append(q);total,buffers=scan(*q)
            if not special:
                seen=int(bool(buffers[4]))
                if seen and (s.allow&255)==1:
                    if timer>10.:notifications.append((s.actor,s.actor,528,0,0,0))
                    timer=0.
    return dict(seed=draw,used=used,total=total,seen=seen,timer_bits=bits(timer),
                queries=queries,notifications=notifications,buffers=buffers)
