"""Source post-ranking target choice with explicit path-query results.

Pathfinding itself is not implemented here. Preserve the caller's decision
sequence, transport fallback, blocker queue and continuation index separately
from the engine-specific geometry service.
"""
from dataclasses import dataclass
import math
from classic_air_model import f32


@dataclass(frozen=True)
class PathTarget:
    uid: int
    same_zone: int = 1
    exists: bool = True
    direct: int = 0
    transport: int = 0
    obstruction: int = 0
    blockers: tuple = ()
    missing_blockers: tuple = ()
    exception_terrains: tuple = ()
    plain_retry: int = 0


def choose_path(targets, ranges=(4.0,), can_transport=0, sn241=0,
                resume=None, start_time=0, ticks=(), time_budget=100):
    radius = f32(16.0)
    for value in ranges:
        if value is None:
            continue
        value = f32(value)
        if value < radius or math.isnan(value) or math.isnan(radius):
            radius = value
    begin = 0 if resume is None else resume
    clock = iter(ticks)
    events = []
    result = dict(target=None, same_zone=-1, need_transport=-1, resume=None,
                  attempts=[], blockers=[], events=events, radius=radius)
    for index in range(begin, len(targets)):
        if index > begin:
            elapsed = (next(clock, start_time) - start_time) & 0xFFFFFFFF
            if elapsed >= time_budget:
                result['resume'] = index
                return result
        target = targets[index]
        if not target.exists:
            continue
        events.append(('direct', target.uid))
        if target.direct == 1:
            result.update(target=target.uid, same_zone=target.same_zone, need_transport=0,
                          attempts=[target.uid])
            return result
        if can_transport == 1 and (target.same_zone == 0 or (target.same_zone == 1 and sn241 == 0)):
            events.append(('transport', target.uid))
            if target.transport == 1:
                need = 1
                if target.same_zone != 0:
                    for terrain in (1, 22, 23, 16, 15):
                        events.append(('exception', target.uid, terrain))
                        if terrain in target.exception_terrains:
                            break
                    else:
                        events.append(('plain-retry', target.uid))
                        if target.plain_retry != 0:
                            need = 0
                result.update(target=target.uid, same_zone=target.same_zone, need_transport=need,
                              attempts=[target.uid])
                return result
        if target.same_zone == 1:
            events.append(('obstruction', target.uid))
            if target.obstruction == 1:
                blockers = [b for b in target.blockers if b not in target.missing_blockers]
                # Source addPriorityUnit accepts 19 entries, despite a 20-slot
                # array. Once full, even the final intended target is omitted.
                queue = (blockers + [target.uid])[:19]
                result.update(target=queue[0], same_zone=target.same_zone, need_transport=0,
                              blockers=queue)
                return result
    return result
