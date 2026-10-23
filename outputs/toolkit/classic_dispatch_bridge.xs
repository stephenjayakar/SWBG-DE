// Development-only DE observation/stop bridge. No active rule invokes this.
// Caller owns source-ordered ground/boat/air ID arrays and initializes groups.
// One complete observation + stop pass must finish before another can begin.
// Requires identity adapter and all classic_attack_dispatch.xs dependencies.
// Goals: 104 player; 112 observed unit; 113 zone; 114 successful observation;
// 115 stop unit; 116/117 stop point; 118 observed stop-unit owner.
int classicBridgePlayer = 0;
int classicBridgeGround = -1;
int classicBridgeBoats = -1;
int classicBridgeAir = -1;
int classicBridgeGroundPercent = 0;
int classicBridgeBoatPercent = 0;
int classicBridgeAirPercent = 0;
int classicBridgeDifficulty = 1;
float classicBridgeRadius = 20.0;
int classicBridgeTime = 0;
int classicBridgeDomain = 0;
int classicBridgeCursor = 0;
int classicBridgeStopCursor = 0;
int classicBridgePending = -1;
int classicBridgeRejected = 0;
bool classicBridgeBusy = false;

bool classicBridgeBegin(int player = 1, int ground = -1, int boats = -1, int air = -1,
    int groundPercent = 0, int boatPercent = 0, int airPercent = 0,
    int difficulty = 1, float radius = 20.0, int now = 0) {
    if (classicBridgeBusy || player < 1 || player > 8 || xsGetGoal(104) != player) return(false);
    classicBridgePlayer = player;
    classicBridgeGround = ground;
    classicBridgeBoats = boats;
    classicBridgeAir = air;
    classicBridgeGroundPercent = groundPercent;
    classicBridgeBoatPercent = boatPercent;
    classicBridgeAirPercent = airPercent;
    classicBridgeDifficulty = difficulty;
    classicBridgeRadius = radius;
    classicBridgeTime = now;
    classicBridgeDomain = 0;
    classicBridgeCursor = 0;
    classicBridgeStopCursor = 0;
    classicBridgePending = -1;
    classicBridgeRejected = 0;
    classicBridgeBusy = true;
    classicDispatchBegin();
    classicDispatchPoolBegin();
    return(true);
}

void swgbClassicDispatchObserveNext() {
    xsSetGoal(112, -1);
    xsSetGoal(113, -1);
    xsSetGoal(114, 0);
    if (classicBridgeBusy == false || xsGetGoal(104) != classicBridgePlayer) return;
    // A failed target lookup cannot reuse a preceding unit's zone.
    if (classicBridgePending >= 0) classicBridgeRejected++;
    classicBridgePending = -1;
    for (pass = 0; < 3) {
        if (classicBridgeDomain >= 3) return;
        int pool = classicBridgeGround;
        int kind = 100;
        int percentage = classicBridgeGroundPercent;
        if (classicBridgeDomain == 1) {
            pool = classicBridgeBoats;
            kind = 102;
            percentage = classicBridgeBoatPercent;
        }
        if (classicBridgeDomain == 2) {
            pool = classicBridgeAir;
            kind = 108;
            percentage = classicBridgeAirPercent;
        }
        int size = 0;
        if (pool >= 0 && percentage > 0) size = xsArrayGetSize(pool);
        int start = classicBridgeCursor;
        for (i = start; < size) {
            classicBridgeCursor = i + 1;
            int unit = xsArrayGetInt(pool, i);
            if (xsDoesUnitExist(unit) == false) {
                // Preserve the source naval stale-ID behavior.
                if (classicBridgeDomain == 1) classicDispatchBoatCandidate(classicBridgePlayer, unit, false);
            } else {
                if (xsGetUnitOwner(unit) == classicBridgePlayer && classicSourceUnitClass(unit) >= 0) {
                    classicBridgePending = unit;
                    xsSetGoal(112, unit);
                    return;
                }
                classicBridgeRejected++;
            }
        }
        classicDispatchPoolFinish(classicBridgePlayer, kind, percentage,
            classicBridgeDifficulty, classicBridgeRadius, classicBridgeTime);
        classicBridgeDomain++;
        classicBridgeCursor = 0;
        classicDispatchPoolBegin();
    }
}

void swgbClassicDispatchObserveCommit() {
    if (classicBridgeBusy == false || xsGetGoal(104) != classicBridgePlayer ||
        classicBridgePending < 0 || xsGetGoal(112) != classicBridgePending || xsGetGoal(114) != 1) return;
    int unit = classicBridgePending;
    classicBridgePending = -1;
    if (xsDoesUnitExist(unit) == false) {
        if (classicBridgeDomain == 1) classicDispatchBoatCandidate(classicBridgePlayer, unit, false);
        return;
    }
    if (xsGetUnitOwner(unit) != classicBridgePlayer) {
        classicBridgeRejected++;
        return;
    }
    int sourceClass = classicSourceUnitClass(unit);
    if (sourceClass < 0) {
        classicBridgeRejected++;
        return;
    }
    vector position = xsGetUnitPosition(unit);
    int zone = xsGetGoal(113);
    if (classicBridgeDomain == 1)
        classicDispatchBoatCandidate(classicBridgePlayer, unit, true, position, zone);
    else
        classicDispatchCandidate(classicBridgePlayer, unit, classicBridgeDomain == 2,
            true, sourceClass, classicBridgeDifficulty, position, zone);
}

void swgbClassicDispatchStopNext() {
    xsSetGoal(115, -1);
    xsSetGoal(116, -1);
    xsSetGoal(117, -1);
    xsSetGoal(118, -1);
    if (classicBridgeBusy == false || classicBridgeDomain < 3 ||
        xsGetGoal(104) != classicBridgePlayer) return;
    int start = classicBridgeStopCursor;
    for (i = start; < classicDispatchStopCount) {
        classicBridgeStopCursor = i + 1;
        int unit = xsArrayGetInt(classicDispatchStops, i);
        if (xsDoesUnitExist(unit)) {
            if (xsGetUnitOwner(unit) == classicBridgePlayer) {
                vector position = xsGetUnitPosition(unit);
                xsSetGoal(115, unit);
                xsSetGoal(116, 0 - xsCeilToInt(0.0 - xsVectorGetX(position)));
                xsSetGoal(117, 0 - xsCeilToInt(0.0 - xsVectorGetY(position)));
                return;
            }
        }
        classicBridgeRejected++;
    }
    classicBridgeBusy = false;
}
