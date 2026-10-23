// DE-native shield adaptation. The source game's independent shield pool is
// not available in DE. Neutral DAT auras become bonus health/regen only while
// a completed generator stack is powered. Head/foundation auras stay neutral.
int swgbDefenseBuildings = -1;
int swgbDefenseOther = -1;

float swgbDefensePowerRange(int player = 1, int id = -1) {
    if (id == 12 || id == 498 || id == 132 || id == 20 ||
        id == 3554 || id == 3555 || id == 3556 || id == 3557)
        return(xsPlayerAttribute(player, 2018));
    if (id == 1009 || id == 1013) return(xsPlayerAttribute(player, 2030));
    return(0.0);
}

bool swgbDefenseFinished(int unit = -1) {
    if (xsDoesUnitExist(unit) == false) return(false);
    if (xsGetUnitHitpoints(unit) <= 0.0) return(false);
    if (xsGetUnitType(unit) != 80) return(true);
    return(xsGetUnitBuildPoints(unit) >= xsGetUnitAttribute(unit, cTrainTime));
}

bool swgbDefensePoweredBy(int unit = -1, int player = 1, int candidates = -1) {
    if (candidates < 0) return(false);
    vector position = xsGetUnitPosition(unit);
    for (i = 0; < xsArrayGetSize(candidates)) {
        int core = xsArrayGetInt(candidates, i);
        if (swgbDefenseFinished(core)) {
            if (xsGetUnitOwner(core) == player && xsGetGarrisonedInUnitId(core) < 0) {
                float radius = swgbDefensePowerRange(player, xsGetUnitCopyId(core));
                if (radius > 0.0) {
                    vector center = xsGetUnitPosition(core);
                    float dx = xsVectorGetX(position) - xsVectorGetX(center);
                    float dy = xsVectorGetY(position) - xsVectorGetY(center);
                    if (dx * dx + dy * dy <= radius * radius) return(true);
                }
            }
        }
    }
    return(false);
}

void swgbDefenseUpdateShield(int unit = -1, int player = 1) {
    if (xsDoesUnitExist(unit) == false) return;
    if (xsGetUnitOwner(unit) != player) return;
    int id = xsGetUnitCopyId(unit);
    // Only completed shield-generator stacks project shields. The foundation
    // and stack can coexist; activating both would duplicate the protection.
    if (id != 335 && id != 336) return;
    bool powered = false;
    bool complete = swgbDefenseFinished(unit);
    // A stack can have zero train time while its head is still a foundation.
    // If its coincident construction head exists, require that head to finish.
    if (swgbDefenseBuildings >= 0) {
        vector here = xsGetUnitPosition(unit);
        for (headIndex = 0; < xsArrayGetSize(swgbDefenseBuildings)) {
            int head = xsArrayGetInt(swgbDefenseBuildings, headIndex);
            if (xsDoesUnitExist(head)) {
                int headType = xsGetUnitCopyId(head);
                if (headType == 213 || headType == 215) {
                    vector there = xsGetUnitPosition(head);
                    if (xsVectorGetX(here) == xsVectorGetX(there) &&
                        xsVectorGetY(here) == xsVectorGetY(there) &&
                        swgbDefenseFinished(head) == false) complete = false;
                }
            }
        }
    }
    if (complete) {
        powered = swgbDefensePoweredBy(unit, player, swgbDefenseBuildings);
        if (powered == false) powered = swgbDefensePoweredBy(unit, player, swgbDefenseOther);
    }
    float radius = xsPlayerAttribute(player, 2024);
    if (radius <= 0.0) { powered = false; radius = 0.0; }
    float recharge = 120.0 * xsPlayerAttribute(player, 2010);
    float interval = xsPlayerAttribute(player, 2025);
    if (interval > 0.0) recharge = recharge / interval;
    else recharge = 0.0;
    int count = xsGetUnitTaskCount(unit);
    for (task = 0; < count) {
        if (xsUnitTaskAmount(unit, task)) {
            if (xsGetTaskAmount(cTaskAttrTaskType) == 155.0) {
                float attribute = xsGetTaskAmount(cTaskAttrSearchWaitTime);
                int target = xsCeilToInt(xsGetTaskAmount(cTaskAttrObjectId));
                if (target >= 0 && (attribute == 0.0 || attribute == 109.0)) {
                    float amount = 0.0;
                    if (powered) {
                        if (attribute == 0.0) amount = xsGetObjectAttribute(player, target, cHitpoints);
                        else amount = recharge;
                    }
                    if (xsGetTaskAmount(cTaskAttrWorkValue1) != amount ||
                        xsGetTaskAmount(cTaskAttrWorkRange) != radius) {
                        xsTaskAmount(cTaskAttrWorkValue1, amount);
                        xsTaskAmount(cTaskAttrWorkRange, radius);
                        xsModifyUnitTasks(unit, task, true);
                    }
                }
            }
        }
    }
}

