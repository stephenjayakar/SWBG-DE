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
