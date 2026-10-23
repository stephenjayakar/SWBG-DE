"""Original base-engine target scoring/ranking, pending live input adapters.

The EF sn-special-attack-type2 hook is deliberately not represented here yet.
This is a differential-test reference, not an installed targeting controller.
"""
from dataclasses import dataclass
import math
from classic_air_model import f32

FLOAT_MAX = f32(3.4028234663852886e38)
ECONOMIC_IDS = frozenset((70, 562, 584, 323, 103, 50, 209, 68))


@dataclass(frozen=True)
class Target:
    uid: int
    source_class: int = 32
    source_id: int = 4
    ttk: float = 10
    ttbk: float = 10
    distance: float = 20
    same_zone: bool = True
    alive: bool = True
    enemy_relic_countdown: bool = False
    carries_relic: bool = False
    enemy_wonder_countdown: bool = False

    @property
    def wall(self):
        return self.source_class in (6, 8)

    @property
    def preferred(self):
        return not (self.source_class in (18, 7) and self.source_id in ECONOMIC_IDS)


def divide(a, b):
    if b == 0:
        return math.nan if a == 0 else math.copysign(math.inf, a)
    return a / b


def target_scores(targets, regicide=False, special1=-1, special2=-1, special3=-1):
    if not targets:
        return []
    ttks = [f32(t.ttk) for t in targets]
    ttbks = [f32(t.ttbk) for t in targets]
    distances = [f32(t.distance) for t in targets]
    lo_ttk, lo_dist = min(ttks), min(distances)
    range_ttk = f32(max(ttks)-lo_ttk)
    range_ttbk = f32(max(ttbks)-min(ttbks))
    range_dist = f32(max(distances)-lo_dist)
    epsilon = f32(1e-7)
    result = []
    for t, ttk, dist in zip(targets, ttks, distances):
        if not t.alive:
            result.append(0.0)
            continue
        if ttk < FLOAT_MAX:
            if regicide and t.source_class == 46:
                result.append(100.0); continue
            if t.enemy_relic_countdown and (t.source_class == 51 or t.source_id == 104):
                result.append(100.0 if t.carries_relic else f32(99.9)); continue
            if t.source_id == 104 and special1 == 1:
                result.append(100.0); continue
            if t.source_class == 8 and special2 == 1:
                result.append(100.0); continue
            if t.source_id == 276 and (special3 == 1 or t.enemy_wonder_countdown):
                result.append(100.0); continue
        kill = 25.0 if range_ttk < epsilon else f32(25.0-divide(ttk-lo_ttk, range_ttk)*25.0)
        # Preserve the original's surprising reuse of TTK/minTTK/rangeTTK here.
        # Only the range gate uses TTBK. Equal TTK with unequal TTBK yields NaN.
        survival = 25.0 if range_ttbk < epsilon else f32(25.0-divide(ttk-lo_ttk, range_ttk)*25.0)
        proximity = 25.0 if range_dist < epsilon else f32(25.0-divide(dist-lo_dist, range_dist)*25.0)
        score = f32(proximity + kill + (25.0 if t.same_zone else 0.0) + survival)
        if t.source_class == 6 and score >= 100:
            score = 99.0
        result.append(score)
    return result


def target_order(targets, scores):
    """Original seven ranking passes, including stable ties and x87 NaNs."""
    predicates = (
        lambda t,s: s >= 100,
        lambda t,s: t.same_zone and not t.wall and t.preferred,
        lambda t,s: t.same_zone and not t.wall and not t.preferred,
        lambda t,s: t.same_zone and t.wall and t.preferred,
        lambda t,s: not t.same_zone and not t.wall and t.preferred,
        lambda t,s: not t.same_zone and not t.wall and not t.preferred,
        lambda t,s: not t.same_zone and t.wall and t.preferred,
    )
    used = set()
    result = []
    for predicate in predicates:
        while True:
            best = -1
            for i,(target,score) in enumerate(zip(targets,scores)):
                if i in used or not predicate(target,score):
                    continue
                if best < 0 or math.isnan(score) or math.isnan(scores[best]) or score > scores[best]:
                    best = i
            if best < 0:
                break
            used.add(best)
            result.append(best)
    return result