void swgbDefenseTick() {
    int lastPlayer = xsGetNumPlayers();
    if (lastPlayer > 8) lastPlayer = 8;
    for (player = 1; <= lastPlayer) {
        if (xsGetPlayerInGame(player)) {
            swgbDefenseBuildings = xsGetPlayerUnitIds(player, 903, swgbDefenseBuildings);
            swgbDefenseOther = xsGetPlayerUnitIds(player, 911, swgbDefenseOther);
            if (swgbDefenseBuildings >= 0) {
                for (index = 0; < xsArrayGetSize(swgbDefenseBuildings)) {
                    swgbDefenseUpdateShield(xsArrayGetInt(swgbDefenseBuildings, index), player);
                }
            }
        }
    }
}

rule swgbDefenseShieldTick
active
minInterval 1
maxInterval 1
{
    swgbDefenseTick();
}

// Astromech resource 212 is isolated at 2212 by the DAT adapter.
int swgbAirQuery = -1;
int swgbAirKeys = -1;
int swgbAirRemainders = -1;
int swgbAirLastSecond = -1;

bool swgbAstromechEligible(int objectId = -1) {
    return(objectId == 6 || objectId == 733 || objectId == 748 || objectId == 752 || objectId == 758 || objectId == 762 || objectId == 769 || objectId == 773 || objectId == 779 || objectId == 783 || objectId == 789 || objectId == 793 || objectId == 799 || objectId == 1675 || objectId == 1036 || objectId == 1046 || objectId == 2504 || objectId == 2506 || objectId == 2524 || objectId == 2526);
}

int swgbAirTimerSlot(int unit = -1) {
    int freeSlot = -1;
    for (slot = 0; < xsArrayGetSize(swgbAirKeys)) {
        int key = xsArrayGetInt(swgbAirKeys, slot);
        if (key == unit) return(slot);
        if (key < 0) freeSlot = slot;
    }
    if (freeSlot < 0) {
        freeSlot = xsArrayGetSize(swgbAirKeys);
        xsArrayResizeInt(swgbAirKeys, freeSlot + 1);
        xsArrayResizeFloat(swgbAirRemainders, freeSlot + 1);
    }
    xsArraySetInt(swgbAirKeys, freeSlot, unit);
    xsArraySetFloat(swgbAirRemainders, freeSlot, 0.0);
    return(freeSlot);
}

void swgbRepairAircraft(int unit = -1, float elapsed = 1.0) {
    if (xsDoesUnitExist(unit) == false) return;
    if (swgbAstromechEligible(xsGetUnitCopyId(unit)) == false) return;
    float health = xsGetUnitHitpoints(unit);
    float maximum = xsGetUnitAttribute(unit, cHitpoints);
    if (health < 1.0 || health >= maximum) return;
    int slot = swgbAirTimerSlot(unit);
    float remainder = xsArrayGetFloat(swgbAirRemainders, slot) + elapsed;
    // Source interval is two seconds, one HP per completed interval.
    while (remainder >= 2.0 && health < maximum) {
        remainder = remainder - 2.0;
        health = health + 1.0;
    }
    if (health > maximum) health = maximum;
    xsArraySetFloat(swgbAirRemainders, slot, remainder);
    xsSetUnitHitpoints(unit, health);
}

