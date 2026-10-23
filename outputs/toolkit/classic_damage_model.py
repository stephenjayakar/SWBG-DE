"""Source armor aggregation for AI estimates; eligibility is a separate query."""
from classic_air_model import f32


def damage_capability(weapons,armor,base_armor=1000,attack_modifier=1.0,terrain_modifier=1.0,
                      target_present=True,has_ai=True,can_attack=True):
    if not target_present or not has_ai:
        return f32(sum(max(0,strength) for _,strength in weapons))
    if not can_attack:
        return 0.0
    return armor_damage(weapons,armor,base_armor,attack_modifier,terrain_modifier)


def attack_modifier(higher_ground=False, attacker_z=0.0, target_z=0.0, special_mode=0, action_133=False,
                    building=False, relics=0, special_relics=0, target_building=False,
                    target_relics=0, target_special_relics=0):
    value=1.25 if higher_ground else 0.75 if f32(attacker_z)<f32(target_z) else 1.0
    if special_mode==3 and action_133:value*=2.0
    if building:
        if special_relics>0:value*=f32(1.2)
        elif relics>0:value*=f32(1.1)
        if target_building:
            if target_special_relics>0:value*=f32(1.0/1.2)
            elif target_relics>0:value*=f32(0.9090908765792847)
    return f32(value)


def armor_damage(weapons, armor, base_armor=1000, attack_modifier=1.0, terrain_modifier=1.0):
    if not weapons:
        return 0.0
    resistance=f32(terrain_modifier)
    if resistance<1.0:resistance=1.0
    modifier=f32(attack_modifier)
    total=0.0
    for kind,strength in weapons:
        protection=base_armor
        for armor_kind,amount in armor:
            if armor_kind==kind:protection=amount  # Last duplicate entry wins.
        contribution=(strength-protection)*resistance*modifier
        if contribution>0.0:total+=contribution
    return f32(max(1.0,total))
