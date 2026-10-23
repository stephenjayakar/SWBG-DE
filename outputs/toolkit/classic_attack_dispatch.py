"""Connect source pool admission, spatial selection and tactical group state.

Percentages are the stored, already difficulty-scaled strategic numbers.
The returned stop queue is a command request; this module does not issue orders.
"""
from classic_air_model import Aircraft, attack_count, source_groups
from classic_army_pool import TacticalGroup, available


def dispatch(state, ground, air, classes, positions, ground_percent, air_percent,
             difficulty=1, radius=20, now=0, fail_after=None, boats=(), boat_percent=0):
    stops = []
    created = 0
    for pool, aircraft, percent, kind in ((ground, False, ground_percent, 100),
                                          (boats, False, boat_percent, 102),
                                          (air, True, air_percent, 108)):
        if percent <= 0:
            continue
        groups = [TacticalGroup(g.kind, tuple(g.members)) for g in state.groups.values()]
        if kind == 102:
            # Source boat collection checks only tactical membership, not world
            # existence; the later spatial routine handles stale IDs.
            admitted = [uid for uid in pool if not state.containing(uid)]
            reported, candidates = len(admitted), list(dict.fromkeys(admitted))
        else:
            reported, candidates = available(pool, classes, groups, aircraft, difficulty)
        requested = attack_count(reported, percent)
        if not candidates or candidates[0] not in classes:
            continue  # The source grouping routine aborts on an absent first ID.
        window = [Aircraft(uid, *positions[uid]) for uid in candidates[:40] if uid in classes]
        clusters = source_groups(window, requested, radius, total_count=len(candidates))
        selected = 0
        for members in clusters:
            handle = state.create(fail=fail_after is not None and created >= fail_after)
            if not handle:
                break
            created += 1
            group = state.groups[handle]
            group.kind = kind
            group.action = 1
            group.flags |= 8
            for uid in members:
                if selected >= requested:
                    break
                state.add(handle, uid, now)
                stops.append(uid)
                selected += 1
            group.desired = len(group.members)
            if difficulty >= 3:
                group.retreat = len(group.members) // 2
    return stops
