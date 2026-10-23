// Development-only source soldier eligibility. Include attack catalog/base first.
// Compare against an unrounded float32 range + exact small buffer. Keep the
// residual so a boundary cannot flip when XS rounds the addition to float32.
int classicAttackRangeCompare(float distance = 0.0, float weaponRange = 0.0,
                             float buffer = 0.0) {
    float threshold = weaponRange + buffer;
    float b = threshold - weaponRange;
    float tail = (weaponRange - (threshold - b)) + (buffer - b);
    if (distance > threshold) return (1);
    if (distance < threshold) return (-1);
    if (distance == threshold) {
        if (tail < 0.0) return (1);
        if (tail > 0.0) return (-1);
        return (0);
    }
    return (2); // unordered
}

// XS permits at most twelve parameters. Supply the motion observation directly
// before every soldier query in the same synchronous pass. This scratch value
// is not a retained per-unit or per-player observation.
bool classicAttackSoldierMotionAllowed = false;
void classicAttackSoldierSetMotion(int stance = 0, int lastAction = 600, int currentOrder = 0,
                                  float weaponRange = 4.0, float stateDistance = 4.0,
                                  int onPatrol = 0, int hasPatrol = 0,
                                  float highestPathDistance = 4.0, float patrolPathDistance = 4.0,
                                  int targetOwner = 2) {
    classicAttackSoldierMotionAllowed = false;
    if (stance == 3 && lastAction != 600) return;
    if (stance == 2 && currentOrder != 701) {
        float buffer = 0.5;
        if (targetOwner == 0) buffer = 2.0;
        if (classicAttackRangeCompare(stateDistance,weaponRange,buffer) == 1) return;
    }
    if (stance == 1) {
        float distance = stateDistance;
        if ((currentOrder == 711 || currentOrder == 733) && onPatrol == 1) distance = highestPathDistance;
        else if (hasPatrol == 1) distance = patrolPathDistance;
        int comparison = classicAttackRangeCompare(distance,weaponRange,5.0);
        if (comparison > 0) return;
    }
    classicAttackSoldierMotionAllowed = true;
}

bool classicAttackSoldier(int attackerClass = -1, int attackerID = -1,
                          int targetClass = -1, int targetID = -1,
                          bool invisible = false, float resource31 = 0.0,
                          bool targetPresent = true, int ownerID = 1,
                          int targetOwner = 2, int targetType = 70,
                          int targetFlag = 0, int actionType = -1) {
    if (targetPresent == false || ownerID == 0) return (false);
    if (targetOwner == 0 && targetClass != 4 && targetClass != 60 && targetClass != 5) return (false);
    if (attackerClass == 34) return (false);
    if ((attackerClass == 36 || attackerID == 109) && (actionType == 124 || actionType == 125)) return (false);
    if (targetClass == 21 || targetClass == 28 || (targetType == 80 && targetFlag != 0)) return (false);
    if (classicAttackSoldierMotionAllowed == false) return (false);
    return (classicAttackBase(attackerClass,attackerID,targetClass,targetID,invisible,resource31));
}

// TribePriestUnitAIModule::canAttackUnit, 0x5B4B60. Uses the same freshly set
// motion observation but replaces the soldier-specific actions/class checks
// with the source held-attribute 57 exclusion. Conversion is a separate call.
bool classicAttackPriest(int attackerClass = -1, int attackerID = -1,
                         int targetClass = -1, int targetID = -1,
                         bool invisible = false, float resource31 = 0.0,
                         bool targetPresent = true, int ownerID = 1,
                         int targetOwner = 2, int targetType = 70,
                         int targetFlag = 0, int heldAttribute = 0) {
    if (targetPresent == false || ownerID == 0) return (false);
    if (targetOwner == 0 && targetClass != 4 && targetClass != 60 && targetClass != 5) return (false);
    if (heldAttribute == 57 || targetClass == 21 || targetClass == 28) return (false);
    if (targetType == 80 && targetFlag != 0) return (false);
    if (classicAttackSoldierMotionAllowed == false) return (false);
    return (classicAttackBase(attackerClass,attackerID,targetClass,targetID,invisible,resource31));
}

// Source siege state observation, supplied immediately before its gate.
int classicAttackSiegeOwnState = 0;
int classicAttackSiegeComputer = 0;
void classicAttackSiegeSetState(int ownState = 0, int computerPlayer = 0) {
    classicAttackSiegeOwnState = ownState;
    classicAttackSiegeComputer = computerPlayer;
}

// TribeSiegeUnitAIModule::canAttackUnit, 0x5B8180.
bool classicAttackSiege(int attackerClass = -1, int attackerID = -1,
                        int targetClass = -1, int targetID = -1,
                        bool invisible = false, float resource31 = 0.0,
                        bool targetPresent = true, int ownerID = 1,
                        int targetOwner = 2, int targetType = 70,
                        int targetFlag = 0, int actionType = -1) {
    if (targetPresent == false || targetClass == 21 || targetClass == 28) return (false);
    if (classicAttackSoldierMotionAllowed == false || ownerID == 0) return (false);
    if ((targetType == 80 && targetFlag != 0) || classicAttackSiegeOwnState < 2) return (false);
    if (attackerClass == 34 && classicAttackSiegeComputer == 0) return (false);
    if (actionType == 124 || actionType == 125) return (false);
    bool buildingClass = targetClass == 18 || targetClass == 6 || targetClass == 8 ||
                         targetClass == 7 || targetClass == 9 || targetClass == 10;
    // This source shortcut deliberately bypasses the base invisibility/ID gate.
    if (attackerClass == 35) return (buildingClass);
    if ((attackerClass == 34 || attackerClass == 36) && buildingClass == false &&
        targetClass != 34 && targetClass != 36) return (false);
    return (classicAttackBase(attackerClass,attackerID,targetClass,targetID,invisible,resource31));
}
