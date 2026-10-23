"""Source addUnit combat estimates; damage/eligibility are supplied observations."""
from dataclasses import dataclass
import math
from classic_air_model import f32
from classic_target_model import FLOAT_MAX, divide


@dataclass(frozen=True)
class Combatant:
    uid: int
    hp: float = 100
    reload: float = 2
    exists: bool = True
    has_ai: bool = True


def estimated_times(own, enemies, target, damage, convertible):
    """damage and convertible are (attacker uid, victim uid) dictionaries.

    These are the original virtual damageCapability/canConvert results, not raw
    attack values. Computing them from DE armor/tasks remains adapter work.
    """
    epsilon = f32(1e-7)
    def dps(attackers, victim, require_ai=False):
        total = 0.0
        for attacker in attackers:
            if not attacker.exists or (require_ai and not attacker.has_ai):
                continue
            hit = f32(damage.get((attacker.uid,victim.uid),0.0))
            if hit <= epsilon and convertible.get((attacker.uid,victim.uid),False):
                amount = f32(victim.hp)*f32(0.1)
            else:
                amount = divide(hit,f32(attacker.reload))
            total = f32(total+amount)
        return total
    attacking = dps(own,target)
    # x87's unordered flag takes the same branch as a below-epsilon value.
    ttk = FLOAT_MAX if math.isnan(attacking) or attacking < epsilon else f32(divide(f32(target.hp),attacking))
    ttbk = 0.0
    for unit in own:
        if not unit.exists:
            continue
        defending = dps(enemies,unit,True)
        if not enemies or math.isnan(defending) or defending < epsilon:
            ttbk = FLOAT_MAX
            break
        ttbk = f32(ttbk+divide(f32(unit.hp),defending))
    if ttbk < epsilon and not enemies:
        ttbk = FLOAT_MAX
    return ttk,ttbk
