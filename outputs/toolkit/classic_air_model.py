"""Source-derived tactical decisions; compared with classic_engine_oracle.

This module is an offline reference for the separate aircraft controller, not
an installed runtime controller. Target selection and orders are still pending.
"""
from dataclasses import dataclass
import math
import struct

GROUND_CLASSES = frozenset((32, 33, 34, 35, 36, 44, 47, 49, 50, 51, 52, 53, 54, 55, 56, 57))
AIR_CLASSES = frozenset((43, 48, 59, 62, 63, 64))
COMBAT_AIR_CLASSES = AIR_CLASSES - {59}


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def scaled_air_percent(value, difficulty, multiplayer=False, no_scaling=False):
    if value <= 0 or no_scaling:
        return value
    # Source difficulty: 0 hardest, 1 hard, 2 moderate, 3 easy, 4 easiest.
    # Hard multiplayer scales some group sizes, but NOT attack percentages.
    factor = (1, 1, .75, .5, .25)[difficulty]
    return max(1, int(value * f32(factor)))


def attack_count(available, percentage):
    if percentage <= 0:
        return 0
    # The executable uses a float32 0.01 constant, ceil, then integer conversion.
    return math.ceil(available * percentage * f32(.01))


@dataclass(frozen=True)
class Aircraft:
    uid: int
    x: float
    y: float
    zone: int = 0


def source_groups(candidates, requested, distance=20, total_count=None):
    """Preserve source input order and its first-40-candidate limitation.

    The source chooses the densest remaining cluster, first candidate on a tie.
    A cluster contains its leader followed by neighbors in original list order.
    Clusters may exceed the requested count; attackNow truncates them afterward.
    The stopping comparison uses the ENTIRE input size, including beyond 40.
    """
    remaining = list(candidates[:40])
    if total_count is None:
        total_count = len(candidates)
    distance = f32(distance)
    result = []
    def near(a, b):
        # Source vector subtraction stores float32 components before squaring.
        dx, dy = f32(f32(a.x) - f32(b.x)), f32(f32(a.y) - f32(b.y))
        return math.sqrt(dx * dx + dy * dy) <= distance and a.zone == b.zone
    while remaining:
        leader = max(remaining, key=lambda a: sum(near(a, b) for b in remaining))
        group = [leader] + [a for a in remaining if a != leader and near(leader, a)]
        result.append([a.uid for a in group])
        members = {a.uid for a in group}
        remaining = [a for a in remaining if a.uid not in members]
        if len(remaining) <= total_count - requested:
            break
    return result


def attack_groups(candidates, percentage, distance=20):
    requested = attack_count(len(candidates), percentage)
    if not requested:
        return []
    result = []
    for group in source_groups(candidates, requested, distance):
        taken = group[:requested]
        requested -= len(taken)
        if taken:
            result.append(taken)
    return result
