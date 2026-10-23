"""Source soldier attack gate; world geometry remains explicit observations."""
from dataclasses import dataclass
import struct
from classic_attack_eligibility import can_attack_base


def f32(value):
    return struct.unpack('<f',struct.pack('<f',value))[0]


@dataclass
class Soldier:
    attacker_class: int = 8
    attacker_id: int = 1
    target_class: int = 8
    target_id: int = 1
    invisible: bool = False
    resource31: float = 0.0
    target_present: bool = True
    owner_id: int = 1
    target_owner: int = 2
    target_type: int = 70
    target_flag: int = 0
    action_type: int = -1
    stance: int = 0
    last_action: int = 600
    current_order: int = 0
    weapon_range: float = 4.0
    state_distance: float = 4.0
    on_patrol: int = 0
    has_patrol: int = 0
    highest_path_distance: float = 4.0
    patrol_path_distance: float = 4.0


def motion_allowed(s):
    if s.stance == 3 and s.last_action != 600:
        return False
    distance,weapon_range=f32(s.state_distance),f32(s.weapon_range)
    if s.stance == 2 and s.current_order != 701:
        limit=weapon_range+0.5+(1.5 if s.target_owner == 0 else 0.0)
        # Unordered comparison does not reject in this stance.
        if distance > limit:
            return False
    if s.stance == 1:
        if s.current_order in (711,733) and s.on_patrol == 1:
            distance=f32(s.highest_path_distance)
        elif s.has_patrol == 1:
            distance=f32(s.patrol_path_distance)
        if not weapon_range+5.0 >= distance:
            return False
    return True


def can_attack_soldier(s, ground_to_air=()):
    if not s.target_present or s.owner_id == 0:
        return False
    if s.target_owner == 0 and s.target_class not in (4,60,5):
        return False
    if s.attacker_class == 34:
        return False
    if (s.attacker_class == 36 or s.attacker_id == 109) and s.action_type in (124,125):
        return False
    if s.target_class in (21,28) or (s.target_type == 80 and s.target_flag != 0):
        return False
    if not motion_allowed(s):
        return False
    return can_attack_base(s.attacker_class,s.attacker_id,s.target_class,s.target_id,
                           s.invisible,s.resource31,ground_to_air)


def can_attack_priest(s, held_attribute=0, ground_to_air=()):
    if not s.target_present or s.owner_id == 0:
        return False
    if s.target_owner == 0 and s.target_class not in (4,60,5):
        return False
    if held_attribute == 57 or s.target_class in (21,28):
        return False
    if s.target_type == 80 and s.target_flag != 0:
        return False
    if not motion_allowed(s):
        return False
    return can_attack_base(s.attacker_class,s.attacker_id,s.target_class,s.target_id,
                           s.invisible,s.resource31,ground_to_air)


def can_attack_siege(s, own_state=2, computer_player=1, ground_to_air=()):
    if not s.target_present or s.target_class in (21,28) or not motion_allowed(s):
        return False
    if s.owner_id == 0 or (s.target_type == 80 and s.target_flag != 0) or own_state < 2:
        return False
    if s.attacker_class == 34 and computer_player == 0:
        return False
    if s.action_type in (124,125):
        return False
    buildings=(18,6,8,7,9,10)
    if s.attacker_class == 35:
        return s.target_class in buildings
    if s.attacker_class in (34,36) and s.target_class not in (*buildings,34,36):
        return False
    return can_attack_base(s.attacker_class,s.attacker_id,s.target_class,s.target_id,
                           s.invisible,s.resource31,ground_to_air)