rule swgbAstromechTick
active
minInterval 1
maxInterval 1
{
    int now = xsGetGameTime();
    if (swgbAirLastSecond < 0) { swgbAirLastSecond = now; return; }
    if (now <= swgbAirLastSecond) return;
    float elapsed = now - swgbAirLastSecond;
    swgbAirLastSecond = now;
    // Reuse dead-unit slots so storage follows peak live aircraft, not total deaths.
    for (slot = 0; < xsArrayGetSize(swgbAirKeys)) {
        int unit = xsArrayGetInt(swgbAirKeys, slot);
        if (unit >= 0) {
            if (xsDoesUnitExist(unit) == false) xsArraySetInt(swgbAirKeys, slot, -1);
        }
    }
    int lastPlayer = xsGetNumPlayers();
    if (lastPlayer > 8) lastPlayer = 8;
    for (player = 1; <= lastPlayer) {
        if (xsGetPlayerInGame(player)) {
            if (xsPlayerAttribute(player, 2212) > 0.0) {
                // Commanded aircraft use military classes after the flight
                // crash repair. Explicit IDs exclude ordinary troops/ships.
                for (query = 0; < 3) {
                    int category = 913;
                    if (query == 1) category = 900;
                    if (query == 2) category = 920;
                    swgbAirQuery = xsGetPlayerUnitIds(player, category, swgbAirQuery);
                    if (swgbAirQuery >= 0) {
                        for (index = 0; < xsArrayGetSize(swgbAirQuery)) {
                            swgbRepairAircraft(xsArrayGetInt(swgbAirQuery, index), elapsed);
                        }
                    }
                }
            }
        }
    }
}

// Source nursery adapter. Experimental: requires current DE unit-query APIs.
// Source 0x55537e uses integer elapsed milliseconds / 1000 as a one-second gate.
// Source 0x555509 credits master work_rate once per class-1 animal inside.
// Power changes work_rate2; it does not scale this source food calculation.
int swgbHerdArray = -1;
int swgbNurseryLastSecond = -1;

bool swgbIsNursery(int id = -1) {
    return(id == 319 || id == 320 || id == 321 || id == 322 || id == 3550 || id == 3551 || id == 3552 || id == 3553);
}

float swgbNurseryRate(int player = 1) {
    float rate = 0.13;
    if (xsGetTechState(82, player) == 3) rate = rate * 1.17;
    if (xsGetTechState(83, player) == 3) rate = rate * 1.33333;
    if (xsGetTechState(127, player) == 3) rate = rate * 1.5;
    if (xsGetTechState(571, player) == 3) rate = rate * 1.1;
    return(rate);
}

rule swgbNurseryTick
active
minInterval 1
maxInterval 1
{
    int now = xsGetGameTime();
    if (swgbNurseryLastSecond < 0) {
        swgbNurseryLastSecond = now;
        return;
    }
    if (now <= swgbNurseryLastSecond) return;
    float elapsed = now - swgbNurseryLastSecond;
    swgbNurseryLastSecond = now;
    // Reuse one array; no array is allocated per animal or per tick.
    int lastPlayer = xsGetNumPlayers();
    if (lastPlayer > 8) lastPlayer = 8;
    for (player = 1; <= lastPlayer) {
        swgbHerdArray = xsGetPlayerUnitIds(player, 958, swgbHerdArray);
        if (swgbHerdArray >= 0) {
            for (index = 0; < xsArrayGetSize(swgbHerdArray)) {
                int animal = xsArrayGetInt(swgbHerdArray, index);
                int building = xsGetGarrisonedInUnitId(animal);
                if (building >= 0) {
                    if (xsDoesUnitExist(building)) {
                        if (swgbIsNursery(xsGetUnitCopyId(building))) {
                            int owner = xsGetUnitOwner(building);
                            // Income belongs to the building owner, including allied livestock.
                            if (owner > 0) {
                                if (xsGetPlayerInGame(owner)) {
                                    xsEffectAmount(cModResource, cAttributeFood, cAddAttribute,
                                                   swgbNurseryRate(owner) * elapsed, owner);
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

void main() {
    swgbAirQuery = xsArrayCreateInt(1, -1, "swgb air query");
    swgbAirKeys = xsArrayCreateInt(1, -1, "swgb air timer keys");
    swgbAirRemainders = xsArrayCreateFloat(1, 0.0, "swgb air timers");
    swgbAirLastSecond = xsGetGameTime();
    swgbHerdArray = xsArrayCreateInt(1, -1, "swgb herd query");
    swgbNurseryLastSecond = xsGetGameTime();
}
