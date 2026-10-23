// Development-only UnitAIModule::canAttackUnit, source 0x41C530.
// Include generated classic_attack_catalog.xs first. Specialized UnitAI
// wrappers and actual target invisibility/player-resource queries are separate.
bool classicAttackBase(int attackerClass = -1, int attackerID = -1,
                       int targetClass = -1, int targetID = -1,
                       bool invisible = false, float resource31 = 0.0) {
    if (invisible || attackerClass == 4 || targetID == 696 ||
        targetClass == 21 || targetClass == 28) return (false);
    if (classicAttackGroundToAir(attackerID)) return (true);
    if (resource31 > 0.0 && (attackerID == 500 || attackerID == 603)) return (true);
    if (attackerClass == 48 || attackerClass == 57 || attackerClass == 62 ||
        attackerClass == 63 || attackerClass == 64) return (true);
    bool airTarget = targetClass == 43 || targetClass == 48 || targetClass == 59 ||
                     targetClass == 62 || targetClass == 63 || targetClass == 64;
    if (attackerClass == 9 || attackerClass == 16 || attackerClass == 33 ||
        attackerClass == 40 || attackerClass == 55) return (airTarget);
    bool groundOnly = attackerClass == 5 || attackerClass == 6 || attackerClass == 7 ||
        attackerClass == 8 || attackerClass == 10 || attackerClass == 11 ||
        attackerClass == 13 || attackerClass == 15 || attackerClass == 18 ||
        attackerClass == 32 || attackerClass == 34 || attackerClass == 35 ||
        attackerClass == 36 || attackerClass == 37 || attackerClass == 38 ||
        attackerClass == 39 || attackerClass == 43 || attackerClass == 44 ||
        attackerClass == 47 || attackerClass == 49 || attackerClass == 50 ||
        attackerClass == 51 || attackerClass == 52 || attackerClass == 53 ||
        attackerClass == 56 || attackerClass == 58 || attackerClass == 60;
    return (groundOnly && airTarget == false);
}

// TribeTowerUnitAIModule::canAttackUnit, source 0x5B7CD0.
bool classicAttackTower(int attackerClass = -1, int attackerID = -1,
                        int targetClass = -1, int targetID = -1,
                        bool invisible = false, float resource31 = 0.0,
                        bool targetPresent = true, int ownerID = 1,
                        int targetOwner = 2, int targetType = 70,
                        int targetFlag = 0, int ownState = 2) {
    if (targetPresent == false || ownerID == 0 || targetClass == 21 || targetClass == 28) return (false);
    if (targetOwner == 0 && targetClass != 4 && targetClass != 60 && targetClass != 5) return (false);
    if (targetType == 80 && targetFlag != 0) return (false);
    if (targetID == 50 || ownState < 2) return (false);
    if (targetClass == 5 && attackerClass != 9) return (true);
    return (classicAttackBase(attackerClass,attackerID,targetClass,targetID,invisible,resource31));
}

// TribeBuildingUnitAIModule::canAttackUnit, source 0x5B8A90: unconditional delegate.
bool classicAttackBuilding(int attackerClass = -1, int attackerID = -1,
                           int targetClass = -1, int targetID = -1,
                           bool invisible = false, float resource31 = 0.0) {
    return (classicAttackBase(attackerClass,attackerID,targetClass,targetID,invisible,resource31));
}

// Civilian (0x5B2F80) and lion (0x5B28F0) guard null before the base predicate.
// The civilian's redundant target class exclusions are already in the base.
bool classicAttackNullable(int attackerClass = -1, int attackerID = -1,
                           int targetClass = -1, int targetID = -1,
                           bool invisible = false, float resource31 = 0.0,
                           bool targetPresent = true) {
    if (targetPresent == false) return (false);
    return (classicAttackBase(attackerClass,attackerID,targetClass,targetID,invisible,resource31));
}

// Medic canAttackUnit and several neutrality slots point to this source result.
bool classicAttackNever() {
    return (false);
}

// Gate kinds: 0 unrestricted base, 1 soldier/tower, 2 priest, 3 siege,
// 4 never (civilian/medic/building). Not the combat-pipeline role enumeration.
bool classicAttackNeutral(int kind = 4, int targetClass = -1) {
    if (kind == 0) return (true);
    if (kind == 4) return (false);
    if (targetClass == 18 || targetClass == 6 || targetClass == 8 || targetClass == 7 ||
        targetClass == 58 || targetClass == 14 || targetClass == 12 || targetClass == 17 || targetClass == 2) return (false);
    if ((kind == 1 || kind == 2) && targetClass == 45) return (false);
    if ((kind == 1 || kind == 3) && targetClass == 59) return (false);
    return (true);
}
