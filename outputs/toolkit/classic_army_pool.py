"""Original tactical-group admission, independent of DE's native group classes.

Pool inputs are already classified source objects, in their original order.
This is a controller component, not an installed native-group replacement.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class TacticalGroup:
    kind: int
    members: tuple


def first_group(uid, groups):
    return next((i for i, group in enumerate(groups) if uid in group.members), -1)


def attack_totals(groups):
    return {name: sum(len(g.members) for g in groups if g.kind == kind)
            for name, kind in (('ground', 100), ('air', 108), ('boat', 102))}


def available(pool, classes, groups, aircraft=False, difficulty=1):
    """Return (source reported count, stable unique queue).

    Source list entries absent from the world are ignored. Transports are never
    air combat candidates. Medics are never ground attack candidates; easy and
    easiest also exclude force users. Membership in ANY group excludes a unit.
    The original return count includes repeated eligible list entries, although
    its output queue deduplicates them. Preserve this distinction explicitly.
    """
    result = []
    reported = 0
    for uid in pool:
        if uid not in classes or first_group(uid, groups) != -1:
            continue
        cls = classes[uid]
        if aircraft and cls == 59:
            continue
        if not aircraft and (cls == 51 or (difficulty > 2 and cls == 50)):
            continue
        reported += 1
        if uid not in result:
            result.append(uid)
    return reported, result
