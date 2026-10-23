"""Idle animal automation from source Artifact::update, not strategic rules."""
from classic_air_model import f32


def nearest_building(buildings,x,y,exclude=-1,economy=False):
    best=-1
    best_distance=-1.0
    roots=(109,68) if economy else (319,)
    for uid,root,state,bx,by in buildings:
        if root not in roots or state!=2 or uid==exclude:
            continue
        unknown_x,unknown_y=f32(x)==-1.0,f32(y)==-1.0
        if (unknown_x and unknown_y) if economy else (unknown_x or unknown_y):
            return uid
        dx,dy=f32(x)-f32(bx),f32(y)-f32(by)
        distance=dx*dx+dy*dy
        if best_distance==-1.0 or best_distance>distance:
            best=uid
            best_distance=f32(distance)
    return best


def nursery_decision(nurseries=(),fallback=None,computer=True,housed=False,busy=False):
    events=[]
    if computer and not housed and not busy:
        events.append(('find-nursery',319,1,2,-1))
        if nurseries:
            uid,capacity,used=nurseries[0]
            if used<capacity:
                events.append(('garrison',uid,1))
            else:
                events.append(('find-nursery',319,1,2,uid))
                if len(nurseries)>1:
                    # The original deliberately does NOT test the next one's
                    # capacity before requesting entry; native entry may fail.
                    events.append(('garrison',nurseries[1][0],1))
        else:
            events.append(('find-economy',109,68,1,2))
            if fallback is not None: events.append(('move',fallback))
    events.append(('state',10))
    return events
