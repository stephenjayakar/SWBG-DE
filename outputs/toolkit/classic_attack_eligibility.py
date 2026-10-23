"""Source base UnitAI attack predicate and installed ground-to-air catalog.

This is the base predicate, not the specialized soldier/priest/tower wrapper.
Inputs use SWGB source master IDs/classes, never the remapped DE classes.
"""
from pathlib import Path
import hashlib
import struct

CATALOG = Path('E:/GOG Games/Star Wars - Galactic Battlegrounds/Game/Data/ground-to-air.txt')
GROUND = frozenset((5,6,7,8,10,11,13,15,18,32,34,35,36,37,38,39,43,44,47,49,50,51,52,53,56,58,60))
AIR = frozenset((9,16,33,40,55))
ALL = frozenset((48,57,62,63,64))
AIR_TARGETS = frozenset((43,48,59,62,63,64))


def catalog():
    data = CATALOG.read_bytes()
    ids = tuple(int(line) for line in data.decode('ascii').splitlines())
    assert ids and all(-32768 <= uid <= 32767 for uid in ids)
    assert len(ids) * 4 < 0x20D8 - 0x1814
    return ids, hashlib.sha256(data).hexdigest()


def can_attack_base(attacker_class, attacker_id, target_class, target_id,
                    invisible=False, resource31=0.0, ground_to_air=()):
    if invisible or attacker_class == 4 or target_id == 696 or target_class in (21,28):
        return False
    if attacker_id in ground_to_air:
        return True
    resource31 = struct.unpack('<f', struct.pack('<f', resource31))[0]
    if resource31 > 0 and attacker_id in (500,603):
        return True
    if attacker_class in ALL:
        return True
    if attacker_class in AIR:
        return target_class in AIR_TARGETS
    return attacker_class in GROUND and target_class not in AIR_TARGETS


def can_attack_tower(attacker_class, attacker_id, target_class, target_id,
                     invisible=False, resource31=0.0, target_present=True,
                     owner_id=1, target_owner=2, target_type=70, target_flag=0,
                     own_state=2, ground_to_air=()):
    if not target_present or owner_id == 0 or target_class in (21,28):
        return False
    if target_owner == 0 and target_class not in (4,60,5):
        return False
    if target_type == 80 and target_flag != 0:
        return False
    if target_id == 50 or own_state < 2:
        return False
    # The source bypasses the base predicate (including invisibility) here.
    if target_class == 5 and attacker_class != 9:
        return True
    return can_attack_base(attacker_class,attacker_id,target_class,target_id,
                           invisible,resource31,ground_to_air)


def can_attack_nullable(attacker_class,attacker_id,target_class,target_id,
                        invisible=False,resource31=0.0,target_present=True,ground_to_air=()):
    return target_present and can_attack_base(attacker_class,attacker_id,target_class,target_id,
                                              invisible,resource31,ground_to_air)


def can_attack_neutral(kind,target_class):
    # Gate kinds: 0 unrestricted base, 1 soldier/tower, 2 priest, 3 siege,
    # 4 never (civilian/medic/building). These are not combat pipeline role IDs.
    if kind==0:return True
    if kind==4:return False
    denied={18,6,8,7,58,14,12,17,2}
    if kind in (1,2):denied.add(45)
    if kind in (1,3):denied.add(59)
    assert kind in (1,2,3)
    return target_class not in denied


def generate_catalog(ids, sha):
    expressions = ['sourceID == ' + str(uid) for uid in dict.fromkeys(ids)]
    return ('// Generated from installed Data/ground-to-air.txt; SHA-256 ' + sha + '\n'
            '// Source master IDs, not DE classes or live object IDs.\n'
            'bool classicAttackGroundToAir(int sourceID = -1) {\n'
            '    return (' + ' ||\n            '.join(expressions) + ');\n}\n')


if __name__ == '__main__':
    ids, sha = catalog()
    output = Path('work/classic-engine/classic_attack_catalog.xs')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generate_catalog(ids, sha))
    print(output, len(ids), 'source overrides', sha)
