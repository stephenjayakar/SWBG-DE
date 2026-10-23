"""Source objectToAttack2 candidate gate; observations are explicit inputs.

This is not a DE observation adapter or a complete target selector. In
particular, current visibility, movement, conversion eligibility and source
zone membership must be supplied by the caller. Source IDs/classes are used.
"""
from dataclasses import dataclass
import math
import struct


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


@dataclass(frozen=True)
class Candidate:
    uid: int = 100
    memory_owner: int = 2
    exists: bool = True
    owner_status: int = 0
    relation: int = 3
    state: int = 2
    hp: float = 100
    master_type: int = 70
    source_id: int = 4
    source_class: int = 32
    object_flags: int = 0
    visibility: int = 1
    fog_flag: int = 0
    moving: int = 0
    zone: int = 1
    x: float = 20
    y: float = 20
    convertible: int = 1


@dataclass(frozen=True)
class SelectionContext:
    player: int = 2
    land_group: int = 1
    group_zone: int = 1
    force_different_zone: int = 0
    all_monks: int = 0
    reference_monk: bool = True
    monk_unit_ai: bool = True
    difficulty: int = 1
    width: int = 100
    height: int = 100
    leader_zone: int = 1


def candidate_admitted(target, context=SelectionContext(), reachable_tiles=()):
    """Match source 0x5934A9..0x593796, before combat-stat collection.

    reachable_tiles contains coordinates whose source zone equals the leader's
    current zone. Only the naval wall exception queries these tiles. Buildings
    intentionally bypass both visibility and isMoving in this source gate.
    """
    if target.uid == -1 or target.memory_owner == 0:
        return False
    if context.player != -1 and target.memory_owner != context.player:
        return False
    if not target.exists or target.owner_status == 2 or target.relation == 1:
        return False
    hp = f32(target.hp)
    if target.state > 2 or hp == 0 or math.isnan(hp):
        return False
    if target.master_type != 80:
        if target.visibility == 0 or (target.visibility == 128 and target.fog_flag == 0):
            return False
        if target.moving == 1:
            return False
    boat = bool(target.object_flags & 2)
    if context.land_group == 1 and (boat or target.master_type == 45):
        return False
    if context.land_group == 0 and not boat and target.source_id != 45:
        if target.source_class != 6:
            return False
        x, y = int(f32(target.x)), int(f32(target.y))
        nearby = any(0 <= tx < context.width and 0 <= ty < context.height
                     and abs(tx - x) <= 3 and abs(ty - y) <= 3
                     for tx, ty in reachable_tiles)
        if not nearby:
            return False
    if (context.force_different_zone == 1 and context.land_group == 1
            and (target.zone & 255) == context.group_zone):
        return False
    if (context.all_monks == 1 and context.reference_monk and context.monk_unit_ai
            and target.convertible == 0):
        return False
    if context.difficulty >= 3 and target.source_class == 58:
        return False
    return True


@dataclass(frozen=True)
class GroupMember:
    uid: int
    source_class: int = 32
    object_flags: int = 0
    zone: int = 1
    position: tuple = (0.0, 0.0, 0.0)
    exists: bool = True


def group_validity(members):
    """Match verifyGroupValidity with caller-initialized output parameters.

    Preserve partial output on failure and the empty-group NaN result. The
    surrounding selector rejects empty groups before calling this function.
    """
    land, zone, all_monks, monk = 1, -1, 1, -1
    centroid = [0.0, 0.0, 0.0]
    for index, member in enumerate(members):
        if not member.exists:
            return False, land, zone, tuple(centroid), all_monks, monk
        this_zone, boat = member.zone & 255, bool(member.object_flags & 2)
        if index == 0:
            land, zone = int(not boat), this_zone
        elif this_zone != zone or boat == bool(land):
            return False, land, zone, tuple(centroid), all_monks, monk
        centroid = [f32(a + f32(b)) for a, b in zip(centroid, member.position)]
        if member.source_class == 50 and monk == -1:
            monk = member.uid
        if member.source_class != 50:
            all_monks = 0
    centroid = [f32(x / len(members)) if members else float('nan') for x in centroid]
    return True, land, zone, tuple(centroid), all_monks, monk
