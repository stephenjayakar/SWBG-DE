"""Original priest canConvert gate at 0x5B48E0; no target lookup inference."""
from dataclasses import dataclass
import struct

EXCLUDED_CLASSES=frozenset((1,2,3,4,60,5,44,46,51,6,8,26,62))
EXCLUDED_IDS=frozenset((4,977,109,276,82,104,24,199,50))
MECHANICAL_CLASSES=frozenset((32,33,34,35,36,59,43,45,48,63,53,57,18,9,10,11,12,13,14,15,16,17,37,38,39,40))


def f32(value):
    return struct.unpack('<f',struct.pack('<f',value))[0]


@dataclass
class Conversion:
    attacker_class: int = 50
    padawan: bool = False
    force: float = 100.0
    ignore_force: bool = False
    target_exists: bool = True
    target_owner: int = 2
    target_class: int = 7
    target_id: int = 1
    target_type: int = 70
    unconvertible: int = 0
    master: bool = True
    resource67: float = 1.0
    resource27: float = 1.0
    resource87: float = 1.0


def can_convert(s):
    if s.padawan or s.attacker_class == 51:
        return False
    if not f32(s.force) >= 100.0 and not s.ignore_force:
        return False
    if not s.target_exists or s.target_owner == 0 or not f32(s.resource67) > 0:
        return False
    if s.target_class in EXCLUDED_CLASSES or s.target_id in EXCLUDED_IDS:
        return False
    if s.target_type in (70,80) and s.unconvertible != 0:
        return False
    if s.target_class in (50,64) and not (s.master and f32(s.resource27) > 0):
        return False
    if s.target_class in MECHANICAL_CLASSES and not (s.master and f32(s.resource87) > 0):
        return False
    return True
